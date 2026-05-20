# CMS Portal

Flask-based course management system backed by MySQL.

## What The App Supports

- Student registration and login
- Admin login and dashboard
- Instructor course creation and module management
- Course catalog and detail pages
- Enrollments and payment records
- Reviews and progress tracking
- Automatic demo catalog seeding on a blank database

## Environment Variables

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

## Local Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure MySQL Server is running and create a database if you are using the default local settings:

```sql
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000/`

On first use, the app creates its tables automatically and seeds demo categories, demo courses, demo users, and the admin account configured in your environment.
