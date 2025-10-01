# backend/ocr_utils.py
import io
import numpy as np
import cv2
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract

# Configure your Tesseract path (you provided this)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def pdf_to_text(pdf_bytes: bytes,
                poppler_path: str,
                dpi: int = 200,
                block_size: int = 61,
                c: int = 11) -> str:
    """
    Convert a PDF (bytes) -> images -> apply OpenCV adaptive thresholding ->
    pytesseract -> return concatenated OCR text.
    """
    images = convert_from_bytes(pdf_bytes, dpi=dpi, poppler_path=poppler_path)
    chunks = []
    for img in images:
        # PIL -> numpy array for OpenCV
        arr = np.array(img)
        # convert to gray (pdf2image returns RGB)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        # Ensure block_size is odd and >=3
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        # Adaptive thresholding (as you said: adaptive with block_size 61, constant 11)
        th = cv2.adaptiveThreshold(gray, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY,
                                   block_size,
                                   c)
        pil = Image.fromarray(th)
        # Use default OCR; if you want you can pass config="--psm 6"
        text = pytesseract.image_to_string(pil, lang='eng')
        chunks.append(text)
    return "\n".join(chunks)
