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

# Global dictionary to store processing status
processing_status = {}

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
        
        # Initialize processing status
        processing_status[filename] = {'status': 'processing', 'details': 'Starting PDF processing...'}
        
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
        
        # File reading
        try:
            with open(filepath, 'rb') as file:
                app.logger.info(f"File opened successfully: {filepath}")
        except IOError as e:
            error_msg = f"Error opening file: {str(e)}"
            app.logger.error(error_msg)
            processing_status[filename] = {'status': 'error', 'details': error_msg}
            return
        
        # Text extraction
        processing_status[filename]['details'] = 'Extracting text from PDF...'
        start_time = time.time()
        app.logger.info("Extracting text from PDF")
        try:
            raw_text = extract_text_from_pdf(filepath)
            extraction_time = time.time() - start_time
            app.logger.info(f"Text extracted from PDF, length: {len(raw_text)}, time taken: {extraction_time:.2f} seconds")
            processing_status[filename]['details'] = f'Text extracted, length: {len(raw_text)} characters'
        except Exception as e:
            error_msg = f"Error extracting text from PDF: {str(e)}"
            app.logger.error(error_msg)
            processing_status[filename] = {'status': 'error', 'details': error_msg}
            return
        
        # Text preprocessing
        processing_status[filename]['details'] = 'Preprocessing extracted text...'
        start_time = time.time()
        app.logger.info("Preprocessing extracted text")
        try:
            processed_text = preprocess_text(raw_text)
            preprocessing_time = time.time() - start_time
            app.logger.info(f"Text preprocessed, length: {len(processed_text)}, time taken: {preprocessing_time:.2f} seconds")
            processing_status[filename]['details'] = f'Text preprocessed, length: {len(processed_text)} characters'
        except Exception as e:
            error_msg = f"Error preprocessing text: {str(e)}"
            app.logger.error(error_msg)
            processing_status[filename] = {'status': 'error', 'details': error_msg}
            return
        
        # Saving processed text
        processed_filename = f"processed_{filename}.txt"
        processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        app.logger.info(f"Saving processed text to: {processed_filepath}")
        processing_status[filename]['details'] = 'Saving processed text...'
        start_time = time.time()
        try:
            with open(processed_filepath, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            saving_time = time.time() - start_time
            app.logger.info(f"Processed text saved successfully: {processed_filepath}, time taken: {saving_time:.2f} seconds")
        except IOError as e:
            error_msg = f"Error saving processed text: {str(e)}"
            app.logger.error(error_msg)
            processing_status[filename] = {'status': 'error', 'details': error_msg}
            return
        
        total_time = extraction_time + preprocessing_time + saving_time
        app.logger.info(f"Total processing time: {total_time:.2f} seconds")
        
        processing_status[filename] = {'status': 'complete', 'filename': processed_filename, 'details': f'Processing completed in {total_time:.2f} seconds'}
    except Exception as e:
        error_msg = f"Unexpected error processing PDF {filename}: {str(e)}"
        app.logger.error(error_msg)
        processing_status[filename] = {'status': 'error', 'details': error_msg}

@app.route('/process_status/<filename>', methods=['GET'])
def process_status(filename):
    app.logger.info(f"Checking process status for: {filename}")
    
    if filename in processing_status:
        return jsonify(processing_status[filename])
    else:
        return jsonify({'status': 'error', 'details': 'File not found or processing not started'})

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
