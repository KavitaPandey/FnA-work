import os
import base64
import tempfile
from PIL import Image
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            
            # Extract text directly from PDF
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    text += page_text + "\n\n"
                else:
                    text += f"[Image-based content on page {page_num+1} - text extraction not available]\n\n"
            
            return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")

def convert_image_to_base64(image_path):
    """
    Convert an image file to base64 encoding for use with OpenAI API.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to convert image to base64: {e}")

def save_uploaded_file(uploaded_file):
    """
    Save an uploaded file to a temporary location.
    
    Args:
        uploaded_file: File uploaded through Streamlit
        
    Returns:
        Path to the saved temporary file
    """
    try:
        # Create a temporary file with the appropriate extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            return temp_file.name
    except Exception as e:
        raise Exception(f"Failed to save uploaded file: {e}")

def read_text_file(file_path):
    """
    Read a text file and return its contents.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Contents of the text file as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try another encoding if utf-8 fails
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Failed to read text file: {e}")

def process_file(file_path, file_type):
    """
    Process a file based on its type and extract text.
    
    Args:
        file_path: Path to the file
        file_type: MIME type of the file
        
    Returns:
        Extracted text content as a string
    """
    try:
        if "pdf" in file_type:
            return extract_text_from_pdf(file_path)
        elif "text" in file_type:
            return read_text_file(file_path)
        else:
            # For image files, we'll return the path for later processing
            return file_path
    except Exception as e:
        raise Exception(f"Failed to process file: {e}")