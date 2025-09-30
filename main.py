import os
from flask import Flask, render_template, request, jsonify
import openai
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

app = Flask(__name__)

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# It's better to load the key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

vector_store = None
if os.path.exists("faiss_index"):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.load_local("faiss_index", embeddings)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data["message"]
    system_prompt = data.get("system_prompt", "You are a helpful assistant.")

    if vector_store:
        docs = vector_store.similarity_search(message)
        context = " ".join([doc.page_content for doc in docs])
        message = f"Context: {context}\n\nQuestion: {message}"

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

@app.route("/upload", methods=["POST"])
def upload():
    global vector_store
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file:
        filename = file.filename
        filepath = os.path.join("uploads", filename)
        file.save(filepath)

        # Process the document
        loader = PyPDFLoader(filepath)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        db = FAISS.from_documents(docs, embeddings)
        db.save_local("faiss_index")
        vector_store = db

        return jsonify({"message": f"File '{filename}' uploaded and processed successfully"})

if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)