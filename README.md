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

- Student and Instructor registration using `roles` and `users`
- Login using the `users` table
- Course catalog from `courses` and `categories`
- Course detail page with modules from `course_content`
- Enrollment flow that creates rows in `enrollments` and `payments`
- Review submission using `reviews`
- Instructor course creation and module management

## Config

Database settings stay in `config.py`.

Default values:

- `DB_HOST=localhost`
- `DB_PORT=3306`
- `DB_USER=root`
- `DB_PASSWORD=1234`
- `DB_NAME=mydb`

You can override them with environment variables if needed.

## Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure MySQL Workbench / MySQL Server is running and the `mydb` schema exists.

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000/`
