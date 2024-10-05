import PyPDF2

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.
    
    :param file_path: Path to the PDF file
    :return: Extracted text as a string
    """
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text
