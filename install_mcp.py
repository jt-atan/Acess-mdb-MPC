"""
Script to install the Access_mdb MCP server in Windsurf and Claude Desktop
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def install_mcp_server():
    """Install the Access_mdb MCP server in Windsurf and Claude Desktop"""
    print("Installing Access_mdb MCP server...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current directory: {current_dir}")
    
    # Windsurf config path
    windsurf_config_path = os.path.expanduser("~/.codeium/windsurf/mcp_config.json")
    
    # Claude Desktop config path
    claude_config_path = os.path.join(os.environ.get("APPDATA"), "Claude", "claude_desktop_config.json")
    
    # MCP server configuration
    mcp_config = {
        "command": "python",
        "args": [
            "-m",
            "server"
        ],
        "cwd": current_dir
    }
    
    # Update Windsurf config
    if os.path.exists(windsurf_config_path):
        try:
            with open(windsurf_config_path, "r") as f:
                windsurf_config = json.load(f)
            
            if "mcpServers" not in windsurf_config:
                windsurf_config["mcpServers"] = {}
            
            windsurf_config["mcpServers"]["access-mdb"] = mcp_config
            
            with open(windsurf_config_path, "w") as f:
                json.dump(windsurf_config, f, indent=2)
            
            print(f"Updated Windsurf MCP config at {windsurf_config_path}")
        except Exception as e:
            print(f"Error updating Windsurf config: {str(e)}")
    else:
        print(f"Windsurf config not found at {windsurf_config_path}")
    
    # Update Claude Desktop config
    if os.path.exists(claude_config_path):
        try:
            with open(claude_config_path, "r") as f:
                claude_config = json.load(f)
            
            if "mcpServers" not in claude_config:
                claude_config["mcpServers"] = {}
            
            claude_config["mcpServers"]["access-mdb"] = mcp_config
            
            with open(claude_config_path, "w") as f:
                json.dump(claude_config, f, indent=2)
            
            print(f"Updated Claude Desktop MCP config at {claude_config_path}")
        except Exception as e:
            print(f"Error updating Claude Desktop config: {str(e)}")
    else:
        print(f"Claude Desktop config not found at {claude_config_path}")
    
    print("\nInstallation complete! Please restart Windsurf and Claude Desktop.")
    print("To test the MCP server, run: python test_server.py")

if __name__ == "__main__":
    install_mcp_server()
