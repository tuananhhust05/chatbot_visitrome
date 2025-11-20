import weaviate

client = weaviate.Client("http://localhost:8080")

# Lấy tất cả object IDs
objects = client.data_object.get(class_name="SupportAgent", limit=1000)  # có thể cần phân trang nếu > 1000

for obj in objects['objects']:
    client.data_object.delete(obj['id'], class_name="SupportAgent")

print("✅ Đã xoá toàn bộ object trong class SupportAgent.")