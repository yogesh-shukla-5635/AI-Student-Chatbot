from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "Prince_AI_Student_2026"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db()
# ------------------------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name,password FROM users WHERE email=?",
            (email,)
        )
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[1], password):
           session["user"] = email
           session["name"] = user[0]
           return redirect(url_for("dashboard"))
        else:
            return "Invalid Email or Password!"

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )
            conn.commit()
            conn.close()

            return render_template("login.html")

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already exists!"

    return render_template("signup.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["name"]
    )
@app.route("/chatbot")
def chatbot():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, question
        FROM chats
        WHERE email=?
        ORDER BY id DESC
    """, (session["user"],))

    chats = cursor.fetchall()
    conn.close()

    return render_template(
        "index.html",
        chats=chats,
        name=session["name"]
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]

    try:
        response = model.generate_content(message)
        reply = response.text

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO chats (email, question, answer) VALUES (?, ?, ?)",
            (session["user"], message, reply)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        reply = f"Error: {e}"

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)