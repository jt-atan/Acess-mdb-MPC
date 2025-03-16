"""
Simple client to test the MCP Access tool
"""
import os
import sys
import asyncio
import json
from pathlib import Path

# Import the MCP client tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to the Access database
DB_PATH = str(Path(__file__).parent / "ific3033.mdb")

async def test_connection():
    """Test connecting to the database"""
    print(f"Testing connection to database: {DB_PATH}")
    
    # Set up the client parameters correctly using StdioServerParameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_access"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Step 1: List available tools
            print("\nStep 1: Listing available tools...")
            tools = await session.list_tools()
            print(f"Available tools: {tools}")
            
            # Step 2: Connect to the database
            print("\nStep 2: Connecting to the database...")
            try:
                connect_result = await session.call_tool("connect", {"db_path": DB_PATH})
                print(connect_result.content[0].text)
                
                # Get the connection ID (filename of the database)
                conn_id = os.path.basename(DB_PATH)
                
                # Step 3: Execute SQL query to find satellite networks with ntf_rsn = 'C'
                print("\nStep 3: Querying com_el table for satellite networks with ntf_rsn = 'C'...")
                sql_query = "SELECT sat_name FROM com_el WHERE ntf_rsn = 'C'"
                query_result = await session.call_tool("execute_sql_tool", {
                    "conn_id": conn_id,
                    "sql_query": sql_query
                })
                
                # Parse and display the results
                result_text = query_result.content[0].text
                print("Query result:")
                print(result_text)
                
                # Extract the JSON part from the result text
                try:
                    # Find the JSON part in the result text
                    json_start = result_text.find('{')
                    if json_start != -1:
                        json_text = result_text[json_start:]
                        result_data = json.loads(json_text)
                        
                        print("\nSatellite Networks with ntf_rsn = 'C':")
                        if 'data' in result_data:
                            for row in result_data['data']:
                                if 'sat_name' in row:
                                    print(f"- {row['sat_name']}")
                        else:
                            print("No data found in the result.")
                    else:
                        print("No JSON data found in the result.")
                except Exception as e:
                    print(f"Error parsing result: {e}")
                
                # Step 4: Disconnect from the database
                print("\nStep 4: Disconnecting from the database...")
                disconnect_result = await session.call_tool("disconnect", {"conn_id": conn_id})
                print(disconnect_result.content[0].text)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
