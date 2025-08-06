"""
Tool MCP untuk pengecekan status order via API toko.
"""

import requests
from fastmcp import FastMCP

WA_API_KEY = "lI54u2OFyfrRzHdXxkJ1JY0hSrMXaE"
WA_SENDER = "6281539302056"
WA_OWNER_NUMBER = "6285159199040"
WA_ENDPOINT = "https://revanetic.my.id/send-message"
ORDER_API_URL = "https://revandastore.com/api/payment/"

def register_order_checker_tool(server: FastMCP):
    @server.tool()
    async def check_order_status(order_id: str):
        try:
            url = ORDER_API_URL + order_id
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()

            if not data.get("success"):
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
                send_whatsapp(msg)
                notify = True
            elif status.lower() in ["canceled", "gagal", "error"]:
                msg = f"Pesanan error:\nOrder ID: {order_id}\nStatus: {status}"
                send_whatsapp(msg)
                notify = True

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
        r = requests.post(WA_ENDPOINT, json=payload, timeout=10)
        r.raise_for_status()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
