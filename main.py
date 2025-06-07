#!/usr/bin/env python3
"""
MCP Client TUI - A Terminal User Interface for Model Context Protocol
Direct communication with Google Gemini
"""

import os
import asyncio
from typing import Optional
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

# Load environment variables
load_dotenv()

class MCPClientApp(App):
    """MCP Client TUI Application"""
    
    TITLE = "MCP Client - Gemini Direct"
    CSS_PATH = "styles.css"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+c", "clear_chat", "Clear Chat"),
        Binding("enter", "send_message", "Send", key_display="Enter"),
    ]
    
    def __init__(self):
        super().__init__()
        self.gemini_model: Optional[genai.GenerativeModel] = None
        self.chat_session = None
        # Don't setup Gemini here - wait for on_mount when UI is ready
    
    def setup_gemini(self):
        """Initialize Gemini AI model"""
        api_key = os.getenv('GEMINI_API_KEY')
        model = os.getenv('GEMINI_MODEL')
        if not api_key or not model:
            self.log_message("❌ Error: GEMINI_API_KEY or GEMINI_MODEL not found in environment variables", "error")
            self.log_message("Please set your Gemini API key and model in a .env file or environment variable", "info")
            return
        
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(model)
            self.chat_session = self.gemini_model.start_chat()
            self.log_message("✅ Connected to Gemini Pro", "success")
        except Exception as e:
            self.log_message(f"❌ Failed to initialize Gemini: {str(e)}", "error")
    
    def compose(self) -> ComposeResult:
        """Create the UI components"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="chat-area"):
                yield Static("🤖 MCP Client - Direct Gemini Communication", id="title")
                yield RichLog(id="chat-log", auto_scroll=True)
            
            with Horizontal(id="input-area"):
                yield Input(placeholder="Type your message to Gemini...", id="message-input")
                yield Button("Send", id="send-button", variant="primary")
        
        yield Footer()
    
    def on_mount(self):
        """Initialize the application"""
        self.log_message("🚀 MCP Client TUI Started", "info")
        self.log_message("Type your message and press Enter to chat with Gemini", "info")
        
        # Setup Gemini after UI is ready
        self.setup_gemini()
        
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
    
    async def send_message_to_gemini(self, message: str) -> str:
        """Send message to Gemini and get response"""
        if not self.gemini_model or not self.chat_session:
            raise Exception("Gemini model not initialized")
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.chat_session.send_message, message
            )
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
            
            # Remove thinking indicator by clearing last line
            chat_log = self.query_one("#chat-log", RichLog)
            
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
    
    def action_quit(self):
        """Quit the application"""
        self.exit()

def main():
    """Run the MCP Client TUI"""
    app = MCPClientApp()
    app.run()

if __name__ == "__main__":
    main() 