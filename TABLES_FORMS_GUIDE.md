# Table and Form Extraction Guide

## Overview

Your OCR backend now supports **three types of data extraction**:

1. **Text Extraction** - Native text or OCR
2. **Table Extraction** - Using Camelot library
3. **Form Field Extraction** - Using PyMuPDF

---

## 🚀 Installation

### 1. System Dependencies (Required for Camelot)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ghostscript python3-tk

# For Camelot CV flavor
sudo apt-get install -y libgl1-mesa-glx
```

### 2. Python Dependencies

```bash
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
pip install -r requirements.txt
```

Or install individually:

```bash
pip install camelot-py[cv]==0.11.0 pandas==2.0.3 tabulate==0.9.0
```

---

## 📊 Features

### 1. Table Extraction (Camelot)

**What it does:**

- Extracts tables from PDF pages
- Tries two methods: `lattice` (for bordered tables) and `stream` (for borderless tables)
- Provides accuracy scores
- Returns data in multiple formats (array, markdown)

**Output format:**

```json
{
  "table_id": 1,
  "accuracy": 0.95,
  "rows": 5,
  "columns": 3,
  "data": [
    ["Header1", "Header2", "Header3"],
    ["Row1Col1", "Row1Col2", "Row1Col3"],
    ["Row2Col1", "Row2Col2", "Row2Col3"]
  ],
  "headers": ["Header1", "Header2", "Header3"],
  "markdown": "| Header1 | Header2 | Header3 |\n|---------|---------|---------|..."
}
```

### 2. Form Field Extraction

**What it does:**

- Detects interactive form fields (text boxes, checkboxes, radio buttons, dropdowns)
- Extracts field names, types, values, and positions
- Identifies readonly and required fields

**Output format:**

```json
{
  "field_name": "full_name",
  "field_type": "Text",
  "field_value": "John Doe",
  "field_label": "Full Name",
  "is_readonly": false,
  "is_required": true,
  "position": {
    "x": 100.5,
    "y": 200.3,
    "width": 300.0,
    "height": 20.0
  }
}
```

### 3. Text Extraction (Enhanced)

Same as before, but now integrated with tables and forms:

- Native text extraction (fast)
- OCR fallback with preprocessing

---

## 📝 Complete API Response

```json
{
  "file": "document.pdf",
  "pages": [
    {
      "page_num": 1,
      "source": "native",
      "text": "Regular text content...",
      "confidence": 1.0,
      "tables": [
        {
          "table_id": 1,
          "accuracy": 0.95,
          "rows": 5,
          "columns": 3,
          "data": [[...], [...]],
          "headers": [...],
          "markdown": "..."
        }
      ],
      "forms": [
        {
          "field_name": "email",
          "field_type": "Text",
          "field_value": "user@example.com",
          "position": {...}
        }
      ]
    }
  ]
}
```

---

## 🧪 Testing

### Restart the Backend

If the backend is already running, restart it to load the new code:

```bash
# Stop the current server (Ctrl+C in the terminal)
# Then restart:
cd /mnt/983C33DC3C33B45A/flutter/orcharland/chatPdf
uvicorn main:app --reload --port 8000
```

### Test with curl

```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/pdf_with_tables.pdf" \
  -H "accept: application/json"
```

### Test with Python Script

```python
import requests
import json

url = "http://localhost:8000/ocr"
files = {"file": open("document_with_tables.pdf", "rb")}
response = requests.post(url, files=files)

data = response.json()

# Access tables
for page in data['pages']:
    print(f"\nPage {page['page_num']}:")
    print(f"  Text length: {len(page['text'])}")
    print(f"  Tables found: {len(page['tables'])}")
    print(f"  Form fields found: {len(page['forms'])}")

    # Print table data
    for table in page['tables']:
        print(f"\n  Table {table['table_id']}:")
        print(f"    Accuracy: {table['accuracy']}")
        print(f"    Size: {table['rows']} rows x {table['columns']} columns")
        print(f"    Markdown:\n{table['markdown']}")

    # Print form fields
    for form in page['forms']:
        print(f"\n  Form field: {form['field_name']}")
        print(f"    Type: {form['field_type']}")
        print(f"    Value: {form['field_value']}")
```

### Test with the HTML Frontend

The existing `test_frontend.html` will automatically show tables and forms data if you update it, or you can use the API response directly.

---

## 🎯 Use Cases

### 1. Extract Tables from Reports

Perfect for:

- Financial statements
- Data reports
- Scientific papers
- Invoices with line items

### 2. Extract Form Data

Perfect for:

- Application forms
- Survey responses
- Registration forms
- Tax documents

### 3. Combined Extraction

Extract text + tables + forms in one pass:

- Complete document analysis
- Data migration
- Document digitization

---

## ⚙️ Configuration

### Table Extraction Settings

In `ocr_pipeline.py`, you can adjust:

```python
# For bordered tables
tables = camelot.read_pdf(
    pdf_path,
    pages=str(page_num + 1),
    flavor='lattice'
)

# For borderless tables
tables = camelot.read_pdf(
    pdf_path,
    pages=str(page_num + 1),
    flavor='stream',
    edge_tol=50,        # Edge tolerance
    row_tol=2           # Row tolerance
)
```

### Form Extraction

Form detection is automatic with PyMuPDF - no configuration needed.

---

## 🐛 Troubleshooting

### Ghostscript Error

```bash
Error: Ghostscript not found
```

**Solution:**

```bash
sudo apt-get install ghostscript
```

### Camelot Import Error

```bash
ModuleNotFoundError: No module named 'cv2'
```

**Solution:**

```bash
pip install opencv-python-headless
```

### Tables Not Detected

**Possible causes:**

1. Table has no borders → Use `stream` flavor
2. Table is in image format → OCR won't detect tables in images
3. Low quality scan → Improve PDF quality

**Solution:**

- Try both `lattice` and `stream` methods (code already does this)
- For scanned tables, consider using table detection ML models

### Form Fields Not Found

**Possible causes:**

1. PDF has static text, not interactive form fields
2. Form fields are flattened

**Note:** This only detects interactive PDF form fields, not printed forms.

---

## 📚 Additional Resources

- [Camelot Documentation](https://camelot-py.readthedocs.io/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR)

---

## 🎓 Example PDFs for Testing

Good test cases:

1. **Financial reports** (tables)
2. **IRS tax forms** (forms + tables)
3. **Scientific papers** (tables)
4. **Application forms** (interactive fields)
5. **Invoices** (tables + text)

---

## ✅ Quick Verification

After installation, verify everything works:

```bash
# 1. Check Ghostscript
gs --version

# 2. Check Python packages
python3 -c "import camelot; print('Camelot OK')"
python3 -c "import pandas; print('Pandas OK')"

# 3. Start backend
uvicorn main:app --reload --port 8000

# 4. Test with your PDF
python3 test_api.py your_pdf_with_tables.pdf
```

You should see table and form extraction logs in the console!
