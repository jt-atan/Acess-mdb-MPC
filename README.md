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
- **Enhanced support for linked tables** - Now properly detects and lists linked tables from external MDB files

## Quick Setup Guide

This guide assumes you already have 32-bit Microsoft Access Database Engine installed on your machine.

### Step 1: Clone the Repository

```bash
git clone https://github.com/jt-atan/Acess-mdb-MPC.git
cd Access_mdb
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -e .
```

This will install all required dependencies:
- mcp
- pyodbc
- anyio
- click

### Step 4: Configure with Windsurf or Claude Desktop

#### For Windsurf:

Add this to your Windsurf MCP configuration file:

```json
{
  "mcpServers": {
    "access-mdb": {
      "command": "python",
      "args": [
        "C:\\Users\\yourusername\\path\\to\\Access_mdb\\server.py"
      ],
      "cwd": "C:\\Users\\yourusername\\path\\to\\Access_mdb"
    }
  }
}
```

Make sure to:
1. Replace `yourusername` and `path\\to` with your actual path
2. Use the full absolute path to the server.py file
3. Set the correct working directory (cwd)

#### For Claude Desktop:

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
           "C:\\Users\\yourusername\\path\\to\\Access_mdb\\server.py"
         ],
         "cwd": "C:\\Users\\yourusername\\path\\to\\Access_mdb"
       }
     }
   }
   ```

3. Restart Claude Desktop

### Step 5: Test the Connection

Use the following commands to test your connection:

```
connect(db_path="C:\\path\\to\\your\\database.mdb")
list_tables_tool(conn_id="database.mdb")
```

## Detailed Usage Guide

### Basic Commands

1. **Connect to a database**:
   ```
   connect(db_path="C:\\path\\to\\database.mdb")
   ```

2. **List all tables** (including linked tables):
   ```
   list_tables_tool(conn_id="database.mdb")
   ```
   Note: The `conn_id` is just the filename of the database, not the full path.

3. **Get table schema**:
   ```
   get_table_schema_tool(conn_id="database.mdb", table_name="tablename")
   ```
   Note: Works with both regular and linked tables.

4. **Query a table** (limit defaults to 100 rows):
   ```
   query_table_tool(conn_id="database.mdb", table_name="tablename", limit=10)
   ```
   Note: Works with both regular and linked tables.

5. **Run a custom SQL query**:
   ```
   execute_sql_tool(conn_id="database.mdb", sql_query="SELECT * FROM tablename WHERE column = 'value'")
   ```
   Advanced example with linked tables:
   ```
   execute_sql_tool(conn_id="database.mdb", sql_query="SELECT t1.field1, t2.field2 FROM local_table t1 JOIN linked_table t2 ON t1.id = t2.id")
   ```

6. **Filter tables by name**:
   ```
   filter_tables_tool(conn_id="database.mdb", substring="user")
   ```
   Example to filter linked tables (if they follow a naming pattern):
   ```
   filter_tables_tool(conn_id="database.mdb", substring="link_")
   ```

7. **Disconnect from database**:
   ```
   disconnect(conn_id="database.mdb")
   ```


### Working with Linked Tables

Linked tables are fully supported and can be used like regular tables:

1. **Finding linked tables**:
   All linked tables are now included when using `list_tables_tool()`.
   
2. **Querying linked tables**:
   ```
   query_table_tool(conn_id="database.mdb", table_name="linked_table")
   ```
   
3. **Joining local and linked tables**:
   ```
   execute_sql_tool(conn_id="database.mdb", sql_query="SELECT a.field1, b.field2 FROM local_table a JOIN linked_table b ON a.id = b.id")
   ```
   
4. **Viewing linked table schema**:
   ```
   get_table_schema_tool(conn_id="database.mdb", table_name="linked_table")
   ```

### Advanced Usage

#### Working with Tables with Spaces in Names

For tables with spaces in their names, use square brackets:

```
query_table_tool(conn_id="database.mdb", table_name="[Table Name]")
```

#### Handling Large Result Sets

When querying large tables, use the limit parameter to restrict the number of rows returned:

```
query_table_tool(conn_id="database.mdb", table_name="large_table", limit=20)
```

#### Working with Access Saved Queries

While there is no dedicated API for saved queries, you can still execute them using the standard SQL execution tool:

```
execute_sql_tool(conn_id="database.mdb", sql_query="SELECT * FROM [QueryName]")
```

Note: In MS Access, saved queries can be referenced in SQL statements just like tables. The square brackets are important if the query name contains spaces.

## Troubleshooting Guide

### "Driver not found" Error

**Problem:** You see an error message about missing Microsoft Access driver.

**Solution:**
1. Verify you installed the 32-bit Microsoft Access Database Engine
2. Check that you're running the tool with a 32-bit Python interpreter
3. On 64-bit Windows, be sure to use the 32-bit ODBC Administrator:
   - Run: `C:\Windows\SysWOW64\odbcad32.exe`
   - Verify "Microsoft Access Driver (*.mdb, *.accdb)" is listed

### "Connection not found" Error

**Problem:** You get "Connection not found" when trying to use tools.

**Solution:**
1. Make sure you've connected first with the connect tool
2. Check that you're using the filename as conn_id, not the full path
3. Try connecting again if the connection might have timed out

### "Table not found" Error

**Problem:** You get a "table doesn't exist" error.

**Solution:**
1. Verify the table exists using list_tables_tool
2. Check for typos in the table name
3. For tables with spaces, ensure the name is in square brackets: `[Table Name]`

### Working with Linked Tables

**Feature:** The connector now properly detects and lists linked tables from external MDB files.

The tool uses two methods to detect linked tables:
1. A more inclusive approach for detecting regular tables
2. A specialized query to the MSysObjects system table to find linked tables (Type=6)

**Notes:**
- Linked tables may have their source files in different locations
- All linked tables can be queried just like regular tables
- If you need to filter only linked tables, use: `filter_tables_tool(conn_id="database.mdb", substring="desired_name")`

## Recent Updates

### Added Support for Linked Tables (April 2025)
- Enhanced the `list_tables` function to properly detect linked tables (Type=6 in MSysObjects)
- Added specialized query to MSysObjects to ensure linked tables are included in listings
- Improved table type detection and filtering to include all relevant table types
- Added debug output to help diagnose table detection issues

## Development and Contribution

### Project Structure

The project has a flat structure with all core files in the root directory:

- `server.py` - The main MCP server implementation
- `__init__.py` - Package initialization
- `__main__.py` - Entry point for running as a module
- `run_server.py` - Helper script for running the server with environment variables
- `simple_client.py` - Test client for verifying functionality
- `pyproject.toml` - Project configuration and dependencies

### Running Tests

To test the functionality without an LLM:

```bash
python simple_client.py
```

This will connect to the included sample database and run some basic queries.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
