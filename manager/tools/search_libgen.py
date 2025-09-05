"""
MCP Tool: Search ebook di Library Genesis
- Cari berdasarkan judul/query
- Ambil detail metadata
- Tambahkan link download
"""

import traceback
import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP

server = FastMCP("libgen-tools")

LIBGEN_JSON_API = "/json.php?object=e&addkeys=*&ids="


def get_download_link(md5: str, mirror: str) -> str:
    """Ambil link download dari halaman ads.php?md5=..."""
    try:
        ads_url = f"{mirror}/ads.php?md5={md5}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(ads_url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        link_el = soup.select_one('a[href^="get.php?md5="]')
        if link_el:
            return f"{mirror}/{link_el['href']}"
        return f"Tidak ada link download (MD5={md5})"
    except Exception as e:
        return f"Error ambil link download: {e}"


@server.tool()
async def search_ebook(
    query: str,
    mirror: str = "https://libgen.li",
    count: int = 5
):
    """
    Cari ebook dari Library Genesis berdasarkan query.
    Argumen:
        query (str): Judul/kata kunci ebook.
        mirror (str): URL mirror Libgen (default: https://libgen.li).
        count (int): Jumlah hasil maksimal.
    """
    try:
        print(f"[MCP] Mencari ebook: {query}")
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        # 1. Cari ID dari index.php
        search_url = (
            f"{mirror}/index.php?req={query}&res={count}&view=detailed&column=def"
        )
        res = requests.get(search_url, headers=headers, timeout=15)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", {"id": "tablelibgen"})
        ids = []

        if table:
            for row in table.find_all("tr")[1:]:
                link = row.find("a", href=True)
                if link and "edition.php?id=" in link["href"]:
                    ids.append(link["href"].split("=")[-1])
                if len(ids) >= count:
                    break

        if not ids:
            return {
                "success": False,
                "summary": f"Tidak ada hasil untuk '{query}'",
                "data": []
            }

        # 2. Ambil detail via JSON API
        json_url = f"{mirror}{LIBGEN_JSON_API}{','.join(ids)}"
        res_json = requests.get(json_url, headers=headers, timeout=15)
        res_json.raise_for_status()
        data = res_json.json()

        results = []
        for item in data:
            if not isinstance(item, dict):
                continue

            md5 = item.get("md5")
            download = get_download_link(md5, mirror) if md5 else "N/A"

            results.append({
                "title": item.get("title"),
                "author": item.get("author"),
                "publisher": item.get("publisher"),
                "year": item.get("year"),
                "pages": item.get("pages"),
                "lang": item.get("language"),
                "md5": md5,
                "download": download,
            })

        # 3. Ringkasan singkat
        summary = "\n".join(
            [f"{r['title']} | {r['author']} | {r['year']} | {r['download']}" for r in results]
        )

        return {
            "success": True,
            "summary": summary,
            "data": results
        }

    except Exception as e:
        print(f"[MCP] ERROR search_ebook: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "summary": "Gagal konek ke Libgen"
        }