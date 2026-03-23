from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
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

SAMPLE_COURSES = [
    {
        "course_name": "Python for Busy Beginners",
        "description": "Learn the basics with short lessons, small wins, and projects you can finish after work or class.",
        "price": 999.00,
        "category_name": "Programming",
        "module_total": 12,
        "review_total": 86,
        "instructor_name": "Ananya Rao",
        "accent": "#1f6f64",
    },
    {
        "course_name": "Design Better Presentations",
        "description": "Turn rough slides into clear, confident decks that feel polished and easy to follow.",
        "price": 749.00,
        "category_name": "Design",
        "module_total": 8,
        "review_total": 41,
        "instructor_name": "Riya Mehta",
        "accent": "#d96c4b",
    },
    {
        "course_name": "Data Skills for Everyday Work",
        "description": "Build confidence with spreadsheets, reports, and dashboards you can actually use on the job.",
        "price": 1199.00,
        "category_name": "Analytics",
        "module_total": 10,
        "review_total": 64,
        "instructor_name": "Karan Shah",
        "accent": "#355c7d",
    },
]


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
    return pymysql.connect(
        host=app.config["DB_HOST"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        db=app.config["DB_NAME"],
        port=app.config["DB_PORT"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def password_matches(stored_password: str | None, provided_password: str) -> bool:
    if not stored_password:
        return False
    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password


def get_user_by_id(user_id: int | str):
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


def get_registration_roles():
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
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM courses")
            row = cursor.fetchone()
            return row["total"] if row else 0
    finally:
        connection.close()


def get_platform_stats() -> dict[str, Any]:
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
                """
                SELECT
                    e.enrollment_id,
                    e.status,
                    e.enrollment_date,
                    p.payment_id,
                    p.amount,
                    p.payment_method,
                    p.payment_status,
                    p.payment_date
                FROM enrollments e
                LEFT JOIN payments p ON p.enrollment_id = e.enrollment_id
                WHERE e.user_id = %s AND e.course_id = %s
                ORDER BY p.payment_id DESC
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


def get_dashboard_snapshot(user: User):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
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
                    p.amount,
                    p.payment_method,
                    p.payment_status,
                    p.payment_date
                FROM enrollments e
                JOIN courses c ON c.Course_id = e.course_id
                LEFT JOIN categories cat ON cat.category_id = c.category_id
                LEFT JOIN users instructor ON instructor.user_id = c.instructor_id
                LEFT JOIN (
                    SELECT course_id, COUNT(*) AS module_total
                    FROM course_content
                    GROUP BY course_id
                ) module_stats ON module_stats.course_id = c.Course_id
                LEFT JOIN (
                    SELECT
                        p1.payment_id,
                        p1.enrollment_id,
                        p1.amount,
                        p1.payment_method,
                        p1.payment_status,
                        p1.payment_date
                    FROM payments p1
                    INNER JOIN (
                        SELECT enrollment_id, MAX(payment_id) AS latest_payment_id
                        FROM payments
                        GROUP BY enrollment_id
                    ) latest ON latest.latest_payment_id = p1.payment_id
                ) p ON p.enrollment_id = e.enrollment_id
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


@login_manager.user_loader
def load_user(user_id: str):
    row = get_user_by_id(user_id)
    return User(row) if row else None


@app.context_processor
def inject_layout_context():
    return {
        "course_count": get_course_count(),
        "current_year": datetime.now().year,
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
        return redirect(url_for("dashboard"))

    role_options = get_registration_roles()
    allowed_roles = {str(role["role_id"]) for role in role_options}

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role_id = request.form.get("role_id", "")

        if len(username) < 2:
            flash("Please enter a username with at least 2 characters.", "error")
            return render_template("register.html", role_options=role_options)
        if len(password) < 8:
            flash("Please use a password with at least 8 characters.", "error")
            return render_template("register.html", role_options=role_options)
        if role_id not in allowed_roles:
            flash("Please choose a valid role.", "error")
            return render_template("register.html", role_options=role_options)

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("That email is already registered. Try logging in instead.", "error")
                    return render_template("register.html", role_options=role_options)

                cursor.execute(
                    """
                    INSERT INTO users (username, email, password, role_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (username, email, generate_password_hash(password), role_id),
                )
                connection.commit()
                user_id = cursor.lastrowid
        finally:
            connection.close()

        user_row = get_user_by_id(user_id)
        login_user(User(user_row))
        flash("Your account has been created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html", role_options=role_options)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user_row = get_user_by_email(email)
        if user_row is None or not password_matches(user_row["password"], password):
            flash("Email or password did not match our records.", "error")
            return render_template("login.html")

        login_user(User(user_row))
        flash("Welcome back. Your dashboard is ready.", "success")
        next_page = request.args.get("next") or request.form.get("next")
        return redirect(next_page or url_for("dashboard"))

    return render_template("login.html")


@app.route("/about")
def about():
    return render_template("about.html", platform_stats=get_platform_stats())


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
        payment_methods=PAYMENT_METHODS,
        can_edit=current_user.is_authenticated and can_manage_course(course_id, current_user),
    )


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


@app.route("/dashboard")
@login_required
def dashboard():
    snapshot = get_dashboard_snapshot(current_user)
    return render_template(
        "dashboard.html",
        user=current_user,
        enrollments=snapshot["enrollments"],
        recommendations=snapshot["recommendations"],
        managed_courses=snapshot["managed_courses"],
        stats=snapshot["stats"],
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
