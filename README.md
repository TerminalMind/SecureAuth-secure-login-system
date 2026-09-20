# 🔐 SecureAuth — Secure Login & Authentication System

A secure user authentication system built using **Python Flask and SQLite**, designed to demonstrate modern web application security practices.

The project implements secure password hashing, user authentication, session management, SQL injection prevention, brute-force protection, and optional Two-Factor Authentication (2FA).

It is designed as a cybersecurity portfolio project to demonstrate practical knowledge of authentication security and secure web development.

---

## 📌 Project Overview

| Information               | Details                                  |
| ------------------------- | ---------------------------------------- |
| Project Name              | SecureAuth                               |
| Category                  | Cybersecurity / Web Application Security |
| Backend                   | Python, Flask                            |
| Frontend                  | HTML, CSS                                |
| Database                  | SQLite                                   |
| Password Hashing          | Argon2id                                 |
| Two-Factor Authentication | TOTP                                     |
| Testing Framework         | pytest                                   |
| Development Status        | Educational / Development                |

## ✨ Features

### 1. User Authentication

* Secure user registration
* Login using username or email
* Password verification
* Logout functionality
* Protected dashboard
* Duplicate account prevention

### 2. Password Security

* Argon2id password hashing
* Password strength validation
* Minimum password length of 12 characters
* Password confirmation
* Passwords are never stored in plaintext

### 3. SQL Injection Protection

* Parameterized SQLite queries
* Server-side input validation
* Protection against common SQL injection attempts

### 4. Session Security

* Session-based authentication
* HTTPOnly session cookies
* SameSite cookie configuration
* Session expiration
* Logout clears authentication session

### 5. Brute-Force Protection

* Login rate limiting
* Failed login attempt tracking
* Temporary account lockout after five failed attempts
* Automatic unlock after ten minutes

### 6. Two-Factor Authentication

Optional TOTP-based two-factor authentication.

Compatible with applications such as Google Authenticator and Microsoft Authenticator.

Authentication flow:

Username / Email → Password → 2FA Code → Dashboard

### 7. CSRF Protection

Flask-WTF provides CSRF protection for forms, including registration, login, logout, and 2FA operations.

### 8. Security Headers

The application configures security headers, including:

* Content-Security-Policy
* X-Content-Type-Options
* X-Frame-Options
* Referrer-Policy

### 9. Security Audit Logs

Records important authentication events, including:

* User registration
* Successful login
* Failed login
* Account lockout
* 2FA activation
* Logout

### 10. Admin Dashboard

An administrator-only dashboard displays registered users and recent security events.

Admin access requires the appropriate database role.

---

## 🛠️ Technology Stack

| Technology    | Purpose                   |
| ------------- | ------------------------- |
| Python        | Backend programming       |
| Flask         | Web framework             |
| SQLite        | Database                  |
| Argon2-cffi   | Password hashing          |
| Flask-WTF     | CSRF protection           |
| Flask-Limiter | Rate limiting             |
| PyOTP         | Two-factor authentication |
| HTML & CSS    | Frontend                  |
| pytest        | Automated testing         |

---

## 📁 Project Structure

```text
Secure-Login-System/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── pytest.ini
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── verify_2fa.html
│   ├── setup_2fa.html
│   └── admin.html
│
├── static/
│   └── style.css
│
└── tests/
    └── test_security.py
```

Note: `pytest.ini` is optional. Local databases, virtual environments, and actual environment secrets should not be committed.

---

## ⚙️ Installation and Setup

### Prerequisites

* Python 3.11 or later
* Git
* pip
* A code editor such as VS Code

### Step 1: Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Secure-Login-System.git
```

```bash
cd Secure-Login-System
```

Replace `YOUR_USERNAME` with your GitHub username.

### Step 2: Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file using `.env.example` as a template.

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Store the generated value in `.env`:

```env
SECRET_KEY=your-generated-secret-key
```

The current application reads `SECRET_KEY` from the process environment. It does not automatically load `.env`, so you must export the variable or configure an environment loader.

For Windows PowerShell:

```powershell
$env:SECRET_KEY="your-generated-secret-key"
```

Never upload your real `.env` file to GitHub.

### Step 5: Initialize the database

```powershell
python -m flask --app app init-db
```

### Step 6: Run the application

```powershell
python app.py
```

Open your browser:

http://127.0.0.1:5000

---

## 🔑 Authentication Workflow

```text
User Registration
       |
       v
Input Validation
       |
       v
Argon2id Password Hashing
       |
       v
Store User in SQLite
       |
       v
Login
       |
       v
Password Verification
       |
       v
Two-Factor Authentication
(if enabled)
       |
       v
Authenticated Session
       |
       v
User Dashboard
       |
       v
Logout
```

---

## 🧪 Automated Security Testing

The project includes automated security tests using pytest.

Run:

```bash
python -m pytest -q
```

The included test suite checks:

| Test                   | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| Registration           | Verify successful registration                        |
| Login                  | Verify valid credentials                              |
| Password Validation    | Reject weak passwords                                 |
| Duplicate Registration | Reject duplicate accounts                             |
| SQL Injection          | Verify a common injection payload cannot authenticate |
| Access Control         | Block unauthenticated dashboard access                |
| Logout                 | Clear the authentication session                      |
| Security Headers       | Verify configured response headers                    |

The registration and login checks share one test, giving seven test functions in the supplied suite.

These tests provide basic coverage and are not a complete penetration test or security audit.

---

## 🛡️ Security Considerations

This project is intended for educational and portfolio use.

Before deploying it publicly:

* Configure a strong production secret key.
* Enable HTTPS.
* Set `SESSION_COOKIE_SECURE=True`.
* Disable Flask debug mode.
* Configure persistent rate-limit storage such as Redis.
* Protect TOTP secrets at rest.
* Implement secure session invalidation.
* Review account lockout and authentication workflows.
* Keep dependencies updated.
* Perform additional security testing.

The development configuration must not be treated as production-ready.

---

## 🚀 Future Enhancements

* Email verification
* Password reset functionality
* Password change functionality
* Recovery codes for 2FA
* WebAuthn / Passkey authentication
* Active session management
* Redis-backed rate limiting
* Docker deployment
* CI/CD security testing
* Dependency vulnerability scanning
* Security monitoring dashboard
* OWASP ASVS-based security review

---

## 📚 Learning Outcomes

This project demonstrates practical knowledge of:

* Secure authentication
* Password hashing
* Web application security
* SQL injection prevention
* Session management
* CSRF protection
* Two-factor authentication
* Brute-force protection
* Security event logging
* Automated security testing

---

## ⚠️ Disclaimer

This project is developed for educational purposes and cybersecurity learning.

It should undergo further security review, testing, and production hardening before being used with real user accounts.

---

## 👨‍💻 Author

**Shivam**

MCA — Cybersecurity Specialization



---

⭐ If you find this project useful, consider giving the repository a star.
