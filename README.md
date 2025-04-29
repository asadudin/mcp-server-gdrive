# Google Drive MCP Server

A Model Context Protocol (MCP) server for interacting with Google Drive API. This server provides a standardized interface for AI systems to access and manipulate files in Google Drive.

## Features

- **File Operations**: List, upload, download, and delete files
- **Folder Management**: Create folders and organize content
- **File Sharing**: Share files with specific users and manage permissions
- **Pagination Support**: Handle large file listings efficiently
- **Comprehensive Error Handling**: Detailed error reporting for easier debugging

<<<<<<< HEAD
More details coming soon...
=======
## Prerequisites

- Python 3.8+
- Google Cloud project with Drive API enabled
- Service account with appropriate permissions

## Setup

### 1. Google Cloud Setup

1. Create a project in Google Cloud Console
2. Enable the Google Drive API
3. Create a service account with appropriate permissions
4. Download the service account JSON key file

### 2. Local Setup

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone <repository-url>
cd mcp-server-gdrive

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy example environment file and edit with your settings
cp .env.example .env
```

Edit the `.env` file with your configuration:

```
HOST=0.0.0.0
PORT=8055
GOOGLE_SERVICE_ACCOUNT_FILE=your-service-account-file.json
```

### 3. Docker Setup

Alternatively, you can use Docker:

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Running the Server

### Local Execution

```bash
python main.py --transport sse
```

### Docker Execution

```bash
docker-compose up
```

## MCP Tools

This server provides the following MCP tools:

### File Operations

- `list_files`: List files in Google Drive with pagination support
- `get_file_info`: Get detailed information about a specific file
- `upload_file`: Upload a file to Google Drive
- `download_file`: Download a file from Google Drive

### Folder Operations

- `create_folder`: Create a new folder in Google Drive

### Sharing and Permissions

- `share_file`: Share a file or folder with another user

### Debugging

- `debug_api_connection`: Debug the Google Drive API connection

## Client Configuration

To connect to this MCP server from a client:

```json
{
  "gdrive": {
    "transport": "sse",
    "serverUrl": "http://localhost:8055/sse"
  }
}
```

Note: Make sure to include `/sse` at the end of the URL for SSE transport.

## Security Considerations

- The service account JSON file contains sensitive credentials. Never commit it to version control.
- Use environment variables for all sensitive configuration.
- Consider implementing additional authentication if deploying publicly.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
>>>>>>> 0f908db (Initial commit: Google Drive MCP server implementation)
