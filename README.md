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
