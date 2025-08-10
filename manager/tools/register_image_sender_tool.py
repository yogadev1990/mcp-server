"""
Tool MCP untuk mengirim gambar pendukung hasil pencarian Milvus via WhatsApp.
"""

import requests
import traceback
from fastmcp import FastMCP

WA_API_KEY = "lI54u2OFyfrRzHdXxkJ1JY0hSrMXaE"
WA_SENDER = "6281539302056"
WA_ENDPOINT = "https://revanetic.my.id/send-media"

def register_image_sender_tool(server: FastMCP):
    @server.tool()
    async def send_milvus_image(number: str, image_url: str, caption: str = "🖼️ Gambar pendukung hasil pencarian"):
        try:
            print(f"[MCP] Mengirim gambar ke {number}")
            payload = {
                "api_key": WA_API_KEY,
                "sender": WA_SENDER,
                "number": number,
                "url": image_url,
                "caption": caption,
                "media_type": "image"
            }

            print(f"[MCP] Payload:\n{payload}")
            r = requests.post(WA_ENDPOINT, json=payload, timeout=10)
            r.raise_for_status()

            print("[MCP] Gambar berhasil dikirim.")
            return {
                "success": True,
                "number": number,
                "image_url": image_url,
                "caption": caption,
                "summary": f"Gambar berhasil dikirim ke {number}"
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mengirim gambar: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal mengirim gambar ke WhatsApp"
            }
