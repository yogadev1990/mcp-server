"""
Tool MCP untuk pengecekan status order via API toko.
"""

import requests
import traceback
from fastmcp import FastMCP

WA_API_KEY = "lI54u2OFyfrRzHdXxkJ1JY0hSrMXaE"
WA_SENDER = "6281539302056"
WA_OWNER_NUMBER = "6285159199040"
WA_ENDPOINT = "https://revanetic.my.id/send-message"
ORDER_API_URL = "https://revandastore.com/api/payment/"

def register_order_checker_tool(server: FastMCP):
    @server.tool()
    async def check_order_status(order_id: str):
        headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        }
        try:
            print(f"[MCP] Memeriksa order ID: {order_id}")
            url = ORDER_API_URL + order_id
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()

            print(f"[MCP] Response dari API:\n{data}")

            if not data.get("success"):
                print(f"[MCP] Order ID {order_id} tidak ditemukan.")
                return {
                    "success": False,
                    "error": "Order tidak ditemukan.",
                    "summary": f"Order ID {order_id} tidak ditemukan."
                }

            status = data.get("status")
            provider = data.get("provider")
            product = data.get("product")
            message = data.get("keterangan")

            notify = False
            if provider == "Manual" and status == "Processing":
                msg = f"Pesanan manual:\nOrder ID: {order_id}\nProduk: {product}\nStatus: {status}"
                print("[MCP] Mengirim notifikasi WA untuk pesanan manual...")
                send_whatsapp(msg)
                notify = True
            elif status.lower() in ["canceled", "gagal", "error"]:
                msg = f"Pesanan error:\nOrder ID: {order_id}\nStatus: {status}"
                print("[MCP] Mengirim notifikasi WA untuk pesanan error...")
                send_whatsapp(msg)
                notify = True

            print("[MCP] Pemeriksaan selesai, mengembalikan hasil.")
            return {
                "success": True,
                "order_id": order_id,
                "status": status,
                "provider": provider,
                "product": product,
                "message": message,
                "notified_owner": notify,
                "summary": f"Order *{product}* berstatus *{status}* (provider: {provider})"
            }

        except Exception as e:
            print(f"[MCP] ERROR saat memeriksa order: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal konek ke API"
            }

def send_whatsapp(message: str):
    payload = {
        "api_key": WA_API_KEY,
        "sender": WA_SENDER,
        "number": WA_OWNER_NUMBER,
        "message": message
    }
    try:
        print(f"[MCP] Mengirim pesan WA ke owner:\n{payload}")
        r = requests.post(WA_ENDPOINT, json=payload, timeout=10)
        r.raise_for_status()
        print("[MCP] Pesan WA berhasil dikirim.")
        return {"success": True}
    except Exception as e:
        print(f"[MCP] Gagal mengirim WA: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}
