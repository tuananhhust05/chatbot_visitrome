


import weaviate
from weaviate.classes.config import Configure
import weaviate.classes as wvc
import json 
from typing import List, Dict
from sentence_transformers import SentenceTransformer
# from scripts_offline.initialize_db.utils.text_processing import load_property_data, process_property_data


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



# Load the property data
property_data = load_property_data(filepath='data/other_agent.json')
print("property_data", property_data)

# Usage
chunked_property_data = process_property_data(property_data)

weaviate_client = weaviate.connect_to_local()

embedding_model = SentenceTransformer('all-distilroberta-v1')




# Create a new collection in Weaviate
# weaviate_client.collections.delete("SupportAgent")
# weaviate_client.collections.create(
#     "SupportAgent",
#     vectorizer_config=Configure.Vectorizer.none(),
#     properties=[
#         wvc.config.Property(name="doc_id", data_type=wvc.config.DataType.INT),
#         wvc.config.Property(name="chunk_id", data_type=wvc.config.DataType.INT),
#         wvc.config.Property(name="url", data_type=wvc.config.DataType.TEXT),
#         wvc.config.Property(name="category", data_type=wvc.config.DataType.TEXT),
#         wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
#         wvc.config.Property(name="agentId", data_type=wvc.config.DataType.TEXT)
#     ]
# )
# Create collection object
collection = weaviate_client.collections.get("SupportAgent")

print("chunked_property_data",chunked_property_data)
# Generate and add data with custom vectors
for item in chunked_property_data:
    # Generate embedding
    vector = embedding_model.encode(item['content'])
    
    # Add object with custom vector
    collection.data.insert(
        properties={
            "doc_id": item['id'],
            "url": item['url'],
            "chunk_id": item['chunk_id'],
            "category": item['category'],
            "content": item['content'],
            "agentId":"1"
        },
        vector=vector.tolist()  # Convert numpy array to list
    )
    print("vector ...",vector.tolist())











