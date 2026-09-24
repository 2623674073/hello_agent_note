# Function Calling 与 MCP：Agent 工具调用笔记

## 一句话理解

**Function Calling（也常称 Tool Calling）让模型提出“调用哪个工具、传什么参数”；Agent 程序负责执行；MCP 让程序按统一协议发现和调用外部能力。**

模型生成工具调用请求，不会仅凭输出一段请求就自动执行 Python 函数、访问数据库或读取文件。

## 各部分分别负责什么

| 部分 | 主要职责 | 不负责什么 |
| --- | --- | --- |
| LLM 的 Function Calling | 根据任务和工具描述，决定是否请求调用工具；选择工具并生成参数 | 亲自运行工具或保证参数一定正确 |
| Agent / Host 程序 | 把可用工具交给模型；接收工具请求；校验、路由和执行；把结果送回模型 | 替模型完成所有自然语言判断 |
| MCP Client | 与 MCP Server 建立会话；发现工具、资源、提示词；发送调用请求并接收结果 | 实现每个外部系统的业务逻辑 |
| MCP Server | 按 MCP 协议暴露能力，并连接具体文件系统、数据库、API 等 | 替 Agent 决定何时调用工具 |

这里的 Host 是承载用户对话和模型调用的应用；一个 Agent 程序通常承担这部分工作。MCP Client 是它与 MCP Server 通信的组件。

## 一次工具调用怎样发生

以“读取笔记文件”为例：

~~~text
用户：请总结 hello.md
  ↓
Agent 通过 MCP Client 获取工具定义
  例如 read_file 的名称、说明、输入参数 Schema
  ↓
Agent 按当前 LLM 接口的格式提供这些工具定义
  ↓
LLM 判断需要读取文件，返回工具调用请求
  例如 name=read_file、arguments={path: ".../hello.md"}
  ↓
Agent 检查请求并路由到对应工具
  ↓
MCP Client 向 MCP Server 发送 tools/call
  ↓
MCP Server 执行实际文件读取，返回结果
  ↓
Agent 把工具结果作为一条工具消息交回 LLM
  ↓
LLM 根据文件内容生成总结
~~~

如果调用的是 Agent 自己的内置函数，“路由到对应工具”之后可以直接执行函数；如果调用的是 MCP 工具，则经过 MCP Client 和 MCP Server。**这两条执行路径可以同时存在于一个 Agent 中。**

## Function Calling 的边界

开发者通常向模型提供工具的名称、描述和参数 Schema。模型据此完成三件事：

1. 判断当前任务是否需要工具。
2. 从可用工具中选择一个或多个工具。
3. 为所选工具生成结构化参数。

因此，Function Calling 不只是“填参数”。模型输出的是**调用意图**；工具请求是否允许执行、参数是否符合要求、执行失败如何处理，都由 Agent 程序和工具实现共同负责。

## MCP 解决了什么

假设 Agent 要同时使用文件系统、数据库和 GitHub。若逐个直接接入，Agent 需要分别处理各系统的 API、认证、参数格式和返回结果。采用 MCP 后，Agent 侧可以通过 MCP Client 用统一的协议发现并调用这些能力：

~~~text
Agent / Host
  └─ MCP Client
       ├─ 文件系统 MCP Server → 文件系统
       ├─ 数据库 MCP Server   → 数据库驱动
       └─ GitHub MCP Server   → GitHub API
~~~

**适配代码没有消失。**具体 API、数据库驱动和业务逻辑仍由相应的 MCP Server 实现；Agent 侧还需要负责将 MCP 工具描述映射为模型可接受的工具格式，并把模型的调用请求转发给正确的 Server。

MCP 的能力也不限于工具：Server 还可以提供 **Resources（资源）** 和 **Prompts（提示词模板）**。本笔记重点讨论模型选择并调用的 Tools。

## 容易混淆的三件事

- **模型会 Tool Calling，不等于已经接入 MCP。**没有 MCP 时，Agent 仍可以把本地 Python 函数提供给模型调用。
- **接入 MCP，不等于模型会自动使用工具。**Agent 仍须取得工具定义、提供给模型、处理模型请求并回传结果。
- **MCP Client 连接成功，不等于模型能直接调用 Python 对象。**模型只接收工具描述并返回调用请求；实际执行发生在 Agent 程序中。

## 记忆版

> Function Calling：模型提出工具调用请求。
>
> Agent / Host：编排模型和工具，执行调用并回传结果。
>
> MCP Client：按 MCP 协议连接和请求 Server。
>
> MCP Server：把具体外部系统封装为 MCP 能力。

## 参考资料

- [MCP 官方 Python SDK：客户端与工具发现](https://py.sdk.modelcontextprotocol.io/client/)
- [MCP 官方 TypeScript SDK：从工具列表到模型调用](https://ts.sdk.modelcontextprotocol.io/v2/get-started/first-client.html)

