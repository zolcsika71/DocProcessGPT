from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "This is a test PDF file.")
    c.drawString(100, 730, "It contains some sample text for processing.")
    c.drawString(100, 710, "The PDF processor should extract this text.")
    c.save()

if __name__ == "__main__":
    create_test_pdf("test.pdf")
    print("Test PDF created: test.pdf")
