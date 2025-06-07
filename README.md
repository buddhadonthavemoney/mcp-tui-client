# MCP Client TUI

A beautiful Terminal User Interface (TUI) for Model Context Protocol with direct Gemini integration.

## Features

- 🤖 Direct communication with Google Gemini Pro
- 🎨 Modern, responsive terminal interface
- 💬 Real-time chat with markdown support
- ⌨️ Keyboard shortcuts for efficient navigation
- 🧹 Chat clearing and session management
- 📱 Beautiful, professional UI design

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key (get one at [Google AI Studio](https://makersuite.google.com/app/apikey))

## Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Gemini API key:
   ```bash
   # Option 1: Create a .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   
   # Option 2: Export as environment variable
   export GEMINI_API_KEY=your_api_key_here
   ```

## Usage

Run the application:
```bash
python main.py
```

### Keyboard Shortcuts

- **Enter**: Send message
- **Ctrl+C**: Clear chat history
- **Ctrl+Q**: Quit application

### Features

- **Chat Interface**: Type your messages and get responses from Gemini
- **Markdown Support**: Gemini responses are rendered with proper markdown formatting
- **Session Management**: Clear chat to start fresh conversations
- **Auto-scroll**: Chat automatically scrolls to show the latest messages
- **Timestamped Messages**: All messages include timestamps

## Project Structure

```
mcp-client/
├── main.py           # Main application file
├── styles.css        # TUI styling
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Configuration

The application looks for the `GEMINI_API_KEY` environment variable. You can set this in several ways:

1. **`.env` file** (recommended):
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

2. **Environment variable**:
   ```bash
   export GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **System environment** (persistent):
   Add to your shell profile (.bashrc, .zshrc, etc.)

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure you've set the API key as described above
- Verify the `.env` file is in the same directory as `main.py`
- Check that there are no extra spaces or quotes around the API key

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Consider using a virtual environment

### API errors
- Verify your API key is valid and active
- Check your internet connection
- Ensure you haven't exceeded API quotas

## Future Enhancements

This is the foundation for a full MCP client. Future versions will include:

- 🔌 MCP server connections
- 🛠️ Tool calling support  
- 📁 Resource management
- 🔄 Multiple conversation sessions
- 💾 Chat history persistence
- 🎛️ Configuration management

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License. 