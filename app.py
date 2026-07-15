from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

@app.route("/")
def home():
    return render_template("index.html")

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