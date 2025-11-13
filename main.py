import os
from flask import Flask, render_template, request, jsonify, session
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

app = Flask(__name__)

# Set a secret key for session management
# In a production application, this should be a complex, securely stored value
app.config['SECRET_KEY'] = 'super-secret-key-for-dev'

# Ensure OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not set.")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variable to store the vector store
vector_store = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    global vector_store
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            # Process the file (assuming PDF for now based on PyPDFLoader)
            # If we want to support other formats, we'd need to check extension
            if filepath.lower().endswith('.pdf'):
                loader = PyPDFLoader(filepath)
                docs = loader.load()

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)

                # Embed and store
                if vector_store is None:
                     vector_store = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
                else:
                     vector_store.add_documents(splits)

                return jsonify({"message": "File processed successfully"})
            else:
                return jsonify({"error": "Only PDF files are supported currently"}), 400
        except Exception as e:
            print(f"Error processing file: {e}")
            return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    global vector_store
    data = request.json
    message = data["message"]
    system_prompt_text = data.get("system_prompt", "You are a helpful assistant.")

    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []

    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo")

        if vector_store:
            retriever = vector_store.as_retriever()

            system_prompt = (
                f"{system_prompt_text}\n\n"
                "Use the following pieces of retrieved context to answer the question. "
                "If you don't know the answer, just say that you don't know. "
                "\n\n"
                "{context}"
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                ]
            )

            question_answer_chain = create_stuff_documents_chain(llm, prompt)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)

            # Convert session chat history to AIMessage and HumanMessage objects
            chat_history_messages = []
            for role, content in session.get('chat_history', []):
                if role == 'human':
                    chat_history_messages.append(HumanMessage(content=content))
                elif role == 'ai':
                    chat_history_messages.append(AIMessage(content=content))

            response = rag_chain.invoke({"input": message, "chat_history": chat_history_messages})
            reply = response["answer"]

        else:
            # Fallback to normal chat if no documents uploaded
            messages = [("system", system_prompt_text)] + session['chat_history'] + [("human", message)]
            response = llm.invoke(messages)
            reply = response.content

        # Update chat history
        session['chat_history'].append(("human", message))
        session['chat_history'].append(("ai", reply))
        session.modified = True # Ensure the session is saved

        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"reply": "I am sorry, I encountered an error."})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000, use_reloader=False)
