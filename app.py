from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from threading import Lock
from typing import Any

import pymysql
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config


app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


STATUS_ACTIONS = {
    "start": "In Progress",
    "complete": "Completed",
    "reset": "Enrolled",
}

PAYMENT_METHODS = ["Card", "UPI", "Net Banking", "Cash"]

COURSE_ACCENTS = {
    "Programming": "#1f6f64",
    "Design": "#d96c4b",
    "Analytics": "#355c7d",
    "Marketing": "#c26a3d",
    "Business": "#6b7f3f",
}

ROLE_SEEDS = [
    (1, "Student"),
    (2, "Instructor"),
    (3, "Admin"),
]

CATEGORY_SEEDS = [
    (1, "Programming"),
    (2, "Design"),
    (3, "Analytics"),
    (4, "Marketing"),
    (5, "Business"),
]

DEMO_USERS = [
    {"username": "Ananya Rao", "email": "ananya.rao@cms.demo", "role_name": "Instructor"},
    {"username": "Riya Mehta", "email": "riya.mehta@cms.demo", "role_name": "Instructor"},
    {"username": "Karan Shah", "email": "karan.shah@cms.demo", "role_name": "Instructor"},
    {"username": "Meera Joshi", "email": "meera.joshi@cms.demo", "role_name": "Instructor"},
    {"username": "Arjun Kapoor", "email": "arjun.kapoor@cms.demo", "role_name": "Instructor"},
    {"username": "Aditi Sen", "email": "aditi.sen@cms.demo", "role_name": "Student"},
    {"username": "Rahul Nair", "email": "rahul.nair@cms.demo", "role_name": "Student"},
    {"username": "Sneha Iyer", "email": "sneha.iyer@cms.demo", "role_name": "Student"},
    {"username": "Vikram Patel", "email": "vikram.patel@cms.demo", "role_name": "Student"},
]

DEMO_COURSES = [
    {
        "course_name": "Python for Busy Beginners",
        "description": "Learn the basics with short lessons, small wins, and projects you can finish after work or class.",
        "price": Decimal("999.00"),
        "category_name": "Programming",
        "accent": "#1f6f64",
        "instructor_email": "ananya.rao@cms.demo",
        "modules": [
            "Set up Python without the usual confusion",
            "Use variables, loops, and conditions in small tasks",
            "Read and clean user input with confidence",
            "Finish a mini tracker project from scratch",
        ],
        "reviews": [
            {
                "user_email": "aditi.sen@cms.demo",
                "rating": Decimal("4.8"),
                "comment": "Short lessons and practical examples made it easy to keep going after work.",
                "status": "Completed",
                "payment_method": "UPI",
            },
            {
                "user_email": "rahul.nair@cms.demo",
                "rating": Decimal("4.6"),
                "comment": "A friendly beginner course with enough practice to feel real.",
                "status": "In Progress",
                "payment_method": "Card",
            },
        ],
    },
    {
        "course_name": "Design Better Presentations",
        "description": "Turn rough slides into clear, confident decks that feel polished and easy to follow.",
        "price": Decimal("749.00"),
        "category_name": "Design",
        "accent": "#d96c4b",
        "instructor_email": "riya.mehta@cms.demo",
        "modules": [
            "Choose layouts that guide attention",
            "Write shorter slide copy that lands faster",
            "Use color and contrast without clutter",
            "Turn a messy deck into a client-ready story",
        ],
        "reviews": [
            {
                "user_email": "sneha.iyer@cms.demo",
                "rating": Decimal("4.7"),
                "comment": "The before-and-after examples were strong and easy to apply immediately.",
                "status": "Completed",
                "payment_method": "Net Banking",
            },
            {
                "user_email": "vikram.patel@cms.demo",
                "rating": Decimal("4.5"),
                "comment": "It helped me simplify my slides instead of decorating them.",
                "status": "Completed",
                "payment_method": "UPI",
            },
        ],
    },
    {
        "course_name": "Data Skills for Everyday Work",
        "description": "Build confidence with spreadsheets, reports, and dashboards you can actually use on the job.",
        "price": Decimal("1199.00"),
        "category_name": "Analytics",
        "accent": "#355c7d",
        "instructor_email": "karan.shah@cms.demo",
        "modules": [
            "Clean messy data without overthinking it",
            "Build formulas that save weekly effort",
            "Create charts that explain the story quickly",
            "Package a dashboard for team updates",
        ],
        "reviews": [
            {
                "user_email": "aditi.sen@cms.demo",
                "rating": Decimal("4.9"),
                "comment": "Exactly the kind of practical analytics course I wanted for office reporting.",
                "status": "Completed",
                "payment_method": "Card",
            },
            {
                "user_email": "rahul.nair@cms.demo",
                "rating": Decimal("4.7"),
                "comment": "The dashboard section was especially helpful for daily work.",
                "status": "In Progress",
                "payment_method": "Cash",
            },
        ],
    },
    {
        "course_name": "Social Media Strategy Sprint",
        "description": "Plan sharper campaigns, write stronger hooks, and map content that supports clear business goals.",
        "price": Decimal("899.00"),
        "category_name": "Marketing",
        "accent": "#c26a3d",
        "instructor_email": "meera.joshi@cms.demo",
        "modules": [
            "Find content themes your audience will care about",
            "Build a one-month posting plan that stays realistic",
            "Write hooks, captions, and calls to action",
            "Measure what is working and adjust fast",
        ],
        "reviews": [
            {
                "user_email": "sneha.iyer@cms.demo",
                "rating": Decimal("4.6"),
                "comment": "Clear framework, useful examples, and no fluff.",
                "status": "Completed",
                "payment_method": "UPI",
            },
            {
                "user_email": "vikram.patel@cms.demo",
                "rating": Decimal("4.4"),
                "comment": "The campaign planning templates made my workflow much cleaner.",
                "status": "In Progress",
                "payment_method": "Card",
            },
        ],
    },
    {
        "course_name": "Project Coordination Without Chaos",
        "description": "Run smoother timelines, clearer handoffs, and calmer weekly updates for cross-functional work.",
        "price": Decimal("1099.00"),
        "category_name": "Business",
        "accent": "#6b7f3f",
        "instructor_email": "arjun.kapoor@cms.demo",
        "modules": [
            "Break work into milestones people can follow",
            "Run updates that surface blockers early",
            "Keep stakeholders aligned without long meetings",
            "Create simple systems for follow-through",
        ],
        "reviews": [
            {
                "user_email": "aditi.sen@cms.demo",
                "rating": Decimal("4.8"),
                "comment": "This course made project updates feel much less stressful.",
                "status": "Completed",
                "payment_method": "Net Banking",
            },
            {
                "user_email": "rahul.nair@cms.demo",
                "rating": Decimal("4.5"),
                "comment": "Helpful for organizing team work without adding more process than needed.",
                "status": "Completed",
                "payment_method": "UPI",
            },
        ],
    },
    {
        "course_name": "Frontend Foundations with Flask Templates",
        "description": "Build cleaner page structure, reusable components, and practical UI polish using HTML, CSS, and Flask templates.",
        "price": Decimal("1299.00"),
        "category_name": "Programming",
        "accent": "#1f6f64",
        "instructor_email": "ananya.rao@cms.demo",
        "modules": [
            "Structure a template layout that scales",
            "Use CSS variables for a consistent visual system",
            "Make cards, forms, and grids feel deliberate",
            "Connect template actions back to Flask routes",
        ],
        "reviews": [
            {
                "user_email": "sneha.iyer@cms.demo",
                "rating": Decimal("4.9"),
                "comment": "Loved how practical this felt for small Flask projects.",
                "status": "In Progress",
                "payment_method": "Card",
            },
            {
                "user_email": "vikram.patel@cms.demo",
                "rating": Decimal("4.7"),
                "comment": "It helped me understand how templates and UI pieces connect together.",
                "status": "Completed",
                "payment_method": "UPI",
            },
        ],
    },
]

SAMPLE_COURSES = [
    {
        "course_name": course["course_name"],
        "description": course["description"],
        "price": float(course["price"]),
        "category_name": course["category_name"],
        "module_total": len(course["modules"]),
        "review_total": len(course["reviews"]),
        "instructor_name": next(
            user["username"] for user in DEMO_USERS if user["email"] == course["instructor_email"]
        ),
        "accent": course["accent"],
    }
    for course in DEMO_COURSES[:3]
]

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS roles (
        role_id INT NOT NULL,
        role_name VARCHAR(45) NOT NULL,
        PRIMARY KEY (role_id),
        UNIQUE KEY uq_roles_role_name (role_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT NOT NULL AUTO_INCREMENT,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role_id INT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id),
        UNIQUE KEY uq_users_email (email),
        KEY idx_users_role_id (role_id),
        CONSTRAINT fk_users_role
            FOREIGN KEY (role_id) REFERENCES roles (role_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        category_id INT NOT NULL AUTO_INCREMENT,
        category_name VARCHAR(45) NOT NULL,
        PRIMARY KEY (category_id),
        UNIQUE KEY uq_categories_category_name (category_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS courses (
        course_id INT NOT NULL AUTO_INCREMENT,
        course_name VARCHAR(255) NOT NULL,
        description TEXT NULL,
        price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        category_id INT NULL,
        instructor_id INT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (course_id),
        KEY idx_courses_category_id (category_id),
        KEY idx_courses_instructor_id (instructor_id),
        CONSTRAINT fk_courses_category
            FOREIGN KEY (category_id) REFERENCES categories (category_id)
            ON DELETE SET NULL,
        CONSTRAINT fk_courses_instructor
            FOREIGN KEY (instructor_id) REFERENCES users (user_id)
            ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS course_content (
        content_id INT NOT NULL AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        video_url VARCHAR(1000) NOT NULL,
        module_number INT NOT NULL,
        course_id INT NOT NULL,
        PRIMARY KEY (content_id),
        KEY idx_course_content_course_id (course_id),
        KEY idx_course_content_module_number (course_id, module_number),
        CONSTRAINT fk_course_content_course
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INT NOT NULL AUTO_INCREMENT,
        enrollment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(45) NOT NULL,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        PRIMARY KEY (enrollment_id),
        UNIQUE KEY uq_enrollments_user_course (user_id, course_id),
        KEY idx_enrollments_course_id (course_id),
        CONSTRAINT fk_enrollments_user
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            ON DELETE CASCADE,
        CONSTRAINT fk_enrollments_course
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INT NOT NULL AUTO_INCREMENT,
        amount DECIMAL(10, 2) NOT NULL,
        payment_method VARCHAR(45) NOT NULL,
        payment_status VARCHAR(45) NOT NULL,
        payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        enrollment_id INT NOT NULL,
        PRIMARY KEY (payment_id),
        KEY idx_payments_enrollment_id (enrollment_id),
        KEY idx_payments_latest (enrollment_id, payment_id),
        CONSTRAINT fk_payments_enrollment
            FOREIGN KEY (enrollment_id) REFERENCES enrollments (enrollment_id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS reviews (
        review_id INT NOT NULL AUTO_INCREMENT,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        rating DECIMAL(3, 1) NOT NULL,
        comment TEXT NULL,
        review_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (review_id),
        UNIQUE KEY uq_reviews_user_course (user_id, course_id),
        KEY idx_reviews_course_id (course_id),
        CONSTRAINT fk_reviews_user
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            ON DELETE CASCADE,
        CONSTRAINT fk_reviews_course
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]

LATEST_PAYMENT_JOIN = """
                LEFT JOIN (
                    SELECT
                        p.payment_id,
                        p.enrollment_id,
                        p.amount,
                        p.payment_method,
                        p.payment_status,
                        p.payment_date
                    FROM payments p
                    INNER JOIN (
                        SELECT enrollment_id, MAX(payment_id) AS latest_payment_id
                        FROM payments
                        GROUP BY enrollment_id
                    ) latest_payment_lookup
                        ON latest_payment_lookup.latest_payment_id = p.payment_id
                ) latest_payment ON latest_payment.enrollment_id = e.enrollment_id
"""

CATALOG_BOOTSTRAPPED = False
SCHEMA_BOOTSTRAPPED = False
BOOTSTRAP_LOCK = Lock()


class User(UserMixin):
    def __init__(self, row: dict[str, Any]):
        self.id = row["user_id"]
        self.username = row["username"]
        self.email = row["email"]
        self.password = row["password"]
        self.role_id = row["role_id"]
        self.role_name = row.get("role_name") or "Student"

    @property
    def is_admin(self) -> bool:
        return self.role_name.lower() == "admin"

    @property
    def is_instructor(self) -> bool:
        return self.role_name.lower() == "instructor"

    @property
    def can_manage_courses(self) -> bool:
        return self.is_admin or self.is_instructor


def get_db_connection():
    database_name = (app.config.get("DB_NAME") or "").strip()
    if not database_name:
        raise RuntimeError(
            "Database name is not configured. Set JAWSDB_URL, JAWSDB_MARIA_URL, "
            "CLEARDB_DATABASE_URL, DATABASE_URL, or DB_NAME before starting the app."
        )

    connect_kwargs: dict[str, Any] = {
        "host": app.config["DB_HOST"],
        "user": app.config["DB_USER"],
        "password": app.config["DB_PASSWORD"],
        "db": database_name,
        "port": app.config["DB_PORT"],
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
        "connect_timeout": app.config["DB_CONNECT_TIMEOUT"],
    }

    ssl_ca = app.config.get("DB_SSL_CA")
    if ssl_ca:
        connect_kwargs["ssl"] = {"ca": ssl_ca}

    return pymysql.connect(**connect_kwargs)


def ensure_schema_ready():
    global SCHEMA_BOOTSTRAPPED

    if SCHEMA_BOOTSTRAPPED:
        return

    with BOOTSTRAP_LOCK:
        if SCHEMA_BOOTSTRAPPED:
            return

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                for statement in SCHEMA_STATEMENTS:
                    cursor.execute(statement)
            connection.commit()
            SCHEMA_BOOTSTRAPPED = True
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def fit_text(value: str | None, max_length: int) -> str | None:
    if value is None or len(value) <= max_length:
        return value
    return f"{value[: max_length - 3].rstrip()}..."


def ensure_catalog_seeded():
    global CATALOG_BOOTSTRAPPED

    if CATALOG_BOOTSTRAPPED:
        return

    ensure_schema_ready()

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for role_id, role_name in ROLE_SEEDS:
                cursor.execute(
                    "SELECT role_id FROM roles WHERE role_name = %s LIMIT 1",
                    (role_name,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO roles (role_id, role_name) VALUES (%s, %s)",
                        (role_id, fit_text(role_name, 45)),
                    )

            role_map: dict[str, int] = {}
            cursor.execute("SELECT role_id, role_name FROM roles")
            for row in cursor.fetchall():
                role_map[row["role_name"]] = row["role_id"]

            admin_username = fit_text(app.config["ADMIN_USERNAME"].strip() or "admin", 50)
            admin_email = app.config["ADMIN_EMAIL"].strip().lower() or "admin@cms.demo"
            admin_password = app.config["ADMIN_PASSWORD"] or "admin123"

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.email,
                    u.password
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                WHERE (
                    LOWER(u.username) = LOWER(%s)
                    OR LOWER(u.email) = LOWER(%s)
                )
                  AND COALESCE(r.role_name, 'Student') = 'Admin'
                LIMIT 1
                """,
                (admin_username, admin_email),
            )
            existing_admin = cursor.fetchone()
            if existing_admin is None:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password, role_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (
                        admin_username,
                        admin_email,
                        generate_password_hash(admin_password),
                        role_map["Admin"],
                    ),
                )
            else:
                update_fields: list[str] = []
                update_params: list[Any] = []

                if existing_admin["username"] != admin_username:
                    update_fields.append("username = %s")
                    update_params.append(admin_username)
                if (existing_admin["email"] or "").lower() != admin_email:
                    update_fields.append("email = %s")
                    update_params.append(admin_email)
                if not password_matches(existing_admin["password"], admin_password):
                    update_fields.append("password = %s")
                    update_params.append(generate_password_hash(admin_password))

                if update_fields:
                    cursor.execute(
                        f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s",
                        (*update_params, existing_admin["user_id"]),
                    )

            for category_id, category_name in CATEGORY_SEEDS:
                cursor.execute(
                    "SELECT category_id FROM categories WHERE category_name = %s LIMIT 1",
                    (category_name,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO categories (category_id, category_name) VALUES (%s, %s)",
                        (category_id, fit_text(category_name, 45)),
                    )

            cursor.execute("SELECT COUNT(*) AS total FROM courses")
            if cursor.fetchone()["total"] > 0:
                connection.commit()
                CATALOG_BOOTSTRAPPED = True
                return

            category_map: dict[str, int] = {}
            cursor.execute("SELECT category_id, category_name FROM categories")
            for row in cursor.fetchall():
                category_map[row["category_name"]] = row["category_id"]

            user_map: dict[str, int] = {}
            for demo_user in DEMO_USERS:
                cursor.execute(
                    "SELECT user_id FROM users WHERE email = %s LIMIT 1",
                    (demo_user["email"],),
                )
                existing_user = cursor.fetchone()
                if existing_user:
                    user_map[demo_user["email"]] = existing_user["user_id"]
                    continue

                cursor.execute(
                    """
                    INSERT INTO users (username, email, password, role_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (
                        fit_text(demo_user["username"], 50),
                        demo_user["email"],
                        generate_password_hash("catalog-demo-access"),
                        role_map[demo_user["role_name"]],
                    ),
                )
                user_map[demo_user["email"]] = cursor.lastrowid

            for course in DEMO_COURSES:
                cursor.execute(
                    """
                    INSERT INTO courses (
                        course_name,
                        description,
                        price,
                        category_id,
                        instructor_id,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        fit_text(course["course_name"], 200),
                        fit_text(course["description"], 400),
                        course["price"],
                        category_map[course["category_name"]],
                        user_map[course["instructor_email"]],
                    ),
                )
                course_id = cursor.lastrowid

                for module_number, module_title in enumerate(course["modules"], start=1):
                    cursor.execute(
                        """
                        INSERT INTO course_content (title, video_url, module_number, course_id)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            fit_text(module_title, 45),
                            f"https://example.com/courses/{course_id}/module-{module_number}",
                            module_number,
                            course_id,
                        ),
                    )

                for review in course["reviews"]:
                    reviewer_id = user_map[review["user_email"]]

                    cursor.execute(
                        """
                        INSERT INTO enrollments (enrollment_date, status, user_id, course_id)
                        VALUES (NOW(), %s, %s, %s)
                        """,
                        (review["status"], reviewer_id, course_id),
                    )
                    enrollment_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO payments (
                            amount,
                            payment_method,
                            payment_status,
                            payment_date,
                            enrollment_id
                        ) VALUES (%s, %s, %s, NOW(), %s)
                        """,
                        (
                            course["price"],
                            fit_text(review["payment_method"], 45),
                            fit_text("Paid", 45),
                            enrollment_id,
                        ),
                    )

                    cursor.execute(
                        """
                        INSERT INTO reviews (user_id, course_id, rating, comment, review_date)
                        VALUES (%s, %s, %s, %s, NOW())
                        """,
                        (
                            reviewer_id,
                            course_id,
                            review["rating"],
                            review["comment"],
                        ),
                    )

            connection.commit()
            CATALOG_BOOTSTRAPPED = True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def password_matches(stored_password: str | None, provided_password: str) -> bool:
    if not stored_password:
        return False
    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password


def get_user_by_id(user_id: int | str):
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.email,
                    u.password,
                    u.role_id,
                    COALESCE(r.role_name, 'Student') AS role_name
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                WHERE u.user_id = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def get_user_by_email(email: str):
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.email,
                    u.password,
                    u.role_id,
                    COALESCE(r.role_name, 'Student') AS role_name
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                WHERE u.email = %s
                """,
                (email,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def get_user_by_username(username: str, role_name: str | None = None):
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    u.user_id,
                    u.username,
                    u.email,
                    u.password,
                    u.role_id,
                    COALESCE(r.role_name, 'Student') AS role_name
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                WHERE LOWER(u.username) = LOWER(%s)
            """
            params: list[Any] = [username]
            if role_name:
                query += " AND COALESCE(r.role_name, 'Student') = %s"
                params.append(role_name)
            cursor.execute(query, tuple(params))
            return cursor.fetchone()
    finally:
        connection.close()


def get_role_id_by_name(role_name: str) -> int | None:
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT role_id FROM roles WHERE role_name = %s LIMIT 1",
                (role_name,),
            )
            row = cursor.fetchone()
            return row["role_id"] if row else None
    finally:
        connection.close()


def get_registration_roles():
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT role_id, role_name
                FROM roles
                WHERE role_name IN ('Student', 'Instructor')
                ORDER BY role_id
                """
            )
            return cursor.fetchall()
    finally:
        connection.close()


def get_categories():
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT category_id, category_name
                FROM categories
                ORDER BY category_name
                """
            )
            return cursor.fetchall()
    finally:
        connection.close()


def get_course_count() -> int:
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM courses")
            row = cursor.fetchone()
            return row["total"] if row else 0
    finally:
        connection.close()


def get_platform_stats() -> dict[str, Any]:
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM courses")
            course_total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM enrollments")
            enrollment_total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM reviews")
            review_total = cursor.fetchone()["total"]

            cursor.execute(
                """
                SELECT COUNT(DISTINCT instructor_id) AS total
                FROM courses
                WHERE instructor_id IS NOT NULL
                """
            )
            instructor_total = cursor.fetchone()["total"]

            cursor.execute(
                """
                SELECT
                    c.category_name,
                    COUNT(cr.Course_id) AS total
                FROM categories c
                LEFT JOIN courses cr ON cr.category_id = c.category_id
                GROUP BY c.category_id, c.category_name
                ORDER BY c.category_name
                """
            )
            category_stats = cursor.fetchall()
    finally:
        connection.close()

    return {
        "course_total": course_total,
        "enrollment_total": enrollment_total,
        "review_total": review_total,
        "instructor_total": instructor_total,
        "categories": category_stats,
    }


def get_featured_courses(limit: int = 3):
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.Course_id AS course_id,
                    c.course_name,
                    c.description,
                    c.price,
                    c.created_at,
                    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                    COALESCE(instructor.username, 'TBA') AS instructor_name,
                    COALESCE(review_stats.avg_rating, 0) AS avg_rating,
                    COALESCE(review_stats.review_total, 0) AS review_total,
                    COALESCE(module_stats.module_total, 0) AS module_total
                FROM courses c
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        ROUND(AVG(rating), 1) AS avg_rating,
                        COUNT(*) AS review_total
                    FROM reviews
                    GROUP BY course_id
                ) review_stats ON review_stats.course_id = c.Course_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        COUNT(*) AS module_total
                    FROM course_content
                    GROUP BY course_id
                ) module_stats ON module_stats.course_id = c.Course_id
                ORDER BY c.created_at DESC, c.Course_id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cursor.fetchall()
    finally:
        connection.close()


def get_catalog_courses(user_id: int | None):
    ensure_catalog_seeded()
    viewer_id = user_id if user_id is not None else -1
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.Course_id AS course_id,
                    c.course_name,
                    c.description,
                    c.price,
                    c.created_at,
                    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                    COALESCE(instructor.username, 'TBA') AS instructor_name,
                    COALESCE(review_stats.avg_rating, 0) AS avg_rating,
                    COALESCE(review_stats.review_total, 0) AS review_total,
                    COALESCE(module_stats.module_total, 0) AS module_total,
                    CASE WHEN e.enrollment_id IS NULL THEN 0 ELSE 1 END AS is_enrolled,
                    COALESCE(e.status, '') AS enrollment_status
                FROM courses c
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        ROUND(AVG(rating), 1) AS avg_rating,
                        COUNT(*) AS review_total
                    FROM reviews
                    GROUP BY course_id
                ) review_stats ON review_stats.course_id = c.Course_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        COUNT(*) AS module_total
                    FROM course_content
                    GROUP BY course_id
                ) module_stats ON module_stats.course_id = c.Course_id
                LEFT JOIN enrollments e
                    ON e.course_id = c.Course_id
                    AND e.user_id = %s
                ORDER BY c.created_at DESC, c.Course_id DESC
                """,
                (viewer_id,),
            )
            return cursor.fetchall()
    finally:
        connection.close()


def get_course_detail(course_id: int, user_id: int | None):
    ensure_catalog_seeded()
    viewer_id = user_id if user_id is not None else -1
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.Course_id AS course_id,
                    c.course_name,
                    c.description,
                    c.price,
                    c.created_at,
                    c.category_id,
                    c.instructor_id,
                    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                    COALESCE(instructor.username, 'TBA') AS instructor_name,
                    COALESCE(review_stats.avg_rating, 0) AS avg_rating,
                    COALESCE(review_stats.review_total, 0) AS review_total,
                    COALESCE(module_stats.module_total, 0) AS module_total,
                    CASE WHEN e.enrollment_id IS NULL THEN 0 ELSE 1 END AS is_enrolled,
                    e.enrollment_id,
                    COALESCE(e.status, '') AS enrollment_status
                FROM courses c
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        ROUND(AVG(rating), 1) AS avg_rating,
                        COUNT(*) AS review_total
                    FROM reviews
                    GROUP BY course_id
                ) review_stats ON review_stats.course_id = c.Course_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        COUNT(*) AS module_total
                    FROM course_content
                    GROUP BY course_id
                ) module_stats ON module_stats.course_id = c.Course_id
                LEFT JOIN enrollments e
                    ON e.course_id = c.Course_id
                    AND e.user_id = %s
                WHERE c.Course_id = %s
                """,
                (viewer_id, course_id),
            )
            course_row = cursor.fetchone()
            if course_row is None:
                return None

            cursor.execute(
                """
                SELECT content_id, title, video_url, module_number
                FROM course_content
                WHERE course_id = %s
                ORDER BY module_number, content_id
                """,
                (course_id,),
            )
            content_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    r.review_id,
                    r.rating,
                    r.comment,
                    r.review_date,
                    COALESCE(u.username, 'Anonymous') AS username
                FROM reviews r
                LEFT JOIN users u ON u.user_id = r.user_id
                WHERE r.course_id = %s
                ORDER BY r.review_date DESC, r.review_id DESC
                """,
                (course_id,),
            )
            review_rows = cursor.fetchall()

            cursor.execute(
                f"""
                SELECT
                    e.enrollment_id,
                    e.status,
                    e.enrollment_date,
                    latest_payment.payment_id,
                    latest_payment.amount,
                    latest_payment.payment_method,
                    latest_payment.payment_status,
                    latest_payment.payment_date
                FROM enrollments e
                {LATEST_PAYMENT_JOIN}
                WHERE e.user_id = %s AND e.course_id = %s
                ORDER BY latest_payment.payment_id DESC
                LIMIT 1
                """,
                (viewer_id, course_id),
            )
            enrollment_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT review_id, rating, comment
                FROM reviews
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
                """,
                (viewer_id, course_id),
            )
            my_review = cursor.fetchone()
    finally:
        connection.close()

    return {
        "course": course_row,
        "content": content_rows,
        "reviews": review_rows,
        "enrollment": enrollment_row,
        "my_review": my_review,
    }


def get_course_content_item(course_id: int, content_id: int):
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT content_id, title, video_url, module_number, course_id
                FROM course_content
                WHERE course_id = %s AND content_id = %s
                LIMIT 1
                """,
                (course_id, content_id),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def is_user_enrolled_in_course(course_id: int, user_id: int | str) -> bool:
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT enrollment_id
                FROM enrollments
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
                """,
                (user_id, course_id),
            )
            return cursor.fetchone() is not None
    finally:
        connection.close()


def can_open_course_modules(course_id: int, user: User) -> bool:
    if user.can_manage_courses and can_manage_course(course_id, user):
        return True
    return is_user_enrolled_in_course(course_id, user.id)


def get_dashboard_snapshot(user: User):
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    e.enrollment_id,
                    e.status,
                    e.enrollment_date,
                    c.Course_id AS course_id,
                    c.course_name,
                    c.description,
                    c.price,
                    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                    COALESCE(instructor.username, 'TBA') AS instructor_name,
                    COALESCE(module_stats.module_total, 0) AS module_total,
                    latest_payment.amount,
                    latest_payment.payment_method,
                    latest_payment.payment_status,
                    latest_payment.payment_date
                FROM enrollments e
                JOIN courses c ON c.Course_id = e.course_id
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT course_id, COUNT(*) AS module_total
                    FROM course_content
                    GROUP BY course_id
                ) module_stats ON module_stats.course_id = c.Course_id
                {LATEST_PAYMENT_JOIN}
                WHERE e.user_id = %s
                ORDER BY e.enrollment_date DESC, e.enrollment_id DESC
                """,
                (user.id,),
            )
            enrollments = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    c.Course_id AS course_id,
                    c.course_name,
                    c.description,
                    c.price,
                    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                    COALESCE(instructor.username, 'TBA') AS instructor_name,
                    COALESCE(review_stats.avg_rating, 0) AS avg_rating,
                    COALESCE(review_stats.review_total, 0) AS review_total,
                    COALESCE(module_stats.module_total, 0) AS module_total
                FROM courses c
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT
                        course_id,
                        ROUND(AVG(rating), 1) AS avg_rating,
                        COUNT(*) AS review_total
                    FROM reviews
                    GROUP BY course_id
                ) review_stats ON review_stats.course_id = c.Course_id
                LEFT JOIN (
                    SELECT course_id, COUNT(*) AS module_total
                    FROM course_content
                    GROUP BY course_id
                ) module_stats ON module_stats.course_id = c.Course_id
                WHERE c.Course_id NOT IN (
                    SELECT course_id FROM enrollments WHERE user_id = %s
                )
                ORDER BY c.created_at DESC, c.Course_id DESC
                LIMIT 3
                """,
                (user.id,),
            )
            recommendations = cursor.fetchall()

            if user.can_manage_courses:
                query = """
                    SELECT
                        c.Course_id AS course_id,
                        c.course_name,
                        c.price,
                        COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                        COALESCE(instructor.username, 'TBA') AS instructor_name,
                        COALESCE(module_stats.module_total, 0) AS module_total,
                        COALESCE(enrollment_stats.enrollment_total, 0) AS enrollment_total
                    FROM courses c
                    LEFT JOIN categories cat ON cat.category_id = c.category_id
                    LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                    LEFT JOIN (
                        SELECT course_id, COUNT(*) AS module_total
                        FROM course_content
                        GROUP BY course_id
                    ) module_stats ON module_stats.course_id = c.Course_id
                    LEFT JOIN (
                        SELECT course_id, COUNT(*) AS enrollment_total
                        FROM enrollments
                        GROUP BY course_id
                    ) enrollment_stats ON enrollment_stats.course_id = c.Course_id
                """
                params: tuple[Any, ...] = ()
                if user.is_admin:
                    query += " ORDER BY c.created_at DESC, c.Course_id DESC"
                else:
                    query += " WHERE c.instructor_id = %s ORDER BY c.created_at DESC, c.Course_id DESC"
                    params = (user.id,)
                cursor.execute(query, params)
                managed_courses = cursor.fetchall()
            else:
                managed_courses = []
    finally:
        connection.close()

    status_counts = {
        "enrolled": sum(1 for item in enrollments if item["status"] == "Enrolled"),
        "in_progress": sum(1 for item in enrollments if item["status"] == "In Progress"),
        "completed": sum(1 for item in enrollments if item["status"] == "Completed"),
    }
    total_paid = sum(float(item["amount"]) for item in enrollments if item.get("amount") is not None)

    return {
        "enrollments": enrollments,
        "recommendations": recommendations,
        "managed_courses": managed_courses,
        "stats": {
            "enrolled_total": len(enrollments),
            "enrolled_status_total": status_counts["enrolled"],
            "in_progress_total": status_counts["in_progress"],
            "completed_total": status_counts["completed"],
            "total_paid": total_paid,
        },
    }


def get_admin_snapshot():
    ensure_catalog_seeded()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN COALESCE(r.role_name, 'Student') = 'Student' THEN 1 ELSE 0 END) AS student_total,
                    SUM(CASE WHEN COALESCE(r.role_name, 'Student') = 'Instructor' THEN 1 ELSE 0 END) AS instructor_total
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                """
            )
            user_counts = cursor.fetchone() or {}

            cursor.execute("SELECT COUNT(*) AS total FROM courses")
            course_total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM enrollments")
            enrollment_total = cursor.fetchone()["total"]

            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM payments
                WHERE payment_status = 'Paid'
                """
            )
            revenue_total = float(cursor.fetchone()["total"] or 0)

            cursor.execute(
                """
                SELECT
                    c.Course_id AS course_id,
                    c.course_name,
                    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
                    COALESCE(instructor.username, 'TBA') AS instructor_name,
                    COALESCE(enrollment_stats.enrollment_total, 0) AS enrollment_total,
                    COALESCE(review_stats.avg_rating, 0) AS avg_rating
                FROM courses c
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT course_id, COUNT(*) AS enrollment_total
                    FROM enrollments
                    GROUP BY course_id
                ) enrollment_stats ON enrollment_stats.course_id = c.Course_id
                LEFT JOIN (
                    SELECT course_id, ROUND(AVG(rating), 1) AS avg_rating
                    FROM reviews
                    GROUP BY course_id
                ) review_stats ON review_stats.course_id = c.Course_id
                ORDER BY enrollment_total DESC, avg_rating DESC, c.course_name ASC
                LIMIT 5
                """
            )
            top_courses = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.email,
                    COALESCE(enrollment_stats.enrolled_total, 0) AS enrolled_total,
                    COALESCE(enrollment_stats.completed_total, 0) AS completed_total,
                    enrollment_stats.last_enrollment_date
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                LEFT JOIN (
                    SELECT
                        e.user_id,
                        COUNT(*) AS enrolled_total,
                        SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_total,
                        MAX(e.enrollment_date) AS last_enrollment_date
                    FROM enrollments e
                    GROUP BY e.user_id
                ) enrollment_stats ON enrollment_stats.user_id = u.user_id
                WHERE COALESCE(r.role_name, 'Student') = 'Student'
                ORDER BY enrolled_total DESC, u.created_at DESC, u.user_id DESC
                LIMIT 10
                """
            )
            students = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.email,
                    COALESCE(course_stats.course_total, 0) AS course_total,
                    COALESCE(course_stats.enrollment_total, 0) AS enrollment_total,
                    COALESCE(course_stats.avg_rating, 0) AS avg_rating
                FROM users u
                LEFT JOIN roles r ON r.role_id = u.role_id
                LEFT JOIN (
                    SELECT
                        c.instructor_id,
                        COUNT(*) AS course_total,
                        COALESCE(SUM(enrollment_stats.enrollment_total), 0) AS enrollment_total,
                        COALESCE(ROUND(AVG(review_stats.avg_rating), 1), 0) AS avg_rating
                    FROM courses c
                    LEFT JOIN (
                        SELECT course_id, COUNT(*) AS enrollment_total
                        FROM enrollments
                        GROUP BY course_id
                    ) enrollment_stats ON enrollment_stats.course_id = c.Course_id
                    LEFT JOIN (
                        SELECT course_id, AVG(rating) AS avg_rating
                        FROM reviews
                        GROUP BY course_id
                    ) review_stats ON review_stats.course_id = c.Course_id
                    GROUP BY c.instructor_id
                ) course_stats ON course_stats.instructor_id = u.user_id
                WHERE COALESCE(r.role_name, 'Student') = 'Instructor'
                ORDER BY enrollment_total DESC, course_total DESC, u.username ASC
                LIMIT 10
                """
            )
            instructors = cursor.fetchall()
    finally:
        connection.close()

    return {
        "stats": {
            "student_total": user_counts.get("student_total", 0) or 0,
            "instructor_total": user_counts.get("instructor_total", 0) or 0,
            "course_total": course_total,
            "enrollment_total": enrollment_total,
            "revenue_total": revenue_total,
        },
        "students": students,
        "instructors": instructors,
        "top_courses": top_courses,
        "favorite_instructors": instructors[:5],
    }


def can_manage_course(course_id: int, user: User) -> bool:
    if user.is_admin:
        return True

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT instructor_id FROM courses WHERE Course_id = %s",
                (course_id,),
            )
            row = cursor.fetchone()
            return bool(row and row["instructor_id"] == user.id)
    finally:
        connection.close()


def course_manager_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.can_manage_courses:
            flash("Only instructors or admins can manage courses.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login", next=request.path))
        if not current_user.is_admin:
            flash("Admin access only.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped


@login_manager.user_loader
def load_user(user_id: str):
    row = get_user_by_id(user_id)
    return User(row) if row else None


@app.context_processor
def inject_layout_context():
    return {
        "course_count": get_course_count(),
        "course_accents": COURSE_ACCENTS,
        "current_year": datetime.now().year,
        "dashboard_endpoint": "admin_dashboard"
        if current_user.is_authenticated and current_user.is_admin
        else "dashboard",
    }


@app.route("/")
@app.route("/index")
def index():
    my_enrollments = 0
    managed_total = 0
    if current_user.is_authenticated:
        snapshot = get_dashboard_snapshot(current_user)
        my_enrollments = snapshot["stats"]["enrolled_total"]
        managed_total = len(snapshot["managed_courses"])

    return render_template(
        "index.html",
        featured_courses=get_featured_courses(),
        sample_courses=SAMPLE_COURSES,
        platform_stats=get_platform_stats(),
        my_enrollments=my_enrollments,
        managed_total=managed_total,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    student_role_id = get_role_id_by_name("Student")
    if student_role_id is None:
        flash("Student registration is not available right now.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if len(username) < 2:
            flash("Please enter a username with at least 2 characters.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Please use a password with at least 8 characters.", "error")
            return render_template("register.html")

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("That email is already registered. Try logging in instead.", "error")
                    return render_template("register.html")

                cursor.execute(
                    """
                    INSERT INTO users (username, email, password, role_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (username, email, generate_password_hash(password), student_role_id),
                )
                connection.commit()
                user_id = cursor.lastrowid
        finally:
            connection.close()

        user_row = get_user_by_id(user_id)
        login_user(User(user_row))
        flash("Your student account has been created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        next_page = request.args.get("next") or request.form.get("next")

        user_row = get_user_by_username(identifier, role_name="Admin")
        if user_row is None:
            user_row = get_user_by_email(identifier.lower())

        if user_row is None or not password_matches(user_row["password"], password):
            flash("Username/email or password did not match our records.", "error")
            return render_template("login.html")

        login_user(User(user_row))
        if user_row["role_name"].lower() == "admin":
            flash("Welcome back. The admin dashboard is ready.", "success")
            return redirect(next_page or url_for("admin_dashboard"))

        flash("Welcome back. Your dashboard is ready.", "success")
        return redirect(next_page or url_for("dashboard"))

    return render_template("login.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    next_page = request.args.get("next")
    if next_page:
        return redirect(url_for("login", next=next_page))
    return redirect(url_for("login"))


@app.route("/about")
def about():
    return render_template("about.html", platform_stats=get_platform_stats())


@app.route("/admin/categories", methods=["POST"])

@admin_required
def create_category():
    category_name = request.form.get("category_name", "").strip()

    if len(category_name) < 2:
        flash("Category name must be at least 2 characters.", "error")
        return redirect(url_for("admin_dashboard", _anchor="categories"))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT category_id
                FROM categories
                WHERE LOWER(category_name) = LOWER(%s)
                LIMIT 1
                """,
                (category_name,),
            )
            if cursor.fetchone():
                flash("That category already exists.", "info")
                return redirect(url_for("admin_dashboard", _anchor="categories"))

            cursor.execute(
                "INSERT INTO categories (category_name) VALUES (%s)",
                (fit_text(category_name, 45),),
            )
            connection.commit()
    finally:
        connection.close()

    flash("Category added successfully.", "success")
    return redirect(url_for("admin_dashboard", _anchor="categories"))


@app.route("/course")
@app.route("/courses")
def course():
    viewer_id = current_user.id if current_user.is_authenticated else None
    return render_template(
        "course.html",
        courses=get_catalog_courses(viewer_id),
        categories=get_categories(),
    )


@app.route("/courses/new", methods=["GET", "POST"])
@course_manager_required
def create_course():
    categories = get_categories()

    if request.method == "POST":
        course_name = request.form.get("course_name", "").strip()
        description = request.form.get("description", "").strip()
        price_raw = request.form.get("price", "").strip()
        category_id = request.form.get("category_id", "").strip()

        if not course_name:
            flash("Course name is required.", "error")
            return render_template("create_course.html", categories=categories)

        try:
            price = Decimal(price_raw)
            if price < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            flash("Please enter a valid course price.", "error")
            return render_template("create_course.html", categories=categories)

        valid_categories = {str(category["category_id"]) for category in categories}
        if category_id not in valid_categories:
            flash("Please choose a valid category.", "error")
            return render_template("create_course.html", categories=categories)

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO courses (
                        course_name,
                        description,
                        price,
                        category_id,
                        instructor_id,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (course_name, description or None, price, category_id, current_user.id),
                )
                connection.commit()
                course_id = cursor.lastrowid
        finally:
            connection.close()

        flash("Course created successfully. Add some modules next.", "success")
        return redirect(url_for("course_detail", course_id=course_id))

    return render_template("create_course.html", categories=categories)


@app.route("/courses/<int:course_id>/edit", methods=["POST"])
@course_manager_required
def edit_course(course_id: int):
    if not can_manage_course(course_id, current_user):
        flash("You can only edit courses assigned to you.", "error")
        return redirect(url_for("course_detail", course_id=course_id))

    categories = get_categories()
    course_name = request.form.get("course_name", "").strip()
    description = request.form.get("description", "").strip()
    price_raw = request.form.get("price", "").strip()
    category_id = request.form.get("category_id", "").strip()

    if not course_name:
        flash("Course name is required.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="course-settings"))

    try:
        price = Decimal(price_raw)
        if price < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        flash("Please enter a valid course price.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="course-settings"))

    valid_categories = {str(category["category_id"]) for category in categories}
    if category_id not in valid_categories:
        flash("Please choose a valid category.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="course-settings"))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE courses
                SET course_name = %s, description = %s, price = %s, category_id = %s
                WHERE Course_id = %s
                """,
                (course_name, description or None, price, category_id, course_id),
            )
            connection.commit()
    finally:
        connection.close()

    flash("Course details updated.", "success")
    return redirect(url_for("course_detail", course_id=course_id, _anchor="course-settings"))


@app.route("/courses/<int:course_id>")
def course_detail(course_id: int):
    viewer_id = current_user.id if current_user.is_authenticated else None
    detail = get_course_detail(course_id, viewer_id)
    if detail is None:
        flash("That course could not be found.", "error")
        return redirect(url_for("course"))

    return render_template(
        "course_detail.html",
        detail=detail,
        categories=get_categories(),
        payment_methods=PAYMENT_METHODS,
        can_edit=current_user.is_authenticated and can_manage_course(course_id, current_user),
    )


@app.route("/courses/<int:course_id>/modules/<int:content_id>")
def open_course_module(course_id: int, content_id: int):
    module = get_course_content_item(course_id, content_id)
    if module is None:
        flash("That module could not be found.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="content"))

    if current_user.is_authenticated and can_open_course_modules(course_id, current_user):
        return redirect(module["video_url"])

    flash("Enroll in this course to open the module.", "info")
    return redirect(url_for("course_detail", course_id=course_id, _anchor="access-panel"))


@app.route("/courses/<int:course_id>/content", methods=["POST"])
@course_manager_required
def add_course_content(course_id: int):
    if not can_manage_course(course_id, current_user):
        flash("You can only edit courses assigned to you.", "error")
        return redirect(url_for("course_detail", course_id=course_id))

    title = request.form.get("title", "").strip()
    video_url = request.form.get("video_url", "").strip()
    module_number_raw = request.form.get("module_number", "").strip()

    if not title or not video_url or not module_number_raw:
        flash("Module title, video URL, and module number are required.", "error")
        return redirect(url_for("course_detail", course_id=course_id))

    try:
        module_number = int(module_number_raw)
        if module_number < 1:
            raise ValueError
    except ValueError:
        flash("Module number must be a positive integer.", "error")
        return redirect(url_for("course_detail", course_id=course_id))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO course_content (title, video_url, module_number, course_id)
                VALUES (%s, %s, %s, %s)
                """,
                (title, video_url, module_number, course_id),
            )
            connection.commit()
    finally:
        connection.close()

    flash("Module added to the course.", "success")
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/courses/<int:course_id>/content/<int:content_id>/edit", methods=["POST"])
@course_manager_required
def edit_course_content(course_id: int, content_id: int):
    if not can_manage_course(course_id, current_user):
        flash("You can only edit courses assigned to you.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="content"))

    module = get_course_content_item(course_id, content_id)
    if module is None:
        flash("That module could not be found.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="content"))

    title = request.form.get("title", "").strip()
    video_url = request.form.get("video_url", "").strip()
    module_number_raw = request.form.get("module_number", "").strip()

    if not title or not video_url or not module_number_raw:
        flash("Module title, video URL, and module number are required.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="content"))

    try:
        module_number = int(module_number_raw)
        if module_number < 1:
            raise ValueError
    except ValueError:
        flash("Module number must be a positive integer.", "error")
        return redirect(url_for("course_detail", course_id=course_id, _anchor="content"))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE course_content
                SET title = %s, video_url = %s, module_number = %s
                WHERE content_id = %s AND course_id = %s
                """,
                (title, video_url, module_number, content_id, course_id),
            )
            connection.commit()
    finally:
        connection.close()

    flash("Module updated successfully.", "success")
    return redirect(url_for("course_detail", course_id=course_id, _anchor="content"))


@app.route("/enroll/<int:course_id>", methods=["POST"])
@login_required
def enroll(course_id: int):
    payment_method = request.form.get("payment_method", "").strip()
    if payment_method not in PAYMENT_METHODS:
        flash("Please choose a valid payment method.", "error")
        return redirect(url_for("course_detail", course_id=course_id))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT Course_id AS course_id, price FROM courses WHERE Course_id = %s",
                (course_id,),
            )
            course_row = cursor.fetchone()
            if course_row is None:
                flash("That course could not be found.", "error")
                return redirect(url_for("course"))

            cursor.execute(
                """
                SELECT enrollment_id
                FROM enrollments
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
                """,
                (current_user.id, course_id),
            )
            if cursor.fetchone():
                flash("You are already enrolled in that course.", "info")
                return redirect(url_for("course_detail", course_id=course_id))

            cursor.execute(
                """
                INSERT INTO enrollments (enrollment_date, status, user_id, course_id)
                VALUES (NOW(), %s, %s, %s)
                """,
                ("Enrolled", current_user.id, course_id),
            )
            enrollment_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO payments (
                    amount,
                    payment_method,
                    payment_status,
                    payment_date,
                    enrollment_id
                ) VALUES (%s, %s, %s, NOW(), %s)
                """,
                (course_row["price"], payment_method, "Paid", enrollment_id),
            )
            connection.commit()
    finally:
        connection.close()

    flash("Enrollment completed and payment recorded.", "success")
    return redirect(url_for("dashboard"))


@app.route("/courses/<int:course_id>/status", methods=["POST"])
@login_required
def update_status(course_id: int):
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "").strip().lower()
    next_status = STATUS_ACTIONS.get(action)

    if next_status is None:
        return jsonify({"ok": False, "message": "Unsupported status action."}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT enrollment_id
                FROM enrollments
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
                """,
                (current_user.id, course_id),
            )
            enrollment = cursor.fetchone()
            if enrollment is None:
                return jsonify({"ok": False, "message": "Enrollment not found."}), 404

            cursor.execute(
                """
                UPDATE enrollments
                SET status = %s
                WHERE enrollment_id = %s
                """,
                (next_status, enrollment["enrollment_id"]),
            )
            connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "course_id": course_id, "status": next_status})


@app.route("/courses/<int:course_id>/review", methods=["POST"])
@login_required
def submit_review(course_id: int):
    rating_raw = request.form.get("rating", "").strip()
    comment = request.form.get("comment", "").strip()

    try:
        rating = Decimal(rating_raw)
        if rating < 1 or rating > 5:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        flash("Rating must be between 1.0 and 5.0.", "error")
        return redirect(url_for("course_detail", course_id=course_id))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT enrollment_id
                FROM enrollments
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
                """,
                (current_user.id, course_id),
            )
            if cursor.fetchone() is None:
                flash("You need to enroll before leaving a review.", "error")
                return redirect(url_for("course_detail", course_id=course_id))

            cursor.execute(
                """
                SELECT review_id
                FROM reviews
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
                """,
                (current_user.id, course_id),
            )
            existing_review = cursor.fetchone()

            if existing_review:
                cursor.execute(
                    """
                    UPDATE reviews
                    SET rating = %s, comment = %s, review_date = NOW()
                    WHERE review_id = %s
                    """,
                    (rating, comment or None, existing_review["review_id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO reviews (user_id, course_id, rating, comment, review_date)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (current_user.id, course_id, rating, comment or None),
                )
            connection.commit()
    finally:
        connection.close()

    flash("Your review has been saved.", "success")
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/courses/<int:course_id>/reviews/<int:review_id>/delete", methods=["POST"])
@admin_required
def delete_review(course_id: int, review_id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT review_id
                FROM reviews
                WHERE review_id = %s AND course_id = %s
                LIMIT 1
                """,
                (review_id, course_id),
            )
            review_row = cursor.fetchone()
            if review_row is None:
                flash("That review could not be found.", "error")
                return redirect(url_for("course_detail", course_id=course_id, _anchor="reviews"))

            cursor.execute(
                """
                DELETE FROM reviews
                WHERE review_id = %s AND course_id = %s
                """,
                (review_id, course_id),
            )
            connection.commit()
    finally:
        connection.close()

    flash("Review deleted successfully.", "success")
    return redirect(url_for("course_detail", course_id=course_id, _anchor="reviews"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    snapshot = get_dashboard_snapshot(current_user)
    return render_template(
        "dashboard.html",
        user=current_user,
        enrollments=snapshot["enrollments"],
        recommendations=snapshot["recommendations"],
        managed_courses=snapshot["managed_courses"],
        stats=snapshot["stats"],
    )


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    snapshot = get_admin_snapshot()
    return render_template(
        "admin_dashboard.html",
        user=current_user,
        categories=get_categories(),
        stats=snapshot["stats"],
        students=snapshot["students"],
        instructors=snapshot["instructors"],
        top_courses=snapshot["top_courses"],
        favorite_instructors=snapshot["favorite_instructors"],
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
