# MCP Access Database Connector

A Model Context Protocol (MCP) tool for connecting to 32-bit Microsoft Access databases.

## Features

- Connect to MS Access MDB databases using 32-bit drivers
- Query database tables and views
- Run SQL queries against Access databases
- View table structures

## Requirements

- Windows OS (for MS Access drivers)
- Python 3.8 or higher
- 32-bit ODBC driver for Microsoft Access
- Node.js (for Claude Desktop and Windsurf IDE integration)

## Installation

### Step 1: Install Required Drivers

1. Install the 32-bit Microsoft Access Database Engine 2016:
   - Download from [Microsoft's website](https://www.microsoft.com/en-us/download/details.aspx?id=54920)
   - Choose the 32-bit version (`AccessDatabaseEngine.exe`)
   - Run the installer and follow the prompts

### Step 2: Set Up Python Environment

1. Install Python 3.8 or higher (32-bit version recommended for compatibility)
2. Clone this repository:
   ```
   git clone https://github.com/yourusername/Access_mdb.git
   cd Access_mdb
   ```
3. Install the package:
   ```
   pip install -e .
   ```

### Step 3: Test the Installation

Run the simple client to test the connection:
```
python simple_client.py
```

## Manual Setup on Another Machine

If you want to set up this tool on another machine without using git, here are the minimal files you need to copy:

### Essential Files:
1. `mcp_access/__init__.py` - Makes the directory a Python package
2. `mcp_access/__main__.py` - Entry point for running as a module
3. `mcp_access/server.py` - Main server implementation with all the MCP tools
4. `pyproject.toml` - Contains package metadata and dependencies
5. `README.md` - Documentation
6. `simple_client.py` - For testing the connection

### After Copying Files:
1. Install dependencies on the target machine:
   ```
   pip install mcp pyodbc anyio click
   ```
2. Install the 32-bit Microsoft Access Database Engine
3. Run the server:
   ```
   python -m mcp_access
   ```

## Integration with LLM Tools

### Claude Desktop Integration

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
         ],
         "cwd": "C:\\path\\to\\Access_mdb"
       }
     }
   }
   ```
   
3. Restart Claude Desktop

### Windsurf IDE Integration

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

## MCP Tool Commands Reference

The MCP Access tool provides the following commands that can be used by LLMs:

### 1. connect

Connects to an MS Access database.

**Parameters:**
- `db_path`: Full path to the .mdb file

**Example:**
```
connect(db_path="C:\\path\\to\\database.mdb")
```

### 2. list_tables_tool

Lists all tables in the connected database.

**Parameters:**
- `conn_id`: Connection ID (filename of the database)

**Example:**
```
list_tables_tool(conn_id="database.mdb")
```

### 3. query_table_tool

Queries data from a specific table.

**Parameters:**
- `conn_id`: Connection ID (filename of the database)
- `table_name`: Name of the table to query
- `limit`: Maximum number of rows to return (default: 100)

**Example:**
```
query_table_tool(conn_id="database.mdb", table_name="customers", limit=50)
```

### 4. execute_sql_tool

Executes a custom SQL query.

**Parameters:**
- `conn_id`: Connection ID (filename of the database)
- `sql_query`: SQL query to execute

**Example:**
```
execute_sql_tool(conn_id="database.mdb", sql_query="SELECT * FROM customers WHERE region='North'")
```

### 5. get_table_schema_tool

Gets the schema of a specific table.

**Parameters:**
- `conn_id`: Connection ID (filename of the database)
- `table_name`: Name of the table to examine

**Example:**
```
get_table_schema_tool(conn_id="database.mdb", table_name="customers")
```

### 6. disconnect

Disconnects from a database.

**Parameters:**
- `conn_id`: Connection ID (filename of the database)

**Example:**
```
disconnect(conn_id="database.mdb")
```

## Using the MCP Tool with LLMs

### Step-by-Step Guide for Effective Prompting

For LLMs to effectively use this MCP tool with MS Access databases, follow these steps:

1. **Start with a clear database connection**:
   ```
   Connect to the MS Access database at C:\path\to\your\database.mdb
   ```

2. **After connecting, use the filename as the connection ID**:
   - The connection ID is simply the filename of the database (e.g., "database.mdb")
   - This ID must be used in all subsequent tool calls

3. **Work in a specific order**:
   1. First, connect to the database
   2. Then list tables to explore the database
   3. Use get_table_schema_tool to understand table structure
   4. After that, query data or execute SQL

4. **Always disconnect when done**:
   ```
   Disconnect from the database.mdb connection
   ```

### Example Conversation Flow with an LLM

Here's a complete example of how to interact with an LLM using this tool:

```
User: Connect to the MS Access database at C:\path\to\database.mdb and list the tables.

LLM: I'll connect to the database and list the tables for you.
[Calls connect tool with db_path]
[Calls list_tables_tool with conn_id="database.mdb"]
Here are the tables in your database: [lists tables]

User: Show me the schema of the customers table.

LLM: I'll show you the schema of the customers table.
[Calls get_table_schema_tool with conn_id="database.mdb", table_name="customers"]
Here's the schema of the customers table: [shows schema]

User: Get me all customers from the North region.

LLM: I'll query the customers from the North region.
[Calls execute_sql_tool with conn_id="database.mdb", sql_query="SELECT * FROM customers WHERE region='North'"]
Here are the customers from the North region: [shows results]
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Tool Not Found Errors

**Problem**: LLM returns "unknown tool name" or fails to use the correct tool.

**Solution**:
- Ensure you're providing the exact tool names as listed in this documentation
- Remember all tool names end with "_tool" except "connect" and "disconnect"
- The most common mistake is forgetting the "_tool" suffix on list_tables_tool, query_table_tool, etc.

#### 2. Connection Issues

**Problem**: "Error connecting to database" or similar messages.

**Solution**:
- Verify the database path is correct and the file exists
- Ensure the 32-bit Microsoft Access Database Engine is installed
- Check that the path uses double backslashes in Windows paths (C:\\path\\to\\file.mdb)
- Make sure the MDB file isn't open in another application

#### 3. SQL Syntax Errors

**Problem**: "Syntax error in query expression" messages.

**Solution**:
- MS Access uses specific SQL syntax that differs from standard SQL:
  - Use `TOP n` instead of `LIMIT n`
  - Use `*` for wildcard selection, not `%`
  - Date literals should be formatted as `#MM/DD/YYYY#`

#### 4. LLM Looping or Confusion

**Problem**: LLM keeps trying incorrect approaches or gets confused.

**Solution**:
- Reset the conversation and start with explicit step-by-step instructions
- Provide complete examples of the exact command syntax
- Remind the LLM of the connection ID (the database filename)
- If using Windsurf IDE, try restarting the MCP server by clicking "Refresh"

#### 5. Table or Field Not Found

**Problem**: "Table or field not found" errors.

**Solution**:
- First list all tables with list_tables_tool to verify the table name
- Get the table schema to verify field names
- MS Access is case-insensitive for table and field names, but exact spelling matters

### Verifying Tool Installation

If you're unsure if the MCP tool is properly installed:

1. Check if the MCP server appears in the hammer icon menu
2. Try a basic connection test:
   ```
   Connect to an MS Access database at C:\path\to\any_existing.mdb
   ```
3. If the LLM reports it can't find the tool, check your configuration file

### MS Access-Specific Notes

1. MS Access has a 2GB file size limit
2. It doesn't support nested queries as well as other database systems
3. Table and column names with spaces need square brackets: `[Table Name]`

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

## Troubleshooting

- **Error: "Driver not found"**: Ensure you've installed the 32-bit Microsoft Access Database Engine
- **Connection issues**: Verify the database path is correct and accessible
- **Integration issues**: Check the configuration file syntax and paths
