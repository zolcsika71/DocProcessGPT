import os
import logging
from flask import Flask, request, jsonify, render_template, send_file, abort, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from pdf_processor import extract_text_from_pdf
from text_preprocessor import preprocess_text

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/', methods=['GET'])
def index():
    try:
        app.logger.info("Rendering index page")
        return render_template('upload.html')
    except Exception as e:
        app.logger.error(f"Error rendering index page: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            app.logger.error("No file part in the request")
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            app.logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            app.logger.info(f"File saved: {filepath}")
            
            # Extract text from PDF
            raw_text = extract_text_from_pdf(filepath)
            
            app.logger.info(f"Text extracted from PDF, length: {len(raw_text)}")
            
            # Preprocess the text
            processed_text = preprocess_text(raw_text)
            
            app.logger.info(f"Text preprocessed, length: {len(processed_text)}")
            
            # Save processed text to a file
            processed_filename = f"processed_{filename}.txt"
            processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            with open(processed_filepath, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            app.logger.info(f"Processed text saved: {processed_filepath}")
            
            return jsonify({'message': 'File successfully processed', 'filename': processed_filename}), 200
        else:
            app.logger.error(f"Invalid file format: {file.filename}")
            return jsonify({'error': 'Invalid file format. Please upload a PDF file.'}), 400
    except Exception as e:
        app.logger.error(f"Error in upload_file: {str(e)}")
        raise

@app.route('/processed/<filename>', methods=['GET'])
def get_processed_text(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return jsonify(error=str(e)), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error="An unexpected error occurred"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
