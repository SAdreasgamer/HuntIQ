"""
Resume processing pipeline.

This package handles the complete resume lifecycle:

- PDF parsing (PyMuPDF + pdfplumber)
- Structured data extraction (skills, experience, etc.)
- JSON storage and versioning
- Embedding generation
- Resume version management

Key constraint: The PDF is parsed EXACTLY ONCE.
All downstream consumers use the stored structured JSON.
"""
