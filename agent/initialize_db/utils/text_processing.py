
from unstructured.partition.text import partition_text
from typing import List, Dict
import json


# Load the property data
def load_property_data(filepath: str) -> List[Dict]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON format in {filepath}")
        return None
    except Exception as e:
        print(f"Error loading JSON: {str(e)}")
        return None



def create_overlapping_chunks(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Create overlapping chunks from text."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Get chunk of specified size
        end = start + chunk_size
        
        # If this is not the first chunk, include overlap from previous chunk
        if start > 0:
            start = start - overlap
            
        # Get the chunk
        chunk = text[start:end]
        
        # If chunk ends mid-sentence, extend to next period
        if end < text_length:
            last_period = chunk.rfind('.')
            if last_period != -1:
                chunk = chunk[:last_period + 1]
                end = start + len(chunk)
        
        chunks.append(chunk.strip())
        start = end

    return chunks

def process_property_data(property_data: List[Dict]) -> List[Dict]:
    """Process each property and create chunks."""
    chunked_data = []
    
    for prop in property_data:
        if not prop.get('processed_data'):
            continue
            
        chunks = create_overlapping_chunks(prop['processed_data'])
        
        for i, chunk in enumerate(chunks):
            chunked_data.append({
                'id': prop['id'],
                'url': prop['url'],
                'chunk_id': i,
                'total_chunks': len(chunks),
                'category': prop['category'],
                'content': chunk
            })
    
    return chunked_data


