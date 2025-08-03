#!/usr/bin/env node

import express from 'express';
import cors from 'cors';
import { z } from 'zod';

// WhatsApp Gateway configuration
const WA_GATEWAY_CONFIG = {
  endpoint: "https://revanetic.my.id/send-message",
  api_key: "lI54u2OFyfrRzHdXxkJ1JY0hSrMXaE", // Ganti dengan API key Anda
  sender: "6281539302056", // Ganti dengan nomor sender Anda
  owner_number: "6285159199040", // Ganti dengan nomor owner/penerima
};

const SERVER_CONFIG = {
  port: parseInt(process.env.PORT || '8000', 10),
  host: process.env.HOST || '0.0.0.0',
};

// Message history storage (in production, use proper database)
interface MessageHistory {
  message: string;
  target: string;
  timestamp: string;
  status: 'sent' | 'failed' | 'error';
  response?: any;
  error?: string;
}

const messageHistory: MessageHistory[] = [];

// MCP Tool Definitions
interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, any>;
    required: string[];
  };
}

interface MCPSearchResult {
  id: string;
  title: string;
  text: string;
  url: string;
}

interface MCPFetchResult {
  id: string;
  title: string;
  text: string;
  url: string;
  metadata?: Record<string, any>;
}

interface SendMessageRequest {
  api_key: string;
  sender: string;
  number: string;
  message: string;
}

// Validation schemas
const SearchSchema = z.object({
  query: z.string().min(1, "Query cannot be empty"),
});

const FetchSchema = z.object({
  id: z.string().min(1, "ID cannot be empty"),
});

class WhatsAppMCPServer {
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
        config: {
          endpoint: WA_GATEWAY_CONFIG.endpoint,
          sender: WA_GATEWAY_CONFIG.sender,
          owner: WA_GATEWAY_CONFIG.owner_number,
        }
      });
    });

    // MCP Server-Sent Events endpoint (required for ChatGPT)
    this.app.get('/sse', (req, res) => {
      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control',
      });

      // Send server info
      const serverInfo = {
        type: 'server_info',
        data: {
          name: 'WhatsApp Gateway MCP Server',
          version: '1.0.0',
          capabilities: ['search', 'fetch'],
          description: 'WhatsApp messaging capabilities for ChatGPT integration'
        }
      };

      res.write(`data: ${JSON.stringify(serverInfo)}\n\n`);

      // Handle MCP tool calls via SSE
      req.on('close', () => {
        console.log('SSE connection closed');
      });

      // Keep connection alive
      const keepAlive = setInterval(() => {
        res.write(`data: ${JSON.stringify({ type: 'ping', timestamp: Date.now() })}\n\n`);
      }, 30000);

      req.on('close', () => {
        clearInterval(keepAlive);
      });
    });

    // MCP Tools endpoint
    this.app.get('/tools', (req, res) => {
      const tools: MCPTool[] = [
        {
          name: "search",
          description: "Search WhatsApp capabilities and message history",
          inputSchema: {
            type: "object",
            properties: {
              query: {
                type: "string",
                description: "Search query for WhatsApp operations or message history"
              }
            },
            required: ["query"]
          }
        },
        {
          name: "fetch",
          description: "Execute WhatsApp operations or retrieve detailed information",
          inputSchema: {
            type: "object",
            properties: {
              id: {
                type: "string",
                description: "Operation ID or capability identifier"
              }
            },
            required: ["id"]
          }
        }
      ];

      res.json({ tools });
    });

    // MCP Tool execution endpoint
    this.app.post('/tools/call', async (req, res) => {
      try {
        const { name, arguments: args } = req.body;

        if (name === 'search') {
          const { query } = SearchSchema.parse(args);
          const result = await this.handleSearch(query);
          res.json({ content: [{ type: 'text', text: JSON.stringify(result) }] });
        } else if (name === 'fetch') {
          const { id } = FetchSchema.parse(args);
          const result = await this.handleFetch(id);
          res.json({ content: [{ type: 'text', text: JSON.stringify(result) }] });
        } else {
          throw new Error(`Unknown tool: ${name}`);
        }
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

    // Direct endpoints for testing
    this.app.post('/search', async (req, res) => {
      try {
        const { query } = SearchSchema.parse(req.body);
        const result = await this.handleSearch(query);
        res.json(result);
      } catch (error) {
        res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
      }
    });

    this.app.post('/fetch', async (req, res) => {
      try {
        const { id } = FetchSchema.parse(req.body);
        const result = await this.handleFetch(id);
        res.json(result);
      } catch (error) {
        res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
      }
    });

    // Legacy endpoints (for backward compatibility)
    this.app.post('/send-to-owner', async (req, res) => {
      try {
        const { message } = req.body;
        if (!message) {
          return res.status(400).json({ success: false, message: "Message required" });
        }

        const result = await this.sendWhatsAppMessage(message);
        res.json({
          success: true,
          message: "Message sent to owner",
          data: result
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          message: error instanceof Error ? error.message : String(error)
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
          'GET /sse',
          'GET /tools',
          'POST /tools/call',
          'POST /search',
          'POST /fetch',
          'POST /send-to-owner',
        ],
      });
    });
  }

  private async handleSearch(query: string): Promise<{ results: MCPSearchResult[] }> {
    console.log(`Searching WhatsApp capabilities for query: '${query}'`);
    
    const results: MCPSearchResult[] = [];
    const queryLower = query.toLowerCase();
    
    // Search capabilities
    const capabilities = [
      {
        id: "send_to_owner",
        title: "Send Message to Owner",
        description: "Send WhatsApp message to the predefined owner number",
        keywords: ["send", "owner", "notification", "alert", "message"]
      },
      {
        id: "send_to_number",
        title: "Send Message to Specific Number", 
        description: "Send WhatsApp message to any specified phone number",
        keywords: ["send", "number", "custom", "specific", "phone"]
      },
      {
        id: "gateway_status",
        title: "Gateway Status",
        description: "Check WhatsApp gateway configuration and status",
        keywords: ["status", "config", "gateway", "health", "check"]
      }
    ];
    
    // Search in capabilities
    for (const capability of capabilities) {
      if (queryLower.includes(capability.title.toLowerCase()) ||
          queryLower.includes(capability.description.toLowerCase()) ||
          capability.keywords.some(keyword => queryLower.includes(keyword))) {
        
        results.push({
          id: capability.id,
          title: capability.title,
          text: capability.description,
          url: `whatsapp://capability/${capability.id}`
        });
      }
    }
    
    // Search in message history
    const recentMessages = messageHistory.slice(-10); // Last 10 messages
    for (let i = 0; i < recentMessages.length; i++) {
      const msg = recentMessages[i];
      if (msg.message.toLowerCase().includes(queryLower)) {
        results.push({
          id: `msg_${i}`,
          title: `Message to ${msg.target}`,
          text: msg.message.length > 100 ? msg.message.substring(0, 100) + "..." : msg.message,
          url: `whatsapp://message/${i}`
        });
      }
    }
    
    // If no specific matches, provide general capabilities
    if (results.length === 0) {
      results.push({
        id: "help",
        title: "WhatsApp Gateway Help",
        text: "Available operations: send messages to owner, send to specific numbers, check status",
        url: "whatsapp://help"
      });
    }
    
    console.log(`WhatsApp search returned ${results.length} results`);
    return { results };
  }

  private async handleFetch(id: string): Promise<MCPFetchResult> {
    console.log(`Executing WhatsApp operation: ${id}`);
    
    // Handle different operation types
    if (id === "send_to_owner") {
      return {
        id,
        title: "Send Message to Owner",
        text: `Send WhatsApp Message to Owner

Configuration:
- Owner Number: ${WA_GATEWAY_CONFIG.owner_number}
- Gateway: ${WA_GATEWAY_CONFIG.endpoint}
- Sender: ${WA_GATEWAY_CONFIG.sender}

To send a message, provide the message content and this operation will
deliver it to the owner via WhatsApp gateway.

Usage: Specify message content to send notification to owner.`,
        url: "whatsapp://send_to_owner",
        metadata: {
          operation: "send_message",
          target: "owner",
          requires_message: true
        }
      };
    }
    
    if (id === "send_to_number") {
      return {
        id,
        title: "Send Message to Specific Number",
        text: `Send WhatsApp Message to Specific Number

Configuration:
- Gateway: ${WA_GATEWAY_CONFIG.endpoint}
- Sender: ${WA_GATEWAY_CONFIG.sender}

This operation allows sending WhatsApp messages to any phone number.
Phone numbers should be in international format (e.g., 628xxxxxxxxx).

Usage: Specify target number and message content.`,
        url: "whatsapp://send_to_number",
        metadata: {
          operation: "send_message",
          target: "custom", 
          requires_message: true,
          requires_number: true
        }
      };
    }
    
    if (id === "gateway_status") {
      return {
        id,
        title: "Gateway Status",
        text: `WhatsApp Gateway Status

Endpoint: ${WA_GATEWAY_CONFIG.endpoint}
API Key: ${'*'.repeat(WA_GATEWAY_CONFIG.api_key.length - 4)}${WA_GATEWAY_CONFIG.api_key.slice(-4)}
Sender: ${WA_GATEWAY_CONFIG.sender}
Owner: ${WA_GATEWAY_CONFIG.owner_number}

Gateway is configured and ready to send messages.
Total messages sent: ${messageHistory.length}`,
        url: "whatsapp://status",
        metadata: {
          status: "active",
          messages_sent: messageHistory.length,
          last_message: messageHistory[messageHistory.length - 1] || null
        }
      };
    }
    
    // Handle message history
    if (id.startsWith("msg_")) {
      const msgIndex = parseInt(id.split("_")[1]);
      if (msgIndex >= 0 && msgIndex < messageHistory.length) {
        const msg = messageHistory[msgIndex];
        return {
          id,
          title: `Message to ${msg.target}`,
          text: `Message Details:
Target: ${msg.target}
Message: ${msg.message}
Timestamp: ${msg.timestamp}
Status: ${msg.status}`,
          url: `whatsapp://message/${msgIndex}`,
          metadata: msg
        };
      }
    }
    
    // Handle direct send operations
    if (id.startsWith("send:")) {
      const parts = id.split(":", 3);
      if (parts.length >= 2) {
        const message = parts[1];
        const targetNumber = parts.length > 2 ? parts[2] : undefined;
        
        const result = await this.sendWhatsAppMessage(message, targetNumber);
        
        return {
          id,
          title: "WhatsApp Message Sent", 
          text: `Message: ${message}\nTarget: ${targetNumber || 'owner'}\nResult: ${JSON.stringify(result, null, 2)}`,
          url: "whatsapp://sent",
          metadata: result
        };
      }
    }
    
    // Default help response
    return {
      id: "help",
      title: "WhatsApp Gateway Help",
      text: `Available Operations:
1. send_to_owner - Send message to predefined owner
2. send_to_number - Send message to specific number
3. gateway_status - Check gateway configuration  
4. send:MESSAGE:NUMBER - Direct send operation

Message History: Access recent messages via msg_X IDs

To send a message, use format: send:Your message here:62888123456
Or just use send:Your message here (sends to owner)`,
      url: "whatsapp://help",
      metadata: {
        available_operations: ["send_to_owner", "send_to_number", "gateway_status"],
        direct_send_format: "send:MESSAGE:NUMBER"
      }
    };
  }

  private async sendWhatsAppMessage(message: string, targetNumber?: string): Promise<any> {
    const target = targetNumber || WA_GATEWAY_CONFIG.owner_number;
    
    const payload: SendMessageRequest = {
      api_key: WA_GATEWAY_CONFIG.api_key,
      sender: WA_GATEWAY_CONFIG.sender,
      number: target,
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

      const result = await response.json();
      
      // Store in message history
      const historyEntry: MessageHistory = {
        message,
        target,
        timestamp: new Date().toISOString(),
        status: response.ok ? 'sent' : 'failed',
        response: result
      };
      messageHistory.push(historyEntry);
      
      console.log(`WhatsApp message sent to ${target}: ${message}`);
      return result;
      
    } catch (error) {
      const errorEntry: MessageHistory = {
        message,
        target,
        timestamp: new Date().toISOString(),
        status: 'error',
        error: error instanceof Error ? error.message : String(error)
      };
      messageHistory.push(errorEntry);
      
      console.error("Error sending WhatsApp message:", error);
      throw error;
    }
  }

  public start() {
    // Validate configuration
    const requiredVars = ['WA_GATEWAY_API_KEY', 'WA_GATEWAY_SENDER', 'WA_GATEWAY_OWNER'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
      console.warn(`⚠️  Missing environment variables: ${missingVars.join(', ')}`);
      console.info('Using default configuration - please set proper values');
    }

    this.app.listen(SERVER_CONFIG.port, SERVER_CONFIG.host, () => {
      console.log(`🚀 WhatsApp Gateway MCP Server running on http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}`);
      console.log(`📱 Health check: http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/health`);
      console.log(`🔗 SSE endpoint: http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/sse/`);
      console.log(`🛠️  Tools endpoint: http://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/tools`);
      console.log(`📨 Gateway: ${WA_GATEWAY_CONFIG.endpoint}`);
      console.log(`👤 Owner: ${WA_GATEWAY_CONFIG.owner_number}`);
      console.log('');
      console.log('💡 For ChatGPT integration, use: http://your-domain.com:8000/sse/');
    });
  }
}

// Main execution
async function main() {
  const server = new WhatsAppMCPServer();
  server.start();
}

// Handle process termination
process.on("SIGINT", () => {
  console.log("\n🛑 Shutting down server...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\n🛑 Shutting down server...");
  process.exit(0);
});

main().catch((error) => {
  console.error("❌ Server error:", error);
  process.exit(1);
});

export { WhatsAppMCPServer };