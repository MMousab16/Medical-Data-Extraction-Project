# frontend/streamlit_app.py
import streamlit as st
from pdf2image import convert_from_bytes
import requests

API_URL = "http://localhost:8000/extract"
POPPLER_PATH = r"C:\poppler-23.01.0\Library\bin"

st.set_page_config(page_title="Medical OCR Extractor", layout="wide")
st.title("Medical OCR Extractor")

doc_type = st.radio("Select document type", options=["prescription", "patient"], index=0)

uploaded_file = st.file_uploader("Upload PDF (only the 4 test PDFs in your resources)", type=["pdf"])
if uploaded_file:
    file_bytes = uploaded_file.read()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Preview (first page)")
        try:
            images = convert_from_bytes(file_bytes, dpi=150, poppler_path=POPPLER_PATH)
            st.image(images[0], use_column_width=True)
        except Exception as e:
            st.error(f"Preview failed: {e}")

    with col2:
        st.subheader("Extraction")
        if st.button("Extract"):
            with st.spinner("Sending to backend..."):
                files = {"file": ("uploaded.pdf", file_bytes, "application/pdf")}
                data = {"doc_type": doc_type}
                try:
                    resp = requests.post(API_URL, files=files, data=data, timeout=90)
                    resp.raise_for_status()
                    result = resp.json()
                    st.success("Extraction completed")
                    # Pretty print extracted fields
                    if result.get("type") == "prescription":
                        st.markdown(f"**Name:** {result.get('name')}")
                        st.markdown(f"**Date:** {result.get('date')}")
                        st.markdown(f"**Address:** {result.get('address')}")
                        st.markdown("**Medicines:**")
                        for m in result.get("medicines", []):
                            st.write(f"- {m}")
                        st.markdown("**Directions:**")
                        st.write(result.get("directions"))
                        st.markdown(f"**Refill:** {result.get('refill')}")
                    else:
                        st.markdown(f"**Name:** {result.get('name')}")
                        st.markdown(f"**Address:** {result.get('address')}")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
