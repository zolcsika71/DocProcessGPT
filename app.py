import os
import logging
import threading
import mimetypes
import time
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
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type != 'application/pdf':
            app.logger.error(f"Invalid file type: {mime_type}")
            return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        app.logger.info(f"File saved: {filepath}")
        
        # Start processing in a background thread
        threading.Thread(target=process_pdf, args=(filepath, filename)).start()
        
        return render_template('processing.html', filename=filename)
    except Exception as e:
        app.logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_pdf(filepath, filename):
    try:
        app.logger.info(f"Starting PDF processing for {filename}")
        file_size = os.path.getsize(filepath)
        app.logger.info(f"File size: {file_size} bytes")
        
        start_time = time.time()
        app.logger.info("Extracting text from PDF")
        try:
            raw_text = extract_text_from_pdf(filepath)
            extraction_time = time.time() - start_time
            app.logger.info(f"Text extracted from PDF, length: {len(raw_text)}, time taken: {extraction_time:.2f} seconds")
        except Exception as e:
            app.logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
        
        start_time = time.time()
        app.logger.info("Preprocessing extracted text")
        try:
            processed_text = preprocess_text(raw_text)
            preprocessing_time = time.time() - start_time
            app.logger.info(f"Text preprocessed, length: {len(processed_text)}, time taken: {preprocessing_time:.2f} seconds")
        except Exception as e:
            app.logger.error(f"Error preprocessing text: {str(e)}")
            raise
        
        processed_filename = f"processed_{filename}.txt"
        processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        app.logger.info(f"Saving processed text to: {processed_filepath}")
        start_time = time.time()
        with open(processed_filepath, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        saving_time = time.time() - start_time
        app.logger.info(f"Processed text saved successfully: {processed_filepath}, time taken: {saving_time:.2f} seconds")
        
        total_time = extraction_time + preprocessing_time + saving_time
        app.logger.info(f"Total processing time: {total_time:.2f} seconds")
    except Exception as e:
        app.logger.error(f"Error processing PDF {filename}: {str(e)}")
        error_filename = f"error_{filename}.txt"
        error_filepath = os.path.join(app.config['UPLOAD_FOLDER'], error_filename)
        with open(error_filepath, 'w', encoding='utf-8') as f:
            f.write(str(e))
        app.logger.error(f"Error details saved to: {error_filepath}")

@app.route('/process_status/<filename>', methods=['GET'])
def process_status(filename):
    app.logger.info(f"Checking process status for: {filename}")
    processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_{filename}.txt")
    error_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"error_{filename}.txt")
    
    if os.path.exists(processed_filepath):
        app.logger.info(f"Processing complete for: {filename}")
        return jsonify({'status': 'complete', 'filename': f"processed_{filename}.txt"})
    elif os.path.exists(error_filepath):
        app.logger.error(f"Error occurred during processing: {filename}")
        with open(error_filepath, 'r', encoding='utf-8') as f:
            error_message = f.read()
        return jsonify({'status': 'error', 'error': error_message})
    elif os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        app.logger.info(f"Processing still in progress for: {filename}")
        return jsonify({'status': 'processing'})
    else:
        app.logger.error(f"File not found: {filename}")
        return jsonify({'status': 'error', 'error': 'File not found'})

@app.route('/processing/<filename>')
def processing(filename):
    return render_template('processing.html', filename=filename)

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
