# Dự Án: AI Life Companion & Digital Twin

## 1. Giới thiệu
Xây dựng một AI Agent tích hợp RAG (Retrieval-Augmented Generation) đóng vai trò là một nhật ký thông minh, đồng thời là một "bản sao số" (Digital Twin) của người dùng. Hệ thống được thiết kế để chạy cá nhân (Self-hosted), mã nguồn mở, dễ dàng triển khai bằng Docker.

## 2. Tính năng Chính

### 🌟 GraphRAG (Knowledge Graph)
- Sử dụng cấu trúc đồ thị tri thức để kết nối các sự kiện, con người, địa điểm và cảm xúc.
- Giúp AI hiểu sâu hơn về ngữ cảnh và mối quan hệ giữa các ký ức.

### 🤖 Proactive Agent (AI Chủ động)
- AI chủ động tương tác, không chỉ đợi người dùng hỏi.
- **Thông báo nhắc nhở**: Gửi email nhắc nhở kỷ niệm hoặc hỏi thăm qua **SMTP (Gmail)**.

### 📸 Đa phương thức (Multimodal)
- Hỗ trợ Nhật ký bằng: Hình ảnh, Video, PDF (Tạm thời chưa hỗ trợ xử lý âm thanh/ghi âm).
- AI có khả năng phân tích hình ảnh để hiểu nội dung và lưu vào Knowledge Graph.

### 📊 Dashboard Phân tích Cuộc đời (Insight Analytics)
- Trực quan hóa dữ liệu cuộc sống: Biểu đồ cảm xúc, thói quen, tần suất sự kiện.
- Cung cấp insights về bản thân.

### ⏳ Time Travel (Ôn lại kỷ niệm)
- Tính năng "Du hành thời gian", gợi nhớ sự kiện "ngày này năm xưa".

## 3. Yêu cầu Phi chức năng & Bảo mật

### 🔒 Bảo mật & Authentication
- **API Key**: Mỗi lần truy cập/request phải có API Key riêng biệt để xác thực.
- **Session**: Cấu hình lưu trữ session dài hạn (Long-lived sessions) trong Redis để trải nghiệm liền mạch.

### 🏗️ Kiến trúc & Chất lượng mã nguồn
- **Clean Code**: Phân chia thư mục, module rõ ràng, tuân thủ các nguyên tắc thiết kế tốt (SOLID, DRY).
- **Open Source Ready**: Cấu trúc dự án chuẩn để người khác có thể clone và tự chạy dễ dàng.
- **Single User**: Tối ưu hóa cho trải nghiệm cá nhân hóa của một người dùng duy nhất.

## 4. Technology Stack (Công nghệ sử dụng)

### Backend & Core
- **Framework**: FastAPI (Python).
- **Database**: PostgreSQL.
- **Deployment**: **Docker & Docker Compose** (Toàn bộ các service được đóng gói container).

### AI & Data Processing
- **LLM**:
  - **Google Gemini**.
  - **OpenAI**.
  - **Ollama**: Kết nối `http://222.253.80.30:11434/` (Auto list models).
- **Orchestration & Framework**:
  - **LlamaIndex**: Quản lý dữ liệu, Indexing và Retrieval cho RAG.
  - **LangGraph**: Xây dựng luồng xử lý (Stateful Multi-Actor Applications) cho Agent.
- **Embedding**: `bge-m3:567m` (via Ollama).
- **Vector DB**: Qdrant.
- **RAG**: GraphRAG (kết hợp sức mạnh của LlamaIndex + Knowledge Graph).

### Storage & Caching
- **Redis**: Lưu session (TTL cao) và context summary.
- **Minio (S3)**: Lưu trữ file gốc (Ảnh, PDF, Video).

## 5. Luồng xử lý (High Level)
1. **Input**: Người dùng gửi text/ảnh/file (kèm API Key).
2. **Processing**: 
   - Upload Minio.
   - Trích xuất thông tin (Image Captioning, OCR PDF).
   - Vector hóa & Graph Construction.
3. **Proactive**: Job chạy ngầm kiểm tra sự kiện/kỷ niệm -> Gửi Email qua SMTP.
4. **Retrieval & Generation**: Query Qdrant/Graph -> LLM trả lời.
