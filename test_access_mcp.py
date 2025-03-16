"""
Test script for MCP Access tool with ific3033.mdb
"""
import os
import sys
import asyncio
import json
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Import the MCP client tools
try:
    from mcp.client.stdio import stdio_client
    from mcp.client.session import ClientSession
except ImportError:
    print("MCP Python SDK not installed. Please install it with: pip install mcp")
    sys.exit(1)

# Path to the Access database
DB_PATH = str(Path(__file__).parent / "ific3033.mdb")

async def test_mcp_access():
    """Test the MCP Access tool with the ific3033.mdb database."""
    
    # Start the MCP Access server as a subprocess
    import subprocess
    import time
    
    print("Starting MCP Access server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "mcp_access"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    
    # Give the server a moment to start
    time.sleep(2)
    
    print(f"Testing connection to database: {DB_PATH}")
    
    # Connect to the server - fixed to use the correct format
    server_params = {
        "command": sys.executable,
        "args": ["-m", "mcp_access"]
    }
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Get available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Connect to the database
            print("\n1. Connecting to the database...")
            connect_result = await session.call_tool("connect", {"db_path": DB_PATH})
            print(connect_result.content[0].text)
            
            # Use the filename as the connection ID
            conn_id = os.path.basename(DB_PATH)
            
            # List tables
            print("\n2. Listing tables...")
            list_tables_result = await session.call_tool("list_tables", {"conn_id": conn_id})
            print(list_tables_result.content[0].text)
            
            # Get the first table name from the result
            tables_text = list_tables_result.content[0].text
            table_names = tables_text.split(": ")[1].split(", ")
            if table_names:
                first_table = table_names[0]
                
                # Get table schema
                print(f"\n3. Getting schema for table '{first_table}'...")
                schema_result = await session.call_tool(
                    "get_table_schema", 
                    {"conn_id": conn_id, "table_name": first_table}
                )
                print(schema_result.content[0].text)
                
                # Query the table
                print(f"\n4. Querying data from table '{first_table}'...")
                query_result = await session.call_tool(
                    "query_table", 
                    {"conn_id": conn_id, "table_name": first_table, "limit": 5}
                )
                print(query_result.content[0].text)
                
                # Execute a custom SQL query
                print("\n5. Executing a custom SQL query...")
                sql_query = f"SELECT TOP 3 * FROM [{first_table}]"
                sql_result = await session.call_tool(
                    "execute_sql", 
                    {"conn_id": conn_id, "sql_query": sql_query}
                )
                print(sql_result.content[0].text)
            
            # Disconnect from the database
            print("\n6. Disconnecting from the database...")
            disconnect_result = await session.call_tool("disconnect", {"conn_id": conn_id})
            print(disconnect_result.content[0].text)
    
    # Terminate the server process
    server_process.terminate()
    server_process.wait()
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_mcp_access())
