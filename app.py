import os
import shutil
import uuid
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from func import (
    merge_pdfs, split_pdf, text_to_audio, extract_text_from_pdf, 
    text_to_audio_offline, compress_pdf, protect_pdf, images_to_pdf, 
    generate_image_from_text
)

app = Flask(__name__)
app.secret_key = "super_secret_key" 

# --- Configurations ---
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_route():
    if 'files' not in request.files:
        flash('No file part')
        return redirect(request.url)
    files = request.files.getlist('files')
    saved_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            saved_paths.append(path)
    if not saved_paths:
        flash('No valid PDF files uploaded')
        return redirect(url_for('index'))
    output_filename = "merged_document.pdf"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    try:
        merge_pdfs(saved_paths, output_path)
        for path in saved_paths: os.remove(path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/split', methods=['POST'])
def split_route():
    if 'file' not in request.files: return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename): return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    try:
        split_folder = os.path.join(app.config['OUTPUT_FOLDER'], 'split_temp')
        if os.path.exists(split_folder): shutil.rmtree(split_folder)
        os.makedirs(split_folder)
        split_pdf(upload_path, split_folder)
        zip_base_name = os.path.join(app.config['OUTPUT_FOLDER'], 'split_files')
        shutil.make_archive(zip_base_name, 'zip', split_folder)
        os.remove(upload_path)
        return send_file(f"{zip_base_name}.zip", as_attachment=True)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/compress', methods=['POST'])
def compress_route():
    if 'file' not in request.files: return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename): return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    try:
        output_filename = f"compressed_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        compress_pdf(upload_path, output_path)
        os.remove(upload_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/protect', methods=['POST'])
def protect_route():
    if 'file' not in request.files: return redirect(url_for('index'))
    file = request.files['file']
    password = request.form.get('password')
    if file.filename == '' or not allowed_file(file.filename): return redirect(url_for('index'))
    if not password: flash('Password required'); return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    try:
        output_filename = f"protected_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        protect_pdf(upload_path, output_path, password)
        os.remove(upload_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/img-to-pdf', methods=['POST'])
def img_to_pdf_route():
    if 'files' not in request.files: return redirect(url_for('index'))
    files = request.files.getlist('files')
    saved_paths = []
    for file in files:
        if file and allowed_image(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            saved_paths.append(path)
    if not saved_paths: flash('No valid images'); return redirect(url_for('index'))
    try:
        output_filename = f"images_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        images_to_pdf(saved_paths, output_path)
        for path in saved_paths: os.remove(path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/generate-image', methods=['POST'])
def generate_image_route():
    prompt = request.form.get('text_prompt')
    if not prompt or not prompt.strip():
         flash('Please enter a description.')
         return redirect(url_for('index'))
    try:
        output_filename = f"generated_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        generate_image_from_text(prompt, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech_route():
    text = request.form.get('text_input')
    accent = request.form.get('accent')
    if not text: flash('Enter text'); return redirect(url_for('index'))
    try:
        filename = f"audio_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        text_to_audio(text, output_path, accent=accent or 'com')
        return render_template('index.html', audio_file=filename)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/pdf-to-audio', methods=['POST'])
def pdf_to_audio_route():
    if 'file' not in request.files: return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename): return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    try:
        extracted_text = extract_text_from_pdf(upload_path)
        if not extracted_text.strip():
            flash("No text found!"); os.remove(upload_path); return redirect(url_for('index'))
        output_filename = f"audiobook_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        text_to_audio_offline(extracted_text, output_path)
        os.remove(upload_path)
        return render_template('index.html', audio_file=output_filename)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/get-audio/<filename>')
def get_audio(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)