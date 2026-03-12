# -*- coding: utf-8 -*-
"""数据库初始化脚本 - 随后端启动自动执行"""
import json


def run():
    """启动时初始化数据库，创建表并填充演示数据"""
    from . import create_app
    from .models import db, Admin, Category, Wardrobe

    app = create_app()
    with app.app_context():
        db.create_all()

        # 填充管理员（测试账号：admin / 123456）
        if Admin.query.filter_by(username='admin').first() is None:
            admin = Admin(username='admin')
            admin.set_password('123456')
            db.session.add(admin)

        # 填充服装分类
        if Category.query.count() == 0:
            for i, name in enumerate(['上衣', '裤子', '外套', '鞋子', '配饰']):
                db.session.add(Category(name=name, order=i))

        # 填充示例服装
        if Wardrobe.query.count() == 0:
            from datetime import datetime
            items = [
                {'name': '白色衬衫', 'category': '上衣', 'tags': ['正式', '百搭'], 'scene': ['通勤'], 'weather': ['晴', '阴']},
                {'name': '休闲牛仔裤', 'category': '裤子', 'tags': ['休闲', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴']},
                {'name': '黑色西服外套', 'category': '外套', 'tags': ['正式', '商务'], 'scene': ['通勤'], 'weather': ['晴', '阴', '雨']},
                {'name': '运动鞋', 'category': '鞋子', 'tags': ['运动', '舒适'], 'scene': ['休息', '通勤'], 'weather': ['晴', '阴']},
                {'name': '条纹T恤', 'category': '上衣', 'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴']},
                {'name': '卡其裤', 'category': '裤子', 'tags': ['休闲', '百搭'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴']},
                {'name': '防风外套', 'category': '外套', 'tags': ['防风', '保暖'], 'scene': ['通勤', '休息'], 'weather': ['晴', '阴', '雨']},
                {'name': '帆布鞋', 'category': '鞋子', 'tags': ['休闲'], 'scene': ['休息'], 'weather': ['晴']},
            ]
            for item in items:
                w = Wardrobe(
                    name=item['name'],
                    category=item['category'],
                    tags=json.dumps(item['tags'], ensure_ascii=False),
                    image='',
                    scene=json.dumps(item['scene'], ensure_ascii=False),
                    weather=json.dumps(item['weather'], ensure_ascii=False),
                )
                db.session.add(w)

        db.session.commit()
