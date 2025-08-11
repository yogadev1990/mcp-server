"""
Tool MCP untuk mencari item dari Torampedia berdasarkan nama item.
Versi ini menggunakan summary yang ringkas dan hemat token untuk LLM.
"""

import requests
import traceback
from fastmcp import FastMCP

TORAMPEDIA_API_URL = "https://torampedia.my.id/api/v1/item/"

def register_search_item_tool(server: FastMCP):
    @server.tool()
    async def search_item(item_name: str):
        try:
            print(f"[MCP] Mencari item: {item_name}")
            url = f"{TORAMPEDIA_API_URL}{item_name}"
            res = requests.get(url, timeout=15)
            res.raise_for_status()
            data = res.json().get("data", [])

            if not data:
                print(f"[MCP] Item '{item_name}' tidak ditemukan.")
                return {
                    "success": False,
                    "error": "Item tidak ditemukan.",
                    "summary": f"Item '{item_name}' tidak ditemukan di Torampedia."
                }

            summary_lines = []
            for item in data:
                name_id = item.get("name_id", "N/A")
                name_en = item.get("name_en", "N/A")
                rarity = item.get("rarity", "N/A")
                sell_price = f"{item.get('sell_price', 'N/A')} Spina"
                proc = item.get("proc_to", "N/A")
                amount_price = f"{item.get('amount_price', '')} pt" if item.get("amount_price") else ""
                slug = item.get("slug", "")
                dropped_by = item.get("dropped_by", [])
                drop_names = ", ".join([m.get("name_id", "Unknown") for m in dropped_by]) if dropped_by else "N/A"

                summary_lines.append(
                    f"{name_id} ({name_en}) | Rarity: {rarity} | Harga: {sell_price} | Proses: {proc} {amount_price} | Drop: {drop_names} | Link: https://torampedia.my.id/item/{slug}"
                )

            summary = "\n".join(summary_lines)

            return {
                "success": True,
                "data": data,
                "summary": summary
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mencari item: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal konek ke API Torampedia. Coba akses manual di https://torampedia.my.id/items/all"
            }
