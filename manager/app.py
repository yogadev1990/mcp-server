#!/usr/bin/env python3
"""
MCP Server Manager - Menampung dan mengelola tools MCP via Flask
"""

from flask import Flask
from tools.order_checker import register_order_checker_tool
from tools.katalog_tool import register_katalog_tool
from tools.register_image_sender_tool import register_image_sender_tool



from fastmcp import FastMCP

app = Flask(__name__)

# Konfigurasi MCP Server Manager
server = FastMCP(
    name="MCP Server Manager",
    instructions="Server ini mengelola berbagai tools MCP."
)

# Register semua tools MCP
register_order_checker_tool(server)
register_katalog_tool(server)
register_image_sender_tool(server)

@app.route("/")
def index():
    return {
        "status": "running",
        "tools": list(server.tools.keys()),
        "instructions": server.instructions
    }

if __name__ == "__main__":
    server.run(transport="sse", host="0.0.0.0", port=2005)
