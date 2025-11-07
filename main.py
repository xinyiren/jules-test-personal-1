import os
import shutil
from flask import Flask, render_template, request, jsonify
import openai
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

app = Flask(__name__)

# Setup for file uploads and FAISS index
UPLOAD_FOLDER = 'uploads'
FAISS_INDEX = 'faiss_index'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FAISS_INDEX, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# It's better to load the key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the document and create FAISS index
        loader = PyPDFLoader(filepath)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        db = FAISS.from_documents(docs, embeddings)
        db.save_local(FAISS_INDEX)

        return jsonify({"success": f"File '{filename}' uploaded and processed."})
    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

@app.route("/clear", methods=['POST'])
def clear_context():
    if os.path.exists(FAISS_INDEX):
        shutil.rmtree(FAISS_INDEX)
        os.makedirs(FAISS_INDEX, exist_ok=True)
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return jsonify({"success": "Context cleared."})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data["message"]
    system_prompt = data.get("system_prompt", "You are a helpful assistant.")

    context = ""
    if os.path.exists(FAISS_INDEX) and os.listdir(FAISS_INDEX):
        embeddings = OpenAIEmbeddings()
        db = FAISS.load_local(FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)
        docs = db.similarity_search(message, k=2)
        context = "\n\n".join([doc.page_content for doc in docs])

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    user_message = message
    if context:
        user_message = f"Based on the following context, please answer the question.\n\nContext:\n{context}\n\nQuestion: {message}"

    messages.append({"role": "user", "content": user_message})

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