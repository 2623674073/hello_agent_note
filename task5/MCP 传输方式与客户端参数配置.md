# MCP 传输方式与客户端参数配置

> 适用范围：本文的可运行示例以本项目安装的 Python MCP SDK 1.16.0 为准。不同版本的客户端 API 有差异，末尾列出迁移提示。

## 先分清三个概念

- **MCP 协议**规定客户端和服务端如何发现工具、调用工具、读取资源、获取提示词等。
- **Transport（传输方式）**规定这些协议消息通过什么通道传递。
- **客户端配置**规定连接目标、启动命令及各传输方式所需的参数。

因此，stdio、Streamable HTTP 和 SSE 是**连接方式**，不是三种不同的 MCP 工具类型。连接建立以后，它们都可以通过 ClientSession 执行 list_tools()、call_tool() 等协议操作。

```text
应用 / Agent
    ↓
ClientSession：初始化、列举工具、调用工具
    ↓
Transport：stdio / Streamable HTTP / SSE
    ↓
MCP Server
```

## 一眼对比

| 方式 | 服务端在哪里 | 客户端提供什么 | 本项目 SDK 1.16.0 的入口 | 何时选用 |
| --- | --- | --- | --- | --- |
| stdio | 客户端启动的本地子进程 | 启动命令、参数、可选环境和工作目录 | StdioServerParameters + stdio_client() | 本地工具、桌面应用启动的服务 |
| Streamable HTTP | 已运行的 HTTP 服务 | MCP 端点 URL；按需提供请求头、认证、超时 | streamablehttp_client() | 新建远程 MCP 接入时优先考虑 |
| SSE（旧传输） | 已运行的 HTTP 服务 | SSE 端点 URL；按需提供请求头、认证、超时 | sse_client() | 对接仍采用旧 SSE 传输的服务 |
| 进程内连接 | 同一 Python 进程中的服务端对象 | 服务端对象或测试夹具 | 取决于使用的 SDK API | 嵌入式场景和测试；无需子进程或 URL |

**选择顺序**：服务需要由你的程序在本机启动，选 stdio；服务已部署并提供 Streamable HTTP 端点，选 Streamable HTTP；只有服务明确提供旧 SSE 端点时才选 SSE。进程内连接属于特殊的嵌入或测试方式，不能把它当成一个远程地址配置。

下文的 async with 示例是代码片段，实际使用时应放进 async def main()，再由 asyncio.run(main()) 启动。

## 1. stdio：描述怎样启动本地服务端

StdioServerParameters 是 **stdio 子进程的启动配置**，并非所有 MCP Server 共用的配置类。客户端启动进程后，通过其标准输入和标准输出交换 MCP 消息；服务端日志应写到标准错误，避免破坏协议消息。

| 参数 | 作用 | 示例 |
| --- | --- | --- |
| command | 可执行命令 | npx、python、uv |
| args | 传给命令的参数列表 | 文件系统服务包名、允许访问的目录 |
| env | 子进程需要的环境变量 | 服务所需的 API Key |
| cwd | 子进程的工作目录 | 项目目录 |
| encoding / encoding_error_handler | stdio 文本编解码设置 | 有特殊编码需求时再配置 |

与本项目 task5 对应的写法：

~~~python
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

notes_dir = Path(__file__).resolve().parent / "notes"
server = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", str(notes_dir)],
)

async with stdio_client(server) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
~~~

这里的 args 是启动文件系统服务端所需的命令行参数；notes_dir 是**服务端允许访问的目录**。使用脚本所在目录定位它，可以避免从不同工作目录运行时误指向不存在的 notes 目录。

## 2. Streamable HTTP：连接已经运行的服务端

客户端传入的是服务端的 **MCP 端点 URL**，例如 http://localhost:8000/mcp。客户端不会因为拿到 URL 就负责启动服务端。不要把一个普通网页地址或旧 SSE 地址当成 Streamable HTTP 端点。

本项目安装的 SDK 1.16.0 使用 streamablehttp_client（注意函数名中没有 streamable 和 http 之间的下划线）：

~~~python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

url = "http://localhost:8000/mcp"

async with streamablehttp_client(url) as (read, write, get_session_id):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
~~~

这个版本的上下文返回三个值：读流、写流和获取 HTTP 会话 ID 的回调。只调用工具时可以不使用 get_session_id，但解包时要保留它。

| 常用参数 | 作用 |
| --- | --- |
| url | MCP 端点 |
| headers | 自定义 HTTP 请求头，例如认证信息 |
| auth | HTTP 认证对象 |
| timeout | 普通请求的超时 |
| sse_read_timeout | 流式响应读取超时 |
| terminate_on_close | 关闭客户端时是否请求终止服务端会话 |

认证、代理等高级配置应按**正在使用的 SDK 版本**查参数签名。不要把新版文档中的 httpx2.AsyncClient 示例直接套在本项目的 1.16.0 上。

## 3. SSE：兼容旧服务端

SSE 是较早的远程传输方式，和 Streamable HTTP 是不同的端点及客户端实现。服务器如果只提供类似 http://localhost:8000/sse 的旧端点，才使用 sse_client：

~~~python
from mcp import ClientSession
from mcp.client.sse import sse_client

url = "http://localhost:8000/sse"

async with sse_client(url) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
~~~

常用配置包括 url、headers、auth、timeout 和 sse_read_timeout。**Streamable HTTP 的响应也可能使用 SSE 事件流**；这不意味着它就是这里所说的旧 SSE 传输。两者应按服务端实际提供的端点和协议选择。

## 4. 进程内连接：用于嵌入和测试

如果服务端对象本来就在同一进程中，有些 SDK API 可以直接连接它，省去子进程和网络。它与前面三种方式相比，更像一种嵌入或测试连接方式。**本项目的 MCP SDK 1.16.0 没有下文提到的高层 Client 类**，不要照搬新版 Client(server_object) 的示例来运行当前代码。

## 参数配置的关键区别

| 问题 | stdio | Streamable HTTP / 旧 SSE |
| --- | --- | --- |
| 谁启动服务端？ | 客户端启动本地子进程 | 服务端预先运行，客户端只连接 |
| 用什么定位服务端？ | command + args | URL |
| 服务所需的环境变量放哪里？ | 子进程启动配置 env | 服务端自己的部署环境；客户端认证通常通过 HTTP 配置 |
| 连接何时可用？ | 进入 stdio_client 上下文并完成 initialize() 后 | 进入 HTTP 客户端上下文并完成 initialize() 后 |
| 何时关闭？ | 退出上下文时结束会话并清理子进程 | 退出上下文时关闭连接及会话 |

无论采用哪种传输，**构造参数对象不等于连接成功**。必须在异步上下文中建立传输、创建 ClientSession、调用 initialize()，之后才能列举或调用工具。

## SDK 版本提示

本项目当前使用 mcp 1.16.0，对应本文示例：

- stdio：StdioServerParameters + stdio_client()。
- Streamable HTTP：streamablehttp_client()，返回三个值。
- 旧 SSE：sse_client()。
- 工具操作：ClientSession.list_tools() / call_tool()。

Python SDK 2.x 的官方文档展示了更高层的 Client：可以通过传入 URL 或 StdioServerParameters 选择传输；其 HTTP 函数名和 HTTP 客户端配置方式也与 1.16.0 不同。**升级 SDK 后再按新文档改写，不能混用两代 API。**

## 参考资料

- [MCP Python SDK 1.x 文档](https://py.sdk.modelcontextprotocol.io/v1/)
- [MCP Python SDK 当前客户端传输文档](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/transports.md)
- [MCP Python SDK 版本变化说明](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md)
