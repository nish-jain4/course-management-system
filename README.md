# Course Management System (Flask)

A Flask-based Course Management System with authentication, protected dashboard access, and modern frontend pages for learners.

## Features

- User registration with password hashing (`werkzeug.security`).
- User login with session handling via `Flask-Login`.
- Protected dashboard route (`/dashboard`) accessible only after login.
- Logout flow that clears authenticated session.
- Route-based navigation using `url_for(...)` in templates.
- Responsive landing page sections (Explore, Courses, Hiring Partners, About).
- Login/Register navigation for desktop and mobile menus.

## Tech Stack

- Python
- Flask
- Flask-Login
- PyMySQL
- MySQL
- HTML/CSS (Jinja templates)

## Project Structure

```text
CMS/
|- app.py
|- config.py
|- templates/
|  |- index.html
|  |- login.html
|  |- register.html
|  |- dashboard.html
|  |- about.html
|  `- course.html
`- static/
   |- index.css
   |- login.css
   |- dashboard.css
   `- logo.png
```

## Routes

- `GET /` -> redirects to `/index`
- `GET /index` -> home/landing page
- `GET, POST /register` -> create account and auto-login on success
- `GET, POST /login` -> authenticate existing user
- `GET /dashboard` -> protected user dashboard (`@login_required`)
- `GET /logout` -> logout and redirect to home
- `GET /about` -> about page
- `GET /course` -> course page

## Database Setup

Create a MySQL database named `cms` and a `users` table:

```sql
CREATE DATABASE IF NOT EXISTS cms;
USE cms;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL
);
```

## Configuration

The app reads database and secret settings from `config.py`.

Current keys used:

- `SECRET_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

Update `config.py` with your local MySQL credentials before running.

## Installation and Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install flask flask-login pymysql werkzeug
```

3. Start the app:

```bash
python app.py
```

4. Open in browser:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/register`
- `http://127.0.0.1:5000/login`

Important: run through Flask on port `5000`; opening templates with Live Server (`127.0.0.1:5500`) will not work for Flask routes/Jinja (`url_for`).

## Authentication Flow

1. New user registers at `/register`.
2. Password is hashed and user is inserted into DB.
3. User is logged in and redirected to `/dashboard`.
4. Returning user logs in at `/login`.
5. Protected routes require authentication (`Flask-Login`).

## Notes

- Duplicate email registration is blocked.
- On failed login, user remains on login page.
- Session-based user state is handled by `Flask-Login` plus current user loading from DB.
