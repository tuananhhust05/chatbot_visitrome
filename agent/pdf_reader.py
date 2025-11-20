#!/usr/bin/env python3
"""
PDF Reader Script
A comprehensive Python script for reading and extracting content from PDF files.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.errors import PdfReadError
except ImportError:
    print("Error: pypdf is not installed. Please install it using:")
    print("pip install pypdf")
    sys.exit(1)


class PDFReader:
    """A comprehensive PDF reader class with various extraction methods."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF reader.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.reader = None
        self._load_pdf()
    
    def _load_pdf(self):
        """Load the PDF file."""
        try:
            if not self.pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
            
            self.reader = PdfReader(self.pdf_path)
            print(f"✓ Successfully loaded PDF: {self.pdf_path.name}")
            print(f"  Pages: {len(self.reader.pages)}")
            
        except PdfReadError as e:
            print(f"Error reading PDF: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
    
    def get_metadata(self) -> Dict:
        """
        Extract metadata from the PDF.
        
        Returns:
            Dict: PDF metadata
        """
        metadata = {}
        if self.reader.metadata:
            for key, value in self.reader.metadata.items():
                if value:
                    # Remove the leading '/' from metadata keys
                    clean_key = key.replace('/', '') if key.startswith('/') else key
                    metadata[clean_key] = str(value)
        
        return metadata
    
    def extract_text(self, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """
        Extract text from the PDF.
        
        Args:
            start_page (int): Starting page number (0-indexed)
            end_page (int, optional): Ending page number (0-indexed). If None, reads to end.
            
        Returns:
            str: Extracted text
        """
        if end_page is None:
            end_page = len(self.reader.pages)
        
        text_parts = []
        for page_num in range(start_page, min(end_page, len(self.reader.pages))):
            try:
                page = self.reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}\n")
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
        
        return "\n".join(text_parts)
    
    def extract_text_by_page(self) -> List[Tuple[int, str]]:
        """
        Extract text page by page.
        
        Returns:
            List[Tuple[int, str]]: List of (page_number, text) tuples
        """
        pages_text = []
        for page_num, page in enumerate(self.reader.pages):
            try:
                text = page.extract_text()
                pages_text.append((page_num + 1, text))
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                pages_text.append((page_num + 1, ""))
        
        return pages_text
    
    def get_page_count(self) -> int:
        """Get the total number of pages."""
        return len(self.reader.pages)
    
    def extract_images_info(self) -> List[Dict]:
        """
        Get information about images in the PDF.
        
        Returns:
            List[Dict]: List of image information dictionaries
        """
        images_info = []
        
        for page_num, page in enumerate(self.reader.pages):
            try:
                if "/XObject" in page["/Resources"]:
                    xObject = page["/Resources"]["/XObject"].get_object()
                    
                    for obj in xObject:
                        if xObject[obj]["/Subtype"] == "/Image":
                            image_info = {
                                "page": page_num + 1,
                                "object_name": obj,
                                "width": xObject[obj]["/Width"],
                                "height": xObject[obj]["/Height"],
                                "color_space": xObject[obj].get("/ColorSpace", "Unknown"),
                                "bits_per_component": xObject[obj].get("/BitsPerComponent", "Unknown")
                            }
                            images_info.append(image_info)
            except Exception as e:
                print(f"Warning: Could not extract image info from page {page_num + 1}: {e}")
        
        return images_info
    
    def save_text_to_file(self, output_path: str, start_page: int = 0, end_page: Optional[int] = None):
        """
        Save extracted text to a file.
        
        Args:
            output_path (str): Path to save the text file
            start_page (int): Starting page number (0-indexed)
            end_page (int, optional): Ending page number (0-indexed)
        """
        text = self.extract_text(start_page, end_page)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"PDF Text Extraction\n")
                f.write(f"Source: {self.pdf_path.name}\n")
                f.write(f"Pages: {start_page + 1} to {end_page if end_page else len(self.reader.pages)}\n")
                f.write("=" * 50 + "\n\n")
                f.write(text)
            
            print(f"✓ Text saved to: {output_path}")
            
        except Exception as e:
            print(f"Error saving text to file: {e}")


def main():
    """Main function to handle command line arguments and execute PDF reading."""
    parser = argparse.ArgumentParser(
        description="PDF Reader - Extract text and metadata from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_reader.py document.pdf                    # Extract all text
  python pdf_reader.py document.pdf --metadata        # Show metadata only
  python pdf_reader.py document.pdf --pages 1-5       # Extract text from pages 1-5
  python pdf_reader.py document.pdf --output text.txt # Save to file
  python pdf_reader.py document.pdf --images          # Show image information
        """
    )
    
    parser.add_argument("pdf_file", help="Path to the PDF file")
    parser.add_argument("--metadata", action="store_true", help="Show PDF metadata")
    parser.add_argument("--pages", help="Page range (e.g., '1-5' or '1,3,5')")
    parser.add_argument("--output", help="Output file to save extracted text")
    parser.add_argument("--images", action="store_true", help="Show image information")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_file):
        print(f"Error: File '{args.pdf_file}' not found.")
        sys.exit(1)
    
    # Initialize PDF reader
    pdf_reader = PDFReader(args.pdf_file)
    
    # Show basic information
    print(f"\n📄 PDF Information:")
    print(f"   File: {pdf_reader.pdf_path.name}")
    print(f"   Size: {pdf_reader.pdf_path.stat().st_size / 1024:.1f} KB")
    print(f"   Pages: {pdf_reader.get_page_count()}")
    
    # Show metadata if requested
    if args.metadata:
        print(f"\n📋 Metadata:")
        metadata = pdf_reader.get_metadata()
        if metadata:
            for key, value in metadata.items():
                print(f"   {key}: {value}")
        else:
            print("   No metadata found")
    
    # Show image information if requested
    if args.images:
        print(f"\n🖼️  Image Information:")
        images_info = pdf_reader.extract_images_info()
        if images_info:
            for img in images_info:
                print(f"   Page {img['page']}: {img['width']}x{img['height']} "
                      f"({img['color_space']}, {img['bits_per_component']} bits)")
        else:
            print("   No images found")
    
    # Extract text based on page range
    if args.pages:
        try:
            if '-' in args.pages:
                # Range format: "1-5"
                start, end = map(int, args.pages.split('-'))
                start_page = start - 1  # Convert to 0-indexed
                end_page = end
                text = pdf_reader.extract_text(start_page, end_page)
                print(f"\n📝 Text from pages {start}-{end}:")
            else:
                # Specific pages format: "1,3,5"
                page_numbers = [int(p) - 1 for p in args.pages.split(',')]  # Convert to 0-indexed
                text_parts = []
                for page_num in page_numbers:
                    if 0 <= page_num < pdf_reader.get_page_count():
                        page_text = pdf_reader.extract_text(page_num, page_num + 1)
                        text_parts.append(page_text)
                text = "\n".join(text_parts)
                print(f"\n📝 Text from pages {args.pages}:")
        except ValueError:
            print("Error: Invalid page range format. Use '1-5' or '1,3,5'")
            sys.exit(1)
    else:
        # Extract all text
        text = pdf_reader.extract_text()
        print(f"\n📝 Full text extraction:")
    
    # Display or save text
    if args.output:
        pdf_reader.save_text_to_file(args.output)
    else:
        if text.strip():
            print(text)
        else:
            print("No text content found in the PDF.")
    
    # Show detailed information if verbose
    if args.verbose:
        print(f"\n🔍 Detailed Information:")
        print(f"   PDF Version: {pdf_reader.reader.pdf_header}")
        print(f"   Is Encrypted: {pdf_reader.reader.is_encrypted}")
        if pdf_reader.reader.is_encrypted:
            print(f"   Encryption Method: {pdf_reader.reader.encryption}")


if __name__ == "__main__":
    main()
