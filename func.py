import os
from pypdf import PdfWriter, PdfReader
from gtts import gTTS

def merge_pdfs(file_paths, output_path):
    """Merges multiple PDFs into one."""
    merger = PdfWriter()
    for path in file_paths:
        merger.append(path)
    merger.write(output_path)
    merger.close()

def split_pdf(file_path, output_folder):
    """Splits a PDF into individual pages."""
    reader = PdfReader(file_path)
    saved_files = []
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        output_filename = f"{base_name}_page_{i+1}.pdf"
        output_path = os.path.join(output_folder, output_filename)
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        saved_files.append(output_path)
    return saved_files

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def text_to_audio(text, output_path, language='en', accent='com'):
    """ONLINE: High quality, but slower."""
    if not text.strip():
        raise ValueError("No text provided to convert.")
    tts = gTTS(text=text, lang=language, tld=accent, slow=False)
    tts.save(output_path)

# --- THIS IS THE MISSING FUNCTION CAUSING THE CRASH ---
def text_to_audio_offline(text, output_path):
    """
    Simulates offline mode using gTTS to prevent crashing on Render.
    """
    if not text.strip():
        raise ValueError("No text provided.")
    # We use gTTS here because pyttsx3 crashes on servers
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_path)