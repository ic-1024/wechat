# -*- coding: utf-8 -*-
"""API 路由"""
import json
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.models import db, Admin, Category, Wardrobe

api_bp = Blueprint('api', __name__)


def _parse_json(s):
    if not s:
        return []
    try:
        return json.loads(s) if isinstance(s, str) else s
    except Exception:
        return []


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
    logged = bool(session.get('admin_id'))
    return jsonify({"code": 0, "message": "ok", "data": {"logged": logged}})


@api_bp.route('/weather', methods=['GET'])
def weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"code": -1, "message": "缺少经纬度参数"})
    return jsonify({
        "code": 0, "message": "ok",
        "data": {"temp": 25, "desc": "晴", "wind": "东风2级", "humidity": 60}
    })


@api_bp.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json() or {}
    weather_desc = (data.get('weather') or {}).get('desc', '晴')
    scene = data.get('scene', '通勤')
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
    cats = Category.query.order_by(Category.sort_order).all()
    return jsonify({
        "code": 0, "message": "ok",
        "data": [{"id": c.id, "name": c.name, "order": c.sort_order} for c in cats]
    })


@api_bp.route('/wardrobe', methods=['GET', 'POST'])
def wardrobe_list():
    if request.method == 'GET':
        keyword = request.args.get('keyword', '')
        cat = request.args.get('category', '')
        q = Wardrobe.query
        if keyword:
            q = q.filter(Wardrobe.name.like(f'%{keyword}%'))
        if cat:
            q = q.filter(Wardrobe.category == cat)
        items = q.order_by(Wardrobe.update_time.desc()).all()
        return jsonify({"code": 0, "message": "ok", "data": {"list": [_wardrobe_to_dict(i) for i in items]}})

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    cat = data.get('category', '').strip()
    if not name:
        return jsonify({"code": -1, "message": "服装名称不能为空"})
    now = datetime.utcnow()
    w = Wardrobe(
        name=name, category=cat,
        tags=json.dumps(data.get('tags') or [], ensure_ascii=False),
        image=(data.get('image') or '').strip(),
        scene=json.dumps(data.get('scene') or [], ensure_ascii=False),
        weather=json.dumps(data.get('weather') or [], ensure_ascii=False),
        create_time=now, update_time=now
    )
    db.session.add(w)
    db.session.commit()
    return jsonify({"code": 0, "message": "ok", "data": {"id": w.id}})


@api_bp.route('/wardrobe/<int:item_id>', methods=['PUT', 'DELETE'])
def wardrobe_item(item_id):
    w = db.session.get(Wardrobe, item_id)
    if not w:
        return jsonify({"code": -1, "message": "服装不存在"})
    if request.method == 'DELETE':
        db.session.delete(w)
        db.session.commit()
        return jsonify({"code": 0, "message": "ok"})
    data = request.get_json() or {}
    if 'name' in data and data['name']:
        w.name = data['name'].strip()
    if 'category' in data:
        w.category = (data['category'] or '').strip()
    if 'tags' in data:
        w.tags = json.dumps(data['tags'] or [], ensure_ascii=False)
    if 'image' in data:
        w.image = (data['image'] or '').strip()
    if 'scene' in data:
        w.scene = json.dumps(data['scene'] or [], ensure_ascii=False)
    if 'weather' in data:
        w.weather = json.dumps(data['weather'] or [], ensure_ascii=False)
    w.update_time = datetime.utcnow()
    db.session.commit()
    return jsonify({"code": 0, "message": "ok"})
