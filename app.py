from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from openai import OpenAI
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

    conn.commit()
    conn.close()

init_db()
# ------------------------------------------

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

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

    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI Student Support Assistant."
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"Error: {e}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)