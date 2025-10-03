from flask import g
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

engine = None

def init_db(app):
    global engine
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"],
        poolclass=QueuePool, pool_size=5, max_overflow=10, pool_pre_ping=True
    )
    app.teardown_appcontext(close_db)

def get_db():
    if 'db' not in g:
        g.db = engine.connect()
    return g.db

def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()