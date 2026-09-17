"""工具注册表"""

from typing import Any, Dict, Callable, Optional

from tool import Tool


class ToolRegistry:
    """
    Agents工具注册表

    提供工具的注册、管理和执行功能。
    支持两种工具注册方式：
    1. Tool对象注册（推荐）
    2. 函数直接注册（简便）
    """

    def __init__(self) -> None:
        self._tools : dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: Tool):
        """
            注册Tool对象
    
            Args:
                tool: Tool实例
        """
        if tool.name in self._tools:
            print(f"⚠️ 警告：工具 '{tool.name}' 已存在，将被覆盖。")
        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 注册成功")

    def register_function(self, name: str, description: str, func: Callable[[str],str]):
        """
            直接注册函数作为工具（简便方式）

            Args:
                name: 工具名称
                description: 工具描述
                func: 工具函数，接受字符串参数，返回字符串结果
            """
        if name in self._functions:
            print(f"⚠️ 警告：工具 '{name}' 已存在，将被覆盖。")

        self._functions[name] = {
            "func": func,
            "description":description
        }
        print(f"✅ 工具 '{name}' 已注册。")

    def unregister(self, name: str):
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            print(f"🗑️ 工具 '{name}' 已注销。")
        elif name in self._functions:
            del self._functions[name]
            print(f"🗑️ 工具 '{name}' 已注销。")
        else:
            print(f"⚠️ 工具 '{name}' 不存在。")

    def get_tool(self, name: str)->Optional[Tool]:
        """获取Tool对象"""
        return self._tools.get(name)

    def get_function(self, name: str)->Optional[Callable]:
        """获取工具函数"""
        func_info = self._functions.get(name)
        return func_info['func'] if func_info else None 

    def execute_tool(self, name: str, input_text: str)->str:
        """
            执行工具

            Args:
                name: 工具名称
                input_text: 输入参数

            Returns:
                工具执行结果
        """
        # 优先查找Tool对象
        if name in self._tools:
            tool = self._tools[name]
            try:
                return tool.run(parameters={"input": input_text})
            except Exception as e:
                return f"错误：执行工具 '{name}' 时发生异常: {str(e)}"

        # 查找function对象
        elif name in self._functions:
            func = self._functions[name]
            try:
                return func['func'](input_text)
            except Exception as e:
                return f"错误：执行工具 '{name}' 时发生异常: {str(e)}"
        else:
            return f"错误：未找到名为 '{name}' 的工具。"

    def get_tools_description(self) -> str:
        """
            获取所有可用工具的格式化描述字符串
    
            Returns:
                工具描述字符串，用于构建提示词
        """
        descripiotns = []
        for tool in self._tools.values():
            descripiotns.append(f"-{tool.name}: {tool.description}")

        for name,info in self._functions.items():
            descripiotns.append(f"-{name}: {info['description']}")

        return "\n".join(descripiotns) if descripiotns else "暂无工具可用"

    def list_tools(self) -> list[str]:
            """列出所有工具名称"""
            return list(self._tools.keys()) + list(self._functions.keys())
    
    def get_all_tools(self) -> list[Tool]:
        """获取所有Tool对象"""
        return list(self._tools.values())

    def clear(self):
        """清空所有工具"""
        self._tools.clear()
        self._functions.clear()
        print("🧹 所有工具已清空。")

# 全局工具注册表
global_registry = ToolRegistry()