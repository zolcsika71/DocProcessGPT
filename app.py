import os
import logging
from logging import Formatter
import threading
import mimetypes
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, abort, send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from pdf_processor import extract_text_from_pdf
from text_preprocessor import preprocess_text
import nltk

app = Flask(__name__)

# Set up file-based logging
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

def delete_old_logs():
    log_files = [f for f in os.listdir(log_directory) if f.startswith('app_') and f.endswith('.log')]
    if len(log_files) > 1:
        log_files.sort(key=lambda x: os.path.getctime(os.path.join(log_directory, x)), reverse=True)
        for old_file in log_files[1:]:
            os.remove(os.path.join(log_directory, old_file))

# Call delete_old_logs before creating a new log file
delete_old_logs()

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_directory, f'app_{current_time}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]', '%Y-%m-%d %H:%M:%S'))
file_handler.formatter.converter = time.gmtime
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global dictionary to store processing status
processing_status = {}

# Timeout for PDF processing (in seconds)
PROCESSING_TIMEOUT = 300  # 5 minutes

def download_nltk_resources():
    app.logger.info("Downloading NLTK resources")
    resources = ['punkt', 'stopwords', 'punkt_tab']
    for resource in resources:
        app.logger.info(f"Downloading NLTK resource: {resource}")
        nltk.download(resource, quiet=True)
    app.logger.info("NLTK resources downloaded successfully")

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
        
        app.logger.info(f"File uploaded successfully: {filepath}")
        
        # Initialize processing status
        processing_status[filename] = {'status': 'processing', 'progress': 0, 'details': 'Starting PDF processing...'}
        
        # Start processing in a background thread
        threading.Thread(target=process_pdf, args=(filepath, filename)).start()
        
        return render_template('processing.html', filename=filename)
    except Exception as e:
        app.logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({'error': str(e)}), 500

def update_progress(filename, progress, details):
    processing_status[filename]['progress'] = progress
    processing_status[filename]['details'] = details
    app.logger.info(f"Processing progress for {filename}: {progress}% - {details}")

def process_pdf(filepath, filename):
    with app.app_context():
        def timeout_handler():
            app.logger.error(f"PDF processing timed out after {PROCESSING_TIMEOUT} seconds for {filename}")
            processing_status[filename] = {'status': 'error', 'progress': 100, 'details': f'PDF processing timed out after {PROCESSING_TIMEOUT} seconds'}

        timer = threading.Timer(PROCESSING_TIMEOUT, timeout_handler)
        timer.start()

        try:
            app.logger.info(f"Starting PDF processing for {filename}")
            file_size = os.path.getsize(filepath)
            app.logger.info(f"File size: {file_size} bytes")
            
            # NLTK resource loading
            update_progress(filename, 5, 'Loading NLTK resources...')
            start_time = time.perf_counter()
            download_nltk_resources()
            nltk_loading_time = time.perf_counter() - start_time
            update_progress(filename, 10, f'NLTK resources loaded in {nltk_loading_time:.3f} seconds')
            
            # File reading
            update_progress(filename, 15, 'Reading PDF file...')
            try:
                with open(filepath, 'rb') as file:
                    app.logger.info(f"File opened successfully: {filepath}")
            except IOError as e:
                error_msg = f"Error opening file: {str(e)}"
                app.logger.error(error_msg)
                processing_status[filename] = {'status': 'error', 'progress': 100, 'details': error_msg}
                return
            
            # Text extraction
            update_progress(filename, 20, 'Extracting text from PDF...')
            start_time = time.perf_counter()
            app.logger.info("Extracting text from PDF")
            try:
                raw_text = extract_text_from_pdf(filepath, lambda progress: update_progress(filename, 20 + int(progress * 0.3), f'Extracting text: {progress:.1f}% complete'), current_app)
                extraction_time = time.perf_counter() - start_time
                app.logger.info(f"Text extracted from PDF, length: {len(raw_text)}, time taken: {extraction_time:.3f} seconds")
                update_progress(filename, 50, f'Text extracted, length: {len(raw_text)} characters, time: {extraction_time:.3f}s')
            except Exception as e:
                error_msg = f"Error extracting text from PDF: {str(e)}"
                app.logger.error(error_msg)
                processing_status[filename] = {'status': 'error', 'progress': 100, 'details': error_msg}
                return
            
            # Text preprocessing
            update_progress(filename, 60, 'Preprocessing extracted text...')
            start_time = time.perf_counter()
            app.logger.info("Preprocessing extracted text")
            try:
                processed_text = preprocess_text(raw_text, lambda progress: update_progress(filename, 60 + int(progress * 0.3), f'Preprocessing text: {progress:.1f}% complete'))
                preprocessing_time = time.perf_counter() - start_time
                app.logger.info(f"Text preprocessed, length: {len(processed_text)}, time taken: {preprocessing_time:.3f} seconds")
                update_progress(filename, 90, f'Text preprocessed, length: {len(processed_text)} characters, time: {preprocessing_time:.3f}s')
            except Exception as e:
                error_msg = f"Error preprocessing text: {str(e)}"
                app.logger.error(error_msg)
                processing_status[filename] = {'status': 'error', 'progress': 100, 'details': error_msg}
                return
            
            # Saving processed text
            update_progress(filename, 95, 'Saving processed text...')
            processed_filename = f"processed_{filename}.txt"
            processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            app.logger.info(f"Saving processed text to: {processed_filepath}")
            start_time = time.perf_counter()
            try:
                with open(processed_filepath, 'w', encoding='utf-8') as f:
                    f.write(processed_text)
                saving_time = time.perf_counter() - start_time
                app.logger.info(f"Processed text saved successfully: {processed_filepath}, time taken: {saving_time:.3f} seconds")
            except IOError as e:
                error_msg = f"Error saving processed text: {str(e)}"
                app.logger.error(error_msg)
                processing_status[filename] = {'status': 'error', 'progress': 100, 'details': error_msg}
                return
            
            total_time = nltk_loading_time + extraction_time + preprocessing_time + saving_time
            app.logger.info(f"Total processing time: {total_time:.3f} seconds")
            
            processing_status[filename] = {
                'status': 'complete',
                'progress': 100,
                'filename': processed_filename,
                'details': f'Processing completed in {total_time:.3f} seconds',
                'file_size': file_size,
                'extracted_length': len(raw_text),
                'processed_length': len(processed_text),
                'extraction_time': extraction_time,
                'preprocessing_time': preprocessing_time,
                'saving_time': saving_time,
                'nltk_loading_time': nltk_loading_time,
                'total_time': total_time,
                'file_path': filepath,
                'processed_file_path': processed_filepath
            }
        except Exception as e:
            error_msg = f"Unexpected error processing PDF {filename}: {str(e)}"
            app.logger.error(error_msg)
            processing_status[filename] = {'status': 'error', 'progress': 100, 'details': error_msg}
        finally:
            timer.cancel()

@app.route('/process_status/<filename>', methods=['GET'])
def process_status(filename):
    app.logger.info(f"Checking process status for: {filename}")
    
    if filename in processing_status:
        return jsonify(processing_status[filename])
    else:
        return jsonify({'status': 'error', 'progress': 100, 'details': 'File not found or processing not started'})

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

@app.route('/view_logs')
def view_logs():
    try:
        log_files = [f for f in os.listdir(log_directory) if f.startswith('app_') and f.endswith('.log')]
        if not log_files:
            return 'No log files found'
        latest_log_file = max(log_files, key=lambda x: os.path.getctime(os.path.join(log_directory, x)))
        with open(os.path.join(log_directory, latest_log_file), 'r') as log_file:
            logs = log_file.read()
        return render_template('view_logs.html', logs=logs)
    except Exception as e:
        return f'Error reading log file: {str(e)}'

@app.route('/latest_logs')
def latest_logs():
    try:
        log_files = [f for f in os.listdir(log_directory) if f.startswith('app_') and f.endswith('.log')]
        if not log_files:
            return jsonify({'logs': ['No log files found']})
        latest_log_file = max(log_files, key=lambda x: os.path.getctime(os.path.join(log_directory, x)))
        with open(os.path.join(log_directory, latest_log_file), 'r') as log_file:
            logs = log_file.readlines()[-50:]  # Get the last 50 lines
        return jsonify({'logs': logs})
    except Exception as e:
        app.logger.error(f"Error fetching latest logs: {str(e)}")
        return jsonify({'error': 'Error fetching latest logs'}), 500

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return jsonify(error=str(e)), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error="An unexpected error occurred"), 500

if __name__ == '__main__':
    download_nltk_resources()
    app.run(host='0.0.0.0', port=5000, debug=True)
