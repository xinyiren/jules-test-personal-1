import os
import shutil
import time
import threading
import requests
from fpdf import FPDF
from main import app

def create_dummy_pdf(filepath, text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(filepath)

def run_app():
    app.run(port=5001)

def test_retrieval():
    # 1. Create a dummy PDF
    dummy_pdf_path = "dummy.pdf"
    dummy_text = "The secret word is 'supercalifragilisticexpialidocious'."
    create_dummy_pdf(dummy_pdf_path, dummy_text)

    # 2. Run Flask app in a separate thread
    flask_thread = threading.Thread(target=run_app)
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(2)  # Give the server some time to start

    # 3. Upload the PDF
    upload_url = "http://127.0.0.1:5001/upload"
    with open(dummy_pdf_path, "rb") as f:
        files = {"file": (os.path.basename(dummy_pdf_path), f, "application/pdf")}
        upload_response = requests.post(upload_url, files=files)
    assert upload_response.status_code == 200
    assert "uploaded and processed successfully" in upload_response.json()["message"]

    # 4. Ask a question that requires the document
    chat_url = "http://127.0.0.1:5001/chat"
    chat_payload = {"message": "What is the secret word?"}
    chat_response = requests.post(chat_url, json=chat_payload)
    assert chat_response.status_code == 200
    reply = chat_response.json()["reply"]
    print(f"Chatbot reply: {reply}")

    # 5. Assert the response contains the secret word
    assert "supercalifragilisticexpialidocious" in reply.lower()

    # 6. Cleanup
    os.remove(dummy_pdf_path)
    if os.path.exists("uploads/dummy.pdf"):
        os.remove("uploads/dummy.pdf")
    if os.path.exists("faiss_index"):
        shutil.rmtree("faiss_index")
