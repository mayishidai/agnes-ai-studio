"""
视频生成服务模块
包含：文件下载、视频轮询
"""

import os
import json
import time
import uuid
import requests
from datetime import datetime

from ..config import get_app_dir, get_vendor_base_url, BASE_URL, shutdown_event
from ..models import video_tasks, task_lock


def build_agnesapi_url(base_url):
    """根据 API Base URL 构造 agnesapi 端点 URL

    agnesapi 端点在域名根路径（无 /v1 前缀）：
    https://api.agnes-ai.cn/v1  ->  https://api.agnes-ai.cn/agnesapi
    """
    base = base_url.rstrip('/')
    if base.endswith('/v1'):
        base = base[:-3]
    return base + '/agnesapi'


def fetch_video_url_from_agnesapi(base_url, video_id, api_key):
    """通过官方推荐端点 /agnesapi 获取视频下载 URL

    Args:
        base_url: API Base URL（如 https://api.agnes-ai.cn/v1）
        video_id: 创建任务时返回的 video_id
        api_key: API Key

    Returns:
        视频 URL 字符串，失败返回空字符串
    """
    if not video_id:
        return ''
    try:
        url = f"{build_agnesapi_url(base_url)}?video_id={video_id}"
        headers = {'Authorization': f'Bearer {api_key}'}
        print(f"[视频URL] 通过 agnesapi 端点获取: {url[:120]}...")
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            video_url = (
                data.get('url')
                or data.get('video_url')
                or data.get('output_url')
                or ''
            )
            if not video_url and isinstance(data.get('metadata'), dict):
                meta = data['metadata']
                video_url = meta.get('url', '') or meta.get('video_url', '') or meta.get('output_url', '')
            if video_url:
                print(f"[视频URL] agnesapi 端点获取成功: {video_url[:150]}")
            else:
                print(f"[视频URL] agnesapi 端点响应中未找到 url 字段: {json.dumps(data, ensure_ascii=False)[:300]}")
            return video_url
        else:
            print(f"[视频URL] agnesapi 端点响应异常: HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[视频URL] agnesapi 端点请求失败: {type(e).__name__}: {e}")
    return ''


def download_and_save_file(url, subdir, prefix, ext, max_retries=3):
    """从 URL 下载文件并保存到本地目录（支持重试）
    
    Args:
        url: 文件下载 URL
        subdir: 子目录名 ('videos' 或 'pictures')
        prefix: 文件名前缀
        ext: 文件扩展名
        max_retries: 最大重试次数
    
    Returns:
        保存后的文件名，失败返回 None
    """
    app_dir = get_app_dir()
    target_dir = os.path.join(app_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_uuid = uuid.uuid4().hex[:8]
    filename = f"{prefix}_{timestamp}_{short_uuid}.{ext}"
    filepath = os.path.join(target_dir, filename)

    # 总下载超时（秒）
    total_timeout = 300 if ext == 'mp4' else 120

    for attempt in range(max_retries):
        try:
            print(f"[下载] {subdir}/{filename} (尝试 {attempt+1}/{max_retries}) url={url[:100]}...")
            resp = requests.get(url, timeout=(30, 60), stream=True)  # 连接超时30s，读取超时60s
            resp.raise_for_status()

            content_type = resp.headers.get('Content-Type', '')
            if ext == 'mp4' and 'video' not in content_type and 'octet-stream' not in content_type and 'mp4' not in content_type:
                print(f"[下载警告] Content-Type 不是视频: {content_type}")

            total_size = int(resp.headers.get('Content-Length', 0))
            if total_size > 0:
                print(f"[下载] 预期文件大小: {total_size // 1024}KB")
            
            downloaded = 0
            start_time = time.time()
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if shutdown_event and shutdown_event.is_set():
                        print(f"[下载] 收到关闭信号，停止下载")
                        return None
                    # 检查总超时
                    if time.time() - start_time > total_timeout:
                        print(f"[下载] 总下载超时({total_timeout}s)，已下载 {downloaded // 1024}KB")
                        raise requests.exceptions.Timeout(f"下载总超时({total_timeout}s)")
                    f.write(chunk)
                    downloaded += len(chunk)

            file_size = os.path.getsize(filepath)
            if file_size < 1000:
                print(f"[下载警告] 文件太小 ({file_size} bytes)，可能是错误响应")
                if attempt < max_retries - 1:
                    os.remove(filepath)
                    time.sleep(2)
                    continue
                else:
                    os.remove(filepath)
                    return None

            elapsed = time.time() - start_time
            print(f"[保存成功] {subdir}/{filename} ({file_size // 1024}KB, {elapsed:.1f}s)")
            return filename
        except Exception as e:
            print(f"[下载失败] {subdir}/{filename} 尝试{attempt+1}: {type(e).__name__}: {e}")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            if attempt < max_retries - 1:
                time.sleep(3)
    return None


def poll_video_status(task_id, api_key, model=None):
    """后台轮询视频生成状态"""
    headers = {'Authorization': f'Bearer {api_key}'}
    base_url = get_vendor_base_url(model) if model else BASE_URL
    max_polls = 120
    poll_interval = 10

    for i in range(max_polls):
        if shutdown_event.wait(timeout=poll_interval):
            print(f"[轮询] 收到关闭信号，退出轮询 task_id={task_id}")
            return
        try:
            resp = requests.get(
                f'{base_url}/videos/{task_id}',
                headers=headers,
                timeout=30
            )

            if resp.status_code == 200:
                result = resp.json()
                status = result.get('status', '')

                with task_lock:
                    if task_id in video_tasks:
                        video_tasks[task_id]['status'] = status

                        if status == 'completed':
                            raw_result = json.dumps(result)
                            print(f"[视频完成] task_id={task_id}, 原始响应: {raw_result}")

                            video_url = (
                                result.get('video_url')
                                or result.get('url')
                                or result.get('output_url')
                                or result.get('video')
                                or result.get('remixed_from_video_id')
                                or ''
                            )
                            if not video_url and isinstance(result.get('data'), dict):
                                video_url = result['data'].get('url', '') or result['data'].get('video_url', '') or result['data'].get('video', '')
                            if not video_url and isinstance(result.get('data'), list) and len(result['data']) > 0:
                                video_url = result['data'][0].get('url', '') or result['data'][0].get('video_url', '')
                            if not video_url and isinstance(result.get('metadata'), dict):
                                meta = result['metadata']
                                video_url = meta.get('video_url', '') or meta.get('url', '') or meta.get('output_url', '')
                            # 官方推荐方式：通过 /agnesapi 端点 + video_id 获取视频 URL
                            if not video_url:
                                video_id = video_tasks[task_id].get('video_id', '')
                                video_url = fetch_video_url_from_agnesapi(base_url, video_id, api_key)
                            if not video_url:
                                try:
                                    content_resp = requests.get(f'{base_url}/videos/{task_id}/content', headers=headers, timeout=30)
                                    if content_resp.status_code == 200:
                                        content_data = content_resp.json()
                                        video_url = content_data.get('url', '') or content_data.get('video_url', '') or content_data.get('video', '')
                                        if not video_url and isinstance(content_data.get('data'), dict):
                                            video_url = content_data['data'].get('url', '') or content_data['data'].get('video_url', '')
                                        print(f"[视频URL] 通过 content 端点获取: {video_url[:150] if video_url else '(无)'}")
                                except Exception as e2:
                                    print(f"[视频URL] content 端点请求失败: {e2}")

                            print(f"[视频URL] {video_url or '(未获取到)'}")

                            local_filename = None
                            if video_url:
                                local_filename = download_and_save_file(
                                    video_url, 'videos', 'video', 'mp4'
                                )

                            video_tasks[task_id]['result'] = {
                                'video_url': video_url,
                                'local_file': local_filename,
                                'raw_response': result
                            }
                            break
                        elif status == 'failed':
                            video_tasks[task_id]['result'] = {
                                'error': result.get('error', '生成失败')
                            }
                            break
        except Exception as e:
            if shutdown_event.is_set():
                return
            continue
