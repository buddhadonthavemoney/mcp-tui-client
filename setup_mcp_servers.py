#!/usr/bin/env python3
"""
MCP Server Setup Script
Helps you install and configure basic MCP servers for testing
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False

def check_node():
    """Check if Node.js is installed"""
    print("🔍 Checking Node.js installation...")
    if run_command("node --version", "Node.js version check"):
        if run_command("npm --version", "npm version check"):
            return True
    
    print("❌ Node.js or npm not found. Please install Node.js first:")
    print("   Visit: https://nodejs.org/")
    return False

def setup_filesystem_server():
    """Set up filesystem MCP server"""
    print("\n📁 Setting up Filesystem MCP Server...")
    
    # Create a test directory
    test_dir = Path.home() / "mcp-test-files"
    test_dir.mkdir(exist_ok=True)
    
    # Create some test files
    (test_dir / "sample.txt").write_text("Hello from MCP Filesystem Server!")
    (test_dir / "data.json").write_text('{"message": "This is test data", "timestamp": "2024-01-01"}')
    
    print(f"✅ Created test directory: {test_dir}")
    print(f"✅ Created sample files in {test_dir}")
    
    return str(test_dir)

def setup_memory_server():
    """Set up memory MCP server"""
    print("\n🧠 Memory MCP Server will be available when started")
    print("   This server provides persistent memory capabilities")
    return True

def create_mcp_config(filesystem_path):
    """Create MCP server configuration file"""
    print("\n📄 Creating MCP server configuration...")
    
    config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", filesystem_path]
            },
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"]
            },
            "fetch": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-fetch"]
            }
        }
    }
    
    # Save configuration
    config_file = "mcp_servers.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created configuration file: {config_file}")
    return config

def test_servers():
    """Test if MCP servers can be started"""
    print("\n🧪 Testing MCP server availability...")
    
    # Instead of running the servers directly, we'll just check if npm/npx is working
    # The actual servers will be tested when the MCP client tries to connect to them
    print("   ✅ MCP servers will be downloaded automatically when first used")
    print("   ✅ npx will handle package installation on-demand")
    
    # Just verify npx is working
    if run_command("npx --version", "Checking npx availability"):
        print("   ✅ npx is ready for MCP server management")
    else:
        print("   ❌ npx may have issues - consider reinstalling Node.js")

def show_next_steps(config):
    """Show next steps to the user"""
    print("\n🎉 MCP Server Setup Complete!")
    print("\n📋 What was configured:")
    
    for name, server_config in config["mcpServers"].items():
        cmd = server_config["command"]
        args = " ".join(server_config["args"])
        print(f"  • {name}: {cmd} {args}")
    
    print(f"\n🚀 Next Steps:")
    print(f"1. Make sure you have your Gemini API key set up:")
    print(f"   echo 'GEMINI_API_KEY=your_api_key_here' > .env")
    print(f"   echo 'GEMINI_MODEL=gemini-pro' >> .env")
    print(f"")
    print(f"2. Run the MCP Client:")
    print(f"   python main.py")
    print(f"")
    print(f"3. Use keyboard shortcuts:")
    print(f"   • Ctrl+S: Show configured servers")
    print(f"   • Ctrl+C: Clear chat")
    print(f"   • Ctrl+Q: Quit")
    print(f"")
    print(f"4. Try asking Gemini to:")
    print(f"   • 'List files in my test directory'")
    print(f"   • 'Remember that I like Python programming'")
    print(f"   • 'Fetch content from a website'")

def main():
    """Main setup function"""
    print("🚀 MCP Server Setup for MCP Client TUI")
    print("=" * 50)
    
    # Check prerequisites
    if not check_node():
        sys.exit(1)
    
    # Set up servers
    filesystem_path = setup_filesystem_server()
    setup_memory_server()
    
    # Create configuration
    config = create_mcp_config(filesystem_path)
    
    # Test servers
    test_servers()
    
    # Show next steps
    show_next_steps(config)

if __name__ == "__main__":
    main() 