# Import the required libraries
import fitz  # PyMuPDF library for handling PDF files
import pytesseract  # Python wrapper for Tesseract OCR
import io  # For handling binary data streams
import os  # For handling file paths
import re


def extract_chunks_from_pdf(directory):
    """Extract text from PDFs and treat each PDF as a chunk."""
    
    chunks = []
    pdf_files = []  # Initialize a list to store all PDF files
    file_names = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Select PDF files only
            if file.lower().endswith(".pdf"):
                # Append the full file path to the list
                file_names.append(file[:-4])
                pdf_files.append(os.path.join(root, file))
    
    for file_path in pdf_files:
        doc = fitz.open(file_path)
        text = ""  # Initialize a variable to store the text content of the current PDF file
        # Traverse each page in the PDF file
        for page_num in range(len(doc)):
            count = 0
            tem_text = []
            # Load the Page object of the current page
            page = doc.load_page(page_num)

            text = page.get_text()
            text = text.replace("www.psands.com", "")
            print(text)
            lines = text.split('\n')

            for line in lines:
                if len(line) < 3:
                    continue
                tokens = re.findall(r'\b\w+\b|[^\w\s]', line)
                if count == 20:
                    tem_text = tem_text[0:-20]
                if len(tokens) < 5 and count >= 20:
                    count += 1
                    continue
                if len(tokens) < 5:
                    count += 1
                else:
                    count = 0
                tem_text.append(line)
            
            text = "\n".join(tem_text)
            chunks.append(text)

    return chunks, file_names  # Return the full text content and file names