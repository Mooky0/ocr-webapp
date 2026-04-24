import io
import pytesseract
from PIL import Image as PILImage

def run_ocr(image_bytes) -> dict:
    img = PILImage.open(io.BytesIO(image_bytes))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    print("OCR data:", data)  # Debug print to check the OCR output
    return data
