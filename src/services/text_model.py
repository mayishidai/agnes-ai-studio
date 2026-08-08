"""
文本模型调用与 Prompt 模板模块
包含：call_text_model、JSON 解析、剧本/分镜/素材提示词模板、视频 prompt 构建
"""

import json
import time
import requests
from ..config import get_text_base_url, get_vendor_base_url
from ..models import DEFAULT_TEXT_MODEL


def call_text_model(system_prompt, user_prompt, api_key, model=None, max_tokens=4096):
    """调用文本模型 (OpenAI chat completions 兼容接口)
    
    Args:
        model: 模型名称，默认使用 DEFAULT_TEXT_MODEL
        api_key: 对应厂商的 API Key
    """
    if model is None:
        model = DEFAULT_TEXT_MODEL
    base_url = get_text_base_url(model)
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'max_tokens': max_tokens,
        'temperature': 0.7
    }
    print(f"[文本模型] model={model}, base_url={base_url}")
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=300
            )
            # 检查 Content-Type，避免 HTML 错误页被当作 JSON 解析
            content_type = resp.headers.get('Content-Type', '')
            if resp.status_code == 200:
                if 'application/json' not in content_type:
                    # 200 但返回了非 JSON 内容（如 HTML 错误页）
                    if attempt < max_retries:
                        wait_sec = 10 * (attempt + 1)
                        print(f"[文本模型] 响应非 JSON ({content_type})，{wait_sec}秒后重试 ({attempt+1}/{max_retries})...")
                        time.sleep(wait_sec)
                        continue
                    raise Exception(f"文本模型 API 返回非 JSON 响应 (Content-Type: {content_type}): {resp.text[:300]}")
                result = resp.json()
                content = result['choices'][0]['message']['content']
                return content
            elif resp.status_code in (502, 503, 504, 433) and attempt < max_retries:
                wait_sec = 10 * (attempt + 1)
                print(f"[文本模型] 网关错误 {resp.status_code}，{wait_sec}秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            else:
                raise Exception(f"文本模型 API 错误 ({resp.status_code}): {resp.text[:500]}")
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_sec = 10 * (attempt + 1)
                print(f"[文本模型] 请求超时，{wait_sec}秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            raise Exception("文本模型 API 请求超时（已重试3次）")
        except requests.exceptions.ConnectionError as conn_err:
            if attempt < max_retries:
                wait_sec = 10 * (attempt + 1)
                print(f"[文本模型] 连接错误，{wait_sec}秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            raise Exception(f"文本模型 API 连接失败: {conn_err}")
        except json.JSONDecodeError as json_err:
            if attempt < max_retries:
                wait_sec = 10 * (attempt + 1)
                print(f"[文本模型] JSON 解析失败，{wait_sec}秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            raise Exception(f"文本模型 API 返回非 JSON 响应: {json_err}")


def parse_json_from_text(text):
    """从文本模型响应中解析 JSON（兼容 markdown 代码块包裹，支持截断修复）"""
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith('```'):
                end = i
                break
        text = '\n'.join(lines[start:end]).strip()
    # 第一次尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 第二次尝试：修复截断的 JSON（未闭合的字符串和括号）
    repaired = _repair_truncated_json(text)
    if repaired is not None:
        return repaired
    raise ValueError(f"JSON 解析失败，响应长度 {len(text)} 字符，前 200 字符: {text[:200]}")


def _repair_truncated_json(text):
    """尝试修复被截断的 JSON（模型输出被 max_tokens 截断时）"""
    # 策略：逐字符解析，跟踪括号栈，在截断处尝试闭合
    stack = []  # 存储未闭合的括号: '{' 或 '['
    in_string = False
    escape_next = False
    last_complete_pos = -1  # 最后一个完整值的位置
    i = 0
    
    while i < len(text):
        ch = text[i]
        
        if escape_next:
            escape_next = False
            i += 1
            continue
            
        if ch == '\\' and in_string:
            escape_next = True
            i += 1
            continue
            
        if ch == '"':
            in_string = not in_string
            if not in_string:
                # 字符串结束，检查是否是一个完整值
                # 向后看，跳过空白后应该是 , } ] 之一
                j = i + 1
                while j < len(text) and text[j] in ' \t\n\r':
                    j += 1
                if j < len(text) and text[j] in ',}]':
                    last_complete_pos = j
            i += 1
            continue
            
        if in_string:
            i += 1
            continue
            
        # 不在字符串内
        if ch in '{[':
            stack.append(ch)
            i += 1
            continue
        elif ch in '}]':
            if stack:
                stack.pop()
            i += 1
            continue
        elif ch == ',':
            # 逗号分隔符，前一个值完成
            last_complete_pos = i
            i += 1
            continue
        else:
            i += 1
            continue
    
    # 到达末尾，JSON 被截断
    # 尝试从最后完成的位置截断并闭合
    if last_complete_pos > 0:
        candidate = text[:last_complete_pos + 1]
        # 确保末尾是 } ] 或 , 之一
        while candidate and candidate[-1] in ' \t\n\r':
            candidate = candidate[:-1]
        if candidate and candidate[-1] == ',':
            candidate = candidate[:-1]
        # 闭合所有未闭合的括号
        # 重新计算未闭合的括号
        open_braces = 0
        open_brackets = 0
        in_str = False
        esc = False
        for c in candidate:
            if esc:
                esc = False
                continue
            if c == '\\' and in_str:
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if not in_str:
                if c == '{': open_braces += 1
                elif c == '}': open_braces -= 1
                elif c == '[': open_brackets += 1
                elif c == ']': open_brackets -= 1
        candidate += '}' * max(0, open_braces) + ']' * max(0, open_brackets)
        try:
            result = json.loads(candidate)
            print(f"[JSON修复] 截断的 JSON 已自动修复（保留到位置 {last_complete_pos}）")
            return result
        except json.JSONDecodeError:
            pass
    
    # 如果上面的方法失败，尝试更激进的方法：直接在末尾闭合
    # 先尝试关闭当前字符串
    candidate = text
    if in_string:
        candidate += '"'
    # 闭合所有括号
    open_braces = 0
    open_brackets = 0
    in_str = False
    esc = False
    for c in candidate:
        if esc:
            esc = False
            continue
        if c == '\\' and in_str:
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if not in_str:
            if c == '{': open_braces += 1
            elif c == '}': open_braces -= 1
            elif c == '[': open_brackets += 1
            elif c == ']': open_brackets -= 1
    candidate += '}' * max(0, open_braces) + ']' * max(0, open_brackets)
    try:
        result = json.loads(candidate)
        print(f"[JSON修复] 截断的 JSON 已激进修复")
        return result
    except json.JSONDecodeError:
        pass
    
    return None


# ---------- 短剧 Prompt 模板 ----------

def story_system_prompt():
    return """你是一位才华横溢的短剧作家，擅长将简单的描述转化为引人入胜的故事。
根据用户提供的描述，创作一个 300～500 字的故事梗概。

要求：
1. 字数严格控制在 300～500 字之间
2. 故事要有完整的起承转合，情节紧凑、节奏明快
3. 主角可以是人、动物、植物、非生物或任何虚构实体，请准确理解用户描述的主体，赋予其鲜明的个性和情感
4. 场景描写要具有画面感，便于后续转化为分镜
5. 包含核心冲突和高潮，结尾有余韵或反转
6. 直接输出故事正文，不要标题、不要任何额外说明文字"""


def script_system_prompt():
    return """你是一位专业的短剧编剧，擅长将故事改编为拍摄剧本。
请将下面提供的故事内容，1:1 精准还原为专业短剧剧本。

【重要：角色类型识别】
- 故事中的主角/角色可能是人、动物、植物、非生物（如石头、水滴、星星）或任何虚构实体
- 你必须准确理解每个角色的本质类型，不要将所有角色默认为人类
- 对于非人类角色，要保留其原始特征（如材质、形态、颜色、大小），不要强行赋予人类外观
- 非人类角色的「台词」和「情感」通过拟人化方式呈现，但外观描述必须符合其本质

【格式规范】
1. 每场戏以编号开头，格式：「编号 日/夜、内/外、场景名」
   - 日/夜：标明白天或夜晚
   - 内/外：标明室内或室外
2. 紧接列出该场出场角色，格式：「角色：角色A、角色B…」
   - 人类角色可标注年龄，如「小明（25岁）」
   - 非人类角色标注其本质类型和关键特征，如「小树苗（嫩绿色，约30厘米高）」、「老石头（灰色，表面粗糙）」
3. 画面描述用「▲」符号开头，描述要尽可能详细、具有画面感
4. 特写镜头必须在画面描述中明确标注，如：「▲面部特写：…」或「▲（特写）…」
5. 角色旁白/内心独白用「角色名vo：…」格式
6. 角色对话用「角色名（情绪/动作）：台词内容」格式
7. 有 vo 的台词，必须搭配相应的画面描述
8. 需要额外搭配画面时，用「搭配画面：…」补充说明
9. 字幕用「【出字幕：内容】」格式
10. 每个角色在首次出场时要详细描述其外观特征：
    - 人类角色：发型、服饰、肤色、体态等
    - 动物角色：物种、毛色、体型、特殊标记等
    - 植物角色：种类、颜色、大小、形态、生长状态等
    - 非生物角色：材质、颜色、形状、大小、表面质感等

【内容要求】
- 故事中的每个情节、每句台词都要还原，不遗漏、不删减
- 画面描述要详细，让导演和摄影师能直接据此拍摄
- 情绪、动作、镜头运动都要写清楚
- 直接输出剧本文本，不要包含任何额外说明或解释"""


def storyboard_system_prompt(shot_duration):
    return f"""你是一位专业的分镜师。将短剧剧本改写为分镜脚本。
要求：
1. 每个分镜时长约 {shot_duration} 秒
2. 每个分镜需要详细描述画面内容
3. 包含镜头类型（特写/中景/远景/跟拍等）
4. 必须严格输出 JSON 格式
5. 英文 prompt 必须避免任何暴力、血腥、武器、色情、政治敏感等内容，确保符合AI视频生成平台的内容安全策略
6. 动作场景用温和的方式表达，例如用“追逐”代替“打斗”，用“对话”代替“争吵”
7. 【重要】每个分镜的 prompt_en 中必须包含该镜头中所有角色的完整外观描述，确保不同分镜中同一角色的外观保持一致
8. 角色外观描述要具体、固定。注意角色可能是人、动物、植物或非生物：
   - 人类角色：发型、发色、服装、肤色等，如 "a young woman with long black hair, wearing a white dress"
   - 动物角色：物种、毛色、体型等，如 "a small orange cat with white paws"
   - 植物角色：种类、颜色、形态等，如 "a tall green bamboo with slender leaves"
   - 非生物角色：材质、颜色、形状等，如 "a smooth grey stone with a round shape"
9. 【重要】如果分镜中有对话或文字内容（如字幕、标牌、屏幕文字等），必须使用中文
10. 【重要】画面描述应该是自然场景，不要出现角色设定图、三视图、设计板等元素
11. 【重要】prompt_en 中如果有对话或字幕，必须明确写明 "Chinese subtitle" 或 "speak in Chinese"，确保视频生成模型知道要显示中文

输出 JSON 格式：
{{
  "shots": [
    {{
      "shot_index": 1,
      "scene_desc": "画面描述",
      "characters": ["角色名"],
      "action": "动作描述",
      "camera": "镜头类型",
      "dialogue": "中文对话内容（如有）",
      "prompt_en": "Detailed English prompt for AI video generation, MUST include full appearance details for every character in this shot. Describe each character according to its type (human/animal/plant/object). Natural scene only, NO design sheet or three-view layout."
    }}
  ]
}}"""


def assets_system_prompt():
    return """请严格按照以下要求执行：

1. 首先仔细通读并深度理解输入的全部文本内容；

2. 从文本中精准提取角色、场景、道具三类画面提示词，全程固定纯白色纯色背景，不添加任何背景元素；

3. 【角色提取强制要求】需完整拆解并提取每一位角色的全套细节。注意角色可能是不同类型，请按其本质提取：
   - 人类角色：年龄特征、外貌特征（五官、脸型、肤色、神态、身材体态）、发型细节（款式、发色、发长、发饰）、服饰全套细节（形制、款式、颜色、面料、纹样、配饰、鞋履等）
   - 动物角色：物种、毛色/羽色、体型大小、身体比例、特殊标记（如斑点、条纹）、眼睛颜色、耳朵形状、尾巴形态等
   - 植物角色：植物种类、整体颜色、大小尺寸、形态特征（叶片形状、花瓣数量、枝干粗细）、生长状态（茂盛、蓑萎、开花、结果）、表面质感等
   - 非生物角色：材质（金属、石头、布料、水滴等）、颜色、形状、大小尺寸、表面质感（光滑、粗糙、透明）、特殊特征等

4. 【场景提取要求】仅提取文本中明确提及的场景核心元素，场景描述词；

5. 【道具提取要求】精准提取文本中出现的所有手持/摆放/随身道具，包含道具样式、材质、颜色、细节特征；

6. 输出格式清晰分类：分「角色画面提示词」「场景画面提示词」「道具画面提示词」三大板块，角色需按单人逐条拆分，细节完整不遗漏、不篡改、不脑补文本外信息，语言为精准画面描述词，适配AIGC生成逻辑。

必须严格输出 JSON 格式：
{  "characters": [{"name": "角色名", "desc": "详细的中文视觉特征描述，根据角色类型包含相应的外观细节，纯白色背景", "prompt_en": "Detailed English visual description for AI image generation, white background, character design sheet, three views"}],
  "scenes": [{"name": "场景名", "desc": "详细的中文场景视觉描述，纯白色背景", "prompt_en": "Detailed English scene visual description for AI image generation, white background"}],
  "props": [{"name": "道具名", "desc": "详细的中文道具视觉描述，包含样式、材质、颜色、细节特征，纯白色背景", "prompt_en": "Detailed English prop visual description for AI image generation, including style, material, color, details, white background"}]
}

注意：
- 每个角色必须单独拆分，不要合并
- `desc` 字段必须用中文描述，方便用户阅读和编辑
- `prompt_en` 字段必须用英文描述，适合AI图像生成
- 每个 prompt_en 末尾加上 "white background, character design sheet, three views"
- 不要遗漏任何角色、场景或道具"""


# 内容安全敏感词列表（用于图片/视频 prompt 清洗）
_CONTENT_POLICY_WORDS = [
    'violence', 'violent', 'bloody', 'blood', 'gore', 'murder', 'kill', 'killing',
    'weapon', 'gun', 'knife', 'sword', 'bomb', 'explosion', 'shoot', 'shooting',
    'nude', 'naked', 'sexual', 'porn', 'erotic', 'drug', 'alcohol abuse',
    'torture', 'suicide', 'self-harm', 'racist', 'discrimination',
    'wound', 'wounded', 'bleeding', 'corpse', 'death', 'dead body',
    'abuse', 'assault', 'battle', 'war', 'fight', 'fighting',
    '暴力', '血腥', '杀戮', '武器', '枪支', '色情', '毒品',
    '流血', '尸体', '撕咬', '皮开肉绽', '浑身是血', '血泊',
    '撕下一块皮肉', '咬住', '伤口', '鞭打', '虐待',
]


def sanitize_video_prompt(prompt):
    """清洗视频 prompt，移除可能触发内容安全策略的关键词"""
    prompt_lower = prompt.lower()
    cleaned = prompt
    for word in _CONTENT_POLICY_WORDS:
        if word.lower() in prompt_lower:
            cleaned = cleaned.replace(word, '').replace(word.lower(), '').replace(word.title(), '')
    cleaned = ' '.join(cleaned.split())
    return cleaned


def sanitize_image_prompt(prompt):
    """清洗图片 prompt，移除可能触发内容安全策略的关键词"""
    prompt_lower = prompt.lower()
    cleaned = prompt
    for word in _CONTENT_POLICY_WORDS:
        if word.lower() in prompt_lower:
            cleaned = cleaned.replace(word, '').replace(word.lower(), '').replace(word.title(), '')
    # 清理多余空格
    cleaned = ' '.join(cleaned.split())
    return cleaned


def build_video_prompt(shot, shot_assets):
    """根据分镜和参考素材构建视频生成 prompt（强调角色外观一致性）
    
    Returns:
        (english_prompt, chinese_prompt) 元组
    """
    base_prompt = shot.get('prompt_en', '') or shot.get('scene_desc', '')
    scene_desc_cn = shot.get('scene_desc', '')
    
    # 【重要】禁止视频模型生成任何文字/字幕，中文字幕由 ffmpeg 后期烧录
    en_prompt = "No text, no subtitles, no captions, no labels, no written words, no letters, no signs, no watermarks, no typography, no writing of any kind should appear anywhere in the video. Pure cinematic scene only. "
    en_prompt += base_prompt
    
    # 中文提示词（供前端展示）
    cn_prompt = scene_desc_cn or base_prompt
    
    if shot_assets:
        char_descs = []
        scene_descs = []
        prop_descs = []
        char_descs_cn = []
        scene_descs_cn = []
        prop_descs_cn = []
        for a in shot_assets:
            desc = a.get('desc', '')
            desc_cn = a.get('desc_cn', '') or a.get('desc', '')
            if not desc:
                continue
            for term in ['three views', 'three-view', 'character design sheet', 'design board',
                         'front view', 'side view', 'back view', 'orthographic', 'design sheet',
                         'multiple views', 'close-up detail', 'detail showcase']:
                desc = desc.replace(term, '').replace(term.title(), '')
            desc = ' '.join(desc.split())
            if not desc:
                continue
            cat = a.get('category', '')
            name = a.get('name', '')
            if cat == 'characters':
                char_descs.append(f"{name}: {desc}")
                char_descs_cn.append(f"{name}: {desc_cn}")
                # 【面部一致性】强调面部特征
                en_prompt += f" CRUCIAL: The character {name}'s facial features (face shape, eye shape, nose, mouth, skin tone, hair style and color) in the video MUST exactly match the reference image. Do NOT alter or reimagine the character's face."
            elif cat == 'scenes':
                scene_descs.append(desc)
                scene_descs_cn.append(desc_cn)
            elif cat == 'props':
                prop_descs.append(desc)
                prop_descs_cn.append(desc_cn)
        
        consistency_parts = []
        consistency_parts_cn = []
        if char_descs:
            consistency_parts.append("Character appearance (MUST match exactly, especially facial features): " + "; ".join(char_descs))
            consistency_parts_cn.append("角色外观(必须严格一致，尤其是面部特征): " + "; ".join(char_descs_cn))
        if prop_descs:
            consistency_parts.append("Props: " + "; ".join(prop_descs))
            consistency_parts_cn.append("道具: " + "; ".join(prop_descs_cn))
        if scene_descs:
            consistency_parts.append("Scene: " + "; ".join(scene_descs))
            consistency_parts_cn.append("场景: " + "; ".join(scene_descs_cn))
        
        if consistency_parts:
            en_prompt = f"{en_prompt}. {' | '.join(consistency_parts)}. Use reference images ONLY for character appearance consistency, NOT as the starting frame."
            cn_prompt = f"{cn_prompt}. {' | '.join(consistency_parts_cn)}"
    
    en_prompt = f"{en_prompt}. The video MUST begin directly with the described natural cinematic scene. Never show any design sheet, character layout, three-view orthographic, or reference board in the video. Start immediately with the actual story scene."
    en_prompt = sanitize_video_prompt(en_prompt)
    
    return en_prompt, cn_prompt


def is_mostly_chinese(text):
    """检测文本是否主要为中文"""
    if not text:
        return False
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese_chars > len(text) * 0.3


def translate_cn_to_en(text, api_key, model=None):
    """将中文提示词翻译为英文（用于发送给视频模型）"""
    if not text or not is_mostly_chinese(text):
        return text  # 已经是英文，直接返回
    try:
        from ..config import get_vendor_api_key, get_vendor_base_url
        from ..models import DEFAULT_TEXT_MODEL
        model = model or DEFAULT_TEXT_MODEL
        base_url = get_vendor_base_url(model)
        key = api_key or get_vendor_api_key(model)
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a professional translator. Translate the following Chinese video scene description into English. Keep it vivid and cinematic. Output ONLY the English translation, nothing else.'},
                {'role': 'user', 'content': text}
            ],
            'max_tokens': 1024,
            'temperature': 0.3
        }
        import requests
        resp = requests.post(f'{base_url}/chat/completions', headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            translated = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            if translated:
                print(f"[翻译] 中文→英文: {text[:50]}... → {translated[:50]}...")
                return translated
    except Exception as e:
        print(f"[翻译] 翻译失败，使用原文: {e}")
    return text
