import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
import os
from pathlib import Path
from typing import Any

import certifi
from dotenv import load_dotenv

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv(Path(__file__).with_name(".env"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


from hello_agents import HelloAgentsLLM

llm = HelloAgentsLLM()



class FilesystemMcpClient:
    def __init__(self,
                 command:str,
                 args:list[str],
                 env:dict[str,Any] | None = None
                 ) -> None:
        self.command = command
        self.args = args
        self.env = env
        self.server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=self.env 
        )
        self.session: ClientSession | None = None

        """
        async with
        → 异步资源生命周期管理

        __aenter__ / __aexit__
        → async with 自动调用的魔术方法

        AsyncExitStack：
        用于统一管理多个异步上下文资源的生命周期。

        正常使用 async with 时，代码块结束后会自动调用对应的 __aexit__，
        从而释放资源。

        这里将 stdio_client、ClientSession 等异步上下文封装到 MCPClient 对象中，
        希望它们在 connect() 结束后仍然保持有效，因此通过 AsyncExitStack
        保存这些上下文的退出逻辑，等到 close() 时再统一释放。

        """
        self._exit_stack = AsyncExitStack()  

    async def connect(self):
        # 1. 启动 MCP Server，并拿到 read/write
        read,write = await self._exit_stack.enter_async_context(
            stdio_client(self.server_params)
        )

        # 2. 创建 ClientSession
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        # 3. MCP 初始化握手
        await self.session.initialize()

    async def list_tool(self):
        self._check_connected()
        return await self.session.list_tools()

    async def call_tools(self,
                        name: str,
                        arguments: dict[str, Any] | None = None
                        ):
        self._check_connected()
        return await self.session.call_tool(
            name=name,
            arguments=arguments or {}
        )

    def _check_connected(self):
        if self.session is None:
            raise RuntimeError("MCP Client 尚未连接，请先调用 connect()")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.aclose()
        self.session = None


class Agent:
    """
    一个可以调用mcp工具的agent
    """
    def __init__(self) -> None:
        pass

async def main():
    notes_dir = Path("./notes").resolve()
    
    mcp_client = FilesystemMcpClient(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(notes_dir),
        ],
    )

    async with mcp_client as client:
        tools = await client.list_tool()
        for tool in tools.tools:
            print(f"tool : {tool}")

        res = await client.call_tools(
            name="read_file",
            arguments = {
            "path": r"E:\0myself\hello_agent_note\task5\notes\hello.md"
            }
        )
        print(f"read_file: {res}")

if __name__ == "__main__":
    
    asyncio.run(main())
    