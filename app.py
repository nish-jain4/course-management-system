from flask import Flask, render_template, request, redirect, url_for, session
from config import Config
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  
import datetime
from functools import wraps



app = Flask(__name__)
app.config.from_object(Config)
# for providing better security to the session e use flask login
# LoginManager main object

black = LoginManager() # keeps the user safe, more secure than session
black.init_app(app)
black.login_view = "login"  # if not logged in, it will redirect to login page
#app.secret_key = app.config['SECRET_KEY'] 

def get_db_connection():
    return pymysql.connect(
        host=app.config['DB_HOST'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        db=app.config['DB_NAME'],
        cursorclass=pymysql.cursors.DictCursor
    )
    
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

#for loading user in a session

@black.user_loader     #black object belongs to flask_login
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()

    if user_data:
        return User(id=user_data['id'], username=user_data['username'], email=user_data['email'], password=user_data['password'])
    return None


@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password) #converts password into a hash value

        conn = get_db_connection()
        cur = conn.cursor() #####

        #check if email is already registered
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))  
        if cur.fetchone():
            cur.close()
            conn.close()
            return render_template("register.html", msg="Email already registered.")  #back to register page if email is already registered

        # save details in table(users) in database
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        user_id = cur.lastrowid
        
        conn.commit()
        cur.close()
        conn.close()

        user_obj = User(id=user_id, username=username, email=email, password=hashed_password)
        login_user(user_obj)
        return redirect(url_for("dashboard"))
    return render_template("register.html") # Required for GET

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method== "POST":
        email=request.form["email"]
        password= request.form["password"]

        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))

        user=cur.fetchone() ##################
        cur.close()
        conn.close()

#if user is found, we store the id in session and the user will remain logged in until they log out or close the browser. 
# We also store the username in session for display purposes on the dashboard.  if user and check_password_hash(user[1], password):
            ##
        if user and check_password_hash(user['password'], password):
            user_obj = User(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                password=user['password']
            )
            login_user(user_obj)
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for("dashboard"))
        
    return render_template("login.html") #back to login page if login fails
        

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/course")
def course():
    return render_template("course.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required #protect routes that require authentication.

def dashboard():
    return render_template("dashboard.html", user=current_user.username)

@app.route("/logout")
@login_required #protect routes that require authentication.
def logout():
    logout_user() #flask login function to log out the user and clear the session
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
