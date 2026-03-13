# -*- coding: utf-8 -*-
"""数据库初始化脚本 - 随后端启动自动执行
   由 run.py 在 app_context 中调用，不再自行创建 app
"""
import json
from .models import db, Admin, Category, Wardrobe


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
        items = [
            {'name': '白色衬衫', 'category': '上衣', 'tags': ['正式', '百搭'], 'scene': ['通勤'], 'weather': ['晴', '阴']},
            {'name': '休闲牛仔裤', 'category': '裤子', 'tags': ['休闲', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴']},
            {'name': '黑色西服外套', 'category': '外套', 'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴', '雨']},
            {'name': '运动鞋', 'category': '鞋子', 'tags': ['运动', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴']},
            {'name': '条纹T恤', 'category': '上衣', 'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴']},
            {'name': '卡其裤', 'category': '裤子', 'tags': ['休闲', '百搭'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴']},
            {'name': '防风外套', 'category': '外套', 'tags': ['防风', '保暖'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴', '雨']},
            {'name': '帆布鞋', 'category': '鞋子', 'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴']},
            {'name': '格子衬衫', 'category': '上衣', 'tags': ['休闲', '文艺'], 'scene': ['休息'], 'weather': ['晴', '阴']},
            {'name': '运动短裤', 'category': '裤子', 'tags': ['运动', '舒适'], 'scene': ['休息'], 'weather': ['晴']},
            {'name': '羽绒服', 'category': '外套', 'tags': ['保暖', '冬季'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴', '雪']},
            {'name': '皮鞋', 'category': '鞋子', 'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴']},
        ]
        for item in items:
            db.session.add(Wardrobe(
                name=item['name'],
                category=item['category'],
                tags=json.dumps(item['tags'], ensure_ascii=False),
                image='',
                scene=json.dumps(item['scene'], ensure_ascii=False),
                weather=json.dumps(item['weather'], ensure_ascii=False),
            ))

    db.session.commit()
    print('[init_db] 数据库初始化完成')
