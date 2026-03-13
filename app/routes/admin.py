# -*- coding: utf-8 -*-
"""Admin 后台路由 - 提供 HTML 静态页面"""
import os
from flask import Blueprint, send_from_directory

admin_bp = Blueprint('admin_pages', __name__)

ADMIN_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'admin')
)


@admin_bp.route('/')
@admin_bp.route('/index.html')
def index():
    return send_from_directory(ADMIN_DIR, 'index.html')


@admin_bp.route('/login.html')
def login():
    return send_from_directory(ADMIN_DIR, 'login.html')


@admin_bp.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(ADMIN_DIR, filename)
