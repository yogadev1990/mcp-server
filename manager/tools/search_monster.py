"""
Tool MCP untuk mencari monster dari Torampedia berdasarkan nama monster.
Versi ini menggunakan summary yang ringkas namun mencakup semua data penting.
"""

import requests
import traceback
from fastmcp import FastMCP

TORAMPEDIA_MONSTER_API_URL = "https://torampedia.my.id/api/v1/monster/"

def register_search_monster_tool(server: FastMCP):
    @server.tool()
    async def search_monster(monster_name: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        try:
            print(f"[MCP] Mencari monster: {monster_name}")
            url = f"{TORAMPEDIA_MONSTER_API_URL}{monster_name}"
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", [])

            if not data:
                print(f"[MCP] Monster '{monster_name}' tidak ditemukan.")
                return {
                    "success": False,
                    "error": "Monster tidak ditemukan.",
                    "summary": f"Monster '{monster_name}' tidak ditemukan di Torampedia."
                }

            summary_lines = []
            for monster in data:
                name_id = monster.get("name_id", "N/A")
                name_en = monster.get("name_en", "N/A")
                level = monster.get("level", "N/A")
                type_ = monster.get("type", "N/A")
                element = monster.get("element", "N/A")
                exp = monster.get("exp", "0")
                hp = monster.get("hp", "0")
                mode = monster.get("mode", "N/A")
                is_tamable = "Ya" if monster.get("is_tamable") else "Tidak"
                info = monster.get("info", "N/A")

                map_name = (
                    monster.get("map", {}).get("name_en")
                    or monster.get("map", {}).get("name_id", "N/A")
                )

                drops = monster.get("items", [])
                drop_names = ", ".join([
                    item.get("name_en") or item.get("name_id", "Unknown")
                    for item in drops
                ]) if drops else "N/A"

                monster_id = monster.get("id", "")

                summary_lines.append(
                    f"{name_id} ({name_en}) | Tipe: {type_} | Lv: {level} | Elemen: {element} | Mode: {mode} | Exp: {exp} | HP: {hp} | Lokasi: {map_name} | Tameable: {is_tamable} | Info: {info} | Drop: {drop_names} | Link: https://torampedia.my.id/monster/{monster_id}"
                )

            summary = "\n".join(summary_lines)

            return {
                "success": True,
                "data": data,
                "summary": summary
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mencari monster: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal konek ke API Torampedia. Coba akses manual di https://torampedia.my.id/monsters/all"
            }
