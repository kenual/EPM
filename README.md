Oracle EPM MCP Server

npx @modelcontextprotocol/inspector uv run --directory ~/Documents/GitHub/epm -m epm.essbase

```json
{
  "mcpServers": {
    "Essbase": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/ken/Documents/GitHub/epm",
        "-m",
        "epm.essbase"
      ],
      "env": {}
    }
  }
}