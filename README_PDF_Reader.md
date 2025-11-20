# PDF Reader Scripts

This repository contains two Python scripts for reading and extracting content from PDF files using the `pypdf` library.

## Files

1. **`pdf_reader.py`** - Comprehensive PDF reader with command-line interface
2. **`simple_pdf_reader.py`** - Simple PDF reader for basic usage
3. **`testpdf.py`** - PDF to Weaviate processor (reads PDF, splits into sentences, inserts into Weaviate)
4. **`README_PDF_Reader.md`** - This documentation file

## Prerequisites

The scripts use the `pypdf` library, which is already included in your `requirements.txt`. If you need to install it separately:

```bash
pip install pypdf
```

## Usage

### 1. Simple PDF Reader (`simple_pdf_reader.py`)

This script provides basic PDF reading functionality without command-line arguments.

#### Basic Usage

```python
from simple_pdf_reader import read_pdf_simple, read_pdf_metadata, save_pdf_text_to_file

# Read PDF and extract text
text = read_pdf_simple("your_document.pdf")
if text:
    print(text)

# Extract metadata
metadata = read_pdf_metadata("your_document.pdf")
print(metadata)

# Save extracted text to file
save_pdf_text_to_file("your_document.pdf", "output.txt")
```

#### Running the Example

```bash
python simple_pdf_reader.py
```

**Note:** Edit the `pdf_file` variable in the script to point to your PDF file.

### 2. Comprehensive PDF Reader (`pdf_reader.py`)

This script provides advanced features with a command-line interface.

### 3. PDF to Weaviate Processor (`testpdf.py`)

This script reads PDF content, splits it into sentences, and inserts the data into Weaviate database with embeddings.

#### Command Line Usage

```bash
# Extract all text from a PDF
python pdf_reader.py document.pdf

# Show PDF metadata only
python pdf_reader.py document.pdf --metadata

# Extract text from specific pages (range)
python pdf_reader.py document.pdf --pages 1-5

# Extract text from specific pages (individual)
python pdf_reader.py document.pdf --pages 1,3,5

# Save extracted text to a file
python pdf_reader.py document.pdf --output extracted_text.txt

# Show image information
python pdf_reader.py document.pdf --images

# Show detailed information
python pdf_reader.py document.pdf --verbose

# Combine multiple options
python pdf_reader.py document.pdf --metadata --pages 1-3 --output output.txt
```

#### Programmatic Usage

```python
from pdf_reader import PDFReader

# Initialize the reader
pdf_reader = PDFReader("your_document.pdf")

# Get basic information
print(f"Pages: {pdf_reader.get_page_count()}")

# Extract all text
text = pdf_reader.extract_text()
print(text)

# Extract text from specific pages (0-indexed)
text = pdf_reader.extract_text(start_page=0, end_page=5)

# Extract text page by page
pages_text = pdf_reader.extract_text_by_page()
for page_num, text in pages_text:
    print(f"Page {page_num}: {text[:100]}...")

# Get metadata
metadata = pdf_reader.get_metadata()
print(metadata)

# Get image information
images_info = pdf_reader.extract_images_info()
print(images_info)

# Save text to file
pdf_reader.save_text_to_file("output.txt")
```

### 3. PDF to Weaviate Processor (`testpdf.py`)

#### Basic Usage

```python
# Run the script directly
python testpdf.py
```

#### Configuration

Edit the following variables in `testpdf.py`:
- `pdf_file = "test.pdf"` - Change to your PDF file path
- `doc_id = 1` - Document ID for the PDF
- `collection_name = "PropertyAgent1"` - Weaviate collection name

#### Features

- ✅ Reads PDF content using pypdf
- ✅ Splits text into sentences using regex
- ✅ Filters out short sentences (< 10 characters)
- ✅ Generates embeddings using SentenceTransformer
- ✅ Inserts data into Weaviate with custom vectors
- ✅ Sets url and category to empty strings as requested
- ✅ Progress tracking during insertion
- ✅ Error handling for failed insertions

#### Output Format

Each sentence becomes a separate chunk with:
- `doc_id`: Document ID (configurable)
- `url`: Empty string ""
- `chunk_id`: Sequential ID for each sentence
- `category`: Empty string ""
- `content`: The sentence text
- `agentId`: "8386" (hardcoded)
- `vector`: Generated embedding vector

## Features

### Simple PDF Reader
- ✅ Basic text extraction
- ✅ Metadata extraction
- ✅ Save text to file
- ✅ Error handling
- ✅ Page-by-page extraction

### Comprehensive PDF Reader
- ✅ All features from simple reader
- ✅ Command-line interface
- ✅ Page range selection
- ✅ Image information extraction
- ✅ Detailed PDF information
- ✅ Verbose output options
- ✅ Flexible page selection (ranges, specific pages)
- ✅ Comprehensive error handling

### PDF to Weaviate Processor
- ✅ PDF text extraction
- ✅ Sentence-based text splitting
- ✅ Embedding generation
- ✅ Weaviate database integration
- ✅ Custom vector insertion
- ✅ Progress tracking
- ✅ Error handling for database operations

## Examples

### Example 1: Basic Text Extraction
```python
from simple_pdf_reader import read_pdf_simple

text = read_pdf_simple("document.pdf")
if text:
    print("Extracted text:")
    print(text)
```

### Example 2: Extract Specific Pages
```python
from pdf_reader import PDFReader

reader = PDFReader("document.pdf")
# Extract pages 2-4 (1-indexed in output, 0-indexed internally)
text = reader.extract_text(start_page=1, end_page=4)
print(text)
```

### Example 3: Get PDF Information
```python
from pdf_reader import PDFReader

reader = PDFReader("document.pdf")
print(f"Total pages: {reader.get_page_count()}")
print(f"Metadata: {reader.get_metadata()}")
print(f"Images: {reader.extract_images_info()}")
```

### Example 4: Process PDF and Insert into Weaviate
```python
# Run the PDF to Weaviate processor
python testpdf.py

# The script will:
# 1. Read test.pdf
# 2. Split content into sentences
# 3. Generate embeddings
# 4. Insert into Weaviate collection "PropertyAgent1"
```

## Error Handling

Both scripts include comprehensive error handling for:
- File not found errors
- PDF reading errors
- Page extraction errors
- File writing errors
- Invalid page ranges

## Output Format

### Text Extraction
- Page numbers are clearly marked
- Empty pages are skipped
- Text is preserved with original formatting where possible

### Metadata
- Clean key names (removes leading '/')
- String values for all metadata
- Empty metadata is handled gracefully

### File Output
- UTF-8 encoding
- Includes source file information
- Page range information
- Clear separation between sections

## Troubleshooting

### Common Issues

1. **"File not found" error**
   - Check the file path is correct
   - Ensure the file exists in the specified location

2. **"pypdf is not installed" error**
   - Install pypdf: `pip install pypdf`
   - Or use your existing requirements.txt

3. **"No text content found"**
   - The PDF might be image-based (scanned document)
   - Try using OCR tools for such documents
   - Check if the PDF is encrypted

4. **"Could not extract text from page"**
   - Some pages might be corrupted or contain only images
   - The script will continue with other pages

### Performance Tips

- For large PDFs, consider extracting specific page ranges
- Use the `--output` option to save results instead of printing to console
- The `--verbose` option provides additional debugging information

## License

This code is provided as-is for educational and practical use.
