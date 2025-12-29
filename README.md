# ChatPDF - AI-Powered PDF Question Answering System

A complete backend and frontend system for uploading PDFs, extracting content (text, tables, forms), and asking intelligent questions using AI.

## 🌟 Features

### Document Processing

- **Native text extraction** using PyMuPDF for fast text-based PDFs
- **OCR fallback** using PaddleOCR for scanned/image-based PDFs
- **Table extraction** using Camelot library (lattice & stream methods)
- **Form field detection** for interactive PDF forms
- **Image preprocessing** with OpenCV (deskew, denoise, threshold)

### AI Chat

- **Vector Search** using ChromaDB for semantic retrieval
- **Embeddings** with sentence-transformers (free, local)
- **LLM Integration** with OpenAI GPT-3.5/GPT-4
- **RAG Pipeline** (Retrieval Augmented Generation)
- **Source Citations** with page numbers and similarity scores
- **Conversation Context** remembers previous questions

### API

- **RESTful API** with FastAPI
- **Upload endpoint** for PDF processing
- **Chat endpoint** for questions
- **Document management** (list, get, delete)
- **OCR-only endpoint** for text extraction without chat

---

## 🚀 Quick Start

### 1. Installation

#### System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils ghostscript python3-tk libgl1-mesa-glx
```

#### Python Dependencies

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
pip install -r requirements.txt
```

### 2. Configuration

#### Set OpenAI API Key (Required for Chat)

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or create `.env` file:

```bash
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Start Backend

```bash
uvicorn main:app --reload --port 8000
```

Server will be at `http://localhost:8000`

### 4. Use the System

#### Option A: Chat Frontend (Recommended)

```bash
# Open in browser
xdg-open chat_frontend.html
```

#### Option B: Test Script

```bash
python test_chatpdf.py test-pdf.pdf
```

#### Option C: API Directly

```bash
# Upload PDF
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test-pdf.pdf"

# Ask question
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc_id", "question": "What is this about?"}'
```

---

## 📡 API Endpoints

### POST /upload

Upload and process PDF for chat

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
  }
}
```

### POST /chat

Ask questions about uploaded document

**Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "document_a1b2c3d4",
    "question": "What is the main topic?"
  }'
```

**Response:**

```json
{
  "answer": "The main topic is...",
  "sources": [
    {
      "page_num": 1,
      "similarity_score": 0.89,
      "text_preview": "..."
    }
  ],
  "document_id": "document_a1b2c3d4",
  "model": "gpt-3.5-turbo"
}
```

### GET /documents

List all uploaded documents

### DELETE /documents/{document_id}

Delete a document

### POST /ocr

OCR only (no chat features)

### GET /health

Health check endpoint

---

## 🎨 Frontend Features

### Chat Interface (`chat_frontend.html`)

- **Upload PDFs** with drag & drop
- **Ask questions** in natural language
- **Get answers** with source citations
- **View page numbers** where answers come from
- **Conversation history** for context
- **Beautiful UI** with gradient design

### OCR Test Interface (`test_frontend.html`)

- Test OCR extraction
- View extracted text, tables, and forms
- See confidence scores
- Export results as JSON

---

## 📂 Project Structure

```
chatPdf/
├── main.py                 # FastAPI backend (API endpoints)
├── ocr_pipeline.py         # OCR, tables, forms extraction
├── rag_pipeline.py         # RAG, embeddings, vector search, LLM
├── requirements.txt        # All dependencies
├── chat_frontend.html      # Main chat interface
├── test_frontend.html      # OCR testing interface
├── test_chatpdf.py         # Python test script
├── test_api.py             # OCR test script
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── CHATPDF_GUIDE.md        # Detailed guide
└── TABLES_FORMS_GUIDE.md   # Table & form extraction guide
```

---

## 🧠 How It Works

### 1. Document Upload & Processing

```
PDF Upload
   ↓
OCR Processing (text, tables, forms)
   ↓
Text Chunking (500 tokens with overlap)
   ↓
Generate Embeddings (sentence-transformers)
   ↓
Store in ChromaDB (vector database)
   ↓
Ready for Questions!
```

### 2. Question Answering

```
User Question
   ↓
Generate Query Embedding
   ↓
Vector Similarity Search (find top 5 chunks)
   ↓
Build Context from Relevant Chunks
   ↓
Send to LLM (GPT-3.5-turbo)
   ↓
Generate Answer with Sources
   ↓
Return Answer + Page Numbers
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required for chat features
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4, gpt-4-turbo-preview
```

### Chunk Settings

Edit `rag_pipeline.py`:

```python
self.chunk_size = 500       # tokens per chunk
self.chunk_overlap = 50     # overlap between chunks
```

### Retrieval Settings

Edit `rag_pipeline.py`:

```python
top_k=5  # Number of relevant chunks to retrieve
```

### LLM Settings

Edit `rag_pipeline.py`:

```python
temperature=0.7,    # Lower = focused, Higher = creative
max_tokens=500      # Maximum answer length
```

---

## 🧪 Testing

### Test with Python Script

```bash
# Test with your PDF
python test_chatpdf.py test-pdf.pdf
```

This will:

1. Check API health
2. Upload the PDF
3. Process with OCR
4. Add to vector database
5. Ask sample questions
6. Show answers with sources

### Test with Frontend

1. Open `chat_frontend.html` in browser
2. Upload your PDF
3. Wait for processing
4. Ask questions in the chat box

### Example Questions (for agriculture PDF)

- "What is agriculture?"
- "What are the types of farming?"
- "Compare farming in India vs USA"
- "What crops need high temperature?"
- "What is the golden fibre?"

---

## 💡 Use Cases

### Education

- Study documents by asking questions
- Get quick summaries
- Find specific information fast

### Research

- Extract data from research papers
- Find relevant sections
- Compare information across pages

### Business

- Analyze reports and contracts
- Extract key points
- Answer specific questions about documents

### Legal

- Search through legal documents
- Find relevant clauses
- Get quick answers

---

## 🐛 Troubleshooting

### "LLM not configured"

**Problem:** No OpenAI API key

**Solution:**

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### "Document not found"

**Problem:** Document wasn't uploaded

**Solution:** Upload document first using `/upload` endpoint

### Ghostscript Error

**Problem:** Camelot can't find Ghostscript

**Solution:**

```bash
sudo apt-get install ghostscript
```

### Backend Not Running

**Problem:** Can't connect to API

**Solution:**

```bash
uvicorn main:app --reload --port 8000
```

### Slow First Request

**Problem:** First request takes long

**Solution:** Normal - models are loading. Subsequent requests are faster.

---

## 💰 Costs

### OpenAI API (GPT-3.5-turbo)

- Input: $0.0015 per 1K tokens
- Output: $0.002 per 1K tokens
- **~$0.005 per question** (typical)

### Free Components

- ✅ OCR: PaddleOCR (free)
- ✅ Embeddings: sentence-transformers (free, local)
- ✅ Vector DB: ChromaDB (free, local)
- ✅ Tables: Camelot (free)

### Cost-Saving Tips

- Use GPT-3.5-turbo instead of GPT-4
- Reduce `max_tokens` in responses
- Cache frequently asked questions
- Use local LLMs with Ollama (free alternative)

---

## 🚀 Production Deployment

### Security

- [ ] Add authentication (JWT tokens)
- [ ] Rate limiting
- [ ] Input validation
- [ ] HTTPS/SSL

### Database

- [ ] Use PostgreSQL for document metadata
- [ ] Persistent storage for ChromaDB
- [ ] Redis for caching

### Monitoring

- [ ] Add logging (ELK stack)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Usage analytics

### Scaling

- [ ] Use Celery for async processing
- [ ] Multiple worker processes
- [ ] Load balancer
- [ ] CDN for static files

---

## 📚 Documentation

- **[CHATPDF_GUIDE.md](CHATPDF_GUIDE.md)** - Complete guide with architecture and examples
- **[TABLES_FORMS_GUIDE.md](TABLES_FORMS_GUIDE.md)** - Table and form extraction guide
- **API Docs** - Visit `http://localhost:8000/docs` when server is running

---

## 🤝 Support

### Get Help

1. Check this README
2. Read CHATPDF_GUIDE.md
3. Check API docs at `/docs`
4. Review error logs

### Common Issues

- **No API key**: Set `OPENAI_API_KEY`
- **Can't install packages**: Check system dependencies
- **Server won't start**: Check if port 8000 is available
- **OCR not working**: Verify PaddleOCR installation

---

## 📝 License

MIT License - Feel free to use in your projects!

---

## 🎉 You're Ready!

Your ChatPDF system is complete and ready to use!

1. ✅ Start the backend: `uvicorn main:app --reload --port 8000`
2. ✅ Open `chat_frontend.html` in your browser
3. ✅ Upload a PDF
4. ✅ Ask questions!

**Enjoy your AI-powered PDF assistant!** 🚀
