# 🔧 Troubleshooting Guide - ChatPDF

## Issue 1: Page Refreshing After Upload

### ✅ FIXED!

**Problem:** Page was refreshing when clicking "Process PDF" button

**Solution:** Updated `chat_frontend.html` to prevent form submission:

- Added `type="button"` to buttons
- Added `event.preventDefault()` in functions
- Added `return false;` to prevent page reload

**Status:** ✅ Fixed - Page no longer refreshes

---

## Issue 2: LLM Not Initialized

### Problem

When you start the backend, you see:

```
INFO: LLM handler initialized
WARNING: No OpenAI API key provided. LLM features disabled.
```

Or the frontend shows:

```
⚠️ LLM Not Initialized!
Set OPENAI_API_KEY in your .env file and restart the server.
```

### Root Causes & Solutions

#### Cause 1: .env File Not Found

**Check:**

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
ls -la .env
```

**If file doesn't exist:**

```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**If file exists but empty:**

```bash
# Edit .env file
nano .env
# Add this line:
OPENAI_API_KEY=sk-your-key-here
# Save: Ctrl+O, Enter, Ctrl+X
```

#### Cause 2: Wrong API Key Format

**Check your .env file:**

```bash
cat .env
```

**Should look like:**

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Common mistakes:**

- ❌ `OPENAI_API_KEY="sk-..."` (no quotes needed)
- ❌ `OPENAI_API_KEY = sk-...` (no spaces around =)
- ❌ `OPENAI_KEY=sk-...` (wrong variable name)
- ✅ `OPENAI_API_KEY=sk-...` (correct!)

#### Cause 3: Server Not Restarted

After changing .env, you MUST restart the server!

```bash
# Stop server: Press Ctrl+C in terminal where uvicorn is running
# Then start again:
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
uvicorn main:app --reload --port 8000
```

#### Cause 4: python-dotenv Not Installed

**Check:**

```bash
pip list | grep python-dotenv
```

**If not found, install:**

```bash
pip install python-dotenv
```

#### Cause 5: .env in Wrong Directory

**.env must be in the project root:**

```
chatPdf/
├── .env          ← HERE!
├── main.py
├── rag_pipeline.py
└── ...
```

**Check location:**

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
pwd  # Should show: /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
ls -la .env  # Should show the file
```

---

## ✅ Verification Steps

### Step 1: Check .env File

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
cat .env
```

Expected output:

```
OPENAI_API_KEY=sk-proj-...your key here...
```

### Step 2: Verify API Key is Valid

Test with curl:

```bash
# Replace YOUR_KEY with your actual key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

Should return list of models (not an error).

### Step 3: Start Backend with Debug

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'API Key loaded: {bool(os.getenv(\"OPENAI_API_KEY\"))}')"
```

Should print: `API Key loaded: True`

### Step 4: Start Server and Check Logs

```bash
uvicorn main:app --reload --port 8000
```

**Look for this in the logs:**

```
INFO: LLM initialized with model: gpt-4o-mini  ← GOOD!
```

**NOT this:**

```
WARNING: No OpenAI API key provided. LLM features disabled.  ← BAD!
```

### Step 5: Test with Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "ocr_initialized": false,
  "rag_initialized": false,
  "llm_initialized": true  ← Should be TRUE!
}
```

---

## 🎯 Quick Fix Script

Run this to diagnose the issue:

```bash
#!/bin/bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf

echo "=== ChatPDF LLM Diagnostic ==="
echo ""

echo "1. Checking .env file..."
if [ -f .env ]; then
    echo "✅ .env file exists"
    if grep -q "OPENAI_API_KEY=" .env; then
        echo "✅ OPENAI_API_KEY found in .env"
        KEY_LENGTH=$(grep "OPENAI_API_KEY=" .env | cut -d'=' -f2 | wc -c)
        if [ $KEY_LENGTH -gt 40 ]; then
            echo "✅ API key looks valid (length: $KEY_LENGTH chars)"
        else
            echo "❌ API key seems too short (length: $KEY_LENGTH chars)"
        fi
    else
        echo "❌ OPENAI_API_KEY not found in .env"
    fi
else
    echo "❌ .env file not found!"
fi

echo ""
echo "2. Checking python-dotenv..."
if python -c "import dotenv" 2>/dev/null; then
    echo "✅ python-dotenv is installed"
else
    echo "❌ python-dotenv not installed"
    echo "   Fix: pip install python-dotenv"
fi

echo ""
echo "3. Testing .env loading..."
python -c "from dotenv import load_dotenv; import os; load_dotenv(); key=os.getenv('OPENAI_API_KEY'); print('✅ API Key loaded!' if key else '❌ API Key NOT loaded')"

echo ""
echo "=== Next Steps ==="
echo "If you see any ❌, fix those issues first."
echo "Then restart the server: uvicorn main:app --reload --port 8000"
```

**Save this as `diagnose.sh` and run:**

```bash
chmod +x diagnose.sh
./diagnose.sh
```

---

## 📝 Complete Fix Procedure

Follow these steps in order:

### 1. Stop the Server

Press `Ctrl+C` in the terminal running uvicorn

### 2. Check/Create .env File

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
nano .env
```

Add this line (replace with your actual key):

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Save: `Ctrl+O`, Enter, `Ctrl+X`

### 3. Verify .env File

```bash
cat .env
```

Should show your API key.

### 4. Install python-dotenv (if needed)

```bash
pip install python-dotenv
```

### 5. Test Loading

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key:', 'FOUND' if os.getenv('OPENAI_API_KEY') else 'NOT FOUND')"
```

Should print: `Key: FOUND`

### 6. Restart Server

```bash
uvicorn main:app --reload --port 8000
```

Look for:

```
INFO: LLM initialized with model: gpt-4o-mini
```

### 7. Test Health

```bash
curl http://localhost:8000/health
```

Check `"llm_initialized": true`

### 8. Test Chat

Open `chat_frontend.html` and upload a PDF!

---

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ Server logs show: `INFO: LLM initialized with model: gpt-4o-mini`
2. ✅ Health check shows: `"llm_initialized": true`
3. ✅ Frontend doesn't show LLM warning
4. ✅ You can ask questions and get AI answers
5. ✅ Page doesn't refresh when uploading PDFs

---

## 💡 Still Having Issues?

### Option 1: Use Virtual Environment

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Option 2: Set Environment Variable Directly

```bash
export OPENAI_API_KEY="sk-your-key-here"
uvicorn main:app --reload --port 8000
```

### Option 3: Check Permissions

```bash
chmod 600 .env  # Make .env readable only by you
```

---

## 📞 Get Your OpenAI API Key

If you don't have one yet:

1. Go to: https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)
5. Add to .env file
6. Restart server

---

**Both issues are now fixed! Your page won't refresh and LLM will initialize properly when configured correctly.** ✅
