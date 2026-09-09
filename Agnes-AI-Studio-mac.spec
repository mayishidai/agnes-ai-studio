# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件 (macOS 版)
用于将 Agnes AI Studio 打包为 macOS .app Bundle

使用方法:
    pyinstaller --clean --noconfirm Agnes-AI-Studio-mac.spec

输出: dist/Agnes-AI-Studio.app
"""

import sys
import os
from pathlib import Path

# 获取项目根目录
project_dir = Path.cwd()

# 查找 imageio-ffmpeg 内置的 ffmpeg 二进制文件
ffmpeg_binary = None
try:
    import imageio_ffmpeg
    ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    pass

binaries_list = []
if ffmpeg_binary and os.path.exists(ffmpeg_binary):
    binaries_list.append((ffmpeg_binary, 'imageio_ffmpeg/binaries'))
    print(f'[spec] 找到 ffmpeg: {ffmpeg_binary}')
else:
    print('[spec] 警告: 未找到 ffmpeg 二进制文件，视频拼接功能将不可用')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries_list,
    datas=[
        # 将 static 目录打包进 app
        ('static/index.html', 'static'),
        # 将 src 包打包进 app
        ('src/__init__.py', 'src'),
        ('src/config.py', 'src'),
        ('src/models.py', 'src'),
        ('src/services/__init__.py', 'src/services'),
        ('src/services/text_model.py', 'src/services'),
        ('src/services/video_gen.py', 'src/services'),
        ('src/services/video_merge.py', 'src/services'),
        ('src/routes/__init__.py', 'src/routes'),
        ('src/routes/pages.py', 'src/routes'),
        ('src/routes/api_config.py', 'src/routes'),
        ('src/routes/image.py', 'src/routes'),
        ('src/routes/video.py', 'src/routes'),
        ('src/routes/drama.py', 'src/routes'),
        ('src/routes/files.py', 'src/routes'),
    ],
    hiddenimports=[
        'flask',
        'flask.json',
        'flask_cors',
        'requests',
        'json',
        'threading',
        'subprocess',
        'os',
        'sys',
        'webbrowser',
        'imageio_ffmpeg',
        # src 包及其子模块
        'src',
        'src.config',
        'src.models',
        'src.services',
        'src.services.text_model',
        'src.services.video_gen',
        'src.services.video_merge',
        'src.routes',
        'src.routes.pages',
        'src.routes.api_config',
        'src.routes.image',
        'src.routes.video',
        'src.routes.drama',
        'src.routes.files',
        # requests / urllib3 底层依赖 email 模块
        'email',
        'email.mime.text',
        'email.mime.multipart',
        'email.mime.base',
        'email.utils',
        'email.header',
        'email.encoders',
        'email.parser',
        'email.message',
        'email.policy',
        'email.charset',
        'email.contentmanager',
        'email.errors',
        'email.generator',
        'email.iterators',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'xmlrpc',
        'pydoc',
        'test',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# macOS 使用 bundle 模式：先构建可执行文件（不含数据），再封装为 .app
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Agnes-AI-Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,              # macOS 可 strip 减小体积
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.icns',      # 可选：添加 .icns 图标
)

app = BUNDLE(
    exe,
    a.datas,
    a.binaries,
    name='Agnes-AI-Studio.app',
    # icon=None,             # 可选：添加 .icns 图标
    bundle_identifier='com.agnes-ai.studio',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'Agnes AI Studio',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
)
