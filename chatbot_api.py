from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import openai
import sqlite3
import os
from typing import List
import shutil

# Initialize FastAPI app
app = FastAPI()

# Set up OpenAI API (Replace with your valid API key)
openai_client = openai.AzureOpenAI(
    api_key="8fJEwLBDb3O6SHQrdK6VVN9nv8nEWyZdftjiWJzDqSgaL3T4vqnMJQQJ99BCACHYHv6XJ3w3AAAAACOGW07i",
    api_version="2023-12-01-preview",
    azure_endpoint="https://anvit-m8dfc32a-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-10-21"
)

# Document storage directory
DOCUMENTS_DIR = "uploaded_documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# SQLite Database Setup
conn = sqlite3.connect("documents.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filepath TEXT
    )
""")
conn.commit()

# Function to save uploaded documents
def save_document(file: UploadFile):
    file_path = os.path.join(DOCUMENTS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    c.execute("INSERT INTO documents (filename, filepath) VALUES (?, ?)", (file.filename, file_path))
    conn.commit()
    return file_path

# Function to get legal response from OpenAI API
def get_legal_response(user_input: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are a legal assistant answering questions based on Indian laws."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# 📌 API Routes

@app.post("/ask-legal/")
async def ask_legal(question: str = Form(...)):
    """API Endpoint to ask legal questions."""
    answer = get_legal_response(question)
    return {"question": question, "answer": answer}

@app.post("/upload-document/")
async def upload_document(file: UploadFile = File(...)):
    """API Endpoint to upload legal documents."""
    file_path = save_document(file)
    return {"message": "File uploaded successfully!", "filename": file.filename, "filepath": file_path}

@app.get("/documents/")
async def list_documents():
    """API Endpoint to list uploaded documents."""
    c.execute("SELECT filename, filepath FROM documents")
    docs = [{"filename": row[0], "filepath": row[1]} for row in c.fetchall()]
    return {"documents": docs}

# Close DB connection on shutdown
@app.on_event("shutdown")
def shutdown():
    conn.close()
