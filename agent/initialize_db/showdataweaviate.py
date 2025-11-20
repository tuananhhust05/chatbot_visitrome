import weaviate
import weaviate.classes as wvc

client = weaviate.Client("http://weaviate:8080") # or .connect_to_wcs() if using cloud

collection = client.collections.get("Hotels")


results = collection.query.fetch_objects(limit=10, include_vector=True)  # increase limit if needed

for obj in results.objects:
    # print(obj)
    print("Properties all:", obj.properties)
    # print("Vector:", obj.vector)  # is list[float]
