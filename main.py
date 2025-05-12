import os
import json
import time
import base64
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Load environment variables
load_dotenv()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8055))
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "mcp-project-458109-5e6bacb68907.json")
SCOPES = os.environ.get("GOOGLE_DRIVE_SCOPES", "https://www.googleapis.com/auth/drive")

# Initialize FastMCP server
mcp = FastMCP(
    "gdrive",
    host=HOST,
    port=PORT
)

# Helper for Google Sheets API
async def make_sheets_request(endpoint: str, method: str = "GET", params: Optional[dict] = None, data: Optional[dict] = None) -> dict:
    """
    Make a request to the Google Sheets API with proper error handling.
    Args:
        endpoint: The API endpoint to call (relative to /v4/)
        method: HTTP method (GET, POST, PUT, PATCH)
        params: Query parameters
        data: JSON data for the request body
    Returns:
        Response from the API as a dictionary
    """
    creds = get_google_creds()
    creds.refresh(Request())
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = f"https://sheets.googleapis.com/v4/{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "POST":
                resp = await client.post(url, headers=headers, params=params, json=data, timeout=30.0)
            elif method.upper() == "PUT":
                resp = await client.put(url, headers=headers, params=params, json=data, timeout=30.0)
            elif method.upper() == "PATCH":
                resp = await client.patch(url, headers=headers, params=params, json=data, timeout=30.0)
            else:
                return {"error": f"Unsupported method: {method}"}
            resp.raise_for_status()
            if resp.headers.get("content-type", "").startswith("application/json"):
                return resp.json()
            else:
                return {"content": resp.content, "headers": dict(resp.headers)}
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"response_text": e.response.text}
            return {
                "error": f"API Error: {e.response.status_code} - {str(e)}",
                "status_code": e.response.status_code,
                "details": error_detail
            }
        except httpx.RequestError as e:
            return {"error": f"Request Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# ---- Google Sheets Tools ----

@mcp.tool()
async def create_spreadsheet(title: str) -> str:
    """
    Create a new Google Spreadsheet.
    Args:
        title: Title of the new spreadsheet
    Returns:
        JSON string with spreadsheetId
    """
    data = {"properties": {"title": title}}
    response = await make_sheets_request("spreadsheets", method="POST", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def read_sheet_values(spreadsheet_id: str, range: str) -> str:
    """
    Read cell values from a Google Spreadsheet.
    Args:
        spreadsheet_id: Spreadsheet (document) ID
        range: A1 notation range (e.g., "Sheet1!A1:C2")
    Returns:
        JSON string with cell values
    """
    endpoint = f"spreadsheets/{spreadsheet_id}/values/{range}"
    response = await make_sheets_request(endpoint, method="GET")
    return json.dumps(response, indent=2)

@mcp.tool()
async def update_sheet_values(spreadsheet_id: str, range: str, values: list, value_input_option: str = "USER_ENTERED") -> str:
    """
    Update cell values in a Google Spreadsheet.
    Args:
        spreadsheet_id: Spreadsheet (document) ID
        range: A1 notation range (e.g., "Sheet1!A1:C2")
        values: 2D array of values
        value_input_option: "RAW" or "USER_ENTERED" (default)
    Returns:
        JSON string with update result
    """
    endpoint = f"spreadsheets/{spreadsheet_id}/values/{range}"
    params = {"valueInputOption": value_input_option}
    data = {"values": values}
    response = await make_sheets_request(endpoint, method="PUT", params=params, data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def append_sheet_values(spreadsheet_id: str, range: str, values: list, value_input_option: str = "USER_ENTERED") -> str:
    """
    Append values to a Google Spreadsheet.
    Args:
        spreadsheet_id: Spreadsheet (document) ID
        range: A1 notation range (e.g., "Sheet1!A1:C2")
        values: 2D array of values
        value_input_option: "RAW" or "USER_ENTERED" (default)
    Returns:
        JSON string with append result
    """
    endpoint = f"spreadsheets/{spreadsheet_id}/values/{range}:append"
    params = {"valueInputOption": value_input_option}
    data = {"values": values}
    response = await make_sheets_request(endpoint, method="POST", params=params, data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def batch_update_sheet(spreadsheet_id: str, requests: list) -> str:
    """
    Batch update a Google Spreadsheet (formatting, find/replace, etc).
    Args:
        spreadsheet_id: Spreadsheet (document) ID
        requests: List of batch update requests (see Sheets API docs)
    Returns:
        JSON string with batch update result
    """
    endpoint = f"spreadsheets/{spreadsheet_id}:batchUpdate"
    data = {"requests": requests}
    response = await make_sheets_request(endpoint, method="POST", data=data)
    return json.dumps(response, indent=2)

def get_google_creds():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[SCOPES] if isinstance(SCOPES, str) else SCOPES
    )
    return creds

async def make_gdrive_request(endpoint: str, method: str = "GET", params: Optional[dict] = None, data: Optional[dict] = None, files: Optional[dict] = None, multipart: bool = False) -> dict:
    """Make a request to the Google Drive API with proper error handling.
    
    Args:
        endpoint: The API endpoint to call (e.g., 'files', 'files/{fileId}', etc.)
        method: HTTP method (GET, POST, PATCH, DELETE)
        params: Query parameters
        data: JSON data for the request body
        files: Files to upload (for multipart requests)
        multipart: Whether this is a multipart request
        
    Returns:
        Response from the API as a dictionary
    """
    creds = get_google_creds()
    creds.refresh(Request())
    
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }
    
    url = f"https://www.googleapis.com/drive/v3/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "POST":
                if multipart and files:
                    # For file uploads
                    resp = await client.post(url, headers=headers, params=params, files=files, data=data, timeout=60.0)
                else:
                    resp = await client.post(url, headers=headers, json=data, params=params, timeout=30.0)
            elif method.upper() == "PATCH":
                if multipart and files:
                    resp = await client.patch(url, headers=headers, params=params, files=files, data=data, timeout=60.0)
                else:
                    resp = await client.patch(url, headers=headers, json=data, params=params, timeout=30.0)
            elif method.upper() == "DELETE":
                resp = await client.delete(url, headers=headers, params=params, timeout=30.0)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            resp.raise_for_status()
            
            # Some endpoints might not return JSON (like file downloads)
            if resp.headers.get("content-type", "").startswith("application/json"):
                return resp.json()
            else:
                return {"content": resp.content, "headers": dict(resp.headers)}
                
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"response_text": e.response.text}
                
            return {
                "error": f"API Error: {e.response.status_code} - {str(e)}",
                "status_code": e.response.status_code,
                "details": error_detail
            }
        except httpx.RequestError as e:
            return {"error": f"Request Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def list_files(page_size: int = 10, q: Optional[str] = None, page_token: Optional[str] = None) -> str:
    """List files in Google Drive with pagination support.
    
    Args:
        page_size: Maximum number of files to return (default: 10)
        q: Search query in Google Drive query format (e.g., "name contains 'report'")
        page_token: Token for pagination (from a previous list_files call)
        
    Returns:
        JSON string with files and pagination info
    """
    params = {
        "pageSize": page_size, 
        "fields": "nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)"
    }
    
    if q:
        params["q"] = q
    if page_token:
        params["pageToken"] = page_token
        
    response = await make_gdrive_request("files", params=params)
    
    if "error" in response:
        return json.dumps({"error": response["error"]}, indent=2)
        
    result = {
        "files": response.get("files", []),
        "nextPageToken": response.get("nextPageToken", None)
    }
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def debug_api_connection() -> str:
    """Debug the Google Drive API connection to help diagnose issues."""
    try:
        creds = get_google_creds()
        creds.refresh(Request())
        
        # Test a simple API call
        about_response = await make_gdrive_request("about", params={"fields": "user,storageQuota"})
        
        return json.dumps({
            "token_valid": creds.valid,
            "token_expiry": str(creds.expiry),
            "scopes": creds.scopes,
            "api_test": "success" if "error" not in about_response else "failed",
            "user_info": about_response.get("user", {}),
            "storage_quota": about_response.get("storageQuota", {})
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
async def get_file_info(file_id: str) -> str:
    """Get detailed information about a specific file in Google Drive.
    
    Args:
        file_id: The ID of the file to get information about
        
    Returns:
        JSON string with file metadata
    """
    params = {"fields": "id,name,mimeType,size,webViewLink,createdTime,modifiedTime,owners,shared,parents"}
    response = await make_gdrive_request(f"files/{file_id}", params=params)
    
    if "error" in response:
        return json.dumps({"error": response["error"]}, indent=2)
        
    return json.dumps(response, indent=2)

@mcp.tool()
async def create_folder(name: str, parent_id: Optional[str] = None) -> str:
    """Create a new folder in Google Drive.
    
    Args:
        name: Name of the folder to create
        parent_id: Optional ID of the parent folder (if not specified, folder will be created in root)
        
    Returns:
        JSON string with created folder metadata
    """
    data = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    
    if parent_id:
        data["parents"] = [parent_id]
        
    response = await make_gdrive_request("files", method="POST", data=data)
    
    if "error" in response:
        return json.dumps({"error": response["error"]}, indent=2)
        
    return json.dumps(response, indent=2)

@mcp.tool()
async def upload_file(name: str, content: str, mime_type: str = "text/plain", parent_id: Optional[str] = None) -> str:
    """Upload a file to Google Drive.
    
    Args:
        name: Name of the file to create
        content: Base64-encoded content of the file
        mime_type: MIME type of the file (default: text/plain)
        parent_id: Optional ID of the parent folder (if not specified, file will be created in root)
        
    Returns:
        JSON string with uploaded file metadata
    """
    try:
        # Decode the base64 content
        file_content = base64.b64decode(content)
        
        # Metadata for the file
        metadata = {
            "name": name
        }
        
        if parent_id:
            metadata["parents"] = [parent_id]
        
        # Parameters for the request
        params = {
            "uploadType": "multipart",
            "fields": "id,name,mimeType,size,webViewLink"
        }
        
        # Create the multipart request
        files = {
            "metadata": ("metadata", json.dumps(metadata), "application/json"),
            "file": (name, file_content, mime_type)
        }
        
        response = await make_gdrive_request("files", method="POST", params=params, files=files, multipart=True)
        
        if "error" in response:
            return json.dumps({"error": response["error"]}, indent=2)
            
        return json.dumps(response, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Upload failed: {str(e)}"}, indent=2)

@mcp.tool()
async def download_file(file_id: str) -> str:
    """Download a file from Google Drive.
    
    Args:
        file_id: The ID of the file to download
        
    Returns:
        JSON string with file content (base64 encoded) and metadata
    """
    try:
        # First get file metadata to get the name and mime type
        file_info = await make_gdrive_request(f"files/{file_id}", params={"fields": "name,mimeType,size"})
        
        if "error" in file_info:
            return json.dumps({"error": file_info["error"]}, indent=2)
            
        # Check if file is too large (limit to 10MB for safety)
        size = int(file_info.get("size", 0))
        if size > 10 * 1024 * 1024:  # 10MB
            return json.dumps({"error": f"File too large to download via MCP: {size} bytes"}, indent=2)
        
        # Download the file content
        response = await make_gdrive_request(f"files/{file_id}?alt=media")
        
        if "error" in response:
            return json.dumps({"error": response["error"]}, indent=2)
            
        # The content is in binary, encode as base64
        content = response.get("content", b"")
        encoded_content = base64.b64encode(content).decode("utf-8")
        
        return json.dumps({
            "name": file_info.get("name"),
            "mimeType": file_info.get("mimeType"),
            "size": file_info.get("size"),
            "content": encoded_content
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Download failed: {str(e)}"}, indent=2)

@mcp.tool()
async def share_file(file_id: str, email: str, role: str = "reader") -> str:
    """Share a file or folder with another user.
    
    Args:
        file_id: The ID of the file or folder to share
        email: Email address of the user to share with
        role: Permission role to grant (reader, writer, commenter, owner)
        
    Returns:
        JSON string with created permission
    """
    data = {
        "type": "user",
        "role": role,
        "emailAddress": email
    }
    
    params = {
        "sendNotificationEmail": "true",
        "fields": "id,type,role,emailAddress"
    }
    
    response = await make_gdrive_request(f"files/{file_id}/permissions", method="POST", data=data, params=params)
    
    if "error" in response:
        return json.dumps({"error": response["error"]}, indent=2)
        
    return json.dumps(response, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--transport', type=str, default='sse', help='Transport type (stdio, sse, etc.)')
    args = parser.parse_args()
<<<<<<< HEAD
    mcp.run(transport=args.transport)
=======
    mcp.run(transport=args.transport)
>>>>>>> 0f908db (Initial commit: Google Drive MCP server implementation)
