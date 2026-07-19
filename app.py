from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from groq import Groq
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "Prince_AI_Student_2026"

# -------------------- DATABASE --------------------

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Conversations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id)
        REFERENCES conversations(id)
    )
    """)

    conn.commit()
    conn.close()


init_db()

# -------------------- GROQ --------------------

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# -------------------- HOME --------------------

@app.route("/")
def home():
    return render_template("login.html")


# -------------------- LOGIN --------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user"] = email
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        return "Invalid Email or Password"

    return render_template("login.html")


# -------------------- SIGNUP --------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"]
        )

        conn = get_db()
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )

            conn.commit()

            return redirect(url_for("login"))

        except:

            return "Email already exists."

        finally:

            conn.close()

    return render_template("signup.html")


# -------------------- DASHBOARD --------------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["name"]
    )


# -------------------- LOGOUT --------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

# -------------------- CHATBOT --------------------

@app.route("/chatbot")
def chatbot():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,title
        FROM conversations
        WHERE email=?
        ORDER BY created_at DESC
    """,(session["user"],))

    conversations = cursor.fetchall()

    current_chat = []

    if "conversation_id" in session:

        cursor.execute("""
            SELECT role,message
            FROM messages
            WHERE conversation_id=?
            ORDER BY id
        """,(session["conversation_id"],))

        current_chat = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        name=session["name"],
        chats=conversations,
        current_chat=current_chat
    )


# -------------------- NEW CHAT --------------------

@app.route("/new_chat")
def new_chat():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversations(email,title)
        VALUES(?,?)
    """,(session["user"],"New Chat"))

    conn.commit()

    session["conversation_id"] = cursor.lastrowid

    conn.close()

    return redirect(url_for("chatbot"))


# -------------------- OPEN OLD CHAT --------------------

@app.route("/conversation/<int:conversation_id>")
def open_conversation(conversation_id):

    if "user" not in session:
        return redirect(url_for("login"))

    session["conversation_id"] = conversation_id

    return redirect(url_for("chatbot"))

# -------------------- CHAT API --------------------

@app.route("/chat", methods=["POST"])
def chat():

    if "user" not in session:
        return jsonify({"reply":"Please login first."})

    message = request.json["message"]

    # Agar New Chat nahi banaya gaya hai to automatically bana do
    if "conversation_id" not in session:

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO conversations(email,title) VALUES(?,?)",
            (session["user"], "New Chat")
        )

        conn.commit()

        session["conversation_id"] = cursor.lastrowid

        conn.close()

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role":"system",
                    "content":"You are a helpful AI Student Support Assistant."
                },
                {
                    "role":"user",
                    "content":message
                }
            ]
        )

        reply = response.choices[0].message.content

        conn = get_db()
        cursor = conn.cursor()

        # User message save
        cursor.execute("""
            INSERT INTO messages
            (conversation_id,role,message)
            VALUES(?,?,?)
        """,(
            session["conversation_id"],
            "user",
            message
        ))

        # AI message save
        cursor.execute("""
            INSERT INTO messages
            (conversation_id,role,message)
            VALUES(?,?,?)
        """,(
            session["conversation_id"],
            "assistant",
            reply
        ))

        # Pehle message se conversation title update
        cursor.execute("""
            SELECT title
            FROM conversations
            WHERE id=?
        """,(session["conversation_id"],))

        row = cursor.fetchone()

        if row["title"] == "New Chat":

            title = message[:35]

            cursor.execute("""
                UPDATE conversations
                SET title=?
                WHERE id=?
            """,(title,session["conversation_id"]))

        conn.commit()
        conn.close()

        return jsonify({"reply":reply})

    except Exception as e:

        return jsonify({
            "reply":f"Error : {e}"
        })


# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run(debug=True)