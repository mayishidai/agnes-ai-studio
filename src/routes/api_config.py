"""
API 配置路由
"""

import os
import json
from flask import Blueprint, request, jsonify
from ..config import (get_config_path, get_custom_models, add_custom_model, remove_custom_model, 
                       get_custom_model_config, get_ollama_config, save_ollama_config, get_ollama_models)

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """获取/保存 API Key 配置（支持各厂商独立 Key）"""
    config_file = get_config_path()
    
    def _mask_key(key):
        if not key:
            return ''
        return key[:8] + '****' + key[-4:] if len(key) > 12 else '****'
    
    if request.method == 'GET':
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            result = {}
            for k, v in data.items():
                if k.endswith('_api_key') or k == 'api_key':
                    result[k] = ''
                    result[f'{k}_masked'] = _mask_key(v) if v else ''
                elif k.endswith('_base_url'):
                    result[k] = v
                else:
                    result[k] = v
            return jsonify(result)
        return jsonify({'api_key': '', 'api_key_masked': ''})

    elif request.method == 'POST':
        data = request.get_json()
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        api_key = data.get('api_key', '').strip()
        if api_key:
            config['api_key'] = api_key
        
        vendor_keys = ['text_api_key', 'deepseek_api_key', 'doubao_api_key', 'minimax_api_key', 'qwen_api_key']
        vendor_urls = ['text_base_url', 'deepseek_base_url', 'doubao_base_url', 'minimax_base_url', 'qwen_base_url']
        
        for key_field in vendor_keys:
            val = data.get(key_field, '').strip()
            if val:
                config[key_field] = val
            # 空值时保留已有配置，不删除
        
        for url_field in vendor_urls:
            val = data.get(url_field, '').strip()
            if val:
                config[url_field] = val
            # 空值时保留已有配置，不删除
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)
        return jsonify({'success': True, 'message': '配置已保存'})


# ==================== 自定义模型管理 ====================

@config_bp.route('/api/custom-models', methods=['GET'])
def list_custom_models():
    """获取所有自定义模型列表"""
    models = get_custom_models()
    # 脱敏 API Key
    for m in models:
        if m.get('api_key'):
            key = m['api_key']
            m['api_key_masked'] = key[:8] + '****' + key[-4:] if len(key) > 12 else '****'
        else:
            m['api_key_masked'] = ''
    return jsonify({'success': True, 'models': models})


@config_bp.route('/api/custom-models', methods=['POST'])
def create_custom_model():
    """添加自定义模型"""
    data = request.get_json()
    model_id = data.get('model_id', '').strip()
    display_name = data.get('display_name', '').strip()
    model_type = data.get('model_type', '').strip()
    base_url = data.get('base_url', '').strip()
    api_key = data.get('api_key', '').strip()
    
    if not model_id or not display_name or not model_type or not base_url:
        return jsonify({'success': False, 'error': '请填写模型ID、名称、类型和 API 地址'}), 400
    
    if model_type not in ('text', 'image', 'video'):
        return jsonify({'success': False, 'error': '模型类型必须是 text/image/video'}), 400
    
    ok, msg = add_custom_model(model_id, display_name, model_type, base_url, api_key)
    if ok:
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'success': False, 'error': msg}), 400


@config_bp.route('/api/custom-models', methods=['DELETE'])
def delete_custom_model():
    """删除自定义模型"""
    data = request.get_json()
    model_id = data.get('model_id', '').strip()
    if not model_id:
        return jsonify({'success': False, 'error': '缺少 model_id'}), 400
    
    config = get_custom_model_config(model_id)
    if not config:
        return jsonify({'success': False, 'error': '模型不存在'}), 404
    
    remove_custom_model(model_id)
    return jsonify({'success': True, 'message': '已删除'})


# ==================== Ollama 本地模型配置 ====================

@config_bp.route('/api/ollama/config', methods=['GET'])
def get_ollama_config_api():
    """获取 Ollama 配置"""
    config = get_ollama_config()
    return jsonify({'success': True, 'config': config})


@config_bp.route('/api/ollama/config', methods=['POST'])
def save_ollama_config_api():
    """保存 Ollama 配置"""
    data = request.get_json()
    config = {
        'enabled': data.get('enabled', False),
        'base_url': data.get('base_url', 'http://localhost:11434').strip().rstrip('/'),
        'models': data.get('models', [])
    }
    save_ollama_config(config)
    return jsonify({'success': True, 'message': 'Ollama 配置已保存'})


@config_bp.route('/api/ollama/detect', methods=['POST'])
def detect_ollama_api():
    """检测 Ollama 服务并获取可用模型列表"""
    data = request.get_json() or {}
    base_url = data.get('base_url', 'http://localhost:11434').strip().rstrip('/')
    
    import requests as req
    try:
        # 先检测服务是否可用
        resp = req.get(f'{base_url}/api/tags', timeout=5)
        if resp.status_code == 200:
            models_data = resp.json()
            models = [m['name'] for m in models_data.get('models', [])]
            return jsonify({'success': True, 'models': models, 'base_url': base_url})
        else:
            return jsonify({'success': False, 'error': f'Ollama 返回状态码 {resp.status_code}'}), 502
    except req.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': f'无法连接到 Ollama ({base_url})，请确认 Ollama 已启动'}), 503
    except req.exceptions.Timeout:
        return jsonify({'success': False, 'error': '连接 Ollama 超时'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': f'检测失败: {e}'}), 500
