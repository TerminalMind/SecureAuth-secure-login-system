import os
import pytest

os.environ["SECRET_KEY"] = "test-secret-key"

import app as app_module


# -----------------------------------
# Test Client Fixture
# -----------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch):

    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        app_module,
        "DB_PATH",
        str(db_path)
    )

    app_module.init_db()

    app_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False
    )

    with app_module.app.test_client() as client:
        yield client


# -----------------------------------
# Registration Helper
# -----------------------------------

def register(
    client,
    username="testuser",
    email="test@example.com",
    password="StrongPassword@123"
):

    return client.post(
        "/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password
        },
        follow_redirects=True
    )


# -----------------------------------
# Test 1: Registration and Login
# -----------------------------------

def test_registration_and_login(client):

    response = register(client)

    assert b"Registration successful" in response.data

    response = client.post(
        "/login",
        data={
            "identifier": "testuser",
            "password": "StrongPassword@123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    assert b"Security Dashboard" in response.data


# -----------------------------------
# Test 2: Weak Password
# -----------------------------------

def test_weak_password_rejected(client):

    response = register(
        client,
        password="weak"
    )

    assert b"Password must be at least 12 characters" in response.data


# -----------------------------------
# Test 3: Duplicate Registration
# -----------------------------------

def test_duplicate_user_rejected(client):

    register(client)

    response = register(client)

    assert b"already registered" in response.data


# -----------------------------------
# Test 4: SQL Injection Protection
# -----------------------------------

def test_sql_injection_does_not_login(client):

    register(client)

    response = client.post(
        "/login",
        data={
            "identifier": "' OR '1'='1",
            "password": "anything"
        }
    )

    assert b"Invalid username or password" in response.data


# -----------------------------------
# Test 5: Dashboard Access Protection
# -----------------------------------

def test_dashboard_requires_login(client):

    response = client.get("/dashboard")

    assert response.status_code == 302


# -----------------------------------
# Test 6: Logout and Session Security
# -----------------------------------

def test_logout(client):

    # Register user
    register(client)

    # Login user
    response = client.post(
        "/login",
        data={
            "identifier": "testuser",
            "password": "StrongPassword@123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    assert b"Security Dashboard" in response.data

    # Logout using POST
    response = client.post(
        "/logout",
        follow_redirects=True
    )

    assert response.status_code == 200

    assert b"logged out" in response.data

    # Check dashboard access after logout
    response = client.get("/dashboard")

    assert response.status_code == 302


# -----------------------------------
# Test 7: Security Headers
# -----------------------------------

def test_security_headers(client):

    response = client.get("/")

    assert response.headers[
        "X-Content-Type-Options"
    ] == "nosniff"

    assert response.headers[
        "X-Frame-Options"
    ] == "DENY"

    assert "Content-Security-Policy" in response.headers