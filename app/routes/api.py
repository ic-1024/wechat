# -*- coding: utf-8 -*-
"""API 路由"""
import os
import json
import uuid
import base64
import random
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime
from app.models import db, Admin, User, Category, Wardrobe, Scene
try:
    from zhconv import convert as zhconv_convert
    def to_simplified(text):
        return zhconv_convert(text, 'zh-cn') if text else text
except ImportError:
    def to_simplified(text):
        return text

api_bp = Blueprint('api', __name__)

WMO_WEATHER_MAP = {
    0: ('晴', '☀️'), 1: ('少云', '🌤'), 2: ('多云', '⛅'), 3: ('阴', '☁️'),
    45: ('雾', '🌫'), 48: ('雾凇', '🌫'),
    51: ('小毛毛雨', '🌦'), 53: ('毛毛雨', '🌦'), 55: ('密毛毛雨', '🌦'),
    56: ('冻毛毛雨', '🌧'), 57: ('冻毛毛雨', '🌧'),
    61: ('小雨', '🌧'), 63: ('中雨', '🌧'), 65: ('大雨', '🌧'),
    66: ('冻雨', '🌧'), 67: ('冻雨', '🌧'),
    71: ('小雪', '🌨'), 73: ('中雪', '🌨'), 75: ('大雪', '🌨'),
    77: ('雪粒', '🌨'),
    80: ('小阵雨', '🌦'), 81: ('阵雨', '🌦'), 82: ('大阵雨', '🌦'),
    85: ('小阵雪', '🌨'), 86: ('大阵雪', '🌨'),
    95: ('雷暴', '⛈'), 96: ('雷暴冰雹', '⛈'), 99: ('雷暴大冰雹', '⛈'),
}

WIND_DIRS = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']


def _wmo_to_desc(code):
    return WMO_WEATHER_MAP.get(code, ('未知', '❓'))


def _wind_direction(deg):
    if deg is None:
        return '无'
    idx = round(deg / 45) % 8
    return WIND_DIRS[idx] + '风'


def _wind_level(speed_kmh):
    if speed_kmh is None:
        return ''
    ms = speed_kmh / 3.6
    if ms < 0.3: return '0级'
    if ms < 1.6: return '1级'
    if ms < 3.4: return '2级'
    if ms < 5.5: return '3级'
    if ms < 8.0: return '4级'
    if ms < 10.8: return '5级'
    if ms < 13.9: return '6级'
    return '7级以上'


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


@api_bp.route('/user/register', methods=['POST'])
def user_register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({"code": -1, "message": "用户名和密码不能为空"})
    if len(username) < 2 or len(username) > 20:
        return jsonify({"code": -1, "message": "用户名长度需在2-20个字符之间"})
    if len(password) < 4:
        return jsonify({"code": -1, "message": "密码长度不能少于4位"})
    if User.query.filter_by(username=username).first():
        return jsonify({"code": -1, "message": "该用户名已被注册"})
    u = User(username=username, nickname=username)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify({"code": 0, "message": "注册成功", "data": u.to_dict()})


@api_bp.route('/user/login', methods=['POST'])
def user_login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({"code": -1, "message": "用户名和密码不能为空"})
    u = User.query.filter_by(username=username).first()
    if not u or not u.check_password(password):
        return jsonify({"code": -1, "message": "用户名或密码错误"})
    return jsonify({"code": 0, "message": "登录成功", "data": u.to_dict()})


@api_bp.route('/user/wxlogin', methods=['POST'])
def user_wxlogin():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    if not code:
        return jsonify({"code": -1, "message": "缺少 code 参数"})
    appid = os.environ.get('WX_APPID', current_app.config.get('WX_APPID', ''))
    secret = os.environ.get('WX_SECRET', current_app.config.get('WX_SECRET', ''))
    if not appid or not secret:
        return jsonify({"code": -1, "message": "服务端未配置 AppID/Secret"})
    try:
        resp = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
            'appid': appid, 'secret': secret,
            'js_code': code, 'grant_type': 'authorization_code'
        }, timeout=10, verify=False)
        wx_data = resp.json()
    except Exception as e:
        return jsonify({"code": -1, "message": f"微信接口请求失败: {str(e)}"})
    openid = wx_data.get('openid')
    if not openid:
        errmsg = wx_data.get('errmsg', '未知错误')
        return jsonify({"code": -1, "message": f"获取 openid 失败: {errmsg}"})
    u = User.query.filter_by(openid=openid).first()
    if not u:
        short_id = openid[-6:]
        u = User(openid=openid, username=f'wx_{short_id}', nickname=f'微信用户{short_id}')
        db.session.add(u)
        db.session.commit()
    return jsonify({"code": 0, "message": "登录成功", "data": u.to_dict()})


@api_bp.route('/user/profile', methods=['PUT'])
def user_profile_update():
    data = request.get_json() or {}
    user_id = data.get('userId') or data.get('user_id')
    if not user_id:
        return jsonify({"code": -1, "message": "缺少用户ID"})
    u = db.session.get(User, int(user_id))
    if not u:
        return jsonify({"code": -1, "message": "用户不存在"})
    if 'nickname' in data:
        u.nickname = (data['nickname'] or '').strip() or u.username
    if 'avatarUrl' in data:
        u.avatar_url = (data['avatarUrl'] or '').strip()
    db.session.commit()
    return jsonify({"code": 0, "message": "ok", "data": u.to_dict()})


@api_bp.route('/weather', methods=['GET'])
def weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"code": -1, "message": "缺少经纬度参数"})

    try:
        lat_f, lon_f = float(lat), float(lon)
    except ValueError:
        return jsonify({"code": -1, "message": "经纬度参数格式错误"})

    city = "未知城市"
    try:
        geo_resp = requests.get(
            'https://nominatim.openstreetmap.org/reverse',
            params={'lat': lat_f, 'lon': lon_f, 'format': 'json', 'accept-language': 'zh-CN,zh-Hans,zh', 'zoom': 10},
            headers={'User-Agent': 'WeatherClothingApp/1.0'},
            timeout=5, verify=False
        )
        geo_data = geo_resp.json()
        addr = geo_data.get('address', {})
        city = addr.get('city') or addr.get('town') or addr.get('county') or addr.get('state') or city
        city = to_simplified(city)
    except Exception:
        try:
            geo_resp2 = requests.get(
                f'https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat_f}&longitude={lon_f}&localityLanguage=zh-CN',
                timeout=5, verify=False
            )
            geo2 = geo_resp2.json()
            city = geo2.get('city') or geo2.get('locality') or geo2.get('principalSubdivision') or city
            city = to_simplified(city)
        except Exception:
            pass

    try:
        resp = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': lat_f,
                'longitude': lon_f,
                'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m',
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min',
                'timezone': 'auto',
                'forecast_days': 7
            },
            timeout=10, verify=False
        )
        api_data = resp.json()
    except Exception as e:
        return jsonify({"code": -1, "message": f"天气API请求失败: {str(e)}"})

    current = api_data.get('current', {})
    wmo_code = current.get('weather_code', 0)
    desc, icon = _wmo_to_desc(wmo_code)
    wind_dir = _wind_direction(current.get('wind_direction_10m'))
    wind_lvl = _wind_level(current.get('wind_speed_10m'))

    daily = api_data.get('daily', {})
    forecast = []
    times = daily.get('time', [])
    maxs = daily.get('temperature_2m_max', [])
    mins = daily.get('temperature_2m_min', [])
    codes = daily.get('weather_code', [])
    for i in range(len(times)):
        d, di = _wmo_to_desc(codes[i] if i < len(codes) else 0)
        forecast.append({
            'date': times[i],
            'desc': d,
            'icon': di,
            'tempMax': maxs[i] if i < len(maxs) else 0,
            'tempMin': mins[i] if i < len(mins) else 0,
        })

    return jsonify({
        "code": 0, "message": "ok",
        "data": {
            "temp": round(current.get('temperature_2m', 0)),
            "desc": desc,
            "icon": icon,
            "wind": f"{wind_dir}{wind_lvl}",
            "humidity": current.get('relative_humidity_2m', 0),
            "city": city,
            "lat": round(lat_f, 4),
            "lon": round(lon_f, 4),
            "forecast": forecast,
            "updateTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "apiSource": "Open-Meteo (open-meteo.com)"
        }
    })


@api_bp.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json() or {}
    weather_info = data.get('weather') or {}
    weather_desc = weather_info.get('desc', '晴')
    scene = data.get('scene', '通勤')
    temp = weather_info.get('temp')

    all_items = Wardrobe.query.all()

    scored = []
    for w in all_items:
        score = 0
        w_scene = _parse_json(w.scene)
        w_weather = _parse_json(w.weather)
        if scene in w_scene:
            score += 10
        if weather_desc in w_weather:
            score += 5
        if score > 0:
            scored.append((score, random.random(), w))

    scored.sort(key=lambda x: (-x[0], x[1]))
    items = [s[2] for s in scored[:6]]

    if not items:
        fallback = list(all_items)
        random.shuffle(fallback)
        items = fallback[:6]

    result = [_wardrobe_to_dict(i) for i in items]

    if temp is not None:
        try:
            temp_val = float(temp)
            for item in result:
                if temp_val < 10:
                    item['tempAdvice'] = '天冷注意保暖'
                elif temp_val < 20:
                    item['tempAdvice'] = '适宜穿着'
                elif temp_val < 30:
                    item['tempAdvice'] = '天气舒适'
                else:
                    item['tempAdvice'] = '天热注意防晒'
        except (ValueError, TypeError):
            pass

    return jsonify({
        "code": 0, "message": "ok",
        "data": {"items": result, "scene": scene, "weather": weather_desc}
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


@api_bp.route('/stats', methods=['GET'])
def stats():
    total = Wardrobe.query.count()
    cats = Category.query.order_by(Category.sort_order).all()
    cat_stats = []
    for c in cats:
        cnt = Wardrobe.query.filter_by(category=c.name).count()
        cat_stats.append({"name": c.name, "count": cnt})

    recent = Wardrobe.query.order_by(Wardrobe.create_time.desc()).limit(5).all()

    scene_stats = {}
    all_items = Wardrobe.query.all()
    for item in all_items:
        scenes = _parse_json(item.scene)
        for s in scenes:
            scene_stats[s] = scene_stats.get(s, 0) + 1

    return jsonify({
        "code": 0, "message": "ok",
        "data": {
            "total": total,
            "categories": cat_stats,
            "recent": [_wardrobe_to_dict(i) for i in recent],
            "sceneStats": [{"name": k, "count": v} for k, v in scene_stats.items()]
        }
    })


@api_bp.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json() or {}
    b64 = data.get('base64', '')
    ext = data.get('ext', 'jpg')
    if not b64:
        return jsonify({"code": -1, "message": "缺少 base64 数据"})
    if ',' in b64:
        b64 = b64.split(',', 1)[1]
    try:
        img_bytes = base64.b64decode(b64)
    except Exception:
        return jsonify({"code": -1, "message": "base64 解码失败"})
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(img_bytes)
    url = f"/uploads/{filename}"
    return jsonify({"code": 0, "message": "ok", "data": {"url": url}})


@api_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"code": -1, "message": "分类名称不能为空"})
    exists = Category.query.filter_by(name=name).first()
    if exists:
        return jsonify({"code": -1, "message": "该分类已存在"})
    max_order = db.session.query(db.func.max(Category.sort_order)).scalar() or 0
    cat = Category(name=name, sort_order=max_order + 1)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"code": 0, "message": "ok", "data": {"id": cat.id, "name": cat.name}})


@api_bp.route('/scenes', methods=['GET'])
def scene_list():
    scenes = Scene.query.order_by(Scene.sort_order).all()
    return jsonify({
        "code": 0, "message": "ok",
        "data": [{"id": s.id, "name": s.name} for s in scenes]
    })


@api_bp.route('/scenes', methods=['POST'])
def add_scene():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"code": -1, "message": "场景名称不能为空"})
    exists = Scene.query.filter_by(name=name).first()
    if exists:
        return jsonify({"code": -1, "message": "该场景已存在"})
    max_order = db.session.query(db.func.max(Scene.sort_order)).scalar() or 0
    s = Scene(name=name, sort_order=max_order + 1)
    db.session.add(s)
    db.session.commit()
    return jsonify({"code": 0, "message": "ok", "data": {"id": s.id, "name": s.name}})


@api_bp.route('/city/search', methods=['GET'])
def city_search():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({"code": -1, "message": "缺少搜索关键词"})
    try:
        resp = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': q, 'format': 'json',
                'accept-language': 'zh-CN,zh-Hans,zh',
                'limit': 10,
                'addressdetails': 1,
                'featuretype': 'city',
            },
            headers={'User-Agent': 'WeatherClothingApp/1.0'},
            timeout=8, verify=False
        )
        results = resp.json()
    except Exception as e:
        return jsonify({"code": -1, "message": f"搜索失败: {str(e)}"})
    cities = []
    for r in results:
        display = to_simplified(r.get('display_name', '').split(',')[0])
        cities.append({
            'name': display,
            'displayName': to_simplified(r.get('display_name', '')),
            'lat': r.get('lat'),
            'lon': r.get('lon'),
        })
    return jsonify({"code": 0, "data": cities})


@api_bp.route('/admin/reset-db', methods=['POST'])
def admin_reset_db():
    from app.init_db import reset_demo_data
    try:
        reset_demo_data()
        return jsonify({"code": 0, "message": "演示数据已重置"})
    except Exception as e:
        return jsonify({"code": -1, "message": f"重置失败: {str(e)}"})
