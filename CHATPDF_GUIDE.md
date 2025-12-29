# ChatPDF Complete Guide

## 🎯 Overview

Your ChatPDF system is now complete! It allows users to:

1. **Upload PDFs** - With OCR, table extraction, and form detection
2. **Ask Questions** - Using AI to answer questions based on the PDF content
3. **Get Intelligent Answers** - With source citations and page numbers

---

## 🏗️ Architecture

```
┌─────────────┐
│  User PDF   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  OCR Pipeline   │  ← Extracts text, tables, forms
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Text Chunking  │  ← Splits into manageable pieces
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Embeddings    │  ← Converts to vector representations
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   ChromaDB      │  ← Stores vectors for fast search
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  User Question  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│Vector Search    │  ← Finds relevant chunks
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  LLM (OpenAI)   │  ← Generates answer with context
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│     Answer      │  ← With sources and page numbers
└─────────────────┘
```

---

## 🚀 Installation & Setup

### 1. System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
  poppler-utils \
  ghostscript \
  python3-tk \
  libgl1-mesa-glx
```

### 2. Python Dependencies

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
pip install -r requirements.txt
```

This installs:

- **OCR**: PaddleOCR, PyMuPDF, pdf2image, OpenCV
- **Tables**: Camelot
- **RAG**: ChromaDB, sentence-transformers
- **LLM**: OpenAI, LangChain
- **API**: FastAPI, Uvicorn

### 3. OpenAI API Key (Required for Chat)

Get your API key from: https://platform.openai.com/api-keys

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

Or set environment variable:

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### 4. Start the Backend

```bash
uvicorn main:app --reload --port 8000
```

Server will be available at `http://localhost:8000`

### 5. Open the Chat Frontend

Open in your browser:

```bash
xdg-open chat_frontend.html
# or simply open the file: /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf/chat_frontend.html
```

---

## 📡 API Endpoints

### 1. Upload & Process PDF

**POST** `/upload`

Processes PDF with OCR and adds to vector database for chat.

**Request:**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "document_id": "document_a1b2c3d4",
  "filename": "document.pdf",
  "status": "success",
  "ocr_result": { ... },
  "rag_summary": {
    "total_chunks": 45,
    "total_pages": 10
  },
  "message": "Document processed successfully. You can now ask questions!"
}
```

### 2. Ask Questions

**POST** `/chat`

Ask questions about an uploaded document.

**Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "document_a1b2c3d4",
    "question": "What is the main topic of this document?"
  }'
```

**Response:**

```json
{
  "answer": "The main topic of this document is agriculture...",
  "sources": [
    {
      "page_num": 1,
      "similarity_score": 0.89,
      "text_preview": "Agriculture is a primary activity..."
    }
  ],
  "document_id": "document_a1b2c3d4",
  "model": "gpt-3.5-turbo"
}
```

### 3. List Documents

**GET** `/documents`

List all uploaded documents.

```bash
curl "http://localhost:8000/documents"
```

### 4. Delete Document

**DELETE** `/documents/{document_id}`

Delete a document and its vector database.

```bash
curl -X DELETE "http://localhost:8000/documents/document_a1b2c3d4"
```

### 5. OCR Only (No Chat)

**POST** `/ocr`

Process PDF for OCR only without adding to chat database.

```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@document.pdf"
```

---

## 🎨 Frontend Usage

### Upload a PDF

1. Click "Click to upload PDF"
2. Select your PDF file
3. Click "🚀 Process PDF"
4. Wait for processing (OCR + vectorization)

### Ask Questions

1. Type your question in the input box
2. Press Enter or click "Send"
3. AI will answer with sources and page numbers

### Features

- **Real-time chat** with your PDF
- **Source citations** showing which pages answers came from
- **Conversation context** - AI remembers previous questions
- **Beautiful UI** with gradient design

---

## 🧠 How It Works

### 1. Document Processing

When you upload a PDF:

1. **OCR** extracts text, tables, and forms
2. **Chunking** splits text into 500-token chunks with 50-token overlap
3. **Embeddings** converts chunks to 384-dimensional vectors using `all-MiniLM-L6-v2`
4. **Storage** saves vectors in ChromaDB for fast retrieval

### 2. Question Answering

When you ask a question:

1. **Query Embedding** converts your question to a vector
2. **Similarity Search** finds top 5 most relevant chunks
3. **Context Building** combines relevant chunks
4. **LLM Generation** GPT-3.5-turbo generates answer with context
5. **Source Attribution** includes page numbers and similarity scores

---

## ⚙️ Configuration

### Chunk Settings

Edit in `rag_pipeline.py`:

```python
self.chunk_size = 500  # tokens per chunk
self.chunk_overlap = 50  # overlap between chunks
```

### Retrieval Settings

Edit in `rag_pipeline.py` `retrieve_relevant_chunks()`:

```python
top_k=5  # Number of chunks to retrieve
```

### LLM Settings

Edit in `rag_pipeline.py` `generate_answer()`:

```python
temperature=0.7,  # Lower = more focused, Higher = more creative
max_tokens=500    # Maximum length of answer
```

### Model Selection

Change model in `.env`:

```bash
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo, gpt-4-turbo-preview
```

---

## 📊 Data Storage

### Vector Database

- **Location**: `./chroma_db/`
- **Type**: ChromaDB (persistent)
- **Collections**: One per document (`doc_{document_id}`)

### Document Metadata

- **Storage**: In-memory dictionary (for testing)
- **Production**: Use PostgreSQL or MongoDB

---

## 🧪 Testing

### Test with Python

```python
import requests

# 1. Upload document
files = {"file": open("test.pdf", "rb")}
response = requests.post("http://localhost:8000/upload", files=files)
doc_id = response.json()["document_id"]

# 2. Ask question
chat_data = {
    "document_id": doc_id,
    "question": "What is this document about?"
}
response = requests.post("http://localhost:8000/chat", json=chat_data)
print(response.json()["answer"])
```

### Test with Frontend

1. Open `chat_frontend.html`
2. Upload `test-pdf.pdf`
3. Ask: "What are the types of farming mentioned?"
4. Ask: "What crops require high temperature?"

---

## 🎯 Example Questions

For your agriculture PDF:

- "What is agriculture?"
- "What are the types of farming mentioned?"
- "Which crops require high temperature?"
- "What is shifting cultivation?"
- "Compare farming in India vs USA"
- "What is the golden fibre?"

---

## 🔧 Troubleshooting

### "LLM not configured"

**Problem**: No OpenAI API key set

**Solution**:

```bash
export OPENAI_API_KEY="your-key-here"
# or add to .env file
```

### "Document not found"

**Problem**: Document wasn't uploaded or was deleted

**Solution**: Upload the document again using `/upload` endpoint

### Slow Response

**Problem**: First request is slow (model loading)

**Solution**: Normal - subsequent requests will be faster

### Out of Memory

**Problem**: Large PDFs cause memory issues

**Solution**: Reduce `chunk_size` or process fewer pages at once

---

## 🚀 Production Deployment

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="your-key"

# Optional
export OPENAI_MODEL="gpt-3.5-turbo"
export CHROMA_DB_PATH="/path/to/persistent/storage"
```

### Use PostgreSQL for Metadata

Replace in-memory `documents_db` with database:

```python
from sqlalchemy import create_engine
# Store document metadata in PostgreSQL
```

### Add Authentication

```python
from fastapi.security import HTTPBearer
# Add JWT authentication
```

### Use Redis for Caching

```python
import redis
# Cache frequently asked questions
```

---

## 💰 Cost Estimation

### OpenAI API Costs (GPT-3.5-turbo)

- **Input**: $0.0015 per 1K tokens
- **Output**: $0.002 per 1K tokens

**Example**:

- 10-page PDF → ~5000 tokens
- Context per question: ~2500 tokens (5 chunks × 500)
- Answer: ~200 tokens
- **Cost per question**: ~$0.0054

### Free Alternatives

- **Embeddings**: sentence-transformers (free, local)
- **Vector DB**: ChromaDB (free, local)
- **LLM**: Use Ollama for local models (free)

---

## 📚 Additional Features

### Future Enhancements

1. **Multi-document chat** - Ask questions across multiple PDFs
2. **Image understanding** - Extract text from images in PDFs
3. **Conversation export** - Save chat history
4. **Advanced filters** - Search by page, confidence, etc.
5. **Streaming responses** - Real-time answer generation
6. **Voice input** - Ask questions by voice

---

## 📖 Files Overview

```
chatPdf/
├── main.py                 # FastAPI backend with all endpoints
├── ocr_pipeline.py         # OCR, table, form extraction
├── rag_pipeline.py         # RAG, embeddings, vector search, LLM
├── requirements.txt        # All Python dependencies
├── chat_frontend.html      # Simple chat UI for testing
├── test_frontend.html      # OCR testing UI
├── test_api.py             # Python test script
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # Main documentation
├── TABLES_FORMS_GUIDE.md   # Table & form extraction guide
└── CHATPDF_GUIDE.md        # This file
```

---

## ✅ Quick Start Checklist

- [ ] Install system dependencies
- [ ] Install Python packages: `pip install -r requirements.txt`
- [ ] Get OpenAI API key
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Start backend: `uvicorn main:app --reload --port 8000`
- [ ] Open `chat_frontend.html` in browser
- [ ] Upload a PDF
- [ ] Ask questions!

---

## 🎉 You're Ready!

Your complete ChatPDF system is ready to use. Upload a PDF and start asking questions!

Need help? Check the troubleshooting section or the API documentation.
