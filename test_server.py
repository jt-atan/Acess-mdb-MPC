"""
Simple test script to verify the MCP Access server can start correctly
"""
import os
import sys
from pathlib import Path

# Ensure we can import from the current directory
sys.path.insert(0, str(Path(__file__).parent))

# Try to import the server module
try:
    print("Importing server module...")
    import server
    print("Server module imported successfully")
except Exception as e:
    print(f"Error importing server module: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    print("Starting MCP Access server test...")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Try to start the server
    try:
        print("Attempting to start the MCP server...")
        server.main()
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        import traceback
        traceback.print_exc()
