import os
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from pdf_processor import extract_text_from_pdf
from text_preprocessor import preprocess_text

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        raw_text = extract_text_from_pdf(filepath)
        
        # Preprocess the text
        processed_text = preprocess_text(raw_text)
        
        # Save processed text to a file
        processed_filename = f"processed_{filename}.txt"
        processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        with open(processed_filepath, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        
        return jsonify({'message': 'File successfully processed', 'filename': processed_filename}), 200
    else:
        return jsonify({'error': 'Invalid file format. Please upload a PDF file.'}), 400

@app.route('/processed/<filename>', methods=['GET'])
def get_processed_text(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
