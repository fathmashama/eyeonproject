from flask import Flask, render_template, request, redirect, session
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("employee_login.html")

# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form["username"]
    password = request.form["password"]

    try:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO employees (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect("/")
    except:
        return "User already exists!"

# ---------------- EMPLOYEE LOGIN ----------------
@app.route("/employee_login", methods=["POST"])
def employee_login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        session["employee"] = username
        return redirect("/employee_dashboard")
    else:
        return "Invalid Credentials"

@app.route("/employee_dashboard")
def employee_dashboard():
    if "employee" not in session:
        return redirect("/")

    df = pd.read_csv("attendance.csv")
    username = session["employee"]

    user_df = df[df["Name"].str.lower().str.contains(username.lower())]

    return render_template(
        "employee_dashboard.html",
        name=username,
        table=user_df.to_html(classes="table table-striped", index=False)
    )

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "admin123":
        session["admin"] = username
        return redirect("/admin_dashboard")
    else:
        return "Invalid Admin Credentials"

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    df = pd.read_csv("attendance.csv")
    total = df["Name"].nunique()

    today = datetime.now().strftime("%Y-%m-%d")
    df["Date"] = df["DateTime"].str[:10]
    today_df = df[df["Date"] == today]
    present = today_df["Name"].nunique()

    return render_template(
        "admin_dashboard.html",
        total=total,
        present=present,
        table=df.to_html(classes="table table-striped", index=False)
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)