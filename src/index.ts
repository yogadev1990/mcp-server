#!/usr/bin/env node

import express from 'express';
import cors from 'cors';
import { z } from 'zod';

// Configuration
const WA_GATEWAY_CONFIG = {
  endpoint: "https://revanetic.my.id/send-message",
  api_key: "lI54u2OFyfrRzHdXxkJ1JY0hSrMXaE", // Ganti dengan API key Anda
  sender: "6281539302056", // Ganti dengan nomor sender Anda
  owner_number: "6285159199040", // Ganti dengan nomor owner/penerima
};

const SERVER_CONFIG = {
  port: parseInt(process.env.PORT || '3000', 10),
  host: process.env.HOST || '0.0.0.0',
};

interface SendMessageRequest {
  api_key: string;
  sender: string;
  number: string;
  message: string;
}

interface MCPToolCall {
  name: string;
  arguments: {
    message: string;
    number?: string;
  };
}

interface MCPResponse {
  content: Array<{
    type: string;
    text: string;
  }>;
  isError?: boolean;
}

// Validation schemas
const SendMessageSchema = z.object({
  message: z.string().min(1, "Pesan tidak boleh kosong"),
  number: z.string().optional(),
});

const MCPToolCallSchema = z.object({
  name: z.string(),
  arguments: z.object({
    message: z.string(),
    number: z.string().optional(),
  }),
});

class WhatsAppGatewayHTTPServer {
  private app: express.Application;

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Logging middleware
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
      next();
    });
  }

  private setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        service: 'WhatsApp Gateway MCP Server',
      });
    });

    // MCP Tools List
    this.app.get('/tools', (req, res) => {
      res.json({
        tools: [
          {
            name: "send_wa_message",
            description: "Mengirim pesan WhatsApp ke owner melalui gateway",
            inputSchema: {
              type: "object",
              properties: {
                message: {
                  type: "string",
                  description: "Pesan yang akan dikirim ke owner",
                },
                number: {
                  type: "string",
                  description: "Nomor tujuan (opsional, default ke owner)",
                },
              },
              required: ["message"],
            },
          },
        ],
      });
    });

    // Direct send message endpoint
    this.app.post('/send', async (req, res) => {
      try {
        const { message, number } = SendMessageSchema.parse(req.body);
        const targetNumber = number || WA_GATEWAY_CONFIG.owner_number;
        
        const result = await this.sendWhatsAppMessage(message, targetNumber);
        
        res.json({
          success: true,
          message: "Pesan berhasil dikirim",
          data: {
            target: targetNumber,
            message: message,
            response: result,
          },
        });
      } catch (error) {
        console.error('Error sending message:', error);
        res.status(400).json({
          success: false,
          message: error instanceof Error ? error.message : String(error),
        });
      }
    });

    // MCP Tool Call endpoint
    this.app.post('/tools/call', async (req, res) => {
      try {
        const toolCall = MCPToolCallSchema.parse(req.body);
        const response = await this.handleToolCall(toolCall);
        res.json(response);
      } catch (error) {
        console.error('Error handling tool call:', error);
        res.status(400).json({
          content: [
            {
              type: "text",
              text: `❌ Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        });
      }
    });

    // Send to owner shortcut
    this.app.post('/send-to-owner', async (req, res) => {
      try {
        const { message } = req.body;
        
        if (!message) {
          return res.status(400).json({
            success: false,
            message: "Pesan tidak boleh kosong",
          });
        }

        const result = await this.sendWhatsAppMessage(message, WA_GATEWAY_CONFIG.owner_number);
        
        res.json({
          success: true,
          message: "Pesan berhasil dikirim ke owner",
          data: {
            target: WA_GATEWAY_CONFIG.owner_number,
            message: message,
            response: result,
          },
        });
      } catch (error) {
        console.error('Error sending message to owner:', error);
        res.status(500).json({
          success: false,
          message: error instanceof Error ? error.message : String(error),
        });
      }
    });

    // Error handler
    this.app.use((error: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
      console.error('Unhandled error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    });

    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({
        success: false,
        message: 'Endpoint not found',
        availableEndpoints: [
          'GET /health',
          'GET /tools',
          'POST /send',
          'POST /tools/call',
          'POST /send-to-owner',
        ],
      });
    });
  }

  private async handleToolCall(toolCall: MCPToolCall): Promise<MCPResponse> {
    if (toolCall.name === "send_wa_message") {
      try {
        const { message, number } = toolCall.arguments;
        const targetNumber = number || WA_GATEWAY_CONFIG.owner_number;

        if (!message) {
          throw new Error("Pesan tidak boleh kosong");
        }

        const result = await this.sendWhatsAppMessage(message, targetNumber);
        
        return {
          content: [
            {
              type: "text",
              text: `✅ Pesan berhasil dikirim ke ${targetNumber}\n\nPesan: ${message}\n\nResponse: ${JSON.stringify(result, null, 2)}`,
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `❌ Gagal mengirim pesan: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    throw new Error(`Tool tidak dikenal: ${toolCall.name}`);
  }

  private async sendWhatsAppMessage(message: string, targetNumber: string): Promise<any> {
    const payload: SendMessageRequest = {
      api_key: WA_GATEWAY_CONFIG.api_key,
      sender: WA_GATEWAY_CONFIG.sender,
      number: targetNumber,
      message: message,
    };

    try {
      const response = await fetch(WA_GATEWAY_CONFIG.endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error("Error sending WhatsApp message:", error);
      throw error;
    }
  }

  public start() {
    this.app.listen(SERVER_CONFIG.port, SERVER_CONFIG.host, () => {
      console.log(`🚀 WhatsApp Gateway MCP Server running on http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}`);
      console.log(`📱 Health check: http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/health`);
      console.log(`🛠️  Tools endpoint: http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/tools`);
      console.log(`📨 Send message: POST http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/send`);
      console.log(`👤 Send to owner: POST http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/send-to-owner`);
    });
  }
}

// Main execution
async function main() {
  const server = new WhatsAppGatewayHTTPServer();
  server.start();
}

// Handle process termination
process.on("SIGINT", async () => {
  console.log("\n🛑 Shutting down server...");
  process.exit(0);
});

process.on("SIGTERM", async () => {
  console.log("\n🛑 Shutting down server...");
  process.exit(0);
});

// Always run the server when this file is executed directly
main().catch((error) => {
  console.error("❌ Server error:", error);
  process.exit(1);
});

export { WhatsAppGatewayHTTPServer };