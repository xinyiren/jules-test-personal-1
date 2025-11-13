import os
import shutil
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max size

# Initialize LangChain components
embeddings = OpenAIEmbeddings()
persist_directory = 'db'

# Ensure db directory exists
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
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

        # Process the file
        try:
            if filename.endswith('.pdf'):
                loader = PyPDFLoader(filepath)
            else:
                loader = TextLoader(filepath)

            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)

            # Initialize vector store here to ensure we have a fresh connection or handling it per request might be safer for concurrency
            # though Chroma is local. Let's instantiate it when needed or keep global but be careful.
            # Re-instantiating to be safe with the file lock issues seen.
            vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
            vector_store.add_documents(documents=splits)
            vector_store.persist()

            return jsonify({"message": "File uploaded and processed successfully", "filename": filename})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "File type not allowed"}), 400

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data["message"]
    system_prompt_text = data.get("system_prompt", "You are a helpful assistant.")

    # If the vector store is empty, fall back to simple chat but we still use LangChain for consistency
    # Ideally we check if we have docs. For now, let's assume we always try RAG if we can,
    # but if there are no docs, retrieval might return nothing.

    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo")

        # Create a retrieval chain
        vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        retriever = vector_store.as_retriever()

        system_prompt = (
            f"{system_prompt_text}\n\n"
            "Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, just say that you don't know. "
            "Context: {context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({"input": message})
        reply = response["answer"]

    except Exception as e:
        print(f"Error: {e}")
        reply = f"I am sorry, I encountered an error: {str(e)}"

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)
