# backend/app.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ocr_utils import pdf_to_text
from hospital import PrescriptionExtractor, PatientExtractor

# Your poppler path you gave
POPPLER_PATH = r"C:\poppler-23.01.0\Library\bin"

app = FastAPI(title="Medical OCR Extractor API")

# Allow Streamlit front-end to call
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/extract")
async def extract_doc(file: UploadFile = File(...), doc_type: str = Form(...)):
    """
    POST /extract
      - form field 'doc_type': 'prescription' or 'patient'
      - file: pdf file
    returns: JSON dict produced by the appropriate extractor
    """
    content = await file.read()
    try:
        text = pdf_to_text(content, poppler_path=POPPLER_PATH, block_size=61, c=11)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"OCR failed: {e}"})

    if doc_type.lower().startswith('pres'):
        ext = PrescriptionExtractor(text)
    else:
        ext = PatientExtractor(text)

    result = ext.extract()
    return result
