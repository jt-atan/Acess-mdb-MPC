# MCP Access Database Connector

A Model Context Protocol (MCP) tool for connecting to 32-bit Microsoft Access databases.

## Features

- Connect to MS Access MDB databases using 32-bit ODBC drivers
- Query database tables and views
- Run SQL queries against Access databases
- View table structures
- Filter tables by name
- Enhanced schema information with primary keys and indexes
- Improved result formatting with vertical display
- Intelligent truncation for large result sets
- Claude integration for large result sets

## Prerequisites

Before you begin, ensure you have the following installed:

- **Windows OS** (required for Microsoft Access ODBC drivers)
- **Python 3.8 or higher** (32-bit version recommended for compatibility)
- **32-bit Microsoft Access Database Engine** (see installation steps below)
- **Node.js** (only if using with Claude Desktop or Windsurf IDE)

## Detailed Installation Guide

### Step 1: Install Microsoft Access Database Engine (Required)

The Microsoft Access Database Engine provides the necessary ODBC drivers to connect to Access databases.

1. Download the 32-bit Microsoft Access Database Engine 2016 from Microsoft's website:
   - Go to: [https://www.microsoft.com/en-us/download/details.aspx?id=54920](https://www.microsoft.com/en-us/download/details.aspx?id=54920)
   - Click "Download" and select **AccessDatabaseEngine.exe** (32-bit version)
   - **Important:** You must use the 32-bit version even on 64-bit Windows

2. Install the downloaded file:
   - Run **AccessDatabaseEngine.exe** as administrator
   - Follow the installation prompts
   - If you already have a 64-bit Office installation, you may see a compatibility warning. Use the `/passive` flag to force installation:
     ```
     AccessDatabaseEngine.exe /passive
     ```

3. Verify installation:
   - Open Control Panel > Administrative Tools > ODBC Data Sources (32-bit)
   - You should see "Microsoft Access Driver (*.mdb, *.accdb)" in the Drivers tab

### Step 2: Set Up the MCP Access Tool

#### Option A: Simple Installation (Recommended)

1. Install the package directly from PyPI:
   ```
   pip install mcp-access
   ```

#### Option B: Manual Installation from Source

1. Download the tool files:
   - Download and extract the ZIP file from the repository, or
   - Clone the repository: `git clone https://github.com/yourusername/Access_mdb.git`

2. Navigate to the directory:
   ```
   cd Access_mdb
   ```

3. Install the package and dependencies:
   ```
   pip install -e .
   ```

#### Option C: Minimal Manual Setup (Advanced)

If you can't use git or pip, copy these essential files to a folder on your machine:

1. Create a directory structure:
   ```
   mkdir -p mcp_access
   ```

2. Create these files:
   - `mcp_access/__init__.py` (empty file)
   - `mcp_access/__main__.py` (with import and main() call)
   - `mcp_access/server.py` (with the MCP server code)
   - `pyproject.toml` (with package metadata)
   - `simple_client.py` (for testing)

3. Install required dependencies manually:
   ```
   pip install mcp pyodbc anyio click
   ```

### Step 3: Verify Your Installation

Run the test client to ensure everything is working:

```
python simple_client.py
```

If you see connection errors:
- Check that the database path in `simple_client.py` exists
- Verify the 32-bit Access driver is installed correctly
- Ensure you don't have the database open in another application

## Integrating with Claude Desktop

1. Locate the Claude configuration file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the MCP Access configuration:
   ```json
   {
     "mcpServers": {
       "access-mdb": {
         "command": "python",
         "args": [
           "-m",
           "mcp_access"
         ]
       }
     }
   }
   ```

3. Restart Claude Desktop

4. Test the connection by asking Claude:
   ```
   Connect to an MS Access database at C:\path\to\your\database.mdb
   ```

## Troubleshooting Guide

### "Driver not found" Error

**Problem:** You see an error message about missing Microsoft Access driver.

**Solution:**
1. Verify you installed the 32-bit Microsoft Access Database Engine
2. Check that you're running the tool with a 32-bit Python interpreter
3. On 64-bit Windows, be sure to use the 32-bit ODBC Administrator:
   - Run: `C:\Windows\SysWOW64\odbcad32.exe`
   - Verify "Microsoft Access Driver (*.mdb, *.accdb)" is listed

### "Cannot install Access Database Engine" Error

**Problem:** Installation fails with an error about Office 64-bit.

**Solution:**
1. Try installing with the /passive flag: `AccessDatabaseEngine.exe /passive`
2. If that fails, you may need to temporarily uninstall 64-bit Office, install the 32-bit Access Database Engine, then reinstall Office

### "Connection not found" Error in Claude

**Problem:** Claude reports "Connection not found" when trying to use tools.

**Solution:**
1. Make sure you've connected first with the connect tool
2. Check that you're using the filename as conn_id, not the full path
3. Try connecting again if the connection might have timed out

### "Table not found" Error

**Problem:** Claude reports a table doesn't exist.

**Solution:**
1. Verify the table exists using list_tables_tool
2. Check for typos in the table name
3. For tables with spaces, ensure the name is in square brackets: `[Table Name]`

## Common Commands for Claude

When using this tool with Claude Desktop, here are the key commands to use:

1. Connect to a database:
   ```
   connect(db_path="C:\\path\\to\\database.mdb")
   ```

2. List all tables:
   ```
   list_tables_tool(conn_id="database.mdb")
   ```

3. Get table schema:
   ```
   get_table_schema_tool(conn_id="database.mdb", table_name="tablename")
   ```

4. Query a table:
   ```
   query_table_tool(conn_id="database.mdb", table_name="tablename", limit=10)
   ```

5. Run a custom SQL query:
   ```
   execute_sql_tool(conn_id="database.mdb", sql_query="SELECT * FROM tablename")
   ```

6. Disconnect:
   ```
   disconnect(conn_id="database.mdb")
   ```

## Technical Notes for Advanced Users

### Python Architecture Considerations

This tool requires a 32-bit ODBC driver, which means:
- The ODBC driver itself must be 32-bit
- If running directly (not through Claude), you need a 32-bit Python interpreter
- When running through Claude Desktop, Claude handles the process architecture

### Environment Variables

You can customize behavior with these environment variables:
- `EXECUTE_QUERY_MAX_CHARS`: Maximum characters to display in query results (default: 4000)
- `CLAUDE_LOCAL_FILES_PATH`: Path where result files should be saved for Claude's access

### Connection Details

- Connection IDs are based on the database filename, not the full path
- Connections remain active until explicitly disconnected or the server is restarted
- MS Access has a limit of 255 concurrent connections

## Function List

The MCP Access tool provides the following key functions:

1. **connect_to_access_db**: Connects to an Access database using the 32-bit ODBC driver
2. **list_tables**: Lists all tables in the Access database
3. **query_table**: Queries data from a specific table
4. **execute_sql**: Executes a custom SQL query
5. **get_table_schema**: Gets basic schema information for a table
6. **get_extended_schema**: Gets detailed schema with primary keys and indexes
7. **format_results**: Formats query results in a clean vertical format
8. **save_results_for_claude**: Saves large result sets for Claude to access

## MCP Tool Commands

The MCP Access tool exposes the following tools to LLMs:

1. **connect**: Connect to an MS Access database
2. **list_tables_tool**: List all tables in the database
3. **filter_tables_tool**: List tables containing a specific substring
4. **query_table_tool**: Query data from a table with formatting
5. **execute_sql_tool**: Execute a custom SQL query
6. **get_table_schema_tool**: Get detailed schema information
7. **disconnect**: Disconnect from a database

## Using the MCP Tool with LLMs

### IMPORTANT: Instructions for LLMs

If you are an LLM (like Claude or GPT) using this MCP tool in Windsurf or other environments, please follow these exact instructions to avoid failures:

1. **Tool Names**: Use the EXACT tool names as specified below:
   - `connect` - NOT "connect_to_database" or any variation
   - `list_tables_tool` - NOT "list_tables" or "get_tables"
   - `filter_tables_tool` - NOT "filter_tables" or "search_tables"
   - `query_table_tool` - NOT "query_table" or "select_from_table"
   - `execute_sql_tool` - NOT "execute_sql" or "run_sql"
   - `get_table_schema_tool` - NOT "get_schema" or "describe_table"
   - `disconnect` - NOT "close_connection" or "disconnect_from_database"

2. **Parameter Names**: Use the EXACT parameter names:
   - For connect: `db_path` (full path to .mdb file)
   - For all other tools: `conn_id` (the database filename)
   - For query/filter tools: `table_name`, `substring`, `limit`, `sql_query` as needed

3. **Connection ID**: Always use the filename (e.g., "database.mdb") as the connection ID, not the full path.

4. **SQL Syntax**: Use MS Access SQL syntax:
   - Use `TOP n` instead of `LIMIT n` (e.g., "SELECT TOP 5 * FROM table")
   - Enclose table/column names with spaces in square brackets (e.g., "[Table Name]")

5. **Error Handling**: If a tool call fails:
   - Check parameter names and values
   - Verify the connection ID is correct
   - Ensure the table name exists (use list_tables_tool first)
   - Try again with corrected parameters

### Example Workflow

```
# Step 1: Connect to the database
connect(db_path="C:\\path\\to\\database.mdb")

# Step 2: List all tables
list_tables_tool(conn_id="database.mdb")

# Step 3: Filter tables containing "customer"
filter_tables_tool(conn_id="database.mdb", substring="customer")

# Step 4: Get schema information
get_table_schema_tool(conn_id="database.mdb", table_name="customers")

# Step 5: Query data
query_table_tool(conn_id="database.mdb", table_name="customers", limit=10)

# Step 6: Execute a custom SQL query
execute_sql_tool(conn_id="database.mdb", sql_query="SELECT TOP 5 * FROM customers WHERE region='North'")

# Step 7: Disconnect
disconnect(conn_id="database.mdb")
```

## Windsurf IDE Integration

1. Open Windsurf IDE
2. Click on the hammer icon in the Cascade toolbar
3. Select "Configure"
4. Add the following configuration:
   ```json
   {
     "mcpServers": {
       "access-mdb": {
         "command": "python",
         "args": [
           "-m",
           "mcp_access"
         ],
         "cwd": "C:\\path\\to\\Access_mdb"
       }
     }
   }
   ```
5. Save and click "Refresh"

## Prompting Guide for LLMs

When working with LLMs like Claude or other models in Windsurf, use these prompt patterns:

1. **Connecting to a database**:
   ```
   Connect to the MS Access database at C:\path\to\database.mdb
   ```

2. **Listing tables**:
   ```
   List all tables in the MS Access database
   ```

3. **Querying data**:
   ```
   Query the [table_name] table in the MS Access database
   ```
   
4. **Running SQL**:
   ```
   Execute this SQL query on the MS Access database: SELECT * FROM [table_name] WHERE [condition]
   ```

5. **Getting schema**:
   ```
   Show me the schema of the [table_name] table in the MS Access database
   ```

## License

MIT License

## Acknowledgements

This project uses the Model Context Protocol (MCP) developed by Anthropic for Claude AI.
