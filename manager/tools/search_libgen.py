"""
Tool MCP untuk mencari ebook dari Library Genesis berdasarkan judul/query.
Versi ini juga mengekstrak link download dari setiap hasil.
"""

import requests
import traceback
from bs4 import BeautifulSoup
from fastmcp import FastMCP

LIBGEN_JSON_API = "/json.php?object=e&addkeys=*&ids="


def get_download_link(md5: str, mirror: str) -> str:
    """Ambil link download dari halaman ads.php berdasarkan MD5"""
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


def register_libgen_search_tool(server: FastMCP):
    @server.tool()
    async def search_ebook(
        query: str,
        mirror: str = "https://libgen.li",
        count: int = 10
    ):
        """
        Cari ebook dari Library Genesis berdasarkan query.
        Argumen:
            query (str): Kata kunci pencarian.
            mirror (str): URL mirror Libgen (default: https://libgen.li).
            count (int): Jumlah hasil maksimal (default: 10).
        """

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        try:
            print(f"[MCP] Mencari ebook: {query}")
            search_url = f"{mirror}/index.php?req={query}&res={count}&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=y&columns%5B%5D=p"
            res = requests.get(search_url, headers=headers, timeout=10)
            res.raise_for_status()

            # parse HTML untuk ambil ID buku
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table", {"id": "tablelibgen"})
            ids = []

            if table:
                for row in table.find_all("tr")[1:]:  # skip header
                    link = row.find("a", href=True)
                    if link and "edition.php?id=" in link["href"]:
                        book_id = link["href"].split("=")[-1]
                        ids.append(book_id)
                        if len(ids) >= count:
                            break

            if not ids:
                return {
                    "success": False,
                    "error": "Tidak ada hasil ditemukan.",
                    "summary": f"Tidak ditemukan hasil untuk '{query}' di Libgen."
                }

            # fetch detail JSON
            json_url = f"{mirror}{LIBGEN_JSON_API}{','.join(ids)}"
            res_json = requests.get(json_url, headers=headers, timeout=10)
            res_json.raise_for_status()
            data = res_json.json()

            # ringkas hasil
            results = []
            summary_lines = []
            for item in data:
                title = item.get("title", "N/A")
                author = item.get("author", "N/A")
                publisher = item.get("publisher", "N/A")
                year = item.get("year", "N/A")
                pages = item.get("pages", "N/A")
                lang = item.get("language", "N/A")
                md5 = item.get("md5")

                download = get_download_link(md5, mirror) if md5 else "N/A"

                results.append({
                    "title": title,
                    "author": author,
                    "publisher": publisher,
                    "year": year,
                    "pages": pages,
                    "lang": lang,
                    "md5": md5,
                    "download": download,
                })

                summary_lines.append(
                    f"{title} | {author} | {publisher}, {year} | {pages} hlm | {lang} | {download}"
                )

            summary = "\n".join(summary_lines)

            return {
                "success": True,
                "data": results,
                "summary": summary
            }

        except Exception as e:
            print(f"[MCP] ERROR saat mencari ebook: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": "Gagal konek ke Libgen. Coba akses manual mirror Libgen."
            }
