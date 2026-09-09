"""
Agnes AI Studio - Flask 应用工厂
"""

import os
# Flask 是一个使用 Python 编写的轻量级 Web 应用框架。
# 它被称为“微框架”，因为其核心简单但易于通过扩展增加功能，非常适合快速开发 Web 应用。
# 这里导入 Flask 类，用于创建和配置 WSGI Web 应用程序的核心实例。
from flask import Flask
from .config import get_base_path, ensure_output_dirs


def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(
        __name__,
        static_folder=os.path.join(get_base_path(), 'static'),
        static_url_path=''
    )

    # 确保输出目录存在
    ensure_output_dirs()

    # 注册 Blueprint
    from .routes.pages import pages_bp
    from .routes.api_config import config_bp
    from .routes.image import image_bp
    from .routes.video import video_bp
    from .routes.drama import drama_bp
    from .routes.files import files_bp
    from .routes.anchor import anchor_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(drama_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(anchor_bp)

    # 蓝图注册完成后，从磁盘恢复短剧任务
    from .models import load_drama_tasks
    load_drama_tasks()

    return app
