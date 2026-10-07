import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

OUTPUT_DIR = "generated_certificates"

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def generate_certificate(recipient_name: str, output_filename: str) -> str:
    """
    Generates a PDF certificate for the recipient.
    Returns the file path.
    """
    setup_directories()
    file_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Intentional error simulation for testing if name is exactly "Error User"
    if recipient_name == "Error User":
        raise ValueError("Simulated error for this recipient")

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    
    # Draw border
    c.setLineWidth(5)
    c.rect(20, 20, width - 40, height - 40)
    
    # Draw Title
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2.0, height - 200, "Certificate of Achievement")
    
    # Draw text
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2.0, height - 300, "This is to certify that")
    
    # Draw Name
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height - 350, recipient_name)
    
    # Draw Subtext
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2.0, height - 400, "has successfully completed the program.")
    
    c.save()
    
    return file_path
