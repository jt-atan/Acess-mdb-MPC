"""
Simple script to run the MCP Access server with environment variable setup
"""
import os
import sys
import tempfile
from pathlib import Path
from mcp_access.server import main

if __name__ == "__main__":
    # Set up environment variables if not already set
    # EXECUTE_QUERY_MAX_CHARS controls the maximum number of characters to display in query results
    if "EXECUTE_QUERY_MAX_CHARS" not in os.environ:
        os.environ["EXECUTE_QUERY_MAX_CHARS"] = "4000"  # Default to 4000 characters
    
    # CLAUDE_LOCAL_FILES_PATH is used to store large result sets for Claude to access
    if "CLAUDE_LOCAL_FILES_PATH" not in os.environ:
        # Create a temporary directory in the user's temp folder
        claude_files_path = Path(tempfile.gettempdir()) / "claude_files"
        os.environ["CLAUDE_LOCAL_FILES_PATH"] = str(claude_files_path)
        
        # Ensure the directory exists
        claude_files_path.mkdir(exist_ok=True)
        print(f"Claude files will be stored in: {claude_files_path}")
    
    # Run the MCP server
    main()
