# 🚀 Quick Start Guide - ChatPDF

Perfect! You have your OpenAI API key in a `.env` file. Let's get your ChatPDF system running!

---

## ✅ Step 1: Verify Your .env File

Make sure your `.env` file in the project root contains:

```bash
OPENAI_API_KEY=your_actual_key_here
```

You can check it:

```bash
cat .env
```

---

## ✅ Step 2: Install All Dependencies

### System Dependencies (if not installed yet)

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils ghostscript python3-tk libgl1-mesa-glx
```

### Python Dependencies

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
pip install -r requirements.txt
```

This will install:

- ✅ FastAPI & Uvicorn (backend)
- ✅ PaddleOCR (OCR processing)
- ✅ Camelot (table extraction)
- ✅ ChromaDB (vector database)
- ✅ sentence-transformers (embeddings)
- ✅ OpenAI (LLM for chat)
- ✅ python-dotenv (loads .env file)

**Note:** Installation may take 5-10 minutes depending on your internet speed.

---

## ✅ Step 3: Start the Backend

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
uvicorn main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Keep this terminal running!** The backend needs to stay active.

---

## ✅ Step 4: Test the API

Open a **NEW terminal** and test:

```bash
# Test health check
curl http://localhost:8000/health
```

You should see:

```json
{
  "status": "healthy",
  "ocr_initialized": false,
  "rag_initialized": false,
  "llm_initialized": true
}
```

**Important:** `llm_initialized: true` means your OpenAI API key is working! ✅

---

## ✅ Step 5: Open the Chat Frontend

**Option A: Using Browser Command**

```bash
xdg-open /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf/chat_frontend.html
```

**Option B: Manual**

1. Open your browser
2. Press `Ctrl+O` (or File → Open)
3. Navigate to: `/mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf/chat_frontend.html`
4. Open the file

---

## ✅ Step 6: Upload & Chat!

### Upload Your PDF

1. Click "Click to upload PDF"
2. Select `test-pdf.pdf` (or any PDF)
3. Click "🚀 Process PDF"
4. Wait 10-30 seconds for processing

You'll see:

```
Document "test-pdf.pdf" loaded! You can now ask questions about it.
```

### Ask Questions!

Try these:

- "What is this document about?"
- "Summarize the main topics"
- "What are the types of farming?"
- "Compare farming in India vs USA"

You'll get AI answers with **page number citations**! 📚

---

## 🧪 Alternative: Test with Python Script

Instead of the frontend, you can test with the Python script:

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
python test_chatpdf.py test-pdf.pdf
```

This will:

1. Check API health ✅
2. Upload your PDF ✅
3. Process with OCR ✅
4. Ask 3 sample questions ✅
5. Show AI answers ✅

---

## 📊 What You Should See

### In the Backend Terminal:

```
INFO: Initializing OCR pipeline...
INFO: OCR pipeline initialized successfully
INFO: Initializing RAG pipeline...
INFO: Loading embeddings model...
INFO: Embeddings model loaded successfully
INFO: Processing file: test-pdf.pdf as document_id: test-pdf_a1b2c3d4
INFO: Running OCR on test-pdf.pdf...
INFO: Processing page 1/10
INFO: Page 1: Using native text
INFO: Page 1: Extracting tables...
INFO: Adding document to vector database...
INFO: Generated embeddings for 45 chunks
INFO: Added 45 chunks to vector database
```

### In the Chat Frontend:

```
📁 Document Info
File: test-pdf.pdf
Pages: 10
Chunks: 45
Status: Ready ✅

💬 Chat
You: What is agriculture?
```
