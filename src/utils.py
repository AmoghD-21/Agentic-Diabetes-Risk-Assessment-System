import io
import re
import numpy as np

# Digital Extraction Engines
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pypdfium2
except ImportError:
    pypdfium2 = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# OCR Engines (For Scanned Images)
try:
    import easyocr
except ImportError:
    easyocr = None

def clean_extracted_text(text: str) -> str:
    """Sanitizes text for LLM processing."""
    if not text:
        return ""
    # Remove null bytes and non-printable characters
    text = "".join(char for char in text if char.isprintable() or char in "\n\t ")
    # Normalize spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Advanced Multi-Engine Extraction.
    Digital: pdfplumber > pypdfium2 > PyPDF2
    Fallback: EasyOCR (No external Tesseract software needed).
    """
    if not file_bytes:
        return ""
    
    pdf_file = io.BytesIO(file_bytes)
    text = ""

    # --- 1. DIGITAL EXTRACTION (First Priority) ---
    if pdfplumber:
        try:
            pdf_file.seek(0)
            with pdfplumber.open(pdf_file) as pdf:
                pages = [page.extract_text(layout=True) for page in pdf.pages]
                text = "\n".join(filter(None, pages))
            if text.strip():
                print(f"[DEBUG utils] Extracted {len(text)} chars via pdfplumber")
                return clean_extracted_text(text)
        except Exception: 
            pass

    if pypdfium2:
        try:
            pdf_file.seek(0)
            pdf = pypdfium2.PdfDocument(pdf_file)
            pages = []
            for page in pdf:
                tp = page.get_textpage()
                pages.append(tp.get_text_range())
                tp.close()
                page.close()
            pdf.close()
            text = "\n".join(filter(None, pages))
            if text.strip():
                print(f"[DEBUG utils] Extracted {len(text)} chars via pypdfium2")
                return clean_extracted_text(text)
        except Exception: 
            pass

    if PyPDF2:
        try:
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            pages = [p.extract_text() for p in reader.pages]
            text = "\n".join(filter(None, pages))
            if text.strip():
                print(f"[DEBUG utils] Extracted {len(text)} chars via PyPDF2")
                return clean_extracted_text(text)
        except Exception: 
            pass

    # --- 2. OCR EXTRACTION (EasyOCR Fallback) ---
    # Triggered if digital extraction returns no text (scanned reports).
    if easyocr and pypdfium2:
        try:
            print("[DEBUG utils] Digital failed. Starting EasyOCR...")
            # Initialize reader (English). Note: This downloads models on the first run (~100MB).
            reader = easyocr.Reader(['en'], gpu=False) # Set gpu=True if you have an NVIDIA GPU
            
            pdf = pypdfium2.PdfDocument(file_bytes)
            ocr_pages = []
            
            for page in pdf:
                # Render page to a bitmap
                bitmap = page.render(scale=2)
                pil_image = bitmap.to_pil()
                
                # Convert PIL image to numpy array for EasyOCR
                img_array = np.array(pil_image)
                
                # Perform OCR (detail=0 returns raw text string)
                results = reader.readtext(img_array, detail=0)
                ocr_pages.append(" ".join(results))
                
                bitmap.close()
                page.close()
            pdf.close()
            
            text = "\n".join(ocr_pages)
            if text.strip():
                print(f"[DEBUG utils] EasyOCR Success: Extracted {len(text)} chars.")
                return clean_extracted_text(text)
        except Exception as e:
            print(f"[ERROR utils] EasyOCR Engine failed: {e}")

    print("[CRITICAL utils] All extraction methods failed.")
    return ""