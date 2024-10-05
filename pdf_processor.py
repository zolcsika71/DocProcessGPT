import PyPDF2
from flask import current_app

def extract_text_from_pdf(file_path, progress_callback=None):
    """
    Extract text from a PDF file with page-by-page progress updates.
    
    :param file_path: Path to the PDF file
    :param progress_callback: Function to call with progress updates
    :return: Extracted text as a string
    """
    current_app.logger.info(f"Starting text extraction from PDF: {file_path}")
    text = ""
    try:
        with open(file_path, 'rb') as file:
            current_app.logger.info("PDF file opened successfully")
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            current_app.logger.info(f"PDF has {num_pages} pages")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                current_app.logger.info(f"Extracting text from page {page_num}/{num_pages}")
                try:
                    page_text = page.extract_text()
                    text += page_text
                    current_app.logger.info(f"Extracted {len(page_text)} characters from page {page_num}")
                    
                    if progress_callback:
                        progress = (page_num / num_pages) * 100
                        progress_callback(progress)
                except Exception as e:
                    current_app.logger.error(f"Error extracting text from page {page_num}: {str(e)}")
                    # Continue with the next page
            
            current_app.logger.info(f"Text extraction complete. Total characters extracted: {len(text)}")
    except Exception as e:
        current_app.logger.error(f"Error during text extraction: {str(e)}")
        raise
    
    return text
