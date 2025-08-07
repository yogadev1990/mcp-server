"""
Tool MCP untuk mengambil detail katalog dari API toko berdasarkan ID.
"""

import requests
import traceback
from fastmcp import FastMCP

KATALOG_API_URL = "https://revandastore.com/api/katalog/"

def register_katalog_tool(server: FastMCP):
    @server.tool()
    async def get_katalog_by_id(katalog_id: int):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

        try:
            print(f"[MCP] Mengambil katalog ID: {katalog_id}")
            url = f"{KATALOG_API_URL}{katalog_id}"
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()

            print(f"[MCP] Response dari API:\n{data}")

            if not data.get("id"):
                print(f"[MCP] Katalog ID {katalog_id} tidak ditemukan.")
                return {
                    "success": False,
                    "error": "Katalog tidak ditemukan.",
                    "summary": f"Katalog ID {katalog_id} tidak ditemukan."
                }

            summary = f"Katalog *{data.get('title')}* seharga *Rp{data.get('price')}* (Kategori: {data.get('category')})"
            return {
                "success": True,
                "data": {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "price": data.get("price"),
                    "category": data.get("category"),
                    "description": data.get("description"),
                },
                "summary": summary
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mengambil katalog: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal konek ke API katalog"
            }
