import weaviate

# Connect to the Weaviate client
client = weaviate.Client("http://localhost:8080")

# Delete the class SupportAgent
client.schema.delete_class("SupportAgent")
