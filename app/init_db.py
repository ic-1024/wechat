# -*- coding: utf-8 -*-
"""数据库初始化脚本 - 随后端启动自动执行
   由 run.py 在 app_context 中调用，不再自行创建 app
"""
import json
from .models import db, Admin, Category, Wardrobe

DEMO_ITEMS = [
    {
        'name': '白色衬衫', 'category': '上衣',
        'tags': ['正式', '百搭'], 'scene': ['通勤'], 'weather': ['晴', '阴'],
        'image': 'https://images.unsplash.com/photo-1598032895397-b9472444bf93?w=300&h=300&fit=crop'
    },
    {
        'name': '休闲牛仔裤', 'category': '裤子',
        'tags': ['休闲', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴'],
        'image': 'https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?w=300&h=300&fit=crop'
    },
    {
        'name': '黑色西服外套', 'category': '外套',
        'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴', '雨'],
        'image': 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=300&h=300&fit=crop'
    },
    {
        'name': '运动鞋', 'category': '鞋子',
        'tags': ['运动', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴'],
        'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300&h=300&fit=crop'
    },
    {
        'name': '条纹T恤', 'category': '上衣',
        'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴'],
        'image': 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=300&h=300&fit=crop'
    },
    {
        'name': '卡其裤', 'category': '裤子',
        'tags': ['休闲', '百搭'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴'],
        'image': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=300&h=300&fit=crop'
    },
    {
        'name': '防风外套', 'category': '外套',
        'tags': ['防风', '保暖'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴', '雨'],
        'image': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=300&h=300&fit=crop'
    },
    {
        'name': '帆布鞋', 'category': '鞋子',
        'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴'],
        'image': 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=300&h=300&fit=crop'
    },
    {
        'name': '格子衬衫', 'category': '上衣',
        'tags': ['休闲', '文艺'], 'scene': ['休息'], 'weather': ['晴', '阴'],
        'image': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=300&h=300&fit=crop'
    },
    {
        'name': '运动短裤', 'category': '裤子',
        'tags': ['运动', '舒适'], 'scene': ['休息', '运动'], 'weather': ['晴'],
        'image': 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=300&h=300&fit=crop'
    },
    {
        'name': '羽绒服', 'category': '外套',
        'tags': ['保暖', '冬季'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴', '雪'],
        'image': 'https://images.unsplash.com/photo-1544923246-77307dd270cb?w=300&h=300&fit=crop'
    },
    {
        'name': '皮鞋', 'category': '鞋子',
        'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴'],
        'image': 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=300&h=300&fit=crop'
    },
]

IMAGE_MAP = {item['name']: item['image'] for item in DEMO_ITEMS}


def run():
    """在已有 app_context 中初始化数据库并填充演示数据"""
    db.create_all()

    if Admin.query.filter_by(username='admin').first() is None:
        admin = Admin(username='admin')
        admin.set_password('123456')
        db.session.add(admin)

    if Category.query.count() == 0:
        for i, name in enumerate(['上衣', '裤子', '外套', '鞋子', '配饰']):
            db.session.add(Category(name=name, sort_order=i))

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
        empty_img_items = Wardrobe.query.filter(
            (Wardrobe.image == '') | (Wardrobe.image.is_(None))
        ).all()
        for w in empty_img_items:
            if w.name in IMAGE_MAP:
                w.image = IMAGE_MAP[w.name]
                updated += 1
        if updated:
            print(f'[init_db] 为 {updated} 件已有服装补充了图片')

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
