"""
Tool MCP untuk melakukan pencarian referensi di Milvus menggunakan embedding dari Gemini.
"""

import os
import traceback
from fastmcp import FastMCP
from pymilvus import connections, Collection
import requests

# Konfigurasi environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA-jiUJ8ybILbppB5FuLVU9upcF_Zx5qek")
MILVUS_HOST = os.getenv("MILVUS_HOST", "146.235.207.145")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "multi_modal_rag")

# Koneksi Milvus
connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
collection = Collection(COLLECTION_NAME)

def get_embedding(text: str):
    """
    Meminta embedding dari Google Gemini API.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={GEMINI_API_KEY}"

    payload = {
        "model": "models/embedding-001",
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": "RETRIEVAL_QUERY"
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data["embedding"]["values"]
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Error saat membuat embedding: {e}")

def register_vector_search_tool(server: FastMCP):
    @server.tool()
    async def search_vector_db(query: str, top_k: int = 5):
        """
        Cari referensi dari Milvus berdasarkan query.
        """
        try:
            # 1. Buat embedding query
            embedding = get_embedding(query)

            # 2. Search ke Milvus
            search_results = collection.search(
                data=[embedding],
                anns_field="embedding",   # sesuaikan dengan nama field embedding di collection
                param={"metric_type": "IP", "params": {"nprobe": 10}},
                limit=top_k,
                output_fields=["text", "source_file", "type", "doc_id"]
            )

            # 3. Format hasil
            formatted = []
            for hits in search_results:
                for item in hits:
                    row = item.entity.get("text", "")
                    formatted.append({
                        "id": item.entity.get("doc_id", ""),
                        "text": row,
                        "source_file": item.entity.get("source_file", ""),
                        "type": item.entity.get("type", ""),
                        "score": float(item.distance)
                    })

            return {
                "success": True,
                "query": query,
                "results": formatted,
                "summary": f"{len(formatted)} hasil ditemukan untuk query: {query}"
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}
