# import sys
# __import__('pysqlite3')
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# from transformers import AutoTokenizer, AutoModelForCausalLM
# import torch
# from loguru import logger
# import asyncio
# import time
# import accelerate
# import chromadb
# from sentence_transformers import SentenceTransformer
# import os
# import json
# from typing import List, Dict, Optional
# from pathlib import Path



# class GemmaWithRAGServices:
#     def __init__(self,
#         collection_name: str = "e6_knowledge_base",
#         chroma_db_path: str = "./chroma_db_e6",
#         model_id: str = "google/gemma-3-1b-it-qat-q4_0-unquantized",
#         cache_dir: str = r"/home/rospc/tanishq/RaithaMithra_v2/RaithaMithra/model"
#     ):
#         self.model_id = model_id
#         self.cache_dir = cache_dir
        
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
 
#         # ✅ Check if GPU is available
#         if torch.cuda.is_available():
#             self.device = "cuda"
#             self.dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
#             logger.info("⚡ GPU detected — running AgriParam on CUDA.")
#         else:
#             self.device = "cpu"
#             self.dtype = torch.float32
#             logger.warning("⚠️ GPU not available. Running AgriParam on CPU (expect slower performance).")

#         # Load tokenizer
#         self.tokenizer = AutoTokenizer.from_pretrained(
#             self.model_id,
#             cache_dir=cache_dir
#         )

#         # Load model with GPU/CPU placement
#         self.model = AutoModelForCausalLM.from_pretrained(
#             self.model_id,
#             dtype=self.dtype,
#             device_map={"": self.device},
#             cache_dir=cache_dir
#         )

#         logger.info(f"✅ Model loaded successfully on {self.device.upper()}")
#         if self.device == "cuda":
#             gpu_name = torch.cuda.get_device_name(0)
#             total_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
#             logger.info(f"🧠 GPU Info: {gpu_name} ({total_mem_gb:.2f} GB VRAM)")

#         logger.info("🌾 Gemma model ready for text generation.")

#      # ======================================================
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

#         for i, item in enumerate(data):
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
#         logger.info(f"✅ Added {len(documents)} documents to the collection")
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


#         logger.info(f"Retrieved documents: {documents}")
#         logger.info(f"Retrieved metadatas: {metadatas}")
#         logger.info(f"Retrieved distances: {distances}")
#         logger.info(f"Retrieved similarities: {similarities}")
        
#         return {
#             "documents": documents,
#             "metadatas": metadatas,
#             "similarities": similarities
#         }

#     # ======================================================
#     # GENERATION (STRICT GROQ PROMPT)
#     # ======================================================
#     async def generate_text(
#         self,
#         prompt: str,
#         retrieved: Dict,
#         max_tokens: int = 200,
#         temperature: float = 0.6
#     ) -> str:
#         documents = retrieved["documents"]
#         logger.info(f"Retrieved documents: {documents}")
#         if not documents:
#             return "Information not available in the document."

#         context = "\n\n".join(documents)
#         logger.info(f"Context: {context}")
#         if len(context.split()) < 40:
#             return "Information not available in the document."

#         system_prompt = (
#             "You are a helpful AI assistant for farmers named KisanVoice. "
#             "Answer the question strictly based on the provided CONTEXT. "
#             "If the answer is in the context, output it directly in the same language as the question."
#         )

#         user_prompt = f"""
# CONTEXT:
# {context}

# QUESTION:
# {prompt}

# ANSWER:
# """
#         # Clean and format prompt
#         if not prompt.strip().startswith("<user>"):
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ]
        
#         logger.info(f"Prompt Messages: {messages}")

#         inputs = self.tokenizer.apply_chat_template(
#             messages,
#             add_generation_prompt=True,
#             tokenize=True,
#             return_dict=True,
#             return_tensors="pt",
#         ).to(self.model.device)

#         if temperature > 0:
#             outputs = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=0.1, do_sample=True)
#         else:
#              outputs = self.model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
#         reply = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
#         logger.info(f"🗣️ Model Reply: {reply}")
#         return reply

#     # ======================================================
#     # CHAT
#     # ======================================================
#     async def chat(
#         self,
#         query: str,
#         top_k: int = 4,
#         show_context: bool = False
#     ) -> str:

#         retrieved = self.retrieve(query, top_k)
#         logger.info(f"Retrieved documents: {retrieved}")
#         answer = await self.generate_text(query, retrieved)
#         logger.info(f"Answer: {answer}")
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




# gemma_with_RAG_service = GemmaWithRAGServices()

# def get_gemma_with_RAG_service() -> GemmaWithRAGServices:
#     return gemma_with_RAG_service


# # ✅ Test Run
# async def test():
#     service = get_gemma_with_RAG_service()
#     json_path = Path(
#     r"/home/rospc/tanishq/RaithaMithra_v2/RaithaMithra/rag/final_clean_merged_dataset.json"
# )
#     #service.add_json(str(json_path))
#     query = "ಸಕ್ಕರೆಕಬ್ಬು ಬೆಳೆಯಲು ಸೂಕ್ತವಾದ ಮಣ್ಣು ಯಾವುದು? "
#     print(
#     await service.chat(
#         query,
#         show_context=True
#     )
# )


# if __name__ == "__main__":
#     st = time.time()
#     asyncio.run(test())
#     et = time.time()
#     print(et - st)