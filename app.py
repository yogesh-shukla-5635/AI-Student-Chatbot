from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

@app.route("/")
def home():
    return render_template("login.html")

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
    @app.route("/login", methods=["GET", "POST"])
    def login():
     return render_template("login.html")
    @app.route("/signup", methods=["GET", "POST"])
    def signup():
     return render_template("signup.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)