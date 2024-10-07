# app.py
import os
import mimetypes
import threading
import time
import nltk
from flask import (
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
    Flask,
)
from werkzeug.utils import secure_filename
from pdf_processor import extract_text_from_pdf
from text_preprocessor import preprocess_text
from logging_config import logger
from config import (
    FILE_TO_PROCESS_FOLDER,
    PROCESSED_FILE_FOLDER,
    MAX_CONTENT_LENGTH,
    PROCESSING_TIMEOUT,
)
from text_preprocessor import download_nltk_resources



app = Flask(__name__)

logger.info("Starting PDF processing server")
logger.info(f"FILE_TO_PROCESS_FOLDER: {FILE_TO_PROCESS_FOLDER}")
logger.info(f"PROCESSED_FILE_FOLDER: {PROCESSED_FILE_FOLDER}")
logger.info(f"MAX_CONTENT_LENGTH: {MAX_CONTENT_LENGTH}")
logger.info(f"PROCESSING_TIMEOUT: {PROCESSING_TIMEOUT}")

app.config["FILE_TO_PROCESS_FOLDER"] = FILE_TO_PROCESS_FOLDER
app.config["PROCESSED_FILE_FOLDER"] = PROCESSED_FILE_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["PROCESSING_TIMEOUT"] = PROCESSING_TIMEOUT


def calculate_processing_time(start_time):
    """Calculate the elapsed time since start_time."""
    return time.perf_counter() - start_time


# Global dictionary to store processing status
processing_status = {}


@app.route("/", methods=["GET"])
def index():
    """Render the index page for file upload."""
    try:
        logger.info("Rendering index page")
        return render_template("upload.html")
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files."""
    return send_from_directory("static", filename)


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and initiate processing."""
    try:
        if "file" not in request.files:
            logger.error("No file part in the request")
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            logger.error("No selected file")
            return jsonify({"error": "No selected file"}), 400

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type != "application/pdf":
            logger.error(f"Invalid file type: {mime_type}")
            return (
                jsonify({"error": "Invalid file type. Please upload a PDF file."}),
                400,
            )

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["RAW_FILE_FOLDER"], filename)
        file.save(filepath)
        logger.info(f"File uploaded successfully: {filepath}")

        # Initialize processing status
        processing_status[filename] = {
            "status": "processing",
            "progress": 0,
            "details": "Starting PDF processing...",
        }

        # Start processing in a background thread
        threading.Thread(target=process_pdf, args=(filepath, filename)).start()
        return render_template("processing.html", filename=filename)
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({"error": str(e)}), 500


def update_progress(filename, progress, details):
    """Update the processing progress of a file."""
    processing_status[filename]["progress"] = progress
    processing_status[filename]["details"] = details
    logger.info(f"Processing progress for {filename}: {progress}% - {details}")


def process_pdf(filepath, filename):
    """Process the uploaded PDF file."""
    with app.app_context():

        def timeout_handler():
            logger.error(
                f"PDF processing timed out after {PROCESSING_TIMEOUT} seconds for {filename}"
            )
            processing_status[filename] = {
                "status": "error",
                "progress": 100,
                "details": f"PDF processing timed out after {PROCESSING_TIMEOUT} seconds",
            }

        timer = threading.Timer(PROCESSING_TIMEOUT, timeout_handler)
        timer.start()
        try:
            logger.info(f"Starting PDF processing for {filename}")
            file_size = os.path.getsize(filepath)
            logger.info(f"File size: {file_size} bytes")

            # NLTK resource loading
            update_progress(filename, 5, "Loading NLTK resources...")
            start_time = time.perf_counter()
            download_nltk_resources()
            nltk_loading_time = calculate_processing_time(start_time)
            update_progress(
                filename,
                10,
                f"NLTK resources loaded in {nltk_loading_time:.3f} seconds",
            )

            # File reading
            update_progress(filename, 15, "Reading PDF file...")
            try:
                with open(filepath, "rb") as file:
                    logger.info(f"File opened successfully: {filepath}")
            except IOError as e:
                error_msg = f"Error opening file: {str(e)}"
                logger.error(error_msg)
                processing_status[filename] = {
                    "status": "error",
                    "progress": 100,
                    "details": error_msg,
                }
                return

            # Text extraction
            update_progress(filename, 20, "Extracting text from PDF...")
            start_time = time.perf_counter()
            logger.info("Extracting text from PDF")
            try:
                raw_text = extract_text_from_pdf(
                    filepath,
                    lambda progress: update_progress(
                        filename,
                        20 + int(progress * 0.3),
                        f"Extracting text: {progress:.1f}% complete",
                    ),
                    current_app,
                )
                extraction_time = calculate_processing_time(start_time)
                logger.info(
                    f"Text extracted from PDF, length: {len(raw_text)}, time taken: {extraction_time:.3f} seconds"
                )
                update_progress(
                    filename,
                    50,
                    f"Text extracted, length: {len(raw_text)} characters, time: {extraction_time:.3f}s",
                )
            except Exception as e:
                error_msg = f"Error extracting text from PDF: {str(e)}"
                logger.error(error_msg)
                processing_status[filename] = {
                    "status": "error",
                    "progress": 100,
                    "details": error_msg,
                }
                return

            # Text preprocessing
            update_progress(filename, 60, "Preprocessing extracted text...")
            start_time = time.perf_counter()
            logger.info("Preprocessing extracted text")
            try:
                processed_text = preprocess_text(
                    raw_text,
                    lambda progress: update_progress(
                        filename,
                        60 + int(progress * 0.3),
                        f"Preprocessing text: {progress:.1f}% complete",
                    ),
                )
                preprocessing_time = calculate_processing_time(start_time)
                logger.info(
                    f"Text preprocessed, length: {len(processed_text)}, time taken: {preprocessing_time:.3f} seconds"
                )
                update_progress(
                    filename,
                    90,
                    f"Text preprocessed, length: {len(processed_text)} characters, time: {preprocessing_time:.3f}s",
                )
            except Exception as e:
                error_msg = f"Error preprocessing text: {str(e)}"
                logger.error(error_msg)
                processing_status[filename] = {
                    "status": "error",
                    "progress": 100,
                    "details": error_msg,
                }
                return

            # Saving processed text
            update_progress(filename, 95, "Saving processed text...")
            processed_filename = f"processed_{filename}.txt"
            processed_filepath = os.path.join(
                app.config["UPLOAD_FOLDER"], processed_filename
            )
            logger.info(f"Saving processed text to: {processed_filepath}")
            start_time = time.perf_counter()
            try:
                with open(processed_filepath, "w", encoding="utf-8") as f:
                    f.write(processed_text)
                saving_time = calculate_processing_time(start_time)
                logger.info(
                    f"Processed text saved successfully: {processed_filepath}, time taken: {saving_time:.3f} seconds"
                )
            except IOError as e:
                error_msg = f"Error saving processed text: {str(e)}"
                logger.error(error_msg)
                processing_status[filename] = {
                    "status": "error",
                    "progress": 100,
                    "details": error_msg,
                }
                return

            total_time = (
                nltk_loading_time + extraction_time + preprocessing_time + saving_time
            )
            logger.info(f"Total processing time: {total_time:.3f} seconds")
            processing_status[filename] = {
                "status": "complete",
                "progress": 100,
                "filename": processed_filename,
                "details": f"Processing completed in {total_time:.3f} seconds",
                "file_size": file_size,
                "extracted_length": len(raw_text),
                "processed_length": len(processed_text),
                "extraction_time": extraction_time,
                "preprocessing_time": preprocessing_time,
                "saving_time": saving_time,
                "nltk_loading_time": nltk_loading_time,
                "total_time": total_time,
                "file_path": filepath,
                "processed_file_path": processed_filepath,
            }
        except Exception as e:
            error_msg = f"Unexpected error processing PDF {filename}: {str(e)}"
            logger.error(error_msg)
            processing_status[filename] = {
                "status": "error",
                "progress": 100,
                "details": error_msg,
            }
        finally:
            timer.cancel()


@app.route("/process_status/<filename>", methods=["GET"])
def process_status(filename):
    """Check the processing status of a file."""
    logger.info(f"Checking process status for: {filename}")
    if filename in processing_status:
        return jsonify(processing_status[filename])
    else:
        return jsonify(
            {
                "status": "error",
                "progress": 100,
                "details": "File not found or processing not started",
            }
        )


@app.route("/processing/<filename>")
def processing(filename):
    """Render the processing page for a specific file."""
    return render_template("processing.html", filename=filename)


@app.route("/processed/<path:filename>", methods=["GET"])
def get_processed_text(filename: str):
    """Download the processed text file."""

    # Path sanitization to prevent directory traversal
    if isinstance(filename, bytes):
        filename = filename.decode("utf-8")  # Convert bytes to string if necessary

    sanitized_filename = os.path.basename(filename)
    folder = app.config["FILE_PROCESSED_FOLDER"]

    if not isinstance(folder, (str, bytes)):
        raise TypeError(
            "Configuration FILE_PROCESSED_FOLDER must be of type str or bytes"
        )

    filepath = os.path.join(folder, sanitized_filename)

    try:
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(500)
def internal_server_error(e):
    """Handle internal server errors."""
    logger.error(f"500 error: {str(e)}")
    return jsonify(error=str(e)), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error="An unexpected error occurred"), 500


if __name__ == "__main__":
    download_nltk_resources()
    app.run(host="0.0.0.0", port=5001, debug=True)
