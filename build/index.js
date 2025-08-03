"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const mcp_js_1 = require("@modelcontextprotocol/sdk/server/mcp.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const zod_1 = require("zod");
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const { WA_API_KEY, WA_SENDER, WA_OWNER_NUMBER, WA_ENDPOINT } = process.env;
const server = new mcp_js_1.McpServer({
    name: "wa_gateway",
    version: "1.0.0",
});
// Register WA Gateway tools
server.tool("send_message", "Send a WhatsApp message", {
    recipient: zod_1.z.string().describe("Recipient's phone number in international format"),
    message: zod_1.z.string().describe("Message content to send"),
}, async ({ recipient, message }) => {
    if (!WA_API_KEY || !WA_SENDER || !WA_ENDPOINT) {
        return {
            content: [
                {
                    type: "text",
                    text: "WA Gateway is not properly configured. Please check your environment variables.",
                },
            ],
        };
    }
    try {
        const response = await fetch(WA_ENDPOINT, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${WA_API_KEY}`,
            },
            body: JSON.stringify({
                sender: WA_SENDER,
                recipient,
                message,
            }),
        });
        if (!response.ok) {
            throw new Error(`Failed to send message. Status: ${response.status}`);
        }
        return {
            content: [
                {
                    type: "text",
                    text: `Message successfully sent to ${recipient}`,
                },
            ],
        };
    }
    catch (error) {
        console.error("Error sending message:", error);
        return {
            content: [
                {
                    type: "text",
                    text: `Failed to send message: ${error}`,
                },
            ],
        };
    }
});
server.tool("get_owner_info", "Get information about the WA Gateway owner", {}, async () => {
    if (!WA_OWNER_NUMBER) {
        return {
            content: [
                {
                    type: "text",
                    text: "Owner information is not configured. Please check your environment variables.",
                },
            ],
        };
    }
    return {
        content: [
            {
                type: "text",
                text: `WA Gateway Owner Number: ${WA_OWNER_NUMBER}`,
            },
        ],
    };
});
async function main() {
    const transport = new stdio_js_1.StdioServerTransport();
    await server.connect(transport);
    console.error("WA Gateway MCP Server running on stdio");
}
main().catch((error) => {
    console.error("Fatal error in main():", error);
    process.exit(1);
});
