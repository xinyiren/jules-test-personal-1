import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# The OpenAI API key is read from the OPENAI_API_KEY environment variable.
# Be sure to set this environment variable before running the application.
client = OpenAI()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Send message to OpenAI API
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
        )

        bot_message = completion.choices[0].message.content
        return jsonify({"message": bot_message})

    except Exception as e:
        # For security, it's better to log the error and return a generic message
        print(f"An error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
