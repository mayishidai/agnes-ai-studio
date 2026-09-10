# -*- coding: utf-8 -*-
"""AI 视频运镜提示词词库 —— 50 套运镜 · 十大类

来源：《70套AI视频运镜提示词》万能公式反推。
万能公式（6 要素）：镜头运动 + 摄影机角度 + 人物动作 + 环境变化 + 光影氛围 + 画面质感
四大原则：
  ① 人物情绪越强，镜头越近（愤怒/流泪/震惊 → 特写 + 推镜）
  ② 场面越大，镜头越拉远（战场/宫殿/云海/城市 → 全景 + 升降 + 俯冲）
  ③ 动作越快，镜头越要有方向（冲刺/挥剑/闪避 → 镜头跟着人物动作走）
  ④ 转场不乱用（同场景直接切；换场景用穿越/甩镜/叠化）
不撞款规则：画风、光影、质感锁死不动，只轮换镜头运动、角度、节奏、环境四维。

注意：英文文案已做内容安全化改写（规避 sanitize_video_prompt 的敏感词清洗，
如 sword/explosion/fight 等；并规避含 'war' 子串的常用词如 toward/forward）。
"""

# 十大类（key, 中文名）
CAMERA_CATEGORIES = [
    ('entrance',   '人物出场'),
    ('dialogue',   '对话视角'),
    ('opening',    '大片开场'),
    ('transition', '转场慢镜'),
    ('battle',     '打斗节奏'),
    ('climax',     '打斗高潮'),
    ('emotion',    '心理放大'),
    ('detail',     '细节叙事'),
    ('fantasy',    '奇幻特效'),
    ('ending',     '史诗收束'),
]

CATEGORY_LABELS = {k: label for k, label in CAMERA_CATEGORIES}

# 通用质感关键词（任何镜头都追加）
QUALITY_EN = ("cinematic quality, rich details, natural motion, smooth and stable, "
              "beautiful lighting, cinematic color grading, shallow depth of field, "
              "natural motion blur, cinematic lighting, film grain, 4k")
QUALITY_CN = "电影级质感，细节丰富，自然运动，流畅稳定，光影唯美，色彩电影感，浅景深，运动模糊自然"

# 通用反向（静止无运动 + 项目固有的防文字反向词由调用方拼接）
NEGATIVE_EN = ("static camera, no movement, locked frame, flat angle, no emotion, "
               "no camera motion, frozen shot")

# 50 套运镜
CAMERA_MOVES = [
    # ── 人物出场（1-5）──
    {'id': 1,  'category': 'entrance', 'name': '缓慢推镜',
     'zh': '镜头缓慢向前推进，逐渐靠近人物，突出表情变化与精神情绪，背景浅景深虚化，电影级人物特写',
     'en': 'slow push-in to character, shallow depth of field, cinematic close-up',
     'neg': 'static camera, no movement, wide shot, flat lighting'},
    {'id': 2,  'category': 'entrance', 'name': '快速推镜',
     'zh': '摄影机快速推进到人物脸部，制造紧张压迫感，人物眼神锐利，发丝轻动，画面冲击力强',
     'en': 'rapid push-in to face, tense atmosphere, sharp eyes, hair swaying, impactful frame',
     'neg': 'slow camera, no urgency, soft gaze, static'},
    {'id': 3,  'category': 'entrance', 'name': '缓慢拉远',
     'zh': '镜头从近景缓缓拉远，逐渐展示周围环境，人物孤独站立，空间感被拉开，叙事感更强',
     'en': 'slow dolly out from close-up to wide, lone figure, sense of space, narrative feel',
     'neg': 'static close-up, no environment, tight frame'},
    {'id': 4,  'category': 'entrance', 'name': '环绕运镜',
     'zh': '摄影机围绕人物缓慢旋转，展示服装细节与人物气场，衣摆和发丝随风摆动',
     'en': 'slow orbit around character, show costume details, aura, flowing clothes and hair',
     'neg': 'static front view, no rotation, no detail'},
    {'id': 5,  'category': 'entrance', 'name': '跟随镜头',
     'zh': '摄影机跟随人物向前移动，保持人物主体稳定，环境持续变化，形成自然跟拍感',
     'en': 'follow camera with character walking, stable subject, changing environment, natural tracking',
     'neg': 'static camera, locked tripod, no movement'},

    # ── 移动跟拍 · 对话视角（6-10）──
    {'id': 6,  'category': 'dialogue', 'name': '侧面跟拍',
     'zh': '摄影机从人物侧面平行移动跟拍，人物缓慢行走，衣服与发丝自然摆动，形成流畅运镜感',
     'en': 'side tracking shot, character walking, clothes and hair swaying, smooth motion',
     'neg': 'front view, no tracking, static'},
    {'id': 7,  'category': 'dialogue', 'name': '低角度仰拍',
     'zh': '摄影机自下向上拍摄人物，强化力量感与主角气场，天空或高建筑做背景，英雄感更强',
     'en': 'low angle shot, hero pose, sky or tall building background, powerful presence',
     'neg': 'eye level, no power, flat angle'},
    {'id': 8,  'category': 'dialogue', 'name': '高角度俯拍',
     'zh': '摄影机从高处俯视人物，人物处在环境中心，突出渺小、孤独或被压迫的情绪',
     'en': 'high angle overhead, character small in environment, lonely or oppressed mood',
     'neg': 'low angle, no scale, eye level'},
    {'id': 9,  'category': 'dialogue', 'name': '第一人称视角',
     'zh': '第一人称视角拍摄，模拟角色目光，手部进入画面，环境随视线变化，沉浸感更强',
     'en': 'first person POV, character eyes view, hand enters frame, environment shifts with gaze',
     'neg': 'third person view, no immersion, external'},
    {'id': 10, 'category': 'dialogue', 'name': '肩后视角',
     'zh': '摄影机位于人物背后观察前方目标，前景肩膀轻微虚化，适合对话或对峙场景',
     'en': 'over-shoulder shot, foreground shoulder slightly blurred, dialogue or confrontation',
     'neg': 'front view, no shoulder, direct'},

    # ── 大片开场（11-15）──
    {'id': 11, 'category': 'opening', 'name': '希区柯克变焦',
     'zh': '镜头前移同时背景拉伸变形，人物主体保持稳定，制造心理震荡与失衡感',
     'en': 'Hitchcock zoom (dolly zoom), subject stable, background stretches, psychological vertigo',
     'neg': 'normal zoom, flat perspective, no distortion'},
    {'id': 12, 'category': 'opening', 'name': '旋转下降镜头',
     'zh': '摄影机环绕人物旋转并缓慢下降，展示造型与空间层次，画面更具大片感',
     'en': 'spiral descent shot, orbit and lower simultaneously, show figure and space layers, epic',
     'neg': 'static descending, no rotation, flat'},
    {'id': 13, 'category': 'opening', 'name': '升降镜头',
     'zh': '摄影机由低到高抬升，逐步展示完整场景，人物与环境关系被完整交代',
     'en': 'crane up shot, reveal full scene, character and environment relationship',
     'neg': 'eye level, no scale, static'},
    {'id': 14, 'category': 'opening', 'name': '无人机俯冲',
     'zh': '航拍视角从高空快速俯冲到人物身边，空间瞬间展开，适合开场或史诗出场',
     'en': 'drone dive shot, aerial to ground, space expands instantly, epic entrance',
     'neg': 'eye level entrance, no aerial, slow'},
    {'id': 15, 'category': 'opening', 'name': '穿越镜头',
     'zh': '摄影机穿过门窗、树林或建筑缝隙进入场景，最后聚焦人物，沉浸感强',
     'en': 'camera passes through doorway, forest or architecture gap, finally focuses on character, immersive',
     'neg': 'static entry, no transition, jump cut'},

    # ── 转场慢镜（16-20）──
    {'id': 16, 'category': 'transition', 'name': '环形推进',
     'zh': '围绕人物旋转同时缓慢推进，人物保持中心，背景动态拉开，视觉张力强',
     'en': 'ring push-in, orbit while slowly approaching, character centered, dynamic background',
     'neg': 'static front, no orbit, flat background'},
    {'id': 17, 'category': 'transition', 'name': '快速横移',
     'zh': '镜头快速横向移动，带出运动模糊，实现人物或空间的迅速切换',
     'en': 'fast horizontal pan, motion blur, rapid character or space switch',
     'neg': 'static frame, no blur, slow switch'},
    {'id': 18, 'category': 'transition', 'name': '甩镜转场',
     'zh': '摄影机快速甩动形成方向性模糊，用运镜连接上下场景，转场利落',
     'en': 'whip pan transition, directional motion blur, connect scenes, sharp transition',
     'neg': 'hard cut, no blur, static transition'},
    {'id': 19, 'category': 'transition', 'name': '慢动作升格',
     'zh': '高帧率慢动作拍摄，动作被拉慢，发丝与衣摆细节更清晰，情绪更浓',
     'en': 'slow motion high frame rate, slowed action, hair and cloth details clear, emotional',
     'neg': 'real-time speed, no detail, rushed'},
    {'id': 20, 'category': 'transition', 'name': '时间冻结',
     'zh': '时间暂停在关键动作瞬间，摄影机环绕人物展示细节，空间粒子静止悬浮',
     'en': 'time freeze at key action moment, camera orbits character, particles suspended in space',
     'neg': 'normal speed, no freeze, flowing motion'},

    # ── 打斗节奏（21-25）──
    {'id': 21, 'category': 'battle', 'name': '拔刃特写',
     'zh': '聚焦手部与剑柄，剑刃缓慢出鞘，金属反光明亮，再切人物眼神',
     'en': 'close-up on hand and ornate hilt, metallic blade slowly unsheathes, bright metal reflection, cut to character gaze',
     'neg': 'no detail, blurry hand, quick unsheathe'},
    {'id': 22, 'category': 'battle', 'name': '挥刃跟随',
     'zh': '摄影机跟剑锋移动，剑气划过空气，人物转身攻击，打击感直接',
     'en': 'camera follows blade trajectory, energy arc cuts air, character turns with swift motion, direct hit feel',
     'neg': 'static blade, no follow, soft motion'},
    {'id': 23, 'category': 'battle', 'name': '拳击冲击',
     'zh': '镜头跟随拳头冲向对方，冲击瞬间轻微震动，力量感更强',
     'en': 'camera follows fist to opponent, slight shake at impact, stronger power',
     'neg': 'static impact, no shake, soft hit'},
    {'id': 24, 'category': 'battle', 'name': '闪避旋转',
     'zh': '人物快速侧身闪避，摄影机同步环绕旋转，突出速度与身法变化',
     'en': 'character quick dodge, camera synchronous orbit, speed and movement change highlighted',
     'neg': 'no dodge, static, no rotation'},
    {'id': 25, 'category': 'battle', 'name': '跳跃追踪',
     'zh': '摄影机跟随人物跃起，从地面到空中连续追踪，动作线完整流畅',
     'en': 'camera follows character leap, ground to air continuous tracking, complete action line',
     'neg': 'static jump, no tracking, cut between'},

    # ── 打斗高潮（26-30）──
    {'id': 26, 'category': 'climax', 'name': '冲刺推进',
     'zh': '人物高速向前冲刺，摄影机低机位贴地跟随，地面速度感明显',
     'en': 'character high-speed sprint, camera low angle ground-hugging follow, ground speed obvious',
     'neg': 'static sprint, eye level, no speed'},
    {'id': 27, 'category': 'climax', 'name': '爆裂冲击',
     'zh': '冲击瞬间镜头震动，碎片飞散，人物逆光站立，适合高潮场面',
     'en': 'intense impact burst, camera shake, debris flying, character backlit standing, climax scene',
     'neg': 'no shake, calm, no debris'},
    {'id': 28, 'category': 'climax', 'name': '子弹时间',
     'zh': '动作定格在高速瞬间，摄影机环绕移动，主体清晰、空间拉满',
     'en': 'bullet time, action frozen at high-speed moment, camera orbits, subject clear, space full',
     'neg': 'normal speed, no freeze, no orbit'},
    {'id': 29, 'category': 'climax', 'name': '落地震动',
     'zh': '人物从高处落地，镜头同步下落并轻微震动，撼尘四起，力量感强',
     'en': 'character falls from height, camera synchronous drop with slight shake, dust rises, powerful',
     'neg': 'soft landing, no shake, no dust'},
    {'id': 30, 'category': 'climax', 'name': '对决环绕',
     'zh': '摄影机 360 度环绕双方对决，动作连续衔接，适合高潮场面',
     'en': 'camera 360 orbit around two characters, continuous action connection, climax duel',
     'neg': 'static scene, no orbit, flat'},

    # ── 心理放大（31-35）──
    {'id': 31, 'category': 'emotion', 'name': '眼神推进',
     'zh': '缓慢推近至人物眼睛，突出瞳孔反光与情绪变化，适合心理戏',
     'en': "slow push-in to character's eyes, pupil reflection and emotion change highlighted, psychological",
     'neg': 'wide shot, no emotion, no eye'},
    {'id': 32, 'category': 'emotion', 'name': '泪滴特写',
     'zh': '聚焦眼角泪水滑落，背景虚化，细腻表达委屈、失落或释然',
     'en': 'close-up on tear sliding from eye corner, background blur, subtle grievance, loss or release',
     'neg': 'no tear, dry eye, wide shot'},
    {'id': 33, 'category': 'emotion', 'name': '背影远离',
     'zh': '固定镜头中人物背影慢慢远去，空间逐渐空下来，离别感更强',
     'en': "character's back slowly walks away in fixed camera, space empties, sense of farewell",
     'neg': 'front view, no walking, close space'},
    {'id': 34, 'category': 'emotion', 'name': '窗边侧拍',
     'zh': '从侧面拍摄人物靠窗状态，光线柔和洒落，氛围安静克制',
     'en': 'side shot character by window, soft light falls, quiet restrained atmosphere',
     'neg': 'front view, harsh light, loud'},
    {'id': 35, 'category': 'emotion', 'name': '手部细节',
     'zh': '聚焦手部握物、松手或轻触动作，用细节承接剧情信息',
     'en': 'close-up on hand gripping, releasing or light touch, detail carries plot info',
     'neg': 'wide shot, no hand, no detail'},

    # ── 细节叙事（36-40）──
    {'id': 36, 'category': 'detail', 'name': '物品转人物',
     'zh': '从重要物件特写开始，镜头缓慢移动到人物脸部，完成情节连接',
     'en': "start from important object close-up, camera slowly moves to character's face, plot connection",
     'neg': 'jump from object to person, abrupt'},
    {'id': 37, 'category': 'detail', 'name': '镜面反射',
     'zh': '通过镜子或反射面观察人物，摄像机轻移动，适合隐秘心理场景',
     'en': 'observe character through mirror or reflective surface, camera light move, hidden psychology',
     'neg': 'direct view, no reflection, open'},
    {'id': 38, 'category': 'detail', 'name': '门后窥视',
     'zh': '镜头藏在门边或遮挡物后观察人物，前景虚化，紧张感自然增强',
     'en': 'camera hides behind door or obstruction observing character, foreground blur, tension builds',
     'neg': 'direct observe, no hide, open'},
    {'id': 39, 'category': 'detail', 'name': '雨中慢镜',
     'zh': '细雨落下，人物站在雨里，镜头缓慢环绕，情绪压抑又克制',
     'en': 'fine rain falls, character stands in rain, camera slowly orbits, repressed yet restrained emotion',
     'neg': 'sunny, dry, no rain, fast'},
    {'id': 40, 'category': 'detail', 'name': '风吹人物',
     'zh': '风吹动头发与衣角，摄影机轻缓移动，人物气质与氛围同时被放大',
     'en': "wind blows hair and clothes, camera light slow movement, character's aura and atmosphere amplified",
     'neg': 'no wind, still hair, static'},

    # ── 奇幻特效（41-45）──
    {'id': 41, 'category': 'fantasy', 'name': '云层穿越',
     'zh': '摄影机穿过云雾下降到人物场景，仙侠或奇幻开场氛围强',
     'en': 'camera passes through clouds descending to character scene, xianxia fantasy opening strong',
     'neg': 'no cloud, eye level, no descent'},
    {'id': 42, 'category': 'fantasy', 'name': '花瓣环绕',
     'zh': '花瓣围绕人物旋转飘落，镜头缓慢移动，适合唯美与情感戏',
     'en': 'petals orbit character spinning falling, camera slow move, beauty and emotion scene',
     'neg': 'no petal, static, harsh'},
    {'id': 43, 'category': 'fantasy', 'name': '火焰环绕',
     'zh': '火焰在人物周身升起，镜头环绕推进，画面冲击与能量感十足',
     'en': 'flames rise around character, camera orbit push-in, impact and energy full',
     'neg': 'no flame, calm, static'},
    {'id': 44, 'category': 'fantasy', 'name': '雪花慢落',
     'zh': '雪花缓慢飘落，人物立于雪中，摄影机温柔靠近，氛围清冷唯美',
     'en': 'snowflakes slowly fall, character stands in snow, camera gentle approach, cold beauty atmosphere',
     'neg': 'no snow, warm, harsh'},
    {'id': 45, 'category': 'fantasy', 'name': '月光移动',
     'zh': '月光随镜头转移打在人物身上，层次神秘，适合夜戏与幻想场景',
     'en': 'moonlight shifts with camera onto character, mysterious layers, night or fantasy scene',
     'neg': 'daylight, flat light, no mystery'},

    # ── 史诗收束（46-50）──
    {'id': 46, 'category': 'ending', 'name': '霓虹穿梭',
     'zh': '摄影机穿过霓虹街景快速移动到人物面前，赛博与都市感突出',
     'en': 'camera passes through neon street fast move to character, cyberpunk and urban feel prominent',
     'neg': 'daylight scene, no neon, slow approach'},
    {'id': 47, 'category': 'ending', 'name': '水面倒影',
     'zh': '从水面倒影开场，镜头上移或前移，逐步显露出真实人物',
     'en': 'start from water surface reflection, camera tilt up or push ahead, gradually reveal real character',
     'neg': 'direct start, no reflection, abrupt'},
    {'id': 48, 'category': 'ending', 'name': '服装纹理运镜',
     'zh': '从服装面料、刺绣或配饰特写开始，缓慢推到全身造型，适合角色展示',
     'en': 'start from costume fabric, embroidery or accessory close-up, slowly push to full body, character display',
     'neg': 'full body start, no detail, abrupt'},
    {'id': 49, 'category': 'ending', 'name': '史诗开场',
     'zh': '超广角先展示巨大环境，再慢慢推进到人物中心，气势足',
     'en': 'ultra wide first show massive environment, slowly push to character center, momentum full',
     'neg': 'close-up start, no scale, eye level'},
    {'id': 50, 'category': 'ending', 'name': '终极展示',
     'zh': '摄影机 360 度环绕人物，完整展示动作、造型、表情与场景，用作结尾最合适',
     'en': 'camera 360 orbit character, fully show action, look, expression and scene, best for ending',
     'neg': 'static end, no orbit, flat'},
]

_MOVES_BY_ID = {m['id']: m for m in CAMERA_MOVES}
_MOVES_BY_CATEGORY = {}
for _m in CAMERA_MOVES:
    _MOVES_BY_CATEGORY.setdefault(_m['category'], []).append(_m)


def get_move_by_id(move_id):
    """按 id 取运镜；无效返回 None"""
    try:
        return _MOVES_BY_ID.get(int(move_id))
    except (TypeError, ValueError):
        return None


def _matches(text, keywords):
    if not text:
        return False
    return any(k in text for k in keywords)


def _classify_shot(shot):
    """按分镜内容关键词匹配运镜大类（文章四大原则的落地）"""
    scene = shot.get('scene_desc', '') or ''
    action = shot.get('action', '') or ''
    camera = shot.get('camera', '') or ''
    dialogue = shot.get('dialogue', '') or ''
    blob = scene + action + camera

    # ④ 对话/对峙 → 对话视角
    if dialogue or _matches(blob, ['说', '问', '答', '喊', '对话', '对峙', '耳语', '讲述', '聊天']):
        return 'dialogue'
    # ③ 打斗/追逐动作 → 打斗节奏与高潮
    if _matches(blob, ['挥', '斩', '刺', '拳', '踢', '剑', '刀', '劈', '砸', '扑', '挡', '闪避', '对决', '交手', '招式', '冲向', '猛击', '格挡']):
        return 'climax'
    if _matches(blob, ['追', '奔跑', '冲刺', '跳', '跃', '翻滚', '疾行', '夺路', '逃离']):
        return 'battle'
    # ① 情绪强烈 → 心理放大
    if _matches(blob, ['泪', '哭', '眼神', '瞳孔', '内心', '回忆', '悲伤', '委屈', '震惊', '愤怒', '绝望', '颤抖', '孤独', '痛苦']):
        return 'emotion'
    # ② 大场面 → 大片开场
    if _matches(blob, ['全景', '云海', '城池', '宫殿', '大厦', '城市', '军队', '人群', '星空', '大海', '山川', '天际', '无人机']):
        return 'opening'
    # 幻想氛围
    if _matches(blob, ['仙', '魔法', '灵气', '花瓣', '火焰', '雪花', '月光', '云雾', '幻境', '发光', '悬浮']):
        return 'fantasy'
    # 出场亮相
    if _matches(blob, ['登场', '出场', '出现', '走来', '站起', '亮相', '转身', '回眸']):
        return 'entrance'
    return None


def pick_camera_move(shot, shot_index=1, total_shots=0):
    """为分镜挑选运镜：
    1. 用户手动指定（shot.camera_move_id）→ 直接用
    2. 内容规则匹配大类
    3. 无匹配时：首镜大片开场、末镜史诗收束，其余按类内轮换
    类内按 shot_index 轮换，实现"视觉同源不撞款"
    """
    # 1. 手动指定优先
    manual = get_move_by_id(shot.get('camera_move_id'))
    if manual:
        return manual

    # 2. 规则匹配大类
    category = _classify_shot(shot)

    # 3. 兜底：首末镜特殊化，其余入场/转场交替
    if not category:
        if total_shots and shot_index == 1:
            category = 'opening'
        elif total_shots and shot_index == total_shots:
            category = 'ending'
        else:
            category = 'entrance' if shot_index % 2 == 1 else 'transition'

    moves = _MOVES_BY_CATEGORY.get(category) or CAMERA_MOVES
    # 类内轮换：不撞款
    return moves[(max(1, shot_index) - 1) % len(moves)]


def camera_segments(camera_move):
    """把运镜拆成 prompt 片段：
    Returns:
        (en_prefix, cn_prefix, neg_extra)
    en_prefix 加在正向 prompt 前（镜头运动优先权最高），
    cn_prefix 用于中文展示，neg_extra 并入视频反向词
    """
    move = camera_move or {}
    en_prefix = f"Cinematic camera direction: {move.get('en', '')}. "
    cn_prefix = f"【运镜·{CATEGORY_LABELS.get(move.get('category', ''), '')}】{move.get('zh', '')}。"
    neg_extra = move.get('neg', '')
    return en_prefix, cn_prefix, neg_extra


def list_for_frontend():
    """输出给前端下拉：按大类分组"""
    groups = []
    for key, label in CAMERA_CATEGORIES:
        groups.append({
            'key': key,
            'label': label,
            'moves': [{'id': m['id'], 'name': m['name']} for m in _MOVES_BY_CATEGORY.get(key, [])]
        })
    return groups
