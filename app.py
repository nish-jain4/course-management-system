from flask import Flask, render_template, request, redirect, url_for, session
from config import Config
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY'] 

def get_db_connection():
    return pymysql.connect(
        host=app.config['DB_HOST'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        db=app.config['DB_NAME'],
        cursorclass=pymysql.cursors.DictCursor
    )
    
@app.route("/")
def home():
    return render_template("register.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password) #converts password into a hash value

        conn = get_db_connection()
        cur = conn.cursor() #####
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        
        conn.commit()
        conn.close()
        return render_template("dashboard.html")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method== "POST":
        email=request.form["email"]
        password= request.form["password"]

        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))

        user=cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']  
            return redirect(url_for("dashboard"))
    return render_template("login.html")
        

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/course")
def course():
    return render_template("course.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)