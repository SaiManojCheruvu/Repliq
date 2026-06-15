from sqlalchemy import text
from models import User, Business
import uuid

def test_db_connection(db_session):
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

def test_create_business(db_session):
    biz = Business(id=str(uuid.uuid4()), name="Test Co", agent_name="Bot")
    db_session.add(biz)
    db_session.commit()
    found = db_session.query(Business).filter_by(name="Test Co").first()
    assert found is not None
    assert found.agent_name == "Bot"

def test_create_user(db_session):
    biz = Business(id=str(uuid.uuid4()), name="Biz", agent_name="Agent")
    db_session.add(biz)
    db_session.flush()

    user = User(
        id=str(uuid.uuid4()),
        email="u@test.com",
        hashed_password="hashed",
        business_id=biz.id
    )
    db_session.add(user)
    db_session.commit()

    found = db_session.query(User).filter_by(email="u@test.com").first()
    assert found is not None
    assert found.business_id == biz.id

def test_user_email_unique(db_session):
    import pytest
    from sqlalchemy.exc import IntegrityError

    biz = Business(id=str(uuid.uuid4()), name="B", agent_name="A")
    db_session.add(biz)
    db_session.flush()

    db_session.add(User(id=str(uuid.uuid4()), email="same@test.com", hashed_password="h", business_id=biz.id))
    db_session.commit()

    db_session.add(User(id=str(uuid.uuid4()), email="same@test.com", hashed_password="h", business_id=biz.id))
    with pytest.raises(IntegrityError):
        db_session.commit()