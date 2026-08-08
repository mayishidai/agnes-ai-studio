"""
模型选项与任务状态模块
包含：模型选项字典、默认模型、视频/短剧任务状态管理
"""

import os
import json
import threading
from .config import get_app_dir

# ---------- 模型选项 ----------
TEXT_MODEL_OPTIONS = {
    'agnes-2.5-flash': 'Agnes 2.5 Flash (推荐，免费)',
    'agnes-2.5-pro-alpha': 'Agnes 2.5 Pro Alpha (高级)',
    'agnes-2.0-flash': 'Agnes 2.0 Flash',
    'deepseek-v4-flash': 'DeepSeek V4 Flash',
    'deepseek-chat': 'DeepSeek Chat',
    'deepseek-reasoner': 'DeepSeek Reasoner',
    'qwen-turbo': 'Qwen Turbo',
    'qwen-plus': 'Qwen Plus',
    'doubao-pro-32k': '豆包 Pro 32K',
    'doubao-lite-32k': '豆包 Lite 32K',
}
IMAGE_MODEL_OPTIONS = {
    'agnes-image-2.1-flash': 'Agnes Image 2.1 Flash (推荐)',
    'agnes-image-2.0-flash': 'Agnes Image 2.0 Flash',
    'doubao-seedream-3-0': '豆包 Seedream 3.0',
    'minimax-image-01': 'MiniMax Image 01',
    'qwen-image-plus': 'Qwen Image Plus',
}
VIDEO_MODEL_OPTIONS = {
    'agnes-video-v2.0': 'Agnes Video 2.0 (推荐)',
    'minimax-video-01': 'MiniMax Video 01',
    'doubao-seaweed-t2v': '豆包 Seaweed T2V',
    'qwen-video-gen': 'Qwen Video Gen',
}
DEFAULT_TEXT_MODEL = 'agnes-2.5-flash'
DEFAULT_IMAGE_MODEL = 'agnes-image-2.1-flash'
DEFAULT_VIDEO_MODEL = 'agnes-video-v2.0'

# ---------- 视频任务状态（内存存储，重启后丢失）----------
video_tasks = {}
task_lock = threading.Lock()

# ---------- 短剧任务状态 ----------
drama_tasks = {}
drama_lock = threading.Lock()

def ensure_drama_dirs(drama_id):
    """确保短剧输出目录存在"""
    app_dir = get_app_dir()
    base = os.path.join(app_dir, 'dramas', drama_id)
    for sub in ('images', 'videos'):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    return base


def _drama_task_path(drama_id):
    """获取短剧任务持久化文件路径"""
    app_dir = get_app_dir()
    return os.path.join(app_dir, 'dramas', drama_id, 'task.json')


def save_drama_task(drama_id):
    """将短剧任务状态保存到磁盘（JSON 文件）"""
    try:
        with drama_lock:
            drama = drama_tasks.get(drama_id)
            if not drama:
                return
            # 复制一份，移除不需要持久化的字段
            data = {k: v for k, v in drama.items()
                    if k not in ('text_api_key',)}
        path = _drama_task_path(drama_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[短剧 {drama_id}] 保存任务状态失败: {e}")


def load_drama_tasks():
    """启动时从磁盘加载所有短剧任务"""
    app_dir = get_app_dir()
    dramas_dir = os.path.join(app_dir, 'dramas')
    if not os.path.isdir(dramas_dir):
        return
    loaded = 0
    for name in os.listdir(dramas_dir):
        subdir = os.path.join(dramas_dir, name)
        if not os.path.isdir(subdir):
            continue
        task_file = os.path.join(subdir, 'task.json')
        if not os.path.isfile(task_file):
            # 旧任务目录没有 task.json，尝试迁移重建
            drama_id = _migrate_old_drama_task(name, subdir)
            if not drama_id:
                continue
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            drama_id = data.get('drama_id')
            if not drama_id:
                continue
            # 如果任务正在进行中（非终态），标记为中断
            status = data.get('status', '')
            if status not in ('completed', 'failed', 'cancelled'):
                data['status'] = 'failed'
                data['message'] = '应用重启导致任务中断，请重新生成'
                print(f"[短剧] 任务 {drama_id} 原状态 {status}，已标记为中断")
            with drama_lock:
                drama_tasks[drama_id] = data
            loaded += 1
            print(f"[短剧] 已恢复任务: {drama_id} (状态: {data.get('status')})")
        except Exception as e:
            print(f"[短剧] 加载任务失败 {name}: {e}")
    if loaded:
        print(f"[短剧] 共恢复 {loaded} 个任务")


def _migrate_old_drama_task(drama_id, subdir):
    """迁移旧任务目录（无 task.json）— 根据文件结构重建元数据"""
    try:
        images_dir = os.path.join(subdir, 'images')
        videos_dir = os.path.join(subdir, 'videos')
        image_files = os.listdir(images_dir) if os.path.isdir(images_dir) else []
        video_files = os.listdir(videos_dir) if os.path.isdir(videos_dir) else []

        # 从视频文件名提取 shot 索引
        shot_indices = set()
        for vf in video_files:
            if vf.startswith('shot_'):
                parts = vf.replace('.mp4', '').split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    shot_indices.add(int(parts[1]))
        shots_count = len(shot_indices) if shot_indices else 0
        completed_shots = len([v for v in video_files if v.startswith('shot_') and v.endswith('.mp4')])

        # 判断状态
        has_merged = any(f.startswith('merged_') for f in video_files)
        status = 'completed' if has_merged or completed_shots > 0 else 'failed'
        message = '短剧生成完成' if status == 'completed' else '短剧生成失败'

        # 构建最小化的任务数据
        data = {
            'drama_id': drama_id,
            'status': status,
            'step': 'completed' if status == 'completed' else 'failed',
            'prompt': f'(历史任务 {drama_id})',
            'shot_duration': 5,
            'style_preset': 'anime',
            'text_model': DEFAULT_TEXT_MODEL,
            'image_model': DEFAULT_IMAGE_MODEL,
            'video_model': DEFAULT_VIDEO_MODEL,
            'script': None,
            'story': None,
            'storyboard': None,
            'shots': [],
            'assets': [],
            'video_results': [],
            'merged_video': next((f for f in video_files if f.startswith('merged_')), None),
            'message': message,
            'created_at': os.path.getctime(subdir),
            'migrated': True,
        }

        # 重建 assets 列表（从图片文件名推断）
        assets = []
        for img in sorted(image_files):
            if img.endswith(('.png', '.jpg', '.jpeg')):
                assets.append({
                    'category': 'unknown',
                    'name': img.split('_')[0] if '_' in img else img,
                    'desc': '',
                    'image_url': f'/dramas/{drama_id}/images/{img}',
                    'local_file': img,
                })
        data['assets'] = assets

        # 重建 video_results
        video_results = []
        for idx in sorted(shot_indices):
            vf = next((f for f in video_files if f.startswith(f'shot_{idx}_') and f.endswith('.mp4')), None)
            if vf:
                video_results.append({
                    'shot_index': idx + 1,
                    'status': 'completed',
                    'video_url': f'/dramas/{drama_id}/videos/{vf}',
                    'local_file': vf,
                    'prompt': '',
                })
        data['video_results'] = video_results

        # 保存 task.json
        task_file = _drama_task_path(drama_id)
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[短剧] 已迁移旧任务: {drama_id} (状态: {status}, {completed_shots} 镜头, {len(assets)} 素材)")
        return drama_id
    except Exception as e:
        print(f"[短剧] 迁移旧任务失败 {drama_id}: {e}")
        return None
