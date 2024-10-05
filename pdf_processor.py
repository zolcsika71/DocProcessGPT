import PyPDF2
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.
    
    :param file_path: Path to the PDF file
    :return: Extracted text as a string
    """
    logger.info(f"Starting text extraction from PDF: {file_path}")
    text = ""
    try:
        with open(file_path, 'rb') as file:
            logger.info("PDF file opened successfully")
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                logger.info(f"Extracting text from page {page_num}/{num_pages}")
                page_text = page.extract_text()
                text += page_text
                logger.info(f"Extracted {len(page_text)} characters from page {page_num}")
            
            logger.info(f"Text extraction complete. Total characters extracted: {len(text)}")
    except Exception as e:
        logger.error(f"Error during text extraction: {str(e)}")
        raise
    
    return text
