import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests")

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def db_engine():
    """
    Один раз создаём таблицы для тестов.
    Используется тот же engine, что и в приложении (Postgres из DATABASE_URL).
    """
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db(db_engine):
    """
    Перед каждым тестом очищаем все таблицы ORM (users, wishes и т.п.),
    чтобы тесты не мешали друг другу.
    """
    with db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(scope="session")
def client(db_engine) -> TestClient:
    """
    Общий TestClient. При создании триггерится startup-событие приложения.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session() -> Session:
    """
    Если в тесте нужно напрямую работать с SessionLocal.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
