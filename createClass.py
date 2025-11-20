import weaviate

client = weaviate.Client("http://weaviate:8080")

if not client.schema.contains({"classes": [{"class": "SupportAgent"}]}):
    class_obj = {
        "class": "tours",
        "description": "A class to store content for agents",
        "vectorizer": "text2vec-openai",  
        "moduleConfig": {
            "text2vec-openai": {
                "vectorizeClassName": False
            }
        },
        "properties": [
            {
                "name": "category",
                "dataType": ["text"]
            },
            {
                "name": "content",
                "dataType": ["text"]
            },
            {
                "name": "url",
                "dataType": ["text"]
            },
            {
                "name": "doc_id",
                "dataType": ["text"]
            },
            {
                "name": "chunk_id",
                "dataType": ["text"]
            },
            {
                "name": "agentId",
                "dataType": ["text"]
            }
        ]
    }

    # Create class in schema
    client.schema.create_class(class_obj)
    print("Class created.")
else:
    print("Class already exists.")
