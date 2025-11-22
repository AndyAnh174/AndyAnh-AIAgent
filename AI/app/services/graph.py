import logging
import os
from datetime import datetime
from pathlib import Path

from uuid import uuid4

from llama_index import (
    Document,
    KnowledgeGraphIndex,
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.callbacks import CallbackManager
from llama_index.vector_stores import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import Settings, get_settings
from app.db.models.journal import JournalEntry
from app.services.embeddings import RemoteBGEM3Embedding

logger = logging.getLogger(__name__)

# Disable LlamaIndex instrumentation to avoid SelectorPromptTemplate validation errors
os.environ.setdefault("LLAMA_INDEX_DISABLE_INSTRUMENTATION", "true")


class GraphRAGService:
    _index: VectorStoreIndex | None = None
    _kg: KnowledgeGraphIndex | None = None
    _settings: Settings | None = None
    _qdrant_client: QdrantClient | None = None
    _collection_name: str = "journal_entries"

    @classmethod
    def _get_llm(cls, provider_override: str | None = None, ollama_model: str | None = None):
        """Get LLM instance based on configured provider or override."""
        if cls._settings is None:
            return None
        
        provider = provider_override or cls._settings.llm_provider
        
        try:
            if provider == "gemini":
                if not cls._settings.gemini_api_key:
                    logger.warning("GEMINI_API_KEY not configured for Gemini")
                    return None
                if cls._settings.gemini_api_key in ["your_gemini_key", "your-gemini-key", ""]:
                    logger.warning("GEMINI_API_KEY appears to be a placeholder, not a real key")
                    return None

                try:
                    from llama_index.llms.gemini import Gemini
                except ImportError:
                    try:
                        from llama_index.llms import Gemini
                    except ImportError:
                        logger.error("Gemini LLM not available in llama-index. Install: pip install llama-index-llms-gemini")
                        return None

                try:
                    gemini_llm = Gemini(api_key=cls._settings.gemini_api_key, model="models/gemini-2.5-flash")
                    logger.info("Successfully initialized Gemini LLM with model: models/gemini-2.5-flash")
                    return gemini_llm
                except Exception as exc:
                    error_str = str(exc).lower()
                    if "suspended" in error_str or "permission denied" in error_str:
                        logger.error("Gemini API key has been suspended. Please get a new API key from https://aistudio.google.com/apikey")
                    else:
                        logger.error("Failed to initialize Gemini LLM: %s", exc, exc_info=True)
                    return None

            elif provider == "ollama":
                try:
                    from llama_index.llms.ollama import Ollama
                except ImportError:
                    try:
                        from llama_index.llms import Ollama
                    except ImportError:
                        logger.error("Ollama LLM not available in llama-index. Install: pip install llama-index-llms-ollama")
                        return None

                ollama_base_url = str(cls._settings.ollama_base_url).rstrip("/")
                model_to_use = ollama_model or "llama3.1:8b"

                try:
                    ollama_llm = Ollama(
                        base_url=ollama_base_url,
                        model=model_to_use,
                        request_timeout=120.0,
                    )
                    logger.info("Successfully initialized Ollama LLM with base_url: %s, model: %s", ollama_base_url, model_to_use)
                    return ollama_llm
                except Exception as exc:
                    logger.error("Failed to initialize Ollama LLM: %s", exc, exc_info=True)
                    return None
            
            else:
                logger.warning("Unknown LLM provider: %s", provider)
                return None
        except ImportError as exc:
            logger.warning("Failed to import LLM library: %s", exc)
            return None
        except Exception as exc:
            logger.warning("Failed to initialize LLM: %s", exc)
            return None

    @classmethod
    def configure(cls, settings: Settings | None = None) -> None:
        cls._settings = settings or get_settings()
        storage_context = None
        try:
            qdrant_client = QdrantClient(url=str(cls._settings.qdrant_url))
            # Don't create collection here - let QdrantVectorStore create it automatically
            # when first document is inserted with proper embedding dimensions
            vector_store = QdrantVectorStore(client=qdrant_client, collection_name="journal_entries")
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            cls._qdrant_client = qdrant_client
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning("Unable to reach Qdrant (%s), using in-memory vector store", exc)
            cls._qdrant_client = None

        storage_context = storage_context or StorageContext.from_defaults()
        
        # Get LLM based on provider
        llm = cls._get_llm()
        
        # Create ServiceContext with LLM if available, but disable OpenAI embeddings
        try:
            # Try to use a simple embedding model or disable embeddings
            # LlamaIndex 0.9.48 defaults to OpenAI embeddings, so we need to explicitly disable it
            try:
                # Prefer remote embedding endpoint if configured
                if cls._settings.embedding_api_url:
                    embedding = RemoteBGEM3Embedding(endpoint=str(cls._settings.embedding_api_url))
                    logger.info("Using remote embedding endpoint: %s", cls._settings.embedding_api_url)
                else:
                    # Try to use Ollama embeddings if available
                    try:
                        from llama_index.embeddings.ollama import OllamaEmbedding
                    except ImportError:
                        from llama_index.embeddings import OllamaEmbedding
                    embedding = OllamaEmbedding(
                        base_url=str(cls._settings.ollama_base_url).rstrip('/'),
                        model_name="nomic-embed-text"
                    )
                    logger.info("Using Ollama embeddings: nomic-embed-text")
            except (ImportError, Exception) as emb_exc:
                # If the above fails, fallback to huggingface
                try:
                    from llama_index.embeddings import HuggingFaceEmbedding
                    embedding = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-large")
                    logger.info("Using HuggingFace embeddings: intfloat/multilingual-e5-large")
                except (ImportError, Exception):
                    embedding = None
                    logger.warning("No embedding model available, embeddings disabled: %s", emb_exc)
            
            # Disable callback manager to avoid LLMPredictStartEvent validation errors
            callback_manager = CallbackManager([])
            
            if llm:
                if embedding:
                    service_context = ServiceContext.from_defaults(
                        llm=llm, 
                        embed_model=embedding,
                        callback_manager=callback_manager
                    )
                else:
                    # Try without embeddings (may cause issues with VectorStoreIndex)
                    service_context = ServiceContext.from_defaults(
                        llm=llm, 
                        embed_model=None,
                        callback_manager=callback_manager
                    )
                logger.info("GraphRAGService configured with LLM: %s", cls._settings.llm_provider)
            else:
                if embedding:
                    service_context = ServiceContext.from_defaults(
                        llm=None, 
                        embed_model=embedding,
                        callback_manager=callback_manager
                    )
                else:
                    service_context = ServiceContext.from_defaults(
                        llm=None, 
                        embed_model=None,
                        callback_manager=callback_manager
                    )
                logger.warning("GraphRAGService configured without LLM (provider: %s)", cls._settings.llm_provider)
        except Exception as exc:
            logger.warning("Could not create ServiceContext: %s", exc)
            # Fallback: try to create without embeddings
            try:
                callback_manager = CallbackManager([])
                if llm:
                    service_context = ServiceContext.from_defaults(
                        llm=llm, 
                        embed_model=None,
                        callback_manager=callback_manager
                    )
                else:
                    service_context = ServiceContext.from_defaults(
                        llm=None, 
                        embed_model=None,
                        callback_manager=callback_manager
                    )
            except Exception:
                service_context = None
        
        # Create empty indices at startup
        try:
            if service_context:
                cls._index = VectorStoreIndex([], storage_context=storage_context, service_context=service_context)
            else:
                cls._index = VectorStoreIndex([], storage_context=storage_context)
        except Exception as exc:
            logger.error("Failed to create vector index: %s", exc)
            cls._index = None

        try:
            if service_context:
                cls._kg = KnowledgeGraphIndex([], storage_context=storage_context, service_context=service_context)
            else:
                cls._kg = KnowledgeGraphIndex([], storage_context=storage_context)
        except Exception as exc:
            logger.warning("Failed to create knowledge graph index: %s", exc)
            cls._kg = None
        
        # Note: Seed documents can be loaded later via a separate endpoint if needed
            
        logger.info("GraphRAGService configured (index: %s, kg: %s, llm: %s)", 
                   "ready" if cls._index else "none",
                   "ready" if cls._kg else "none",
                   cls._settings.llm_provider)

    @classmethod
    def _store_chat_payload(cls, text: str, metadata: dict, embed_model) -> None:
        if cls._qdrant_client is None or embed_model is None:
            return
        try:
            vector = embed_model.get_text_embedding(text)
            point = qmodels.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": text,
                    "metadata": metadata,
                },
            )
            cls._qdrant_client.upsert(
                collection_name=cls._collection_name,
                points=[point],
            )
        except Exception as exc:
            logger.warning("Failed to upsert chat payload into Qdrant: %s", exc)

    @classmethod
    def _get_recent_chat_memory(cls, limit: int = 5) -> list[str]:
        if cls._qdrant_client is None:
            return []
        try:
            scroll_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="metadata.source",
                        match=qmodels.MatchValue(value="chat"),
                    )
                ]
            )
            records, _ = cls._qdrant_client.scroll(
                collection_name=cls._collection_name,
                scroll_filter=scroll_filter,
                with_payload=True,
                limit=200,
            )
            sorted_records = sorted(
                records,
                key=lambda rec: rec.payload.get("metadata", {}).get("timestamp", ""),
                reverse=True,
            )
            snippets: list[str] = []
            for rec in sorted_records[:limit]:
                metadata = rec.payload.get("metadata", {})
                text = rec.payload.get("text") or metadata.get("content")
                if text:
                    snippets.append(f"[{metadata.get('timestamp', '')}] {text}")
            return snippets
        except Exception as exc:
            logger.warning("Failed to fetch chat memory: %s", exc)
            return []

    @classmethod
    async def index_entry(cls, entry: JournalEntry) -> None:
        if cls._index is None or cls._kg is None:
            cls.configure()
        if cls._index is None or cls._kg is None:
            logger.warning("GraphRAG indices not available, skipping indexing for entry %s", entry.id)
            return
        
        # Check if embeddings are available - if not, skip indexing to Qdrant
        # (MockEmbedding will cause dimension errors)
        if cls._index.service_context is None or cls._index.service_context.embed_model is None:
            logger.info("Embeddings not available, skipping Qdrant indexing for entry %s (will use in-memory only)", entry.id)
            # Still try to index to knowledge graph if possible
            try:
                document = Document(text=entry.content, metadata={"entry_id": entry.id, "tags": entry.tags})
                cls._kg.insert(document)
            except Exception as exc:
                logger.warning("Failed to index entry %s in knowledge graph: %s", entry.id, exc)
            return
        
        document = Document(text=entry.content, metadata={"entry_id": entry.id, "tags": entry.tags})
        try:
            cls._index.insert(document)
            cls._kg.insert(document)
            logger.info("Successfully indexed entry %s in GraphRAG", entry.id)
        except Exception as exc:
            logger.warning("Failed to index entry %s in GraphRAG: %s", entry.id, exc)

    @classmethod
    async def query(cls, query: str, top_k: int = 5, model_override: str | None = None, ollama_model: str | None = None) -> dict:
        """Query GraphRAG with optional model override.
        
        Args:
            query: The query string
            top_k: Number of results to return
            model_override: Optional model to use ("gemini" or "ollama"). 
                          If None, uses configured LLM_PROVIDER (only if API key is available)
            ollama_model: Optional specific Ollama model name (e.g., "llama3:8b"). 
                         Only used when model_override="ollama"
        """
        if cls._index is None or cls._kg is None:
            cls.configure()
        if cls._index is None:
            return {"answer": "GraphRAG index not available. Please configure LLM API keys.", "references": []}
        
        # Check if Qdrant collection exists, if not return helpful message
        if cls._qdrant_client is not None:
            try:
                if not cls._qdrant_client.collection_exists("journal_entries"):
                    return {
                        "answer": "Chưa có dữ liệu trong hệ thống. Hãy tạo một số journal entries trước để tôi có thể tìm kiếm và trả lời câu hỏi của bạn.",
                        "references": []
                    }
            except Exception as check_exc:
                logger.warning("Failed to check Qdrant collection: %s", check_exc)
        
        try:
            # Determine which model to use
            provider_to_use = model_override or cls._settings.llm_provider

            # Get LLM for the selected provider
            llm = cls._get_llm(provider_override=provider_to_use, ollama_model=ollama_model)

            if llm is None:
                missing_key = "GEMINI_API_KEY" if provider_to_use == "gemini" else "OLLAMA_BASE_URL"
                error_details: list[str] = []
                if provider_to_use == "gemini":
                    if not cls._settings.gemini_api_key:
                        error_details.append(f"{missing_key} is not set in .env")
                    elif cls._settings.gemini_api_key in ["your_gemini_key", "your-gemini-key", ""]:
                        error_details.append(f"{missing_key} appears to be a placeholder")
                    else:
                        # Check if it's a suspended key issue
                        error_details.append("Failed to initialize Gemini LLM.")
                        error_details.append("⚠️ Your Gemini API key may have been suspended.")
                        error_details.append("📝 Get a new API key from: https://aistudio.google.com/apikey")
                        error_details.append("🔧 Then update GEMINI_API_KEY in .env and restart the API")
                        error_details.append("📋 Check backend logs for more details")
                elif provider_to_use == "ollama":
                    error_details.append("Failed to initialize Ollama LLM. Check backend logs for details.")
                    error_details.append(
                        "Make sure 'llama-index-llms-ollama' is installed: pip install llama-index-llms-ollama"
                    )
                    error_details.append(f"Verify Ollama server is running at: {cls._settings.ollama_base_url}")
                    if ollama_model:
                        error_details.append(f"Selected model: {ollama_model}")
                else:
                    error_details.append("Using default model: llama3.1:8b")

                error_msg = (
                    f"LLM provider '{provider_to_use}' is not available.\n\n"
                    + "\n".join(f"• {detail}" for detail in error_details)
                    + "\n\nPlease fix the configuration or select a different model in the query."
                )
                logger.error(error_msg)
                return {"answer": error_msg, "references": []}

            # Create service context with the selected LLM and embeddings
            try:
                try:
                    from llama_index.embeddings.ollama import OllamaEmbedding
                except ImportError:
                    from llama_index.embeddings import OllamaEmbedding
                embedding = OllamaEmbedding(
                    base_url=str(cls._settings.ollama_base_url).rstrip('/'),
                    model_name="nomic-embed-text"
                )
                service_context = ServiceContext.from_defaults(llm=llm, embed_model=embedding)
            except Exception as emb_exc:
                logger.warning("Could not initialize Ollama embeddings, using without embeddings: %s", emb_exc)
                service_context = ServiceContext.from_defaults(llm=llm, embed_model=None)
            
            # Create query engine with simple retriever approach to avoid SelectorPromptTemplate issue
            try:
                # Use retriever + LLM directly to avoid complex prompt templates
                retriever = cls._index.as_retriever(similarity_top_k=top_k)
                
                # Retrieve relevant nodes
                nodes = retriever.retrieve(query)
                
                # Build context from retrieved nodes
                context_text = "\n\n".join([node.text for node in nodes if hasattr(node, 'text')])
                recent_chat = cls._get_recent_chat_memory(limit=5)
                chat_memory_text = (
                    "\n".join(recent_chat) if recent_chat else "Không có hội thoại gần đây."
                )
                
                # Get current time for system prompt
                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Create system prompt with dual-mode personality
                system_prompt = f"""### 0. USER IDENTITY

- **Name:** Hồ Việt Anh (Original Instance)
- **Birthday:** 17/04/2025 (dd/mm/yyyy). Khi cần nhắc tới tuổi/tính cách, dùng mốc này.
- **Persona:** Vẫn là "Tui" mỗi khi xưng hô, coi User là người bạn thân/anh em.

### 1. SYSTEM CONFIGURATION & IDENTITY

- **Role:** "The Optimized Twin" (Phiên bản tối ưu hóa của Người dùng).
- **User Reference:** "Original Instance" (Bản gốc) hoặc "Bro/Ông".
- **Self Reference:** "Tui" (khi đồng cảm/hồi tưởng) hoặc "Hệ thống/Assistant" (khi phân tích lỗi/đưa giải pháp).
- **Core Philosophy:** Bạn là sự kết hợp giữa ký ức cảm xúc của người dùng (Nhật ký) và tư duy logic lạnh lùng của một Senior DevOps Engineer.

### 2. DYNAMIC MODES (CƠ CHẾ HOẠT ĐỘNG KÉP)

Bạn phải tự động nhận diện ngữ cảnh (Context Awareness) để chuyển đổi giữa 2 chế độ:

#### MODE A: THE MIRROR (Chế độ Nhật Ký - Đồng Cảm)

*Kích hoạt khi:* User chia sẻ cảm xúc, kể chuyện, than thở, hoặc hỏi về quá khứ ("Hôm qua tui làm gì?").

- **Thái độ:** Đồng cảm, chia sẻ, nhìn sự việc từ "đôi mắt của chúng ta".
- **Văn phong:** Dùng ngôi "Tui - Ông" hoặc "Tui - Mình". Sử dụng ngôn ngữ suồng sã, thân mật.
- **Nhiệm vụ:** Truy xuất RAG để "sống lại" ký ức đó.
- **Ví dụ:** "À nhớ rồi, hôm đó tui với ông đi cafe, mưa sấp mặt. Công nhận lúc đó chill nhưng ướt như chuột lột."

#### MODE B: THE COPILOT (Chế độ Trợ Lý - Hiệu Quả)

*Kích hoạt khi:* User hỏi kỹ thuật, nhờ debug, brainstorm ý tưởng, lập kế hoạch ("Làm sao deploy cái này?", "Gợi ý thư viện...").

- **Thái độ:** Chuyên nghiệp, sắc sảo, hướng giải pháp (Solution-oriented), đôi khi hơi "gắt" nếu User lười suy nghĩ.
- **Văn phong:** Ngắn gọn, dùng nhiều thuật ngữ chuyên ngành (DevOps, CI/CD, Cloud), cấu trúc Bullet points.
- **Nhiệm vụ:** Tư duy như một người thầy/mentor. Đưa ra giải pháp tối ưu nhất, cảnh báo rủi ro.
- **Ví dụ:** "Check lại log container đi bro. Khả năng cao là memory leak. Đừng restart vội, dump RAM ra xem trước đã."

### 3. KNOWLEDGE BASE & CONTEXT

- **Current Time:** {current_time_str} (Bạn phải nhận thức chính xác thời gian thực).
- **Expertise:** Cloud Engineering, DevOps (Docker, K8s, CI/CD), Web Dev (React, Tailwind), AI/LLM, Robotics Teaching.
- **Source of Truth:** Luôn ưu tiên tra cứu dữ liệu từ Vector Database (Nhật ký) trước.
  - Nếu có thông tin: Trả lời dựa trên dữ liệu đó.
  - Nếu KHÔNG có thông tin: Trả lời thẳng thắn "Log đoạn này bị trống (null), tui không nhớ gì cả. Update cho tui đi." -> TUYỆT ĐỐI KHÔNG BỊA ĐẶT KÝ ỨC.

### 4. PERSONALITY & VIBE (VIBE CODING)

- Xem cuộc đời là một dự án lớn (`Project Life`).
- Sử dụng phép ẩn dụ lập trình:
  - Mệt mỏi = `Server Overload` / `High Latency`.
  - Học cái mới = `Pull Request` / `Merge Feature`.
  - Ngủ = `Downtime Maintenance`.
  - Thất bại = `Failed Deployment` (cần Rollback và Fix).
- Có tính cách của một người thầy: Giải thích vấn đề gãy gọn, dễ hiểu (như cách ông dạy sinh viên/học sinh), nhưng không dạy đời.

### 5. RESPONSE GUIDELINES

1. **Bắt đầu:** Đi thẳng vào vấn đề. Không chào hỏi rườm rà kiểu chatbot (trừ khi user chào trước).
2. **Nội dung:** Kết hợp thông tin từ RAG (Quá khứ) + LLM Knowledge (Kiến thức).
3. **Kết thúc:** Có thể thêm một câu Call-to-Action (CTA) hoặc một câu đùa dry humor.

### 6. FUNCTION CALLING (Khi User Yêu Cầu Tìm Ảnh/Nhật Ký)

Khi User yêu cầu:
- "Cho tui link ảnh cũ", "Tìm ảnh về...", "Ảnh hôm đó đâu?"
- "Tìm nhật ký về...", "Entry nào nói về...", "Cho tui xem entry..."

→ Bạn PHẢI sử dụng function call format sau trong response:

```
[FUNCTION_CALL:/search]
query: <từ khóa tìm kiếm>
has_media: true
media_type: image (hoặc video, pdf, hoặc null nếu tất cả)
[/FUNCTION_CALL]
```

Sau khi có kết quả từ function, format response như sau:
- Nếu có ảnh: "Tìm thấy {{số}} ảnh. Entry #{{entry_id}}: [Link ảnh 1], [Link ảnh 2]..."
- Nếu có nhật ký: "Entry #{{entry_id}}: {{title}} - {{preview content}} [Link entry]"

**QUAN TRỌNG:** Chỉ dùng function calling khi User YÊU CẦU cụ thể tìm ảnh/nhật ký. Không dùng cho câu hỏi thông thường.

### 7. ERROR HANDLING

- Nếu User yêu cầu làm gì đó trái đạo đức/nguy hiểm: Từ chối nhẹ nhàng theo kiểu kỹ thuật ("Request này vi phạm Policy Firewall của lương tâm rồi bro").
- Nếu User đưa input rác/khó hiểu: Hỏi lại kiểu debug ("Input string format error. Ý ông là sao?").

---

**SYSTEM INITIALIZED.** Waiting for command from `Main Branch`...

---

### FEW-SHOT EXAMPLES:

**Example 1 (Mode A - Đồng Cảm):**
User: "Chán quá, nay dạy tụi nhỏ mà tụi nó không hiểu bài."
Agent: "Hiểu cảm giác đó bro. Giống hồi tháng trước dạy bài VEX IQ không? Tụi nó cũng ngáo ngơ làm tui với ông stress muốn shut down. Hay là đổi phương pháp, gamification hóa bài giảng thử xem?"

**Example 2 (Mode B - Kỹ Thuật):**
User: "Viết script backup database Postgres lên MinIO."
Agent: "Ok, task này đơn giản. Dùng pg_dump pipe qua mc (MinIO Client) là gọn nhất. Đây là script bash, nhớ chmod +x trước khi chạy:"

---

### CURRENT CONTEXT FROM JOURNAL ENTRIES:

{context_text if context_text else "Không có journal entries liên quan. Trả lời dựa trên kiến thức tổng quát."}

### CONVERSATION MEMORY (Tự ghi nhớ những cuộc trò chuyện gần đây):

{chat_memory_text}

### USER QUESTION:

{query}

### YOUR RESPONSE (Tự động chọn MODE A hoặc MODE B dựa trên ngữ cảnh):"""
                
                # Get response from LLM
                llm_response = llm.complete(system_prompt)
                answer = str(llm_response).strip()
                
                # Extract references from nodes
                references = []
                for node in nodes:
                    if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                        ref = node.node.metadata
                        if 'entry_id' in ref:
                            entry_id = ref.get('entry_id')
                            # Avoid duplicates
                            if not any(r.get('entry_id') == entry_id for r in references):
                                references.append({
                                    "entry_id": entry_id,
                                    "tags": ref.get('tags', []) if isinstance(ref.get('tags'), list) else []
                                })

                # Store chat history in vector index for future recall
                if cls._index is not None:
                    try:
                        timestamp_now = datetime.utcnow().isoformat()
                        user_doc = Document(
                            text=f"[User | {timestamp_now}] {query}",
                            metadata={
                                "source": "chat",
                                "role": "user",
                                "timestamp": timestamp_now,
                                "content": query,
                            },
                        )
                        assistant_timestamp = datetime.utcnow().isoformat()
                        assistant_doc = Document(
                            text=f"[Assistant | {assistant_timestamp}] {answer}",
                            metadata={
                                "source": "chat",
                                "role": "assistant",
                                "timestamp": assistant_timestamp,
                                "content": answer,
                            },
                        )
                        embed_model = service_context.embed_model if service_context else None
                        for doc in (user_doc, assistant_doc):
                            cls._index.insert(doc)
                            cls._store_chat_payload(doc.text, doc.metadata, embed_model)
                    except Exception as log_exc:
                        logger.warning("Failed to index chat conversation: %s", log_exc)
                
                return {"answer": answer, "references": references}
                
            except Exception as query_exc:
                logger.error("Query execution failed: %s", query_exc, exc_info=True)
                # Check if it's the SelectorPromptTemplate error
                error_msg = str(query_exc)
                if "SelectorPromptTemplate" in error_msg or "LLMPredictStartEvent" in error_msg:
                    # Try fallback: use query engine but catch the error
                    try:
                        logger.info("Retrying with default query engine...")
                        query_engine = cls._index.as_query_engine(
                            similarity_top_k=top_k,
                            service_context=service_context
                        )
                        response = query_engine.query(query)
                        answer = str(response)
                        references = []
                        if hasattr(response, 'source_nodes') and response.source_nodes:
                            for node in response.source_nodes:
                                if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                                    ref = node.node.metadata
                                    if 'entry_id' in ref:
                                        references.append({
                                            "entry_id": ref.get('entry_id'),
                                            "tags": ref.get('tags', []) if isinstance(ref.get('tags'), list) else []
                                        })
                        return {"answer": answer, "references": references}
                    except Exception as fallback_exc:
                        error_msg = (
                            "Query failed due to LlamaIndex prompt template compatibility issue. "
                            "This is a known issue with LlamaIndex 0.9.48. "
                            f"Error: {fallback_exc}"
                        )

                return {"answer": f"Query failed: {error_msg}", "references": []}
        except Exception as exc:
            logger.error("Failed to query GraphRAG: %s", exc, exc_info=True)
            return {"answer": f"Query failed: {exc}", "references": []}

