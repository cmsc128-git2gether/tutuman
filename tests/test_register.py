from werkzeug.security import check_password_hash
from database import get_user_by_email

EMAIL = "ana@test.invalid"

VALID = {
    "email": EMAIL,
    "display_name": "Ana",
    "password": "password123",
    "confirm_password": "password123",
}


def post_register(client, **overrides):
    return client.post("/register", data={**VALID, **overrides})


# Scenario 1: each validation error shows its own message
def test_empty_fields(client):
    response = post_register(client, email="", display_name="", password="", confirm_password="")
    assert b"All fields are required." in response.data


def test_bad_email(client):
    response = post_register(client, email="abc")
    assert b"valid email" in response.data


def test_short_password(client):
    response = post_register(client, password="abc", confirm_password="abc")
    assert b"at least 8 characters" in response.data


def test_passwords_do_not_match(client):
    response = post_register(client, confirm_password="different123")
    assert b"Passwords do not match." in response.data


def test_fields_stay_filled_after_error(client):
    response = post_register(client, confirm_password="different123")
    assert EMAIL.encode() in response.data
    assert b"Ana" in response.data


# Scenario 2: a valid account redirects to login
def test_valid_registration_redirects_to_login(client):
    response = post_register(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert get_user_by_email(EMAIL) is not None


# Scenario 3: the password is stored hashed
def test_password_is_hashed(client):
    post_register(client)
    user = get_user_by_email(EMAIL)
    assert user["password_hash"] != "password123"
    assert user["password_hash"].startswith(("scrypt:", "pbkdf2:"))
    assert check_password_hash(user["password_hash"], "password123")


# Scenario 4: duplicates are rejected, including different letter case
def test_duplicate_email_rejected(client):
    post_register(client)
    response = post_register(client)
    assert b"already exists" in response.data


def test_duplicate_email_different_case_rejected(client):
    post_register(client)
    response = post_register(client, email="ANA@test.invalid")
    assert b"already exists" in response.data