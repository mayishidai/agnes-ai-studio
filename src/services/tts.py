"""
TTS 语音合成服务模块 (edge-tts)
包含：音频生成、音频时长获取、音色列表
"""

import asyncio
import os
import edge_tts

# 常用中文音色
ANCHOR_VOICES = {
    'zh-CN-XiaoxiaoNeural': {'name': '晓晓（女声·温暖）', 'gender': 'female'},
    'zh-CN-XiaoyiNeural': {'name': '晓伊（女声·活泼）', 'gender': 'female'},
    'zh-CN-YunxiNeural': {'name': '云希（男声·阳光）', 'gender': 'male'},
    'zh-CN-YunjianNeural': {'name': '云健（男声·沉稳）', 'gender': 'male'},
    'zh-CN-XiaochenNeural': {'name': '晓辰（女声·知性）', 'gender': 'female'},
    'zh-CN-XiaohanNeural': {'name': '晓涵（女声·优雅）', 'gender': 'female'},
    'zh-CN-XiaomoNeural': {'name': '晓墨（女声·沉稳）', 'gender': 'female'},
    'zh-CN-XiaoruiNeural': {'name': '晓睿（女声·干练）', 'gender': 'female'},
    'zh-CN-XiaoshuangNeural': {'name': '晓双（女声·甜美）', 'gender': 'female'},
    'zh-CN-XiaoxuanNeural': {'name': '晓萱（女声·温柔）', 'gender': 'female'},
    'zh-CN-XiaoyanNeural': {'name': '晓颜（女声·清新）', 'gender': 'female'},
    'zh-CN-YunxiaNeural': {'name': '云夏（男声·少年）', 'gender': 'male'},
    'zh-CN-YunyangNeural': {'name': '云扬（男声·专业）', 'gender': 'male'},
    'zh-CN-YunyeNeural': {'name': '云野（男声·故事感）', 'gender': 'male'},
}

DEFAULT_VOICE = 'zh-CN-XiaoxiaoNeural'


async def _generate_tts_async(text, voice, output_path):
    """异步生成 TTS 音频"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_tts_audio(text, voice=None, output_path=None):
    """生成 TTS 音频文件
    
    Args:
        text: 要合成的文本
        voice: 音色名称，默认 zh-CN-XiaoxiaoNeural
        output_path: 输出文件路径
    
    Returns:
        成功返回输出文件路径，失败返回 None
    """
    if not text or not text.strip():
        return None
    
    if voice is None:
        voice = DEFAULT_VOICE
    
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 运行异步 TTS
        asyncio.run(_generate_tts_async(text.strip(), voice, output_path))
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"[TTS] 音频生成成功: {output_path} ({os.path.getsize(output_path) // 1024}KB)")
            return output_path
        else:
            print(f"[TTS] 音频文件为空或不存在")
            return None
    except Exception as e:
        print(f"[TTS] 音频生成失败: {e}")
        return None


def get_audio_duration(audio_path):
    """获取音频文件时长（秒）
    
    使用 ffprobe 获取音频时长，如果失败则用 ffmpeg 备选
    
    Args:
        audio_path: 音频文件路径
    
    Returns:
        音频时长（秒），失败返回 0
    """
    from .video_merge import get_ffprobe_path, get_ffmpeg_path
    import subprocess
    import json
    import re
    
    ffprobe = get_ffprobe_path()
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', audio_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get('format', {}).get('duration', 0))
        except Exception:
            pass
    
    # 备选：用 ffmpeg
    ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        try:
            result = subprocess.run(
                [ffmpeg, '-i', audio_path],
                capture_output=True, text=True, timeout=30
            )
            match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', result.stderr)
            if match:
                h, m, s, ms = match.groups()
                return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100
        except Exception:
            pass
    
    return 0


def get_available_voices():
    """获取可用的中文音色列表
    
    Returns:
        音色列表，每项包含 id, name, gender
    """
    voices = []
    for voice_id, info in ANCHOR_VOICES.items():
        voices.append({
            'id': voice_id,
            'name': info['name'],
            'gender': info['gender']
        })
    return voices
