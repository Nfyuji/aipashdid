# -*- coding: utf-8 -*-
"""
إضافة الأعمدة المفقودة لجدول analyzed_emails إن وُجدت قاعدة بيانات قديمة.
شغّل مرة واحدة: python migrate_add_columns.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            for col, default in [
                ('classification', "'legitimate'"),
                ('model_used', "'rules'"),
            ]:
                try:
                    conn.execute(text(f'ALTER TABLE analyzed_emails ADD COLUMN {col} VARCHAR(20) DEFAULT {default}'))
                    conn.commit()
                    print(f'Added column: {col}')
                except Exception as e:
                    err = str(e).lower()
                    if 'duplicate column name' in err or 'already exists' in err:
                        print(f'Column {col} already exists, skip.')
                    else:
                        raise
    print('Migration done.')

if __name__ == '__main__':
    migrate()
