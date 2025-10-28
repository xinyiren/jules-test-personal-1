import os
import threading
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# It's better to load the key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_openai_response(messages, results, index):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        results[index] = response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        results[index] = "I am sorry, I am having trouble connecting to the service."

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

    results = ["", ""]
    thread1 = threading.Thread(target=get_openai_response, args=(messages, results, 0))
    thread2 = threading.Thread(target=get_openai_response, args=(messages, results, 1))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    return jsonify({"reply1": results[0], "reply2": results[1]})

if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)