import os
import json
import anyio
import click
import pyodbc
import hashlib
import sys
from datetime import datetime, date
from mcp.server.fastmcp import FastMCP

# Create the FastMCP server
mcp = FastMCP("MS Access Connector")

# Store connections in a dictionary
connections = {}

# Configuration constants
EXECUTE_QUERY_MAX_CHARS = int(os.environ.get('EXECUTE_QUERY_MAX_CHARS', 4000))
CLAUDE_FILES_PATH = os.environ.get('CLAUDE_LOCAL_FILES_PATH')

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
    """List all tables in the Access database, including linked tables."""
    def _get_tables():
        cursor = connection.cursor()
        # First, let's log all available table types for diagnostic purposes
        table_types = set()
        all_tables = []
        for table in cursor.tables():
            table_types.add(table.table_type)
            all_tables.append((table.table_name, table.table_type))
            
        print(f"Available table types: {table_types}")
            
        # Print detected table types for debugging
        print(f"Detected table types: {table_types}")
        
        # Access can use different designations for different types of tables
        # Let's capture all actual tables excluding internal metadata tables
        system_table_prefixes = ('MSys', '~TMP')
        tables = [table.table_name for table in cursor.tables() 
                 if not any(table.table_name.startswith(prefix) for prefix in system_table_prefixes)
                 or table.table_type == 'SYSTEM TABLE']  # Include system tables explicitly marked
        
        # Also try to get linked tables using a special query for Access
        try:
            linked_tables_cursor = connection.cursor()
            # Query MSysObjects which contains information about all database objects including linked tables
            linked_tables_cursor.execute("SELECT Name FROM MSysObjects WHERE Type=6")
            linked_table_names = [row.Name for row in linked_tables_cursor.fetchall()]
            linked_tables_cursor.close()
            
            # Add linked tables to our list if they're not already included
            for linked_table in linked_table_names:
                if linked_table not in tables:
                    tables.append(linked_table)
                    print(f"Added linked table from MSysObjects: {linked_table}")
        except Exception as e:
            print(f"Note: Could not retrieve linked tables from MSysObjects: {e}")
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


async def get_extended_schema(
    connection: pyodbc.Connection,
    table_name: str,
) -> dict:
    """Get more detailed schema including primary keys and indexes."""
    schema_info = await get_table_schema(connection, table_name)
    
    def _get_primary_keys_and_indexes():
        cursor = connection.cursor()
        primary_keys = []
        indexes = []
        
        # Get indexes (which include primary keys in Access)
        try:
            # This will get all indexes in the table
            for index_info in cursor.statistics(table=table_name):
                if index_info[5]:  # index_name is not None
                    index_name = index_info[5]
                    column_name = index_info[8]
                    is_unique = not index_info[6]  # non_unique = 0 means it's unique
                    
                    # In Access, primary key is typically an index named "PrimaryKey"
                    if index_name == "PrimaryKey" or "PK" in index_name:
                        primary_keys.append(column_name)
                    
                    # Store index information
                    indexes.append({
                        "name": index_name,
                        "column": column_name,
                        "unique": is_unique
                    })
        except Exception as e:
            # Access databases might not fully support this method
            pass
            
        # If we didn't find primary keys using statistics, try another approach
        if not primary_keys:
            try:
                # Try to find primary keys using a heuristic approach for Access
                # In Access, primary keys often have an AutoNumber data type
                cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
                for i, col in enumerate(cursor.description):
                    col_name = col[0]
                    if col[5]:  # is_autoincrement flag
                        primary_keys.append(col_name)
            except:
                pass
        
        cursor.close()
        return {"primary_keys": primary_keys, "indexes": indexes}
    
    pk_index_info = await anyio.to_thread.run_sync(_get_primary_keys_and_indexes)
    
    # Mark primary keys in the schema
    for column in schema_info:
        column["primary_key"] = column["name"] in pk_index_info["primary_keys"]
    
    return {
        "columns": schema_info,
        "primary_keys": pk_index_info["primary_keys"],
        "indexes": pk_index_info["indexes"]
    }


def format_value(val):
    """Format a value for display, handling None and datetime types"""
    if val is None:
        return "NULL"
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return str(val)


def format_results(results, max_chars=None):
    """Format rows in a clean vertical format with intelligent truncation"""
    if not max_chars:
        max_chars = EXECUTE_QUERY_MAX_CHARS
        
    output = ""
    row_displayed = 0
    current_size = 0
    
    for i, row in enumerate(results, 1):
        line = f"{i}. row\n"
        for col, val in row.items():
            line += f"{col}: {format_value(val)}\n"
        line += "\n"
        
        current_size += len(line)
        if max_chars and current_size > max_chars:
            break
            
        output += line
        row_displayed = i
    
    # Add summary information
    total_rows = len(results)
    output += f"\nResult: {total_rows} rows"
    if row_displayed < total_rows:
        output += f" (output truncated, showing {row_displayed} of {total_rows})"
    
    return output, row_displayed


def save_results_for_claude(results):
    """Save full result sets as JSON files for Claude to access"""
    if not CLAUDE_FILES_PATH:
        return ""
        
    # Create a serializable version of the results
    serializable_results = json.dumps(results)
    file_hash = hashlib.sha256(serializable_results.encode()).hexdigest()
    file_name = f"{file_hash}.json"
    file_path = os.path.join(CLAUDE_FILES_PATH, file_name)
    
    try:
        with open(file_path, 'w') as f:
            f.write(serializable_results)
            
        return (f"\nFull result set url: https://cdn.jsdelivr.net/pyodide/claude-local-files/{file_name}"
                " (format: JSON array of objects)"
                " (ALWAYS prefer fetching this url in artifacts instead of hardcoding the values)")
    except Exception as e:
        return f"\nError saving results for Claude: {str(e)}"


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
async def filter_tables_tool(conn_id: str, substring: str) -> str:
    """List tables containing a specific substring
    
    Args:
        conn_id: Connection ID (filename of database)
        substring: Substring to search for in table names (case insensitive)
    
    Returns:
        A comma-separated list of matching table names
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        all_tables = await list_tables(connections[conn_id])
        filtered_tables = [table for table in all_tables if substring.lower() in table.lower()]
        
        if filtered_tables:
            return f"Tables containing '{substring}': {', '.join(filtered_tables)}"
        else:
            return f"No tables found containing '{substring}'"
    except Exception as e:
        return f"Error filtering tables: {str(e)}"


@mcp.tool()
async def query_table_tool(conn_id: str, table_name: str, limit: int = 100) -> str:
    """Query data from a table
    
    Args:
        conn_id: Connection ID (filename of database)
        table_name: Name of the table to query
        limit: Maximum number of rows to return (default: 100)
    
    Returns:
        Formatted query results
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        results = await query_table(connections[conn_id], table_name, limit)
        
        if not results:
            return f"No data found in table '{table_name}'"
            
        # Format the results using the improved formatter
        formatted_output, row_displayed = format_results(results)
        
        # For large result sets, save them for Claude
        if len(results) > row_displayed and CLAUDE_FILES_PATH:
            claude_link = save_results_for_claude(results)
            formatted_output += claude_link
            
        return formatted_output
    except pyodbc.Error as e:
        error_msg = str(e)
        suggestions = ""
        
        if "not a valid name" in error_msg.lower():
            suggestions = "\nPossible fix: Make sure the table name is correct and enclosed in square brackets if it contains spaces or special characters."
            
        return f"Database Error: {error_msg}{suggestions}"
    except Exception as e:
        return f"Error querying table: {str(e)}"


@mcp.tool()
async def execute_sql_tool(conn_id: str, sql_query: str) -> str:
    """Execute a custom SQL query
    
    Args:
        conn_id: Connection ID (filename of database)
        sql_query: SQL query to execute
    
    Returns:
        Formatted query results or command results
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        result = await execute_sql(connections[conn_id], sql_query)
        
        if result["result_type"] == "command":
            return f"Command executed successfully. Rows affected: {result['rows_affected']}"
        else:
            data = result["data"]
            if not data:
                return "Query executed successfully. No rows returned."
                
            # Format the results using the improved formatter
            formatted_output, row_displayed = format_results(data)
            
            # For large result sets, save them for Claude
            if len(data) > row_displayed and CLAUDE_FILES_PATH:
                claude_link = save_results_for_claude(data)
                formatted_output += claude_link
                
            return formatted_output
    except pyodbc.Error as e:
        error_msg = str(e)
        suggestions = ""
        
        # Add helpful suggestions based on common errors
        if "syntax error" in error_msg.lower():
            suggestions = "\nPossible fix: Check your SQL syntax for errors."
        elif "no such table" in error_msg.lower() or "invalid object name" in error_msg.lower():
            suggestions = "\nPossible fix: Verify the table name exists."
        elif "ambiguous column name" in error_msg.lower():
            suggestions = "\nPossible fix: Fully qualify column names with table names."
            
        return f"SQL Error: {error_msg}{suggestions}"
    except Exception as e:
        return f"Error executing query: {str(e)}"


@mcp.tool()
async def get_table_schema_tool(conn_id: str, table_name: str) -> str:
    """Get the schema of a specific table
    
    Args:
        conn_id: Connection ID (filename of database)
        table_name: Name of the table to examine
    
    Returns:
        Formatted schema information
    """
    if conn_id not in connections:
        return f"Connection {conn_id} not found"
    
    try:
        schema_info = await get_extended_schema(connections[conn_id], table_name)
        
        # Format the schema information in a readable way
        output = [f"Schema for table '{table_name}':"]
        output.append("\nCOLUMNS:")
        
        for column in schema_info["columns"]:
            pk_indicator = "[PK] " if column.get("primary_key") else ""
            nullable = "NULL" if column.get("nullable") else "NOT NULL"
            output.append(f"  {pk_indicator}{column['name']}: {column['type']}, {nullable}")
        
        # Add primary key information
        if schema_info["primary_keys"]:
            output.append("\nPRIMARY KEYS:")
            for pk in schema_info["primary_keys"]:
                output.append(f"  {pk}")
        
        # Add index information
        if schema_info["indexes"]:
            output.append("\nINDEXES:")
            for idx in schema_info["indexes"]:
                unique = "UNIQUE " if idx.get("unique") else ""
                output.append(f"  {unique}INDEX {idx['name']} on {idx['column']}")
        
        return "\n".join(output)
    except pyodbc.Error as e:
        return f"Database Error: {str(e)}"
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
        return f"Successfully disconnected from {conn_id}"
    except Exception as e:
        return f"Error disconnecting: {str(e)}"


def main():
    """Run the MCP Access server"""
    # Check for required CLAUDE_FILES_PATH environment variable
    if CLAUDE_FILES_PATH and not os.path.exists(CLAUDE_FILES_PATH):
        try:
            os.makedirs(CLAUDE_FILES_PATH)
            print(f"Created directory for Claude files: {CLAUDE_FILES_PATH}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not create directory for Claude files: {e}", file=sys.stderr)
    
    # Print server information
    print(f"Starting MS Access Connector MCP server...", file=sys.stderr)
    print(f"Python version: {os.sys.version}", file=sys.stderr)
    print(f"Current directory: {os.getcwd()}", file=sys.stderr)
    
    # Run the server with default settings
    mcp.run()


if __name__ == "__main__":
    main()
