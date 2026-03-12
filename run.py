# -*- coding: utf-8 -*-
"""Flask 启动入口"""
import os
import sys

# 确保控制台输出使用 UTF-8，避免中文乱码
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.init_db import run as init_db_run

app = create_app()

if __name__ == '__main__':
    # 启动时执行数据库初始化
    with app.app_context():
        init_db_run()
    # 支持命令行参数或环境变量
    host = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('HOST', '0.0.0.0')
    port = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.environ.get('PORT', 80))
    app.run(host=host, port=port, debug=os.environ.get('FLASK_DEBUG', '0') == '1')
