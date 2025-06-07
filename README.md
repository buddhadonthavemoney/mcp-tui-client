# MCP Client TUI

A Terminal User Interface (TUI) for connecting to Model Context Protocol (MCP) servers with Google Gemini integration. This client enables Gemini to use tools from MCP servers through a clean chat interface.

## What This Is

This is an **MCP client** - it connects to existing MCP servers (made by others) and lets you chat with Gemini while giving it access to tools from those servers. Think of it as a bridge between Gemini and MCP servers.

## Key Features

- 🤖 **Gemini Chat Interface** with tool calling support
- 🔧 **MCP Server Integration** - connects to any MCP server
- 🔄 **Multi-step Tool Execution** - Gemini can chain tool calls automatically  
- 💬 **Clean TUI** built with Textual framework
- ⌨️ **Keyboard Shortcuts** for efficient navigation
- 📊 **Server Monitoring** - view connected servers and available tools

## How It Works

1. You configure which MCP servers to connect to
2. The client starts those servers and discovers their tools
3. You chat with Gemini through the TUI
4. Gemini can call tools from connected MCP servers
5. Results are sent back to Gemini to continue the conversation

For example: Ask "list my files" → Gemini calls filesystem server tools → Gets results → Presents them to you

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 3. Set Up MCP Servers (Optional)
Run the setup script to configure some basic servers:
```bash
python setup_mcp_servers.py
```

Or manually edit `mcp_servers.json` to add your own servers.

### 4. Run the Client
```bash
python main.py
```

## Configuration

### MCP Servers
Configure servers in `mcp_servers.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro  # optional, defaults to gemini-pro
```

## Usage

### Keyboard Shortcuts
- **Enter**: Send message
- **Ctrl+C**: Quit
- **Ctrl+L**: Clear chat
- **Ctrl+S**: Show server status  
- **Ctrl+T**: Show available tools

### Example Usage
```
You: "read my config file"
Gemini: [calls read_file tool → presents contents]

You: "remember I like Python"  
Gemini: [calls memory server → stores information]

You: "what files are in my home directory?"
Gemini: [calls list_directory → shows file listing]
```

## What MCP Servers Can You Connect To?

This client works with any MCP server. Popular ones include:

- **Filesystem servers** - file operations
- **Memory servers** - persistent knowledge graphs  
- **Database servers** - SQL operations
- **Web servers** - fetch content, search
- **Git servers** - repository operations
- **API servers** - various external services

Find servers at: https://github.com/modelcontextprotocol/servers

## Technical Details

- **JSON-RPC 2.0** communication with MCP servers
- **Subprocess management** for server lifecycle
- **Tool calling loop** that sends results back to Gemini
- **Error handling** and connection recovery

## Project Structure

```
├── main.py              # Main TUI application  
├── mcp_client.py        # MCP client implementation
├── setup_mcp_servers.py # Helper to set up basic servers
├── styles.css           # TUI styling
├── requirements.txt     # Dependencies
└── mcp_servers.json     # Server configuration
```

## Troubleshooting

**API Key Issues:**
```bash
echo $GEMINI_API_KEY  # Check if set
cat .env              # Verify .env file
```

**Server Issues:**
```bash
# Test if servers work independently
npx -y @modelcontextprotocol/server-filesystem --help

# Check server status in app with Ctrl+S
```

**Connection Issues:**
- Ensure internet access for Gemini API
- Verify Node.js installed for npm-based servers
- Check server logs for errors

## Contributing

This is an MCP client implementation. PRs welcome for:
- Better error handling
- UI improvements  
- Additional client features
- Documentation improvements

## License

MIT License - see LICENSE file.