"""
Tool MCP untuk mencari skill dari Torampedia berdasarkan nama atau kata kunci.
Versi ini menampilkan semua data penting termasuk info.
"""

import requests
import traceback
from fastmcp import FastMCP

TORAMPEDIA_SKILL_API_URL = "https://torampedia.my.id/api/v1/skill/"

def register_search_skill_tool(server: FastMCP):
    @server.tool()
    async def search_skill(query: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

        import re
        if not query.strip():
            return {"success": False, "summary": "Query kosong. Masukkan nama skill."}
        if len(query) > 50:
            return {"success": False, "summary": "Query terlalu panjang. Maksimal 50 karakter."}
        if not re.match(r"^[a-zA-Z0-9\s\-]+$", query):
            return {"success": False, "summary": "Karakter tidak valid. Gunakan huruf, angka, spasi, atau tanda minus saja."}

        try:
            print(f"[MCP] Mencari skill: {query}")
            url = f"{TORAMPEDIA_SKILL_API_URL}{query}"
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", [])

            if not data:
                return {
                    "success": False,
                    "summary": f"Skill '{query}' tidak ditemukan di Torampedia."
                }

            filtered_data = []
            summary_lines = []

            for skill in data:
                filtered_skill = {
                    "id": skill.get("id"),
                    "name_id": skill.get("name_id", "N/A"),
                    "name_en": skill.get("name_en", "N/A"),
                    "type": skill.get("type", "N/A"),
                    "mp": skill.get("mp", "N/A"),
                    "combo_start": skill.get("combo_start"),
                    "combo_mid": skill.get("combo_mid"),
                    "element": skill.get("element", "N/A"),
                    "range": skill.get("range", "N/A"),
                    "tier": skill.get("tier", "N/A"),
                    "description": skill.get("desc_id", "N/A"), 
                    "info": skill.get("info", "N/A"),
                    "weapon": skill.get("weapon", []),
                    "parent": {
                        "id": skill.get("parent", {}).get("id"),
                        "name_id": skill.get("parent", {}).get("name_id", "N/A"),
                        "name_en": skill.get("parent", {}).get("name_en", "N/A")
                    },
                    "link": f"https://torampedia.my.id/skills/{skill.get('parent', {}).get('id', '')}"
                }
                filtered_data.append(filtered_skill)

                combo_text = []
                if skill.get("combo_start"): combo_text.append("Start")
                if skill.get("combo_mid"): combo_text.append("Mid")
                combo_str = ", ".join(combo_text) if combo_text else "N/A"

                summary_lines.append(
                    f"{filtered_skill['name_id']} ({filtered_skill['name_en']}) | "
                    f"Tipe: {filtered_skill['type']} | MP: {filtered_skill['mp']} | "
                    f"Range: {filtered_skill['range']}m | Elemen: {filtered_skill['element']} | "
                    f"Tier: {filtered_skill['tier']} | Combo: {combo_str} | "
                    f"Deskripsi: {filtered_skill['description']} | "
                    f"Info: {filtered_skill['info']} | "
                    f"Kategori: {filtered_skill['parent']['name_id']} ({filtered_skill['parent']['name_en']}) | "
                    f"Link: {filtered_skill['link']}"
                )

            summary = "\n".join(summary_lines)

            return {
                "success": True,
                "data": filtered_data,
                "summary": summary
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mencari skill: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "summary": "Gagal konek ke API Torampedia. Coba akses manual di https://torampedia.my.id/others/skill"
            }
