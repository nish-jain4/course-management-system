# CMS Portal

Flask-based course management system connected directly to the MySQL Workbench schema `mydb`.

## Database Tables Used

- `roles`
- `users`
- `categories`
- `courses`
- `enrollments`
- `payments`
- `course_content`
- `reviews`

## What The App Supports

- Student registration using `roles` and `users`
- Single login page for students, instructors, and admin
- Admin username/password that redirects to a separate admin dashboard
- Login for student and instructor accounts using the `users` table
- Course catalog from `courses` and `categories`
- Course detail page with modules from `course_content`
- Enrollment flow that creates rows in `enrollments` and `payments`
- Review submission using `reviews`
- Instructor course creation and module management
- Admin dashboard with student, instructor, course, and enrollment insights
- Admin tools to add categories, edit courses/modules, and delete reviews

## Config

Database settings stay in `config.py`.

Default values:

- `DB_HOST=localhost`
- `DB_PORT=3306`
- `DB_USER=root`
- `DB_PASSWORD=1234`
- `DB_NAME=mydb`
- `ADMIN_USERNAME=admin`
- `ADMIN_EMAIL=admin@cms.demo`
- `ADMIN_PASSWORD=admin123`

You can override them with environment variables if needed.

## Database Setup

MySQL Workbench itself does not need any special app-specific plugin. The important part is that your MySQL Server connection, schema, and tables match what the Flask app expects.

1. Start your local MySQL Server.
2. Open MySQL Workbench and connect to the same server used by the app:
   - Host: `localhost`
   - Port: `3306`
   - Username: `root`
   - Password: `1234`
3. Open [`schema.sql`](schema.sql) in Workbench and run it.
4. If your server uses different credentials or a different schema name, update `config.py` or set environment variables before starting the app.

## Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure MySQL Server is running, then run [`schema.sql`](schema.sql) once so the `mydb` schema and required tables exist.

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000/`

Use the regular login page at `http://127.0.0.1:5000/login`.
Students and instructors sign in with email, while admin signs in there with the admin username and password.
