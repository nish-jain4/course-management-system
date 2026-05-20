# CMS Portal

Flask-based course management system backed by MySQL and prepared for Heroku deployment.

## What The App Supports

- Student registration and login
- Admin login and dashboard
- Instructor course creation and module management
- Course catalog and detail pages
- Enrollments and payment records
- Reviews and progress tracking
- Automatic demo catalog seeding on a blank database

## Environment Variables

The app supports either a single MySQL URL or individual connection fields.

- `JAWSDB_URL`
- `JAWSDB_MARIA_URL`
- `CLEARDB_DATABASE_URL`
- `DATABASE_URL`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_SSL_CA`
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

If a MySQL URL is present, it takes priority over the individual `DB_*` values.

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

## Heroku Deployment With MySQL

This repository is ready for Heroku with `gunicorn`, a `Procfile`, and automatic MySQL schema bootstrap.

1. Log in to Heroku:

```bash
heroku login
```

2. Create the Heroku app:

```bash
heroku create your-app-name
```

3. Provision MySQL with JawsDB:

```bash
heroku addons:create jawsdb
```

4. Set the app secrets:

```bash
heroku config:set SECRET_KEY=change-me ADMIN_USERNAME=admin ADMIN_EMAIL=admin@cms.demo ADMIN_PASSWORD=admin123
```

5. Deploy:

```bash
git push heroku main
```

6. Open the app:

```bash
heroku open
```

7. Check logs if needed:

```bash
heroku logs --tail
```

## Heroku Notes

- JawsDB creates a `JAWSDB_URL` or `JAWSDB_MARIA_URL` config var automatically. This app reads either value directly, so you do not need extra code changes.
- A brand-new JawsDB database can take a few minutes before it is fully ready.
- The first request will create the required tables and seed the demo catalog if the database is empty.
