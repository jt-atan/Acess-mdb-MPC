import os
import json
import anyio
import click
import pyodbc
from mcp.server.fastmcp import FastMCP

# Create the FastMCP server
mcp = FastMCP("MS Access Connector")

# Store connections in a dictionary
connections = {}

async def connect_to_access_db(
    db_path: str,
) -> pyodbc.Connection:
    """Connect to an Access database using the 32-bit ODBC driver."""
    # Note: Must be running on Windows with 32-bit Access ODBC driver installed
    connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
    
    # Use a thread pool to run ODBC operations asynchronously
    # since pyodbc operations are blocking
    connection = await anyio.to_thread.run_sync(
        lambda: pyodbc.connect(connection_string)
    )
    return connection


async def list_tables(
    connection: pyodbc.Connection,
) -> list[str]:
    """List all tables in the Access database."""
    def _get_tables():
        cursor = connection.cursor()
        tables = [table.table_name for table in cursor.tables() 
                 if table.table_type == 'TABLE']
        cursor.close()
        return tables
    
    tables = await anyio.to_thread.run_sync(_get_tables)
    return tables


async def query_table(
    connection: pyodbc.Connection,
    table_name: str,
    limit: int = 100,
) -> list[dict]:
    """Query data from a table."""
    def _run_query():
        cursor = connection.cursor()
        cursor.execute(f"SELECT TOP {limit} * FROM [{table_name}]")
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            # Convert row to a list of values that can be serialized to JSON
            row_values = [str(value) if isinstance(value, (bytes, bytearray)) else value for value in row]
            results.append(dict(zip(columns, row_values)))
        cursor.close()
        return results
    
    results = await anyio.to_thread.run_sync(_run_query)
    return results


async def execute_sql(
    connection: pyodbc.Connection,
    sql_query: str,
) -> dict:
    """Execute a custom SQL query."""
    def _run_query():
        cursor = connection.cursor()
        cursor.execute(sql_query)
        
        # If the query returns results
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                # Convert row to a list of values that can be serialized to JSON
                row_values = [str(value) if isinstance(value, (bytes, bytearray)) else value for value in row]
                results.append(dict(zip(columns, row_values)))
            return {"result_type": "query", "data": results}
        else:
            # For non-query operations like INSERT, UPDATE, DELETE
            connection.commit()
            return {"result_type": "command", "rows_affected": cursor.rowcount}
    
    result = await anyio.to_thread.run_sync(_run_query)
    return result


async def get_table_schema(
    connection: pyodbc.Connection,
    table_name: str,
) -> list[dict]:
    """Get the schema of a specific table."""
    def _get_schema():
        cursor = connection.cursor()
        cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
        columns = []
        for column in cursor.description:
            columns.append({
                "name": column[0],
                "type": type_mapping.get(column[1].__name__, column[1].__name__),
                "nullable": column[6],
            })
        cursor.close()
        return columns
    
    # Mapping from Python types to more friendly names
    type_mapping = {
        "str": "text",
        "int": "integer",
        "float": "float",
        "datetime": "datetime",
        "bool": "boolean",
        "bytes": "binary",
    }
    
    schema = await anyio.to_thread.run_sync(_get_schema)
    return schema


# Define MCP tools using FastMCP decorators

@mcp.tool()
async def connect(db_path: str) -> str:
    """Connect to an MS Access database
    
    Args:
        db_path: Path to the MS Access .mdb file
    
    Returns:
        A message indicating success or failure
    """
    conn_id = os.path.basename(db_path)
    
    try:
        connection = await connect_to_access_db(db_path)
        connections[conn_id] = connection
        return f"Successfully connected to database: {db_path}"
    except Exception as e:
        return f"Error connecting to database: {str(e)}"


@mcp.tool()
async def list_tables_tool(conn_id: str) -> str:
    """List all tables in the connected database
    
    Args:
        conn_id: Connection ID (filename of database)
    
    Returns:
        A comma-separated list of table names
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        tables = await list_tables(connections[conn_id])
        return f"Tables in database: {', '.join(tables)}"
    except Exception as e:
        return f"Error listing tables: {str(e)}"


@mcp.tool()
async def query_table_tool(conn_id: str, table_name: str, limit: int = 100) -> str:
    """Query data from a table
    
    Args:
        conn_id: Connection ID (filename of database)
        table_name: Name of the table to query
        limit: Maximum number of rows to return (default: 100)
    
    Returns:
        JSON-formatted query results
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        results = await query_table(connections[conn_id], table_name, limit)
        # Format results as a readable table
        formatted_results = json.dumps(results, indent=2)
        return f"Query results:\n{formatted_results}"
    except Exception as e:
        return f"Error querying table: {str(e)}"


@mcp.tool()
async def execute_sql_tool(conn_id: str, sql_query: str) -> str:
    """Execute a custom SQL query
    
    Args:
        conn_id: Connection ID (filename of database)
        sql_query: SQL query to execute
    
    Returns:
        JSON-formatted query results or command results
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        result = await execute_sql(connections[conn_id], sql_query)
        # Format results as a readable table
        formatted_result = json.dumps(result, indent=2)
        return f"SQL execution result:\n{formatted_result}"
    except Exception as e:
        return f"Error executing SQL: {str(e)}"


@mcp.tool()
async def get_table_schema_tool(conn_id: str, table_name: str) -> str:
    """Get the schema of a specific table
    
    Args:
        conn_id: Connection ID (filename of database)
        table_name: Name of the table to examine
    
    Returns:
        JSON-formatted schema information
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        schema = await get_table_schema(connections[conn_id], table_name)
        # Format schema as a readable table
        formatted_schema = json.dumps(schema, indent=2)
        return f"Table schema:\n{formatted_schema}"
    except Exception as e:
        return f"Error getting table schema: {str(e)}"


@mcp.tool()
async def disconnect(conn_id: str) -> str:
    """Disconnect from a database
    
    Args:
        conn_id: Connection ID (filename of database)
    
    Returns:
        A message indicating success or failure
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        await anyio.to_thread.run_sync(lambda: connections[conn_id].close())
        del connections[conn_id]
        return f"Successfully disconnected from database: {conn_id}"
    except Exception as e:
        return f"Error disconnecting: {str(e)}"


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """Run the MCP Access server"""
    if transport == "sse":
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    main()
