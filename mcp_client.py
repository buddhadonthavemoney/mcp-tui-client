#!/usr/bin/env python3
"""
MCP Client Implementation
Handles connection and communication with MCP servers
"""

import asyncio
import json
import subprocess
import sys
import os
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str


class MCPServer:
    """Represents a connected MCP server"""
    
    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None, logger: Optional[Callable[[str, str], None]] = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = self._resolve_env_variables(env or {})
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[MCPTool] = []
        self.connected = False
        self.next_id = 1
        self.logger = logger or self._default_logger
    
    def _resolve_env_variables(self, env_dict: Dict[str, str]) -> Dict[str, str]:
        """Resolve environment variable references in the format ${VAR_NAME}"""
        resolved_env = {}
        for key, value in env_dict.items():
            # Look for ${VAR_NAME} patterns
            def replace_env_var(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name)
                if env_value is None:
                    raise ValueError(f"Environment variable '{var_name}' not found for server '{self.name}'")
                return env_value
            
            # Replace ${VAR_NAME} with actual environment variable values
            resolved_value = re.sub(r'\$\{([^}]+)\}', replace_env_var, value)
            resolved_env[key] = resolved_value
        
        return resolved_env
    
    def _default_logger(self, message: str, level: str = "info"):
        """Default logger that does nothing"""
        pass
    
    def _log(self, message: str, level: str = "info"):
        """Log a message using the provided logger"""
        self.logger(message, level)
    
    async def start(self) -> bool:
        """Start the MCP server process"""
        try:
            # Prepare environment
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            # Start the server process
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=full_env,
                bufsize=0  # Unbuffered
            )
            
            # Wait a moment for the process to start
            await asyncio.sleep(0.5)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read() if self.process.stderr else ""
                raise Exception(f"Server process exited: {stderr_output}")
            
            # Initialize the MCP connection
            await self._initialize()
            return True
            
        except Exception as e:
            self._log(f"Failed to start MCP server {self.name}: {e}", "error")
            if self.process:
                self.process.terminate()
            return False
    
    async def _initialize(self):
        """Initialize MCP connection with the server"""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "mcp-client-tui",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_request(init_request)
            if not response or "error" in response:
                raise Exception(f"Initialize failed: {response}")
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            await self._send_notification(initialized_notification)
            
            # List available tools
            await self._list_tools()
            
            self.connected = True
            
        except Exception as e:
            raise Exception(f"Failed to initialize MCP server {self.name}: {e}")
    
    def _get_next_id(self) -> int:
        """Get next request ID"""
        current_id = self.next_id
        self.next_id += 1
        return current_id
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification (no response expected)"""
        if not self.process or not self.process.stdin:
            return
        
        try:
            notification_str = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_str)
            self.process.stdin.flush()
        except Exception as e:
            self._log(f"Error sending notification to {self.name}: {e}", "error")
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to the server"""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None
        
        try:
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str)
            self.process.stdin.flush()
            
            # Read response with timeout
            response_str = ""
            max_attempts = 10
            for _ in range(max_attempts):
                await asyncio.sleep(0.1)
                if self.process.stdout.readable():
                    line = self.process.stdout.readline()
                    if line:
                        response_str = line.strip()
                        break
            
            if response_str:
                try:
                    return json.loads(response_str)
                except json.JSONDecodeError as e:
                    self._log(f"Invalid JSON response from {self.name}: {response_str}", "error")
                    return None
            else:
                self._log(f"No response from {self.name}", "error")
                return None
            
        except Exception as e:
            self._log(f"Error sending request to {self.name}: {e}", "error")
            return None
    
    async def _list_tools(self):
        """List available tools from the server"""
        try:
            list_tools_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/list"
            }
            
            response = await self._send_request(list_tools_request)
            
            if response and "result" in response and "tools" in response["result"]:
                self.tools = []
                for tool_data in response["result"]["tools"]:
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("inputSchema", {}),
                        server_name=self.name
                    )
                    self.tools.append(tool)
            elif response and "error" in response:
                self._log(f"Error listing tools from {self.name}: {response['error']}", "error")
            
        except Exception as e:
            self._log(f"Error listing tools from {self.name}: {e}", "error")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool on this server"""
        try:
            call_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self._send_request(call_request)
            return response
            
        except Exception as e:
            self._log(f"Error calling tool {tool_name} on {self.name}: {e}", "error")
            return None
    
    async def stop(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(asyncio.to_thread(self.process.wait), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
        self.connected = False


class MCPClient:
    """Main MCP Client that manages multiple servers"""
    
    def __init__(self, logger: Optional[Callable[[str, str], None]] = None):
        self.servers: Dict[str, MCPServer] = {}
        self.logger = logger or self._default_logger
    
    def _default_logger(self, message: str, level: str = "info"):
        """Default logger that does nothing"""
        pass
    
    def _log(self, message: str, level: str = "info"):
        """Log a message using the provided logger"""
        self.logger(message, level)
    
    async def load_servers(self, config: Dict[str, Dict[str, Any]]):
        """Load and start MCP servers from configuration"""
        for name, server_config in config.items():
            command = server_config.get("command", "")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            server = MCPServer(name, command, args, env, self.logger)
            self.servers[name] = server
            
            self._log(f"🔌 Starting MCP server: {name}", "info")
            success = await server.start()
            
            if success:
                self._log(f"   ✅ {name} connected ({len(server.tools)} tools available)", "success")
                for tool in server.tools:
                    self._log(f"      └── {tool.name}: {tool.description}", "info")
            else:
                self._log(f"   ❌ {name} failed to connect", "error")
    
    def get_all_tools(self) -> List[MCPTool]:
        """Get all available tools from all connected servers"""
        all_tools = []
        for server in self.servers.values():
            if server.connected:
                all_tools.extend(server.tools)
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool by name (searches all servers)"""
        for server in self.servers.values():
            if server.connected:
                for tool in server.tools:
                    if tool.name == tool_name:
                        return await server.call_tool(tool_name, arguments)
        return None
    
    def get_tools_summary(self) -> str:
        """Get a summary of all available tools for the LLM"""
        tools = self.get_all_tools()
        if not tools:
            return "No MCP tools available."
        
        summary = "Available MCP tools:\n"
        for tool in tools:
            summary += f"- {tool.name}: {tool.description}\n"
        
        return summary
    
    async def shutdown(self):
        """Shutdown all MCP servers"""
        for server in self.servers.values():
            await server.stop() 