"""
Simple client to test the MCP Access tool
"""
import os
import sys
import asyncio
from pathlib import Path

# Import the MCP client tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to the Access database
DB_PATH = str(Path(__file__).parent / "ific3033.mdb")

async def test_connection():
    """Test connecting to the database and demonstrate tool usage"""
    print(f"Testing connection to database: {DB_PATH}")
    
    # Set up the client parameters correctly using StdioServerParameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["__main__.py"]  # Use the root module directly
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("\n========================================")
            print("Step 1: Connect to the database")
            print("========================================")
            try:
                connect_result = await session.call_tool("connect", {"db_path": DB_PATH})
                print(connect_result.content[0].text)
                
                # Get the connection ID (filename of the database)
                conn_id = os.path.basename(DB_PATH)
                
                print("\n========================================")
                print("Step 2: List available tables")
                print("========================================")
                tables_result = await session.call_tool("list_tables_tool", {"conn_id": conn_id})
                print(tables_result.content[0].text)
                
                print("\n========================================")
                print("Step 3: Filter tables containing 'com'")
                print("========================================")
                filter_result = await session.call_tool("filter_tables_tool", {
                    "conn_id": conn_id,
                    "substring": "com"
                })
                print(filter_result.content[0].text)
                
                print("\n========================================")
                print("Step 4: Get detailed schema for com_el table")
                print("========================================")
                schema_result = await session.call_tool("get_table_schema_tool", {
                    "conn_id": conn_id,
                    "table_name": "com_el"
                })
                print(schema_result.content[0].text)
                
                print("\n========================================")
                print("Step 5: Query data with formatted output")
                print("========================================")
                query_result = await session.call_tool("query_table_tool", {
                    "conn_id": conn_id,
                    "table_name": "com_el",
                    "limit": 5
                })
                print(query_result.content[0].text)
                
                print("\n========================================")
                print("Step 6: Execute a custom SQL query")
                print("========================================")
                sql_query = "SELECT sat_name, ntf_rsn FROM com_el WHERE ntf_rsn = 'C' LIMIT 5"
                sql_result = await session.call_tool("execute_sql_tool", {
                    "conn_id": conn_id,
                    "sql_query": sql_query
                })
                print(sql_result.content[0].text)
                
                print("\n========================================")
                print("Step 7: Disconnect from the database")
                print("========================================")
                disconnect_result = await session.call_tool("disconnect", {"conn_id": conn_id})
                print(disconnect_result.content[0].text)
                
            except Exception as e:
                print(f"Error: {e}")
                
            print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_connection())
