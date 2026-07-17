# 🛡️ PII Redaction Tool

> An intelligent document redaction system that automatically detects and anonymizes Personally Identifiable Information (PII) from Microsoft Word documents while preserving document structure and formatting.

Built using **Python**, **FastAPI**, **Streamlit**, **spaCy**, **Regex**, **Faker**, and **python-docx**.

---

## ✨ Features

- 🔍 Detects multiple categories of Personally Identifiable Information
- 📝 Redacts Microsoft Word (.docx) documents while preserving formatting
- 🎭 Replaces sensitive information with realistic fake values instead of generic placeholders
- 🔁 Consistent replacement mapping throughout the document
- ⚡ FastAPI REST API
- 🎨 Interactive Streamlit interface
- 📊 Automatic redaction summary report
- ⚠️ Flags ambiguous detections for manual review
- 📈 Offline evaluation pipeline with Precision, Recall and F1 Score
- 🧩 CLI support for batch processing

---

# Demo

## Input

Upload any `.docx` document containing personal information such as:

- Names
- Email addresses
- Phone numbers
- Company names
- Addresses
- Social Security Numbers
- Credit Card Numbers
- Dates of Birth
- IP Addresses

↓

## Processing

The engine detects sensitive information using a hybrid pipeline consisting of

- Regular Expressions
- spaCy Named Entity Recognition
- Address Heuristics
- Luhn Validation for Credit Cards

↓

## Output

- Fully redacted Word document
- Downloadable DOCX
- JSON redaction log
- Human-readable summary report
- Review suggestions for ambiguous detections

---

# Supported PII Types

| Category | Detection Method |
|-----------|------------------|
| Person Name | spaCy NER |
| Organization | spaCy NER + Filtering |
| Email Address | Regex |
| Phone Number | Regex |
| Address | Heuristic + Regex |
| Date of Birth | Regex + Context Detection |
| Credit Card | Regex + Luhn Validation |
| SSN | Regex |
| IP Address | Regex |

---

# Project Architecture

```
                 +----------------------+
                 |   Streamlit Frontend |
                 +----------+-----------+
                            |
                            |
                            ▼
                 +----------------------+
                 |    FastAPI Backend   |
                 +----------+-----------+
                            |
              -----------------------------
             |             |               |
             ▼             ▼               ▼
     Regex Engine     spaCy NER     Address Detector
             \             |              /
              \            |             /
               --------------------------
                           |
                    Overlap Resolver
                           |
                    Fake Value Generator
                           |
                  Consistent Value Mapper
                           |
                    Redacted DOCX Output
```

---

# Repository Structure

```
.
├── backend/
│   └── FastAPI REST API
│
├── frontend/
│   └── Streamlit Web Application
│
├── src/
│   ├── PII Detection Engine
│   └── DOCX Redaction Utility
│
├── eval/
│   ├── Evaluation Pipeline
│   ├── Synthetic Dataset
│   ├── Ground Truth Labels
│   ├── Evaluation Report
│   └── Metrics
│
├── requirements.txt
└── LICENSE
```

---

# Technology Stack

### Backend

- FastAPI
- Uvicorn

### Frontend

- Streamlit

### NLP

- spaCy
- en_core_web_sm

### Document Processing

- python-docx

### Data Generation

- Faker

### Language

- Python

---

# Installation

Clone the repository

```bash
git clone https://github.com/AryanDhanuka10/pii_redaction_tool.git

cd pii_redaction_tool
```

Install dependencies

```bash
pip install -r requirements.txt
```

Download the spaCy model

```bash
python -m spacy download en_core_web_sm
```

---

# Running the Backend

```bash
cd backend

uvicorn main:app --reload
```

Backend runs on

```
http://localhost:8000
```

---

# Running the Frontend

Open a new terminal

```bash
cd frontend

streamlit run app.py
```

The application launches automatically in your browser.

---

# REST API

## Health Check

```
GET /api/health
```

---

## Redact Document

```
POST /api/redact
```

Upload a `.docx` file.

Returns

- Job ID
- Summary Report
- Counts per PII Type
- Review Suggestions

---

## Download Redacted File

```
GET /api/download/{job_id}
```

---

## View Match Report

```
GET /api/report/{job_id}
```

Returns the complete JSON log containing

- Original Value
- Fake Replacement
- PII Category

---

# Evaluation

The repository includes an offline evaluation framework using a manually labeled synthetic dataset.

Metrics include

- Precision
- Recall
- F1 Score
- Instance Accuracy
- False Positive Analysis

Run

```bash
cd eval

python evaluate.py
```

---

# Evaluation Results

| Metric | Score |
|---------|--------|
| Precision | **96%** |
| Recall | **88.9%** |
| F1 Score | **92.3%** |
| Instance Accuracy | **90.6%** |
| False Positives (Control Set) | **0** |

---

# How It Works

The system follows a hybrid detection pipeline.

### Step 1

Detect structured entities using Regex

- Emails
- Phones
- Credit Cards
- SSNs
- DOB
- IP Addresses

↓

### Step 2

Detect unstructured entities using spaCy

- Person Names
- Organizations

↓

### Step 3

Detect mailing addresses using custom heuristics

↓

### Step 4

Resolve overlapping matches

↓

### Step 5

Generate realistic fake replacements

↓

### Step 6

Replace every occurrence consistently across the document

↓

### Step 7

Generate

- Redacted DOCX
- JSON Report
- Summary Statistics

---

# Design Highlights

- Hybrid NLP + Rule-Based Detection
- Consistent Replacement Mapping
- Formatting Preservation
- Nested Table Support
- Header/Footer Processing
- Luhn Validation for Credit Cards
- Review Flags for Ambiguous Matches
- Offline Benchmarking Framework

---

# Current Limitations

- Uses the lightweight `en_core_web_sm` model, which may occasionally confuse person and organization entities.
- Address detection relies on heuristics and may miss highly fragmented address blocks.
- URL-embedded organization names are not explicitly detected.
- PDF documents are currently not supported.

---

# Future Improvements

- Transformer-based spaCy models
- PDF support
- OCR for scanned documents
- Batch document processing
- Docker deployment
- Kubernetes support
- Authentication
- Role-based access
- Audit logs
- Export reports as CSV and Excel
- Cloud deployment

---

# License

This project is licensed under the **Apache License 2.0**.

---

# Author

## Aryan Dhanuka

AI/ML Engineer

GitHub

https://github.com/AryanDhanuka10

---

⭐ If you found this project useful, consider giving it a star.