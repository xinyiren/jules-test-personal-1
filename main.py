import os
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# It's better to load the key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data["message"]
    system_prompt = data.get("system_prompt", "You are a helpful assistant.")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        reply = "I am sorry, I am having trouble connecting to the service."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)