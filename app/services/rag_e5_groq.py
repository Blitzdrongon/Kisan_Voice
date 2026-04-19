
# """
# RAG System with E5 Multilingual Instruct + Groq
# (JSON Q&A INGESTION – HALLUCINATION SAFE)
# """
# import sys
# __import__('pysqlite3')
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# import os
# import sys

# # Ensure project root is in sys.path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(os.path.dirname(current_dir)) # RaithaMithra/
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

# # Also add 'app' directory
# app_dir = os.path.join(project_root, 'app')
# if app_dir not in sys.path:
#     sys.path.insert(0, app_dir)

# from dotenv import load_dotenv

# # Load .env explicitly
# env_path = os.path.join(project_root, '.env')
# load_dotenv(env_path)

# # Debug env vars
# # print(f"Loaded .env from {env_path}")
# # print(f"GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}")

# import json
# from typing import List, Dict, Optional
# from pathlib import Path
# import chromadb
# from sentence_transformers import SentenceTransformer
# from groq import Groq
# from core.config import get_settings
# from loguru import logger


# class E5RAGSystem:
#     def __init__(
#         self,
#         collection_name: str = "e6_knowledge_base",
#         chroma_db_path: str = "./chroma_db_e6",
#         groq_api_key: Optional[str] = None
#     ):
        

#         # ---------- E5 Task ----------
#         self.retrieval_task = (
#             "Given a question, retrieve relevant passages that answer the question"
#         )

#         # ---------- Embedding Model ----------
#         self.embedding_model = SentenceTransformer(
#             "intfloat/multilingual-e5-large-instruct"
#         )

#         # ---------- ChromaDB ----------
#         self.client = chromadb.PersistentClient(path=chroma_db_path)
#         self.collection = self.client.get_or_create_collection(
#             name=collection_name,
#             metadata={"hnsw:space": "cosine"}
#         )

#         # ---------- Groq ----------
#         self.settings = get_settings()
#         self.groq_api_key = self.settings.groq_api_key
#         self.base_url = "https://api.groq.com/openai/v1"
#         if not self.groq_api_key:
#             raise ValueError("GROQ_API_KEY not found in environment variables")


#         self.groq_client = Groq(api_key=self.groq_api_key, base_url=self.base_url)

#     # ======================================================
#     # JSON INGESTION (Q&A SCHEMA – YOUR FILE)
#     # ======================================================
#     def add_json(self, json_path: str) -> int:
#         """
#         Ingest Q&A-style JSON like sugar_cane.json
#         """
#         with open(json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         if not isinstance(data, list):
#             raise ValueError("Expected a list of Q&A objects")

#         documents = []
#         metadatas = []
#         ids = []

#         source = Path(json_path).name

#         for i,item in enumerate(data):
#             q = item.get("question", "").strip()
#             a = item.get("answer", "").strip()
#             qid = item.get("id")

#             if not qid:
#                 qid = f"{source}_{i}"

#             if not q or not a:
#                 continue


#             # ✅ Combine Q + A (BEST PRACTICE)
#             text = f"Question: {q}\nAnswer: {a}"

#             documents.append(text)
#             metadatas.append({
#                 "source": source,
#                 "id": qid
#             })
#             ids.append(qid)

#         if not documents:
#             return 0

#         embeddings = self.embedding_model.encode(
#             documents,
#             normalize_embeddings=True,
#             show_progress_bar=True
#         )

#         self.collection.upsert(
#             documents=documents,
#             embeddings=embeddings.tolist(),
#             metadatas=metadatas,
#             ids=ids
#         )
#         logger.info(f"Added {len(documents)} documents to the collection")

#         return len(documents)

#     # ======================================================
#     # RETRIEVAL
#     # ======================================================
#     def retrieve(self, query: str, top_k: int = 5) -> Dict:
#         instructed_query = (
#             f"Instruct: {self.retrieval_task}\nQuery: {query}"
#         )

#         query_embedding = self.embedding_model.encode(
#             instructed_query,
#             normalize_embeddings=True
#         )

#         results = self.collection.query(
#             query_embeddings=[query_embedding.tolist()],
#             n_results=top_k
#         )

#         documents = results["documents"][0]
#         metadatas = results["metadatas"][0]
#         distances = results["distances"][0]
#         similarities = [1 / (1 + d) for d in distances]

#         logger.info(f"Retrieved {documents} documents")
#         logger.info(f"Similarities: {similarities}")

#         return {
#             "documents": documents,
#             "metadatas": metadatas,
#             "similarities": similarities
#         }

#     # ======================================================
#     # GENERATION (STRICT GROQ PROMPT)
#     # ======================================================
#     def generate_response(
#         self,
#         query: str,
#         retrieved: Dict,
#         model: str = "llama-3.3-70b-versatile"
#     ) -> str:

#         documents = retrieved["documents"]

#         if not documents:
#             return "Information not available in the document."

#         context = "\n\n".join(documents)

#         if len(context.split()) < 40:
#             return "Information not available in the document."

#         system_prompt = (
#             "You are a factual question-answering system.\n"
#             "Rules:\n"
#             "1. Answer ONLY using the provided CONTEXT.\n"
#             "2. Do NOT use outside knowledge.\n"
#             "3. If the answer is not explicitly present, reply exactly:\n"
#             "   'Information not available in the document.'\n"
#             "4. Be concise."
#         )

#         user_prompt = f"""
# CONTEXT:
# {context}

# QUESTION:
# {query}

# ANSWER:
# """

#         response = self.groq_client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             temperature=0.0,
#             max_tokens=200
#         )

#         return response.choices[0].message.content.strip()

#     # ======================================================
#     # CHAT
#     # ======================================================
#     def chat(
#         self,
#         query: str,
#         top_k: int = 5,
#         show_context: bool = False
#     ) -> str:

#         retrieved = self.retrieve(query, top_k)
#         answer = self.generate_response(query, retrieved)
        
#         if not show_context:
#             return answer

#         output = [
#             "=" * 70,
#             "RETRIEVED CONTEXT",
#             "=" * 70
#         ]

#         for i, (doc, meta, sim) in enumerate(zip(
#             retrieved["documents"],
#             retrieved["metadatas"],
#             retrieved["similarities"]
#         ), 1):
#             output.append(f"\n[{i}] {meta.get('id')} | {meta.get('source')} ({sim:.1%})")
#             output.append(doc)

#         output.extend([
#             "\n" + "=" * 70,
#             "RESPONSE",
#             "=" * 70,
#             answer,
#             "=" * 70
#         ])

#         return "\n".join(output)


# # Global service instance
# e5_rag_service = E5RAGSystem()


# def get_e5_rag_service() -> E5RAGSystem:
#     """Get E5 RAG service instance"""
#     return e5_rag_service




# def test():
#     e5_rag_service = get_e5_rag_service()
    
#     json_path = Path(
#         "/home/rospc/tanishq/RaithaMithra_v2/RaithaMithra/rag/final_clean_merged_dataset.json"
#     )

#     e5_rag_service.add_json(str(json_path))

#     print(
#         e5_rag_service.chat(
#             "ಪ್ರತಿ ಏಕರೆಗೆ ಬೇಕಾಗುವ ಬೀಜ ಕಬ್ಬಿನ ಪ್ರಮಾಣ ಎಷ್ಟು?",
#             show_context=True
#         )
#     )


# def main():
#     test()


# if __name__ == "__main__":
#     main()