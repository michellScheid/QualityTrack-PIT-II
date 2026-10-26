"""Conexão e esquema SQLite do QualityTrack."""
import sqlite3
from pathlib import Path
from flask import current_app, g

DEFAULT_SECTORS = ('Produção', 'Qualidade', 'Logística', 'Manutenção')


def get_db():
    if 'db' not in g:
        db = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        g.db = db
    return g.db


def close_db(exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = Path(__file__).with_name('schema.sql')
    db.executescript(schema_path.read_text(encoding='utf-8'))
    for sector in DEFAULT_SECTORS:
        db.execute('INSERT OR IGNORE INTO sectors (name) VALUES (?)', (sector,))
    db.commit()


def query(sql, params=(), one=False):
    rows = get_db().execute(sql, params).fetchall()
    return rows[0] if one and rows else (None if one else rows)


def record_history(nc_id, actor_id, event, details):
    get_db().execute(
        'INSERT INTO audit_history (nc_id,actor_id,event,details) VALUES (?,?,?,?)',
        (nc_id, actor_id, event, details)
    )
