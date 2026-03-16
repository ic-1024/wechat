# -*- coding: utf-8 -*-
"""数据库初始化脚本 - 随后端启动自动执行
   由 run.py 在 app_context 中调用，不再自行创建 app
"""
import json
from .models import db, Admin, User, Category, Wardrobe, Scene

DEMO_ITEMS = [
    {
        'name': '白色衬衫', 'category': '上衣',
        'tags': ['正式', '百搭'], 'scene': ['通勤'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/shirt-white/300/300'
    },
    {
        'name': '休闲牛仔裤', 'category': '裤子',
        'tags': ['休闲', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/jeans-casual/300/300'
    },
    {
        'name': '黑色西服外套', 'category': '外套',
        'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴', '雨'],
        'image': 'https://picsum.photos/seed/blazer-black/300/300'
    },
    {
        'name': '运动鞋', 'category': '鞋子',
        'tags': ['运动', '舒适'], 'scene': ['运动', '休息'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/sneakers-sport/300/300'
    },
    {
        'name': '条纹T恤', 'category': '上衣',
        'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴'],
        'image': 'https://picsum.photos/seed/tshirt-stripe/300/300'
    },
    {
        'name': '卡其裤', 'category': '裤子',
        'tags': ['休闲', '百搭'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/pants-khaki/300/300'
    },
    {
        'name': '防风外套', 'category': '外套',
        'tags': ['防风', '保暖'], 'scene': ['通勤', '运动'], 'weather': ['晴', '阴', '雨'],
        'image': 'https://picsum.photos/seed/jacket-wind/300/300'
    },
    {
        'name': '帆布鞋', 'category': '鞋子',
        'tags': ['休闲'], 'scene': ['休息', '约会'], 'weather': ['晴'],
        'image': 'https://picsum.photos/seed/canvas-shoes/300/300'
    },
    {
        'name': '格子衬衫', 'category': '上衣',
        'tags': ['休闲', '文艺'], 'scene': ['约会', '休息'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/shirt-plaid/300/300'
    },
    {
        'name': '运动短裤', 'category': '裤子',
        'tags': ['运动', '舒适'], 'scene': ['运动'], 'weather': ['晴'],
        'image': 'https://picsum.photos/seed/shorts-sport/300/300'
    },
    {
        'name': '羽绒服', 'category': '外套',
        'tags': ['保暖', '冬季'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴', '雪'],
        'image': 'https://picsum.photos/seed/down-jacket/300/300'
    },
    {
        'name': '皮鞋', 'category': '鞋子',
        'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/leather-shoes/300/300'
    },
    {
        'name': '瑜伽裤', 'category': '裤子',
        'tags': ['运动', '弹力'], 'scene': ['运动'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/yoga-pants/300/300'
    },
    {
        'name': '速干运动T恤', 'category': '上衣',
        'tags': ['运动', '速干'], 'scene': ['运动'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/sport-tee/300/300'
    },
    {
        'name': '碎花连衣裙', 'category': '上衣',
        'tags': ['甜美', '约会'], 'scene': ['约会'], 'weather': ['晴'],
        'image': 'https://picsum.photos/seed/floral-dress/300/300'
    },
    {
        'name': '针织开衫', 'category': '外套',
        'tags': ['温柔', '百搭'], 'scene': ['约会', '休息'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/knit-cardigan/300/300'
    },
    {
        'name': '小白鞋', 'category': '鞋子',
        'tags': ['百搭', '清新'], 'scene': ['约会', '休息'], 'weather': ['晴'],
        'image': 'https://picsum.photos/seed/white-sneaker/300/300'
    },
    {
        'name': '跑步鞋', 'category': '鞋子',
        'tags': ['运动', '专业'], 'scene': ['运动'], 'weather': ['晴', '阴'],
        'image': 'https://picsum.photos/seed/running-shoe/300/300'
    },
]

IMAGE_MAP = {item['name']: item['image'] for item in DEMO_ITEMS}


def run():
    """在已有 app_context 中初始化数据库并填充演示数据"""
    db.create_all()

    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    if 'users' in insp.get_table_names():
        cols = [c['name'] for c in insp.get_columns('users')]
        if 'openid' not in cols:
            db.session.execute(text('ALTER TABLE users ADD COLUMN openid VARCHAR(128)'))
            db.session.commit()
            print('[init_db] users 表新增 openid 列')

    if Admin.query.filter_by(username='admin').first() is None:
        admin = Admin(username='admin')
        admin.set_password('123456')
        db.session.add(admin)

    if User.query.filter_by(username='user').first() is None:
        u = User(username='user', nickname='测试用户',
                 avatar_url='https://picsum.photos/seed/default-avatar/200/200')
        u.set_password('123456')
        db.session.add(u)
        print('[init_db] 创建测试用户 user/123456')

    if Category.query.count() == 0:
        for i, name in enumerate(['上衣', '裤子', '外套', '鞋子', '配饰']):
            db.session.add(Category(name=name, sort_order=i))

    DEFAULT_SCENES = ['通勤', '休息', '运动', '约会']
    if Scene.query.count() == 0:
        for i, name in enumerate(DEFAULT_SCENES):
            db.session.add(Scene(name=name, sort_order=i))
        print('[init_db] 初始化默认场景数据')

    if Wardrobe.query.count() == 0:
        for item in DEMO_ITEMS:
            db.session.add(Wardrobe(
                name=item['name'],
                category=item['category'],
                tags=json.dumps(item['tags'], ensure_ascii=False),
                image=item.get('image', ''),
                scene=json.dumps(item['scene'], ensure_ascii=False),
                weather=json.dumps(item['weather'], ensure_ascii=False),
            ))
        print('[init_db] 插入演示服装数据（含图片）')
    else:
        updated = 0
        for w in Wardrobe.query.all():
            if w.name in IMAGE_MAP and (not w.image or 'unsplash.com' in (w.image or '')):
                w.image = IMAGE_MAP[w.name]
                updated += 1
        if updated:
            print(f'[init_db] 为 {updated} 件服装更新了图片URL')
        existing_names = {w.name for w in Wardrobe.query.all()}
        added = 0
        for item in DEMO_ITEMS:
            if item['name'] not in existing_names:
                db.session.add(Wardrobe(
                    name=item['name'],
                    category=item['category'],
                    tags=json.dumps(item['tags'], ensure_ascii=False),
                    image=item.get('image', ''),
                    scene=json.dumps(item['scene'], ensure_ascii=False),
                    weather=json.dumps(item['weather'], ensure_ascii=False),
                ))
                added += 1
        if added:
            print(f'[init_db] 新增 {added} 件演示服装')

    db.session.commit()
    print('[init_db] 数据库初始化完成')


def reset_demo_data():
    """强制重置演示数据（管理员调用）"""
    Wardrobe.query.delete()
    for item in DEMO_ITEMS:
        db.session.add(Wardrobe(
            name=item['name'],
            category=item['category'],
            tags=json.dumps(item['tags'], ensure_ascii=False),
            image=item.get('image', ''),
            scene=json.dumps(item['scene'], ensure_ascii=False),
            weather=json.dumps(item['weather'], ensure_ascii=False),
        ))
    db.session.commit()
    print('[init_db] 演示数据已重置')
