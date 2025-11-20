# PDF Upload API

API để upload file PDF, xử lý nội dung và insert vào Weaviate database.

## 🚀 Tính năng

- ✅ Upload file PDF qua HTTP API
- ✅ Đọc và trích xuất nội dung từ PDF
- ✅ Chia tách văn bản thành các câu
- ✅ Tạo embeddings sử dụng SentenceTransformer
- ✅ Xóa toàn bộ dữ liệu cũ trong Weaviate collection
- ✅ Insert dữ liệu mới vào Weaviate với vectors
- ✅ Giao diện web đơn giản để test
- ✅ Kiểm tra trạng thái API

## 📁 Cấu trúc file

```
app/
├── routers/
│   └── pdf_upload.py          # API router cho PDF upload
├── views/
│   └── pdf_upload.html        # Giao diện web upload
└── __init__.py               # Đã cập nhật để include router

uploads/                      # Thư mục lưu file tạm (tự động tạo)
```

## 🔧 Cài đặt

1. **Đảm bảo các dependencies đã cài:**
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

2. **Khởi động server:**
   ```bash
   python run.py
   ```

3. **Truy cập giao diện web:**
   ```
   https://agent.dev.bridgeo.ai/rag/upload-page
   ```

## 📡 API Endpoints

### 1. Upload PDF
```http
POST /rag/upload
Content-Type: multipart/form-data

file: [PDF file]
```

**Response:**
```json
{
  "success": true,
  "message": "PDF processed and inserted into Weaviate successfully",
  "data": {
    "filename": "document.pdf",
    "total_sentences": 150,
    "inserted_chunks": 145,
    "collection": "PropertyAgent1"
  }
}
```

### 2. Kiểm tra trạng thái
```http
GET /rag/status
```

**Response:**
```json
{
  "status": "healthy",
  "weaviate_connected": true,
  "collection": "PropertyAgent1",
  "collection_properties": [
    {"name": "doc_id", "type": "text"},
    {"name": "chunk_id", "type": "text"},
    {"name": "url", "type": "text"},
    {"name": "category", "type": "text"},
    {"name": "content", "type": "text"},
    {"name": "agentId", "type": "text"}
  ]
}
```

### 3. Giao diện web
```http
GET /rag/upload-page
```

## 🔄 Quy trình xử lý

1. **Upload file:** Người dùng upload file PDF
2. **Lưu tạm:** File được lưu vào thư mục `uploads/`
3. **Đọc PDF:** Sử dụng `pypdf` để trích xuất text
4. **Chia câu:** Sử dụng regex để chia văn bản thành các câu
5. **Lọc dữ liệu:** Chỉ giữ lại câu có độ dài > 10 ký tự
6. **Xóa dữ liệu cũ:** Xóa toàn bộ dữ liệu trong Weaviate collection
7. **Tạo embeddings:** Sử dụng `all-distilroberta-v1` model
8. **Insert vào Weaviate:** Insert từng câu với vector tương ứng
9. **Dọn dẹp:** Xóa file tạm sau khi xử lý xong

## 📊 Cấu trúc dữ liệu

Mỗi câu được lưu trong Weaviate với cấu trúc:

```json
{
  "doc_id": "1",              // ID document (string)
  "url": "",                  // URL (rỗng như yêu cầu)
  "chunk_id": "0",            // ID chunk (string)
  "category": "",             // Category (rỗng như yêu cầu)
  "content": "Nội dung câu...", // Nội dung câu
  "agentId": "8386",          // Agent ID (hardcoded)
  "vector": [0.1, 0.2, ...]   // Embedding vector
}
```

## 🛠️ Sử dụng với cURL

### Upload PDF:
```bash
curl -X POST "https://agent.dev.bridgeo.ai/rag/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

### Kiểm tra trạng thái:
```bash
curl -X GET "https://agent.dev.bridgeo.ai/rag/status"
```

## 🐍 Sử dụng với Python

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('https://agent.dev.bridgeo.ai/rag/upload', files=files)
    print(response.json())

# Kiểm tra trạng thái
response = requests.get('https://agent.dev.bridgeo.ai/rag/status')
print(response.json())
```

## ⚙️ Cấu hình

Các thông số có thể thay đổi trong `app/routers/pdf_upload.py`:

```python
UPLOAD_DIR = "uploads"                    # Thư mục lưu file tạm
WEAVIATE_COLLECTION = "PropertyAgent1"    # Tên collection Weaviate
ALLOWED_EXTENSIONS = {".pdf"}             # Loại file được phép
```

## 🚨 Xử lý lỗi

### Lỗi thường gặp:

1. **File không phải PDF:**
   ```json
   {
     "detail": "Invalid file type. Only PDF files are allowed."
   }
   ```

2. **Không thể đọc PDF:**
   ```json
   {
     "detail": "Error reading PDF: [error message]"
   }
   ```

3. **Weaviate không kết nối được:**
   ```json
   {
     "detail": "Error connecting to Weaviate: [error message]"
   }
   ```

4. **Không có nội dung trong PDF:**
   ```json
   {
     "detail": "No content extracted from PDF"
   }
   ```

## 📝 Logs

API sử dụng Python logging để ghi log:

- **INFO:** Thông tin về quá trình xử lý
- **WARNING:** Cảnh báo về lỗi không nghiêm trọng
- **ERROR:** Lỗi nghiêm trọng

## 🔒 Bảo mật

- Chỉ chấp nhận file PDF
- File tạm được xóa sau khi xử lý
- Validation đầy đủ cho input
- Error handling toàn diện

## 🚀 Deployment

1. **Production:**
   ```bash
   uvicorn run:app --host 0.0.0.0 --port 8501 --workers 4
   ```

2. **Development:**
   ```bash
   python run.py
   ```

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. Weaviate server đã chạy chưa
2. Collection `PropertyAgent1` đã tồn tại chưa
3. File PDF có thể đọc được không
4. Logs để debug lỗi cụ thể
