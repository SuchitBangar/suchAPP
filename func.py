import os
import requests
from urllib.parse import quote
from pypdf import PdfWriter, PdfReader
from gtts import gTTS
from PIL import Image

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

def text_to_audio_offline(text, output_path):
    """Simulates offline mode using gTTS to prevent crashing on Render."""
    if not text.strip():
        raise ValueError("No text provided.")
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_path)

def compress_pdf(input_path, output_path):
    """Compresses PDF by removing duplication and compacting streams."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    # 1. First add pages to the writer
    for page in reader.pages:
        writer.add_page(page)
        
    # 2. Then compress the content streams from the writer
    for page in writer.pages:
        page.compress_content_streams()
        
    # 3. Remove identical objects
    writer.compress_identical_objects()
    
    with open(output_path, "wb") as f:
        writer.write(f)

def protect_pdf(input_path, output_path, password):
    """Encrypts a PDF with a password."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(output_path, "wb") as f:
        writer.write(f)

def images_to_pdf(image_paths, output_path):
    """Converts a list of images to a single PDF."""
    images = []
    for path in image_paths:
        img = Image.open(path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)
    if images:
        images[0].save(output_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])

# --- NEW AI IMAGE GENERATOR ---
def generate_image_from_text(prompt, output_path):
    """Generates an image from text using a free external API."""
    encoded_prompt = quote(prompt)
    
    # Updated to the new API endpoint
    api_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
    
    # Increased timeout to 120s just to be safe
    response = requests.get(api_url, timeout=120)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"API Error: {response.status_code}")