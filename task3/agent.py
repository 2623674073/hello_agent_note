
import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv(Path(__file__).resolve().parent / ".env")

from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool
from hello_agents.memory.embedding import get_text_embedder

# summary 使用空查询；当前嵌入服务对空文本返回不同维度。
# 在创建记忆工具前，为共享嵌入器替换空文本。
embedder = get_text_embedder()
original_encode = embedder.encode


def encode_with_empty_fallback(texts):
    if isinstance(texts, str):
        if not texts.strip():
            texts = "重要记忆"
    else:
        texts = [text if text.strip() else "重要记忆" for text in texts]
    return original_encode(texts)


embedder.encode = encode_with_empty_fallback

# 创建具有记忆能力的Agent
llm = HelloAgentsLLM()
agent = SimpleAgent(name="记忆助手", llm=llm)

# 创建记忆工具
memory_tool = MemoryTool(user_id="user123")
tool_registry = ToolRegistry()
tool_registry.register_tool(memory_tool)
agent.tool_registry = tool_registry
 
# 体验记忆功能
print("=== 添加多个记忆 ===")

# 添加第一个记忆
result1 = memory_tool.execute("add", content="用户张三是一名Python开发者，专注于机器学习和数据分析", memory_type="semantic", importance=0.8)
print(f"记忆1: {result1}")

# 添加第二个记忆
result2 = memory_tool.execute("add", content="李四是前端工程师，擅长React和Vue.js开发", memory_type="semantic", importance=0.7)
print(f"记忆2: {result2}")

# 添加第三个记忆
result3 = memory_tool.execute("add", content="王五是产品经理，负责用户体验设计和需求分析", memory_type="semantic", importance=0.6)
print(f"记忆3: {result3}")

print("\n=== 搜索特定记忆 ===")
# 搜索前端相关的记忆
print("🔍 搜索 '前端工程师':")
result = memory_tool.execute("search", query="前端工程师", limit=3)
print(result)

print("\n=== 记忆摘要 ===")
result = memory_tool.execute("summary")
print(result)
