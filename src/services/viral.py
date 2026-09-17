# -*- coding: utf-8 -*-
"""爆款视频复刻引擎 —— Hypit 能力移植

来源：Hypit（https://github.com/hypit-ai/hypit）的核心方法论：
"Clone any viral video with AI agents —— Not just a script, the whole workflow.
One workflow, 100 variants."

移植到 Agnes AI Studio 的落地形式：
1. 爆款结构模板库：把 Hypit 示例验证过的爆款范式（UGC 盘点/播客对撞/街头采访/
   带货口播/剧情反转）沉淀为结构模板，文本模型按模板写剧本，保证"爆款结构"可复用
2. Hypit 创作铁律融入模板：
   - 前 3 秒强钩子（Hook），流失发生在第一屏
   - 词锚定（word-anchored）：画面变化跟着台词走，而不是机械秒数
   - A-roll（表演/口播）与 B-roll（插入素材）分层调度
   - 字幕爆点与节奏卡点：每个转折点有视觉强调
   - 结尾互动 CTA：引导评论/关注，喂算法
3. 一键量产变体（One workflow, 100 variants）：
   同一套结构，按变体策略批量改写——换主角人设 / 换场景时代 / 换产品对象 /
   反转视角立场 / 换语言风格，结构与节奏原封不动
"""

# 爆款结构模板库（key, 名称, 适用场景, 结构说明——直接注入创作指令）
VIRAL_TEMPLATES = [
    {
        'key': 'ugc_tierlist',
        'name': 'UGC 锐评盘点',
        'desc': '博主对某个领域做排名/分级，观点犀利拉满争议（参考：GOAT DEBATE 足球 Tier List）',
        'structure': (
            '【钩子0-3秒】一句暴论开场直接炸场，如"我把XX排进了D级，不服来喷"，配博主的挑衅表情特写；'
            '【主体】逐条盘点3-5个对象，每条30秒内：先抛出争议结论→给出一个出人意料的理由→甩一个细节证据；'
            '【爆点】在倒数第二个对象处放最大争议（观众最爱的对象被踩/最被低估的对象封神）；'
            '【互动CTA】结尾挑衅式提问"你同意吗？评论区报出你的排序"，引导站队互撕'
        ),
    },
    {
        'key': 'podcast_clash',
        'name': '播客对撞切片',
        'desc': '双人对坐访谈，观点激烈对撞+产品软植入（参考：DAILY CREATINE 肌肉芭比推销肌酸）',
        'structure': (
            '【钩子0-3秒】嘉宾说出一句反常识暴论，主持人的震惊反应做反应镜头；'
            '【对撞】两人围绕争议话题展开2-3轮攻防：嘉宾抛暴论→主持人质疑→嘉宾用夸张案例回击；'
            '【植入】话题自然引到产品/服务，嘉宾用亲身经历带出，主持人顺势追问细节；'
            '【收尾】主持人总结一句金句+互动引导"你觉得谁说得对"'
        ),
    },
    {
        'key': 'street_interview',
        'name': '街头采访揭秘',
        'desc': '街采式人物故事，三段式揭示+反转punchline（参考：NICE RIDE 黑帮太太的三个百万规则）',
        'structure': (
            '【钩子0-3秒】采访者抛出"你是怎么做到XX的"，被访者说出一个反差身份/反差事实；'
            '【三段揭示】被访者分三条讲核心干货，每条配一个具体场景画面（B-roll 插入），一条比一条劲爆；'
            '【punchline】最后一条藏着全场最大反转，或一个出人意料的自嘲；'
            '【互动CTA】采访者总结"第X条你学会了吗"，引导评论区打卡'
        ),
    },
    {
        'key': 'product_hook',
        'name': '带货口播爆款',
        'desc': '单人口播带货，钩子-痛点-产品-CTA 四段式，适合日更换 SKU',
        'structure': (
            '【钩子0-3秒】直击痛点的问题或暴论，如"还在花冤枉钱买XX？";'
            '【痛点】放大不使用产品的糟糕场景，观众代入；'
            '【产品】引出产品，讲清一个核心卖点+一个信任证据（数据/对比/亲测）；'
            '【CTA】限时优惠/点击小黄车/评论区扣1，制造紧迫感'
        ),
    },
    {
        'key': 'plot_twist',
        'name': '剧情反转短剧',
        'desc': '强情节短剧，结尾大反转，情绪浓度高（Agnes 原生强项）',
        'structure': (
            '【钩子0-3秒】直接从冲突最高点切入（摔门/对峙/意外瞬间），观众一脸懵想知道前因；'
            '【铺垫】倒回事件起点，快速建立人物关系与误会/执念；'
            '【升级】矛盾两轮升级，每轮出一个情绪爆点台词；'
            '【反转】结尾揭穿隐藏事实，前文所有细节都指向这个反转，回味无穷'
        ),
    },
]

# 默认变体策略（Hypit 理念：同一结构，换内容不换骨架）
DEFAULT_VARIANT_STRATEGIES = [
    '换主角人设：把主角换成完全不同的人物类型（性别/年龄/职业/性格反差），保持观点和结构不变',
    '换场景时代：把故事搬到完全不同的场景或时代背景（古装/未来/校园/职场），冲突内核不变',
    '反转视角立场：让原本的对立面当主角，从反方视角讲同一个结构，结论完全相反',
    '换语言风格：换成极端不同的说话风格（文言文/东北话/互联网黑话/偶像剧腔），内容逻辑不变',
    '换产品对象：把涉及的产品/领域整体替换为另一个品类，套路原封不动',
]


def get_template(template_key):
    """按 key 取模板；无效返回 None"""
    for t in VIRAL_TEMPLATES:
        if t['key'] == template_key:
            return t
    return None


def build_viral_brief(template_key, topic, variant_instruction=None):
    """构造爆款复刻的创作 brief（作为 drama 任务的 prompt 输入）

    结构模板注入 Hypit 创作铁律，让故事自带爆款基因；
    variant_instruction 存在时，是"变体任务"的 brief（保结构换内容）。
    """
    tpl = get_template(template_key)
    if not tpl:
        return topic

    parts = [
        f"【爆款结构】{tpl['name']}：{tpl['desc']}",
        f"【结构要求】{tpl['structure']}",
        "【创作铁律】前3秒必须有强钩子；台词驱动画面变化（每句关键台词都要有对应的视觉动作）；"
        "关键转折点要有字幕爆点或音效点；结尾必须留互动钩子（提问/站队/自嘲）。",
        f"【创作主题】{topic}",
    ]
    if variant_instruction:
        parts.append(
            f"【变体要求】这是同款爆款结构的变体版本：{variant_instruction}。"
            "结构与节奏必须和原版完全一致（钩子位置/段落划分/爆点位置/CTA方式都不变），只更换人物、场景、措辞与内容对象。")
    return "\n".join(parts)


def build_variant_briefs(template_key, topic, variant_count=2, custom_instructions=None):
    """批量生成变体 brief 列表

    优先使用用户自定义变体指令，不足部分用默认策略轮换补齐。
    Returns:
        [(label, brief), ...] 长度 = variant_count
    """
    instructions = list(custom_instructions or [])
    pool = [s for s in DEFAULT_VARIANT_STRATEGIES if s not in instructions]
    while len(instructions) < variant_count and pool:
        instructions.append(pool.pop(0))
    instructions = instructions[:variant_count]

    briefs = []
    for i, ins in enumerate(instructions, 1):
        briefs.append((f"变体{i}", build_viral_brief(template_key, topic, ins)))
    return briefs


def list_for_frontend():
    """输出给前端模板选择卡片"""
    return [{'key': t['key'], 'name': t['name'], 'desc': t['desc']} for t in VIRAL_TEMPLATES]
