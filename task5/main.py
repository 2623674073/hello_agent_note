import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    notes_dir = Path("./notes").resolve()

    server = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(notes_dir),
        ],
    )

    async with stdio_client(server) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # tools = await session.list_tools()

            # for tool in tools.tools:
            #     print(tool.name)

            result = await session.call_tool(
                "write_file",
                {
                    "path":str(notes_dir / "hello.md"),
                    "content": "# Hello MCP\n\n这是我的第一个 MCP 文件。",
                }
            )


asyncio.run(main())