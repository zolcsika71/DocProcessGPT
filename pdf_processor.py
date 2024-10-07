import PyPDF2
from logging_config import logger


def extract_text_from_pdf(file_path, progress_callback=None, flask_app=None):
    """
    Extract text from a PDF file with page-by-page progress updates and error handling.
    :param file_path: Path to the PDF file
    :param progress_callback: Function to call with progress updates
    :param flask_app: Flask application instance for logging
    :return: Extracted text as a string
    """

    logger.info(f"Starting text extraction from PDF: {file_path}")
    text_parts = []
    try:
        with open(file_path, "rb") as file:
            logger.info("PDF file opened successfully")
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            for page_num, page in enumerate(pdf_reader.pages, 1):
                logger.info(f"Extracting text from page {page_num}/{num_pages}")
                try:
                    if page_text := page.extract_text():
                        text_parts.append(page_text)
                        logger.info(
                            f"Extracted {len(page_text)} characters from page {page_num}"
                        )
                    if progress_callback:
                        try:
                            progress = (page_num / num_pages) * 100
                            progress_callback(progress)
                        except Exception as progress_callback_error:
                            logger.error(
                                f"Error in progress_callback: {str(progress_callback_error)}"
                            )
                    # Add more granular progress updates
                    if page_num % 5 == 0 or page_num == num_pages:
                        logger.info(
                            f"Extraction progress: {progress:.2f}% ({page_num}/{num_pages} pages)"
                        )
                except Exception as e:
                    logger.error(
                        f"Error extracting text from page {page_num}: {str(e)}"
                    )
                    # Continue with the next page, but log the error
                    logger.warning(f"Skipping page {page_num} due to extraction error")
            full_text = "".join(text_parts)
            logger.info(
                f"Text extraction complete. Total characters extracted: {len(full_text)}"
            )
    except Exception as e:
        logger.error(f"Error during text extraction: {str(e)}")
        raise
    return full_text
