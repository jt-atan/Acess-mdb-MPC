# TASKS.md — MCP Access-COM

## Project Goal
Local-only Python MCP tool for MS Access via COM, callable by Claude Desktop and Windsurf (stdio transport).

---

## Key Rules
- List endpoints/tools return only first 5 items by default.
- Always prompt before returning full lists.

---

## Essential Tasks & Status
- [x] MCP COM server is standalone (access_com.py); legacy server.py and HTTP code removed.
- [x] Singleton/global AccessCOMManager pattern enforced to preserve COM connection across tool calls.
- [x] New tools: list_linked_tables, list_macros (use COM or fallback to MSysObjects.csv).
- [x] Windsurf/Claude integration tested; MCP server launches via mcp_config.json.
- [x] Module listing works after restart (singleton fix confirmed).
- [ ] Remove all ODBC/ADO endpoints (COM-only)
- [ ] Remove any port configuration/usage
- [ ] Finalize documentation (README_COM.md)
- [ ] Add troubleshooting/logging for COM errors

---

## Findings & Best Practices
- Linked tables: Type=6, Connect field non-empty (see MSysObjects).
- Macros: Type=-32766 in MSysObjects.
- Use readable, line-per-record output for lists.
- User must open the MDB in Access before using the tool (COM attaches to running instance).
- Only show complete lists if explicitly requested by user.
- **After creating or modifying objects via COM, always disconnect the automation session before reopening or refreshing in Access UI. This prevents file locking issues and ensures all changes are visible to both automation and UI.**

---

## Next Steps
- Remove obsolete ODBC/ADO code.
- Complete documentation and troubleshooting guide.
- Test all COM endpoints (modules, queries, forms, MSys tables) via MCP tool interface.
- **Implement create_query tool:**
    - Add AccessCOMManager.create_query(name, sql) using self.db.CreateQueryDef
    - Register as MCP tool (create_query)
    - Test by creating Query_mla with provided SQL
- Update TASKS.md after each subtask or new issue.

- 2025-04-16: Project reset for local-only stdio MCP COM tool. Tasks and architecture clarified.


## Current Tasks

1. Create README_COM.md for the new COM-based MCP (done)
2. Research latest Python SDK/MCP patterns (done)
3. Research pywin32 COM access to Access modules and queries (done)
4. Design new MCP structure (in progress)
5. Implement core COM access logic
6. Expose API endpoints for modules, queries, forms, MSys tables
7. Documentation and sync plan with Access-mdb MCP

## Progress Log

- [2025-04-16] Initialized TASKS.md and created README_COM.md for new MCP
- [2025-04-16] Researched MCP Python SDK patterns:
    - FastAPI or Flask recommended for endpoints
    - Clear resource/tool endpoint structure
    - Handle lifecycle events, use HTTP/stdio/SSE
    - Security best practices
- [2025-04-16] Researched pywin32 COM access to MS Access:
    - Use win32com.client.Dispatch("Access.Application")
    - Open DB with OpenCurrentDatabase(path)
    - List modules: AccessObj.VBE.VBProjects(1).VBComponents
    - List queries: AccessObj.CurrentDb().QueryDefs
- [2025-04-16] Clarified requirements:
    - User opens MDB in Access UI first (linked tables resolved, security bypassed)
    - COM MCP attaches to running Access instance (GetActiveObject)
    - Full access to modules, queries, forms, MSys tables

## Linked Tables Detection: access-mdb vs access-com (2025-04-17)

### access-mdb findings
- Listing tables via access-mdb returns all tables (user and system), but does **not** distinguish linked tables from local tables.
- Attempting to query `MSysObjects` for linked tables fails due to lack of read permissions ("no read permission on 'MSysObjects'").
- Conclusion: access-mdb cannot reliably detect or list linked tables unless permissions are changed.

### access-com findings
- Successfully queried `MSysObjects` system table.
- [ ] **Implement linked table detection in access-com**: Create a dedicated tool/endpoint that queries MSysObjects for entries where Type=4 or Type=6 and Connect is not null. This tool should:
    - Return a list of linked table names
    - Include their source path (from Connect field)
    - Optionally provide additional metadata (e.g., ForeignName, DateCreate)
    - Make it easy for users to distinguish local vs. linked tables
- [ ] **Implement macro detection in access-com**: Add a tool/endpoint to list macros by querying MSysObjects for entries where Type = -32766. Example macros detected: AutoExec, MacroRemoveSpaces. Return macro names and relevant metadata.
- Linked tables are identified by:
  - `Type=6` (ODBC/linked table)
  - `Connect` field contains the path to the source database (non-null)
- Example linked tables detected:
  - `freq`, `history`, `grp`, `provn`, `emiss`, `all_aff_ntw`, `grp_aff_rec`, `gpub`, `assgn`, `orbit_lnk` (and others)
  - All have `Type=6` and their `Connect` field points to another `.mdb` file (e.g., `C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb`)
- Local tables have `Type=1` and an empty/null `Connect` field.
- Conclusion: access-com can reliably detect and enumerate linked tables using metadata in `MSysObjects`.

**Summary:**
- access-mdb: cannot detect linked tables (without extra permissions)
- access-com: can detect linked tables (via `MSysObjects`)

---

(Logged: 2025-04-17)

---

### [2025-04-17] MSysObjects.csv Analysis: Linked Tables & Macros Extraction

**Subtask Completed:** Analyzed MSysObjects.csv to extract all linked tables and macros with their metadata.

#### Linked Tables (Type=6)
| Name         | ForeignName   | Database Source                                    | Connect Path                                    | Type |
|--------------|--------------|----------------------------------------------------|--------------------------------------------------|------|
| freq         | freq         | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb        | 6    |
| history      | history      | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb        | 6    |
| grp          | grp          | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb        | 6    |
| provn        | provn        | C:\BR_SOFT\SRS_DB\srs_link_part3of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part3of3.mdb        | 6    |
| emiss        | emiss        | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb        | 6    |
| all_aff_ntw  | all_aff_ntw  | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb        | 6    |
| grp_aff_rec  | grp_aff_rec  | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb        | 6    |
| gpub         | gpub         | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb        | 6    |
| assgn        | assgn        | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb        | 6    |
| orbit_lnk    | orbit_lnk    | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb           | C:\BR_SOFT\SRS_DB\srs_link_part2of3.mdb        | 6    |

#### Macros (Type=-32766)
| Name                | Type     |
|---------------------|----------|
| AutoExec            | -32766   |
| MacroRemoveSpaces   | -32766   |

- All linked tables have non-empty `Database` and `Connect` fields, and Type=6.
- Macros are identified by Type=-32766.

**Implementation:**
- Added two new MCP tools to access_com.py: `list_linked_tables` and `list_macros`.
- Each tool uses COM (live MSysObjects) if available, otherwise falls back to parsing MSysObjects.csv.
- Existing working code was not modified; new code is clearly separated and commented.

**Next Step:** Test the new endpoints via MCP client and document results. Expand/adjust if more rows are present in the CSV or if further metadata is needed.

---

## Planned MCP Tools / Endpoints

- connect_access_db: Attach to running Access instance with open DB
- disconnect_access_db
- list_modules / get_module_code
- list_queries / get_query_sql
- list_forms / get_form_properties
- list_msys_tables / get_msys_table_data

## [2025-04-16] MCP Tool Integration and Automation

- [x] Configured Access_COM MCP server for automatic startup via Windsurf MCP tool system using mcp_config.json.
  - Entry "access-com" added to mcp_config.json with correct command, args, and cwd.
  - Windsurf will launch the FastAPI server automatically when the tool is used.
  - No need to manually run uvicorn/server.py from terminal.
- [x] Removed "access-mdb" from mcp_config.json to avoid confusion; Access_COM supports both ODBC and COM endpoints.
- [x] Comply with .windsurf rules: always manage MCP tool servers via Windsurf configuration, not manually.
- [x] Troubleshooting: If the server does not start automatically, check mcp_config.json syntax, path correctness, and Windsurf logs for errors.
- [2025-04-16] Updated mcp_config.json to launch access_com.py instead of server.py. Confirmed tool connects as expected via Windsurf/Claude Desktop.

## Next Steps
- Test all COM endpoints (list/get modules, queries, forms, MSys tables) via MCP tool interface.
- Update TASKS.md with results of endpoint tests or any integration issues.
- Continue documentation and sync plan with Access-mdb MCP if needed.

---

## Best Practices / Output Formatting (2025-04-17)
- For all table/list outputs (e.g., linked tables), format each record on its own line for readability:
  
  Name         | Foreign Name  | Source Database
  ------------ | ------------- | ---------------------------------------------
  freq         | freq          | C:\BR_SOFT\SRS_DB\srs_link_part1of3.mdb
  ...
- This should be the default output format for access-com.py endpoints.

## Default Tool Behavior: Preview vs Full List
- By default, only return a preview (first 5 records) for any list endpoint.
- Always ask the user for confirmation before returning the full list to avoid flooding the context or overwhelming the UI.
- Only show the complete list if the user explicitly requests it.

Update this file after each subtask or when new info/problems arise.
