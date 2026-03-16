# -*- coding: utf-8 -*-
"""Flask 应用工厂"""
import os
from pathlib import Path
from flask import Flask, send_from_directory
from .models import db


def create_app(config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / 'data' / 'app.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URI', f'sqlite:///{db_path}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    app.config['WX_APPID'] = os.environ.get('WX_APPID', 'wx987d07e1139db4f1')
    app.config['WX_SECRET'] = os.environ.get('WX_SECRET', '')

    uploads_dir = base_dir / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = str(uploads_dir)

    if config:
        app.config.update(config)

    db.init_app(app)

    @app.after_request
    def after_req(resp):
        if resp.content_type and 'application/json' in resp.content_type:
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    from .routes import api_bp, admin_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/')
    def root():
        from flask import redirect
        return redirect('/admin/')

    return app
