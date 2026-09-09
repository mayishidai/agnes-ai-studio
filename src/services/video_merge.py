"""
视频拼接模块 (ffmpeg)
包含：ffmpeg 路径查找、视频合并、中文字幕烧录
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from ..config import get_app_dir


def get_ffmpeg_path():
    """获取 ffmpeg 可执行文件路径（优先系统 PATH，其次 imageio-ffmpeg 内置）"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'ffmpeg'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.exists(ffmpeg_exe):
            return ffmpeg_exe
    except ImportError:
        pass
    return None


def get_ffprobe_path():
    """获取 ffprobe 路径（跨平台兼容）"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return None
    if ffmpeg == 'ffmpeg':
        # 系统 PATH 中的 ffmpeg
        ffprobe_cmd = 'ffprobe.exe' if sys.platform == 'win32' else 'ffprobe'
        try:
            result = subprocess.run([ffprobe_cmd, '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return ffprobe_cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None
    else:
        # imageio-ffmpeg 内置的，同目录下找 ffprobe
        ffmpeg_dir = os.path.dirname(ffmpeg)
        # 跨平台查找：先找无后缀（macOS/Linux），再找 .exe（Windows）
        for name in ['ffprobe', 'ffprobe.exe']:
            ffprobe = os.path.join(ffmpeg_dir, name)
            if os.path.exists(ffprobe):
                return ffprobe
        return None


def get_video_duration(video_path, ffmpeg=None):
    """获取视频时长（秒）"""
    ffprobe = get_ffprobe_path()
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', video_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get('format', {}).get('duration', 0))
        except Exception:
            pass
    # 备选：用 ffmpeg 尝试获取
    if not ffmpeg:
        ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        try:
            result = subprocess.run(
                [ffmpeg, '-i', video_path],
                capture_output=True, text=True, timeout=30
            )
            # ffmpeg -i 输出在 stderr
            import re
            match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', result.stderr)
            if match:
                h, m, s, ms = match.groups()
                return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100
        except Exception:
            pass
    return 0


def burn_chinese_subtitle(video_path, dialogue_text, output_path=None):
    """在视频底部烧录中文字幕
    
    Args:
        video_path: 输入视频路径
        dialogue_text: 中文字幕文本
        output_path: 输出路径（默认覆盖原文件）
    
    Returns:
        成功返回输出路径，失败返回 None
    """
    if not dialogue_text or not dialogue_text.strip():
        return video_path  # 没有字幕，直接返回原文件
    
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        print(f"[字幕] 警告: 未找到 ffmpeg，跳过字幕烧录")
        return video_path
    
    if not output_path:
        output_path = video_path
    
    # 查找中文字体
    font_path = _find_chinese_font()
    
    # 转义字幕文本中的特殊字符
    escaped_text = dialogue_text.replace("'", "'\\''").replace(":", "\\:")
    
    # 构建 drawtext 滤镜
    if font_path:
        # 使用找到的中文字体
        font_escaped = font_path.replace('\\', '/').replace(':', '\\:')
        drawtext = (
            f"drawtext=text='{escaped_text}'"
            f":fontfile='{font_escaped}'"
            f":fontsize=36:fontcolor=white"
            f":borderw=2:bordercolor=black"
            f":x=(w-text_w)/2:y=h-th-40"
        )
    else:
        # 无字体文件，使用默认字体（可能不支持中文）
        drawtext = (
            f"drawtext=text='{escaped_text}'"
            f":fontsize=36:fontcolor=white"
            f":borderw=2:bordercolor=black"
            f":x=(w-text_w)/2:y=h-th-40"
        )
    
    # 如果输出路径和输入相同，使用临时文件
    temp_output = None
    if output_path == video_path:
        temp_output = video_path + '.subtitle_temp.mp4'
        actual_output = temp_output
    else:
        actual_output = output_path
    
    try:
        cmd = [
            ffmpeg, '-i', video_path,
            '-vf', drawtext,
            '-c:a', 'copy', '-y', actual_output
        ]
        print(f"[字幕] 烧录中文字幕: {dialogue_text[:30]}...")
        # 使用 Popen 以便超时后强制杀死 ffmpeg 进程
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=120)
            if proc.returncode == 0 and os.path.exists(actual_output) and os.path.getsize(actual_output) > 0:
                if temp_output:
                    os.replace(temp_output, video_path)
                print(f"[字幕] 烧录成功")
                return output_path
            else:
                err_msg = stderr.decode('utf-8', errors='replace')[:300] if stderr else ''
                print(f"[字幕] 烧录失败 (returncode={proc.returncode}): {err_msg}")
                if temp_output and os.path.exists(temp_output):
                    os.remove(temp_output)
                return video_path
        except subprocess.TimeoutExpired:
            print(f"[字幕] 烧录超时(120s)，强制终止 ffmpeg...")
            proc.kill()
            proc.wait(timeout=10)
            if temp_output and os.path.exists(temp_output):
                os.remove(temp_output)
            return video_path
    except Exception as e:
        print(f"[字幕] 烧录异常: {e}")
        if temp_output and os.path.exists(temp_output):
            os.remove(temp_output)
        return video_path


def _find_chinese_font():
    """查找系统中可用的中文字体（跨平台：Windows / macOS / Linux）"""
    search_dirs = []
    candidates = []

    if sys.platform == 'win32':
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        search_dirs.append(os.path.join(windir, 'Fonts'))
        candidates = [
            'msyh.ttc',      # 微软雅黑
            'msyhbd.ttc',    # 微软雅黑 Bold
            'simhei.ttf',    # 黑体
            'simsun.ttc',    # 宋体
            'simkai.ttf',    # 楷体
            'STZHONGS.TTF',  # 华文宋体
            'STKAITI.ttf',   # 华文楷体
        ]
    elif sys.platform == 'darwin':
        # macOS 字体路径
        search_dirs = [
            '/System/Library/Fonts',
            '/System/Library/Fonts/Supplemental',
            '/Library/Fonts',
            os.path.expanduser('~/Library/Fonts'),
        ]
        candidates = [
            'PingFang.ttc',             # 苹方（macOS 默认中文）
            'STHeiti Light.ttc',        # 华文黑体 Light
            'STHeiti Medium.ttc',       # 华文黑体 Medium
            'Songti.ttc',               # 宋体
            'STSong.ttf',               # 华文宋体
            'Kaiti.ttc',                # 楷体
            'Hiragino Sans GB.ttc',     # 冬青黑体简中
            'Arial Unicode.ttf',        # Arial Unicode
        ]
    else:
        # Linux 字体路径
        search_dirs = [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            os.path.expanduser('~/.fonts'),
            os.path.expanduser('~/.local/share/fonts'),
        ]
        candidates = [
            'wqy-zenhei/wqy-zenhei.ttc',
            'wqy-microhei/wqy-microhei.ttc',
            'truetype/wqy/wqy-zenhei.ttc',
            'truetype/wqy/wqy-microhei.ttc',
            'NotoSansCJK-Regular.ttc',
            'NotoSansSC-Regular.otf',
        ]

    for d in search_dirs:
        for font in candidates:
            font_path = os.path.join(d, font)
            if os.path.exists(font_path):
                return font_path

    return None


def merge_videos(drama_id, video_results, shot_order=None, output_prefix='merged'):
    """使用 ffmpeg 将多个分镜视频拼接为一个完整视频
    
    Args:
        drama_id: 短剧 ID
        video_results: 视频结果列表（包含 local_file 字段）
        shot_order: 可选，指定镜头顺序 [shot_index, ...]。为 None 时按 shot_index 排序
        output_prefix: 输出文件名前缀
    
    Returns:
        合并后的文件名，失败返回 None
    """
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        print(f"[短剧 {drama_id}] 警告: 未找到 ffmpeg，跳过视频拼接")
        return None
    
    # 按指定顺序或默认排序获取视频
    if shot_order:
        # 按用户指定顺序
        result_map = {}
        for v in video_results:
            if v.get('status') == 'completed' and v.get('local_file'):
                result_map[v.get('shot_index')] = v
        success_videos = []
        for si in shot_order:
            v = result_map.get(si)
            if v:
                app_dir = get_app_dir()
                full_path = os.path.join(app_dir, 'dramas', drama_id, 'videos', v['local_file'])
                if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                    success_videos.append(full_path)
    else:
        success_videos = []
        for v in sorted(video_results, key=lambda x: x.get('shot_index', 0)):
            if v.get('status') == 'completed' and v.get('local_file'):
                app_dir = get_app_dir()
                full_path = os.path.join(app_dir, 'dramas', drama_id, 'videos', v['local_file'])
                if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                    success_videos.append(full_path)
    
    if len(success_videos) < 2:
        print(f"[短剧 {drama_id}] 成功视频少于 2 个，跳过拼接")
        return None
    
    print(f"[短剧 {drama_id}] 开始拼接 {len(success_videos)} 个视频...")
    
    app_dir = get_app_dir()
    videos_dir = os.path.join(app_dir, 'dramas', drama_id, 'videos')
    list_file = os.path.join(videos_dir, 'concat_list.txt')
    
    try:
        with open(list_file, 'w', encoding='utf-8') as f:
            for video_path in success_videos:
                safe_path = video_path.replace('\\', '/')
                f.write(f"file '{safe_path}'\n")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'{output_prefix}_{timestamp}.mp4'
        output_path = os.path.join(videos_dir, output_file)
        
        cmd = [
            ffmpeg, '-f', 'concat', '-safe', '0',
            '-i', list_file, '-c', 'copy', '-y', output_path
        ]
        
        print(f"[短剧 {drama_id}] 执行: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=120)
            if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path) // 1024
                print(f"[短剧 {drama_id}] 拼接成功: {output_file} ({file_size}KB)")
                return output_file
            else:
                err_msg = stderr.decode('utf-8', errors='replace')[:500] if stderr else ''
                print(f"[短剧 {drama_id}] 拼接失败: {err_msg}")
                print(f"[短剧 {drama_id}] 尝试重新编码模式...")
                cmd_reencode = [
                    ffmpeg, '-f', 'concat', '-safe', '0',
                    '-i', list_file, '-c:v', 'libx264', '-c:a', 'aac', '-y', output_path
                ]
                proc2 = subprocess.Popen(cmd_reencode, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    stdout2, stderr2 = proc2.communicate(timeout=300)
                    if proc2.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        file_size = os.path.getsize(output_path) // 1024
                        print(f"[短剧 {drama_id}] 重新编码拼接成功: {output_file} ({file_size}KB)")
                        return output_file
                    else:
                        err_msg2 = stderr2.decode('utf-8', errors='replace')[:500] if stderr2 else ''
                        print(f"[短剧 {drama_id}] 重新编码也失败: {err_msg2}")
                        return None
                except subprocess.TimeoutExpired:
                    print(f"[短剧 {drama_id}] 重新编码超时(300s)，强制终止")
                    proc2.kill()
                    proc2.wait(timeout=10)
                    return None
        except subprocess.TimeoutExpired:
            print(f"[短剧 {drama_id}] 拼接超时(120s)，强制终止")
            proc.kill()
            proc.wait(timeout=10)
            return None
    except Exception as e:
        print(f"[短剧 {drama_id}] 拼接异常: {e}")
        return None
    finally:
        if os.path.exists(list_file):
            try:
                os.remove(list_file)
            except:
                pass
