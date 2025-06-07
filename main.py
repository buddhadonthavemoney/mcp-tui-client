#!/usr/bin/env python3
"""
MCP Client TUI - A Terminal User Interface for Model Context Protocol
Direct communication with Google Gemini and MCP servers
"""

import os
import asyncio
import json
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

import google.generativeai as genai
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Input, RichLog, Button, Static, Label
)
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv

from mcp_client import MCPClient

# Load environment variables
load_dotenv()

class MCPClientApp(App):
    """MCP Client TUI Application"""
    
    TITLE = "MCP Client - Gemini + MCP Servers"
    CSS_PATH = "styles.css"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear Chat"),
        Binding("ctrl+s", "show_servers", "Show Servers"),
        Binding("ctrl+t", "show_tools", "Show Tools"),
        Binding("enter", "send_message", "Send", key_display="Enter"),
    ]
    
    def __init__(self):
        super().__init__()
        self.gemini_model: Optional[genai.GenerativeModel] = None
        self.chat_session = None
        self.mcp_servers: Dict[str, Dict[str, Any]] = {}
        self.mcp_client = MCPClient(logger=self.log_message)
        # Don't setup Gemini here - wait for on_mount when UI is ready
    
    def setup_gemini(self):
        """Initialize Gemini AI model"""
        api_key = os.getenv('GEMINI_API_KEY')
        model = os.getenv('GEMINI_MODEL', 'gemini-pro')
        if not api_key:
            self.log_message("❌ Error: GEMINI_API_KEY not found in environment variables", "error")
            self.log_message("Please set your Gemini API key in a .env file or environment variable", "info")
            return
        
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(model)
            self.chat_session = self.gemini_model.start_chat()
            self.log_message(f"✅ Connected to {model}", "success")
        except Exception as e:
            self.log_message(f"❌ Failed to initialize Gemini: {str(e)}", "error")
    
    def load_mcp_config(self):
        """Load MCP server configuration"""
        # Check for MCP configuration file
        config_paths = [
            "mcp_servers.json",
            os.path.expanduser("~/.config/mcp/servers.json"),
            os.path.expanduser("~/claude_desktop_config.json")
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    # Extract MCP servers configuration
                    if "mcpServers" in config:
                        self.mcp_servers = config["mcpServers"]
                        self.log_message(f"📋 Loaded {len(self.mcp_servers)} MCP server configurations", "success")
                        return
                except Exception as e:
                    self.log_message(f"❌ Error loading MCP config from {config_path}: {str(e)}", "error")
        
        # Create example configuration if none found
        self.create_example_mcp_config()
    
    def create_example_mcp_config(self):
        """Create an example MCP configuration file"""
        example_config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
                },
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"]
                }
            }
        }
        
        try:
            with open("mcp_servers.json", 'w') as f:
                json.dump(example_config, f, indent=2)
            
            self.log_message("📄 Created example MCP configuration: mcp_servers.json", "info")
            self.log_message("Edit this file to configure your MCP servers", "info")
            self.mcp_servers = example_config["mcpServers"]
        except Exception as e:
            self.log_message(f"❌ Error creating example config: {str(e)}", "error")

    async def start_mcp_servers(self):
        """Start and connect to MCP servers"""
        if not self.mcp_servers:
            self.log_message("⚠️ No MCP servers configured", "info")
            return
        
        self.log_message("🔌 Starting MCP servers...", "info")
        
        try:
            await self.mcp_client.load_servers(self.mcp_servers)
            
            tools = self.mcp_client.get_all_tools()
            if tools:
                self.log_message(f"🛠️ Loaded {len(tools)} MCP tools", "success")
                
                # Update Gemini with available tools
                await self.update_gemini_system_message()
            else:
                self.log_message("⚠️ No MCP tools available", "info")
                
        except Exception as e:
            self.log_message(f"❌ Error starting MCP servers: {str(e)}", "error")

    async def update_gemini_system_message(self):
        """Update Gemini with information about available MCP tools"""
        tools_summary = self.mcp_client.get_tools_summary()
        
        system_message = f"""You are an AI assistant with access to MCP (Model Context Protocol) tools. 

{tools_summary}

IMPORTANT: When a user asks you to do something that requires using these tools:
1. Think through ALL the steps needed to complete the task
2. Make ALL necessary tool calls in a SINGLE response 
3. Complete the ENTIRE task before finishing your response
4. Present the final results clearly to the user

For example, if asked to "list files in a directory":
- First call list_allowed_directories to check permissions
- Then call list_directory with the appropriate path
- Present the complete file listing to the user

To call a tool, use this format:
```mcp-tool-call
{{
  "tool": "tool_name",
  "arguments": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
```

You can and SHOULD call multiple tools in sequence within the same response. Don't stop after the first tool call - continue until the user's request is fully completed.

Example of multi-step response:
I'll help you list the files. Let me first check what directories I can access.

```mcp-tool-call
{{
  "tool": "list_allowed_directories",
  "arguments": {{}}
}}
```

Now I'll list the contents of your home directory:

```mcp-tool-call
{{
  "tool": "list_directory", 
  "arguments": {{
    "path": "/home/username"
  }}
}}
```

Here are the files in your directory: [results would be shown here]
"""
        
        # Send system message to Gemini
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.chat_session.send_message, system_message
            )
            self.log_message("🧠 Updated Gemini with MCP tools information", "success")
        except Exception as e:
            self.log_message(f"❌ Error updating Gemini: {str(e)}", "error")

    def compose(self) -> ComposeResult:
        """Create the UI components"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="chat-area"):
                yield Static("🤖 MCP Client - Gemini + MCP Servers", id="title")
                yield RichLog(id="chat-log", auto_scroll=True)
            
            with Horizontal(id="input-area"):
                yield Input(placeholder="Type your message to Gemini...", id="message-input")
                yield Button("Send", id="send-button", variant="primary")
        
        yield Footer()
    
    async def on_mount(self):
        """Initialize the application"""
        self.log_message("🚀 MCP Client TUI Started", "info")
        
        # Setup Gemini after UI is ready
        self.setup_gemini()
        
        # Load MCP configuration
        self.load_mcp_config()
        
        # Start MCP servers
        await self.start_mcp_servers()
        
        self.log_message("✅ Ready! Type your message and press Enter to chat", "info")
        
        # Focus on input
        input_widget = self.query_one("#message-input", Input)
        input_widget.focus()
    
    def log_message(self, message: str, msg_type: str = "info"):
        """Add a message to the chat log"""
        chat_log = self.query_one("#chat-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if msg_type == "user":
            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append("You: ", style="bold blue")
            text.append(message)
            chat_log.write(text)
        elif msg_type == "assistant":
            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append("Gemini: ", style="bold green")
            chat_log.write(text)
            # Render markdown response
            try:
                md = Markdown(message)
                chat_log.write(md)
            except:
                chat_log.write(message)
        elif msg_type == "tool":
            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append("Tool: ", style="bold magenta")
            text.append(message, style="magenta")
            chat_log.write(text)
        elif msg_type == "error":
            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append("Error: ", style="bold red")
            text.append(message, style="red")
            chat_log.write(text)
        elif msg_type == "success":
            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append("System: ", style="bold green")
            text.append(message, style="green")
            chat_log.write(text)
        else:  # info
            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append("Info: ", style="bold cyan")
            text.append(message, style="cyan")
            chat_log.write(text)
    
    def _extract_content_from_result(self, result: Dict[str, Any]) -> str:
        """Extract meaningful content from MCP tool result"""
        try:
            # Handle successful results
            if "result" in result:
                result_data = result["result"]
                
                # Handle content array format (common in MCP)
                if isinstance(result_data, dict) and "content" in result_data:
                    content_items = result_data["content"]
                    if isinstance(content_items, list) and len(content_items) > 0:
                        # Extract text from content items
                        text_parts = []
                        for item in content_items:
                            if isinstance(item, dict):
                                if item.get("type") == "text" and "text" in item:
                                    text_parts.append(item["text"])
                                elif "text" in item:
                                    text_parts.append(item["text"])
                        
                        if text_parts:
                            return "\n".join(text_parts)
                
                # Handle direct text result
                if isinstance(result_data, str):
                    return result_data
                
                # Handle other structured data - format nicely
                if isinstance(result_data, (dict, list)):
                    # Try to find common text fields
                    if isinstance(result_data, dict):
                        for key in ["text", "message", "content", "output", "data"]:
                            if key in result_data:
                                value = result_data[key]
                                if isinstance(value, str):
                                    return value
                    
                    # Fall back to formatted JSON but make it readable
                    return json.dumps(result_data, indent=2)
            
            # Handle error results
            if "error" in result:
                error_info = result["error"]
                if isinstance(error_info, dict):
                    message = error_info.get("message", str(error_info))
                    return f"Error: {message}"
                else:
                    return f"Error: {error_info}"
            
            # Fallback - return the whole result but formatted
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    async def send_message_to_gemini(self, message: str) -> str:
        """Send message to Gemini and get response with tool calling loop"""
        if not self.gemini_model or not self.chat_session:
            raise Exception("Gemini model not initialized")
        
        try:
            current_message = message
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Send message to Gemini
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.chat_session.send_message, current_message
                )
                
                # Check if response contains tool calls
                tool_call_pattern = r'```mcp-tool-call\n(.*?)\n```'
                tool_calls = re.findall(tool_call_pattern, response.text, re.DOTALL)
                
                if not tool_calls:
                    # No tool calls, return the final response
                    return response.text
                
                # Process tool calls and prepare results for Gemini
                tool_results = []
                response_with_results = response.text
                
                for tool_call_json in tool_calls:
                    try:
                        tool_call = json.loads(tool_call_json)
                        tool_name = tool_call.get("tool")
                        arguments = tool_call.get("arguments", {})
                        
                        if tool_name:
                            self.log_message(f"🔧 Calling tool: {tool_name} with {arguments}", "tool")
                            
                            # Call the MCP tool
                            result = await self.mcp_client.call_tool(tool_name, arguments)
                            
                            if result:
                                # Extract meaningful content from the result
                                content_text = self._extract_content_from_result(result)
                                
                                # Replace the tool call with the result in the response
                                tool_call_block = f"```mcp-tool-call\n{tool_call_json}\n```"
                                replacement = f"**Tool Result ({tool_name}):**\n{content_text}"
                                response_with_results = response_with_results.replace(tool_call_block, replacement)
                                
                                # Store result for sending back to Gemini
                                tool_results.append({
                                    "tool": tool_name,
                                    "result": content_text
                                })
                                
                                self.log_message(f"✅ Tool {tool_name} executed successfully", "tool")
                            else:
                                self.log_message(f"❌ Tool {tool_name} failed to execute", "error")
                                
                    except json.JSONDecodeError:
                        self.log_message(f"❌ Invalid tool call JSON: {tool_call_json}", "error")
                    except Exception as e:
                        self.log_message(f"❌ Error processing tool call: {str(e)}", "error")
                
                # If we have tool results, send them back to Gemini to continue
                if tool_results:
                    results_message = "Here are the tool results:\n\n"
                    for result in tool_results:
                        results_message += f"**{result['tool']} result:**\n{result['result']}\n\n"
                    results_message += "Please continue with your response based on these results."
                    
                    current_message = results_message
                else:
                    # No successful tool results, return what we have
                    return response_with_results
            
            # If we hit max iterations, return the last response
            self.log_message("⚠️ Maximum tool calling iterations reached", "info")
            return response.text
            
        except Exception as e:
            raise Exception(f"Failed to get response from Gemini: {str(e)}")
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        if event.input.id == "message-input":
            await self.handle_send_message()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "send-button":
            await self.handle_send_message()
    
    async def handle_send_message(self):
        """Handle sending a message"""
        input_widget = self.query_one("#message-input", Input)
        message = input_widget.value.strip()
        
        if not message:
            return
        
        # Clear input
        input_widget.value = ""
        
        # Log user message
        self.log_message(message, "user")
        
        if not self.gemini_model:
            self.log_message("Gemini model not initialized. Please check your API key.", "error")
            return
        
        # Show thinking indicator
        self.log_message("🤔 Thinking...", "info")
        
        try:
            # Send to Gemini
            response = await self.send_message_to_gemini(message)
            
            # Log assistant response
            self.log_message(response, "assistant")
            
        except Exception as e:
            self.log_message(str(e), "error")
    
    def action_send_message(self):
        """Action to send message"""
        asyncio.create_task(self.handle_send_message())
    
    def action_clear_chat(self):
        """Clear the chat log"""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.clear()
        
        # Restart chat session
        if self.gemini_model:
            self.chat_session = self.gemini_model.start_chat()
            self.log_message("🧹 Chat cleared and session restarted", "info")
            # Re-send system message about MCP tools
            asyncio.create_task(self.update_gemini_system_message())
    
    def action_show_servers(self):
        """Show available MCP servers"""
        self.log_message("🔧 MCP Server Status:", "info")
        if not self.mcp_client.servers:
            self.log_message("  No MCP servers running", "info")
        else:
            for name, server in self.mcp_client.servers.items():
                status = "✅ Connected" if server.connected else "❌ Disconnected"
                tools_count = len(server.tools)
                self.log_message(f"  └── {name}: {status} ({tools_count} tools)", "info")
    
    def action_show_tools(self):
        """Show available MCP tools"""
        tools = self.mcp_client.get_all_tools()
        self.log_message("🛠️ Available MCP Tools:", "info")
        if not tools:
            self.log_message("  No tools available", "info")
        else:
            for tool in tools:
                self.log_message(f"  └── {tool.name} ({tool.server_name}): {tool.description}", "info")
    
    def action_quit(self):
        """Quit the application"""
        # Shutdown MCP servers
        asyncio.create_task(self.mcp_client.shutdown())
        self.exit()

def main():
    """Run the MCP Client TUI"""
    app = MCPClientApp()
    app.run()

if __name__ == "__main__":
    main() 