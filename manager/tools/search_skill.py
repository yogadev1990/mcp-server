"""
Tool MCP untuk mencari skill dari Torampedia berdasarkan nama atau kata kunci.
Versi ini menggunakan summary yang ringkas dan hemat token untuk LLM.
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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        }
        try:
            print(f"[MCP] Mencari skill: {query}")
            url = f"{TORAMPEDIA_SKILL_API_URL}{query}"
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", [])

            if not data:
                print(f"[MCP] Skill '{query}' tidak ditemukan.")
                return {
                    "success": False,
                    "error": "Skill tidak ditemukan.",
                    "summary": f"Skill '{query}' tidak ditemukan di Torampedia."
                }

            summary_lines = []
            for skill in data:
                name_id = skill.get("name_id", "N/A")
                name_en = skill.get("name_en", "N/A")
                skill_type = skill.get("type", "N/A")
                mp = f"{skill.get('mp', 'N/A')} MP"
                range_ = f"{skill.get('range', 'N/A')}m"
                element = skill.get("element", "N/A")
                tier = skill.get("tier", "N/A")
                combo_parts = []
                if skill.get("combo_start"): combo_parts.append("Start")
                if skill.get("combo_mid"): combo_parts.append("Mid")
                combo_text = ", ".join(combo_parts) if combo_parts else "N/A"
                desc = skill.get("desc_id", "N/A")
                parent = skill.get("parent", {})
                category = f"{parent.get('name_id', 'N/A')} ({parent.get('name_en', 'N/A')})"
                link = f"https://torampedia.my.id/skills/{parent.get('id', '')}"

                summary_lines.append(
                    f"{name_id} ({name_en}) | Tipe: {skill_type} | MP: {mp} | Range: {range_} | Elemen: {element} | Tier: {tier} | Combo: {combo_text} | Kategori: {category} | Link: {link}"
                )

            summary = "\n".join(summary_lines)

            return {
                "success": True,
                "data": data,
                "summary": summary
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mencari skill: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal konek ke API Torampedia. Coba akses manual di https://torampedia.my.id/others/skill"
            }
