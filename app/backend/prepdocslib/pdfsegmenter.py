import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
import tkinter as tk
from tkinter import filedialog
import re
import logging

# Set up logging to display information messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pdf(input_path: Path, output_dir: Path):
    """
    Processes a single PDF file:
    - If the PDF has fewer than 25 pages, it copies the file to the output directory unchanged.
    - If the PDF has 25 pages or more, it splits the PDF into segments:
        - The first segment contains the first 5 pages.
        - Subsequent segments contain overlapping pages, each segment starting 5 pages ahead,
          with an overlap of 1 page.
    """
    # Create a PdfReader object to read the PDF file
    reader = PdfReader(str(input_path))
    # Get the base name of the PDF file without extension
    base_name = input_path.stem
    # Get the total number of pages in the PDF
    total_pages = len(reader.pages)
    
    if total_pages < 25:
        # If the PDF has fewer than 25 pages, copy it directly to the output directory
        output_path = output_dir / input_path.name
        with open(input_path, 'rb') as src, open(output_path, 'wb') as dst:
            dst.write(src.read())
        logger.info(f"Copied {input_path.name} (under 25 pages)")
        return

    # Process the first segment (first 5 pages)
    logger.info("Processing first segment")
    writer = PdfWriter()
    for i in range(5):
        # Add each of the first 5 pages to the writer
        writer.add_page(reader.pages[i])
    
    # Define the output path for the first segment
    output_path = output_dir / f"{base_name}_intro_to_page1.pdf"
    # Write the first segment to a new PDF file
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    # Initialize segment numbering
    segment_num = 1
    # Start processing from the 5th page (index 4) in steps of 5 pages
    for start in range(4, total_pages - 1, 5):
        logger.info(f"Processing segment {segment_num}")
        writer = PdfWriter()
        # Calculate the end index, ensuring it doesn't exceed the total pages
        end = min(start + 6, total_pages)
        
        for i in range(start, end):
            # Add pages to the writer for the current segment
            writer.add_page(reader.pages[i])
        
        # Define the output path for the current segment with appropriate page numbers
        output_path = output_dir / f"{base_name}_page{start-3}_to_page{end-4}.pdf"
        # Write the current segment to a new PDF file
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        # Increment the segment number
        segment_num += 1

def process_directory():
    """
    Processes all PDF files within a selected directory:
    - Prompts the user to select a directory containing PDFs.
    - Creates an output directory named "<original_directory>_parsed".
    - Processes each PDF file found in the directory.
    """
    # Prompt the user to select a folder
    input_dir = select_folder()
    if not input_dir:
        logger.info("No folder selected. Exiting.")
        return
        
    # Convert the input directory to a Path object
    input_path = Path(input_dir)
    # Define the output directory path
    output_dir = input_path.parent / f"{input_path.name}_parsed"
    # Create the output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Recursively find all PDF files in the input directory
    pdf_files = list(input_path.rglob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Process each PDF file found
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing {pdf_file.name}")
            process_pdf(pdf_file, output_dir)
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")

def select_folder():
    """
    Opens a dialog window for the user to select a directory.
    Returns the selected directory path as a string.
    """
    # Initialize Tkinter root window
    root = tk.Tk()
    # Hide the root window
    root.withdraw()
    # Open a directory selection dialog
    return filedialog.askdirectory(title="Select Folder with PDFs")

if __name__ == "__main__":
    # Entry point of the script
    process_directory()
