# -*- coding: utf-8 -*-
"""API 路由"""
import json
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.models import db, Admin, Category, Wardrobe

api_bp = Blueprint('api', __name__)


def _parse_json(s, default=None):
    if default is None:
        default = []
    if not s:
        return default
    try:
        return json.loads(s) if isinstance(s, str) else s
    except Exception:
        return default


def _wardrobe_to_dict(w):
    return {
        "id": w.id,
        "name": w.name,
        "category": w.category,
        "tags": _parse_json(w.tags),
        "image": w.image or "",
        "scene": _parse_json(w.scene),
        "weather": _parse_json(w.weather),
        "createTime": w.create_time.isoformat() if w.create_time else "",
        "updateTime": w.update_time.isoformat() if w.update_time else "",
    }


@api_bp.route('/count', methods=['POST'])
def count():
    data = request.get_json() or {}
    action = data.get('action', '')
    if action == 'inc':
        return jsonify({"code": 0, "message": "ok", "data": {}})
    return jsonify({"code": -1, "message": "invalid action"})


@api_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({"code": -1, "message": "用户名和密码不能为空"})
    admin = Admin.query.filter_by(username=username).first()
    if not admin or not admin.check_password(password):
        return jsonify({"code": -1, "message": "用户名或密码错误"})
    session['admin_id'] = admin.id
    return jsonify({"code": 0, "message": "ok", "data": {"username": username}})


@api_bp.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_id', None)
    return jsonify({"code": 0, "message": "ok"})


@api_bp.route('/admin/check', methods=['GET'])
def admin_check():
    if session.get('admin_id'):
        return jsonify({"code": 0, "message": "ok", "data": {"logged": True}})
    return jsonify({"code": 0, "message": "ok", "data": {"logged": False}})


@api_bp.route('/weather', methods=['GET'])
def weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"code": -1, "message": "缺少经纬度参数"})
    # 占位返回，实际可对接和风天气等 API
    return jsonify({
        "code": 0, "message": "ok",
        "data": {"temp": 25, "desc": "晴", "wind": "东风2级", "humidity": 60}
    })


@api_bp.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json() or {}
    weather_desc = (data.get('weather') or {}).get('desc', '晴')
    scene = data.get('scene', '通勤')
    # 根据天气和场景筛选服装（文本包含匹配）
    items = Wardrobe.query.filter(
        Wardrobe.weather.contains(weather_desc),
        Wardrobe.scene.contains(scene)
    ).limit(6).all()
    if not items:
        items = Wardrobe.query.limit(6).all()
    return jsonify({
        "code": 0, "message": "ok",
        "data": {"items": [_wardrobe_to_dict(i) for i in items]}
    })


@api_bp.route('/categories', methods=['GET'])
def categories():
    cats = Category.query.order_by(Category.order).all()
    return jsonify({
        "code": 0, "message": "ok",
        "data": [{"id": c.id, "name": c.name, "order": c.order} for c in cats]
    })


@api_bp.route('/wardrobe', methods=['GET', 'POST'])
def wardrobe():
    if request.method == 'GET':
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        q = Wardrobe.query
        if keyword:
            q = q.filter(Wardrobe.name.like(f'%{keyword}%'))
        if category:
            q = q.filter(Wardrobe.category == category)
        items = q.order_by(Wardrobe.update_time.desc()).all()
        return jsonify({"code": 0, "message": "ok", "data": {"list": [_wardrobe_to_dict(i) for i in items]}})
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        category = data.get('category', '').strip()
        tags = data.get('tags') or []
        image = (data.get('image') or '').strip()
        scene = data.get('scene') or []
        weather = data.get('weather') or []
        if not name:
            return jsonify({"code": -1, "message": "服装名称不能为空"})
        now = datetime.utcnow()
        w = Wardrobe(
            name=name, category=category,
            tags=json.dumps(tags, ensure_ascii=False),
            image=image,
            scene=json.dumps(scene, ensure_ascii=False),
            weather=json.dumps(weather, ensure_ascii=False),
            create_time=now, update_time=now
        )
        db.session.add(w)
        db.session.commit()
        return jsonify({"code": 0, "message": "ok", "data": {"id": w.id}})


@api_bp.route('/wardrobe/<int:item_id>', methods=['PUT', 'DELETE'])
def wardrobe_item(item_id):
    w = Wardrobe.query.get(item_id)
    if not w:
        return jsonify({"code": -1, "message": "服装不存在"})
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'name' in data:
            w.name = (data.get('name') or '').strip() or w.name
        if 'category' in data:
            w.category = (data.get('category') or '').strip()
        if 'tags' in data:
            w.tags = json.dumps(data.get('tags') or [], ensure_ascii=False)
        if 'image' in data:
            w.image = (data.get('image') or '').strip()
        if 'scene' in data:
            w.scene = json.dumps(data.get('scene') or [], ensure_ascii=False)
        if 'weather' in data:
            w.weather = json.dumps(data.get('weather') or [], ensure_ascii=False)
        w.update_time = datetime.utcnow()
        db.session.commit()
        return jsonify({"code": 0, "message": "ok"})
    if request.method == 'DELETE':
        db.session.delete(w)
        db.session.commit()
        return jsonify({"code": 0, "message": "ok"})
    return jsonify({"code": -1, "message": "method not allowed"})
