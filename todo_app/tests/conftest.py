import pytest
from app import app
from database import get_db_connection

TEST_DOMAIN = "@test.invalid"


def delete_test_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email LIKE %s", ("%" + TEST_DOMAIN,))
    conn.commit()
    cursor.close()
    conn.close()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    delete_test_users()
    with app.test_client() as test_client:
        yield test_client
    delete_test_users()