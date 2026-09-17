"""
对于React范式的智能体，其实从名字出发就能理解：Reason-Act
本质上就是先思考，在行动。

具体思路：
用户：输入xxx问题；

Agent：

1、推理：模型基于现在的已知上下文进判断，是否能回答问题，如果能给出答案。否则，判断有哪些工具能调用（工具本质上就是act）
2、行动：执行相关的工具
3、开始迭代，回到1，模型根据最新的上下文来判断是否能够回答用户问题。如果能给出答案。否则，继续判断有哪些工具能调用

对应到代码上：

1. llm类    用于思考推理
2. tool类   用于注册和调用工具
3. agent类  将llm和工具连接在一起，也就是harness，这其中有上下文管理，提示词，循环什么时候结束等。 

"""


import json
import os
import re
import inspect
from dotenv import load_dotenv
from typing import Any
from openai import OpenAI


load_dotenv()

class LLM:
    """
    为Agent提供大脑llm
    兼容所有支持openai接口的服务，默认流式响应
    """

    def __init__(self,
                *,
                base_url:str = "",
                api_key:str = "",
                model:str ="",
                temperature: float = 0.1,
                ):
        self.base_url = base_url or os.getenv("BASE_URL")
        self.api_key = api_key or os.getenv("API_KEY")
        self.model = model or os.getenv("MODEL_NAME")
        self.temperature = temperature

        self.client = OpenAI(base_url=self.base_url,api_key=self.api_key)

    def invoke(self, message:list[dict[str,Any]]):
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                temperature=self.temperature,
                stream=True
            )

            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # 在流式输出结束后换行
            return "".join(collected_content)
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

class ToolExecutor:
    """
    提供工具服务：
    1、注册工具
    2、获取已有工具
    3、调用工具
    """
    def __init__(self) -> None:
        self.tools:dict[str,dict[str,Any]] = {}

    def register_tool(self, name:str, description:str, func):

        self.tools[name] = {
            "description": description,
            "func":func,
            "signature":inspect.signature(func)
        }

    def get_tool(self, name:str)->dict[str, dict]:
        tool = self.tools.get(name,{})
        return tool

    def get_tools_description(self):

        descriptions = []
        for name,tool in self.tools.items():
            descriptions.append(f"{name}{tool['signature']}: {tool['description']}")
        return "\n".join(descriptions)
    
    def execute(self, name:str, arguments:dict[str, Any]) -> str:
        """执行工具。任何出错都返回字符串，作为 Observation 回灌给模型，
        而不是抛异常打断整个循环。"""

        tool = self.tools.get(name)

        if tool is None:
            return f"错误：不存在工具 '{name}'。可用工具: {list(self.tools)}"
        if not isinstance(arguments, dict):
            return "错误：工具参数必须是 JSON 对象"

        try:
            # 校验缺少参数、多余参数等问题
            bound_arguments = tool["signature"].bind(**arguments)
            bound_arguments.apply_defaults()
        except TypeError as e:
            return f"参数错误：{e}"

        try:
            tool_result = tool["func"](**bound_arguments.arguments)
        except Exception as e:
            return f"工具执行失败：{type(e).__name__}: {e}"

        return tool_result if isinstance(tool_result, str) else str(tool_result)
            

## 具体工具    
# To install: pip install tavily-python
from tavily import TavilyClient
def search(query:str)->str:
    """
    一个基于tavily的实战网页搜索引擎工具。
    它会智能地解析搜索结果，返回搜索结果。
    """
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=query,
        search_depth="advanced"
    )
    return response.get("results","")



class ReActAgent:
    """
    agent类，包括一个循环（可以是死循环，输入q/Q退出），
    还有就是ReActAgent的逻辑实现：

    属性包含：
    1、llm
    2、工具
    3、上下文
    4、提示词
    """
    def __init__(self,
                 *,
                 base_url:str = "",
                 api_key:str = "",
                 max_iter:int = 5,
                 tool_executor:ToolExecutor | None = None) -> None:
        self.max_iter = max_iter
        self.llm = LLM(base_url=base_url,api_key=api_key)
        self.tool_executor = tool_executor if tool_executor is not None else ToolExecutor()
        self.history = []
        self.prompt = """请注意，你是一个有能力调用外部工具的智能助手。
            可用工具如下:
            {tools}

            严格按照以下格式回应：

            Thought: 简要说明下一步
            Action: 工具名[JSON参数对象]

            工具调用示例：
            Action: search[{{"query": "今天郑州的天气"}}]

            如果你不需要调用工具，直接用已有知识回答：
            Action: Finish[最终答案]

            现在，请开始解决以下问题:
            Question: {question}
            History: {history}
            """
    def run(self):

        while True:
            user_input = input("请输入您的问题(输入q/Q退出) ：").strip()
            if user_input.upper() == 'Q':
                break
            if not user_input:
                continue

            self.history = [f"Question: {user_input}"]

            for step in range(1, self.max_iter + 1):
                print(f"\n--- 第 {step} 步 ---")

                message = [
                    {
                        "role":"user",
                        "content":self.prompt.format(
                        tools = self.tool_executor.get_tools_description(),
                        question = user_input,
                        history = "\n".join(self.history)
                        )
                    }
                ]

                answer = self.llm.invoke(message=message)
                ## 需要进行判断，是直接回答，还是调用工具
                if not answer:
                    print("错误：LLM 未返回有效响应，本次提问终止。")
                    break

                thought, action = self._parse_output(text=answer)
                if thought:
                    print(f"思考: {thought}")

                if not action:
                    print("警告:未能解析出有效的Action，流程终止。")
                    break

                if thought:
                    self.history.append(f"Thought: {thought}")
                self.history.append(f"Action: {action}")

                # 4. 执行Action
                if action.startswith("Finish"):
                    # 如果是Finish指令，提取最终答案并结束
                    final_answer = self._parse_finish(action)
                    if final_answer is None:
                        print("警告:Finish 格式不合法，本次提问终止。")
                        break
                    print(f"\n🎉 最终答案:\n{final_answer}")
                    break          # ★ 必须跳出：否则会掉进下面的 _parse_action

                tool_name, tool_arguments = self._parse_action(action)
                if tool_name is None or tool_arguments is None:
                    # 不要直接跳出，把错误当作 Observation 回灌，让模型自我修正
                    hint = 'Observation: Action 格式错误，请按 工具名[{"参数名": 参数值}] 的 JSON 格式重新输出。'
                    print("工具调用格式错误，已反馈给模型重试")
                    self.history.append(hint)
                    continue

                observation = self.tool_executor.execute(
                    tool_name,
                    tool_arguments
                )
                print(f"观察结果: {observation}")
                self.history.append(f"Observation: {observation}")
            else:
                print(f"⚠️ 已达到最大循环次数 {self.max_iter}，本次提问结束。")
        print("退出agent成功，欢迎下次使用")


    def _parse_finish(self, action_text: str):
        """解析 Finish[...] 指令，提取最终答案。

        注意：最终答案通常是多段文本，必须加 re.DOTALL，
        否则 `.` 不匹配换行符，正则会在第一个换行处就失配。
        """
        match = re.fullmatch(
            r"Finish\s*\[(.*)\]\s*",
            action_text.strip(),
            re.DOTALL,
        )
        return match.group(1).strip() if match else None

    def _parse_output(self, text: str):
        """解析LLM的输出，提取Thought和Action。
        """
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """解析Action字符串，提取工具名称和输入参数。
        """
        match = re.fullmatch(
          r"([A-Za-z_]\w*)\s*\[(.*)\]",
          action_text.strip(),
          re.DOTALL,
        )

        if not match:
            return None, None

        tool_name = match.group(1)
        arguments_text = match.group(2).strip()

        try:
            arguments = json.loads(arguments_text)
        except json.JSONDecodeError as exc:
            print(f"工具参数不是合法 JSON: {exc}")
            return None, None

        if not isinstance(arguments, dict):
            print("工具参数必须是 JSON 对象")
            return None, None

        return tool_name, arguments

            



if __name__ == "__main__":

    # message = [
    #     {
    #         "role":"user",
    #         "content":"介绍一下正则基础用法"
    #     }
    # ]
    # llm = LLM()
    # llm.invoke(message=message)
    # res = search("中国的首都")
    # print(f"search: {res}")

   
    # print(toolExecutor.get_tools_description())

    # import inspect

    # def example(a: int, b: str = "hello", *, c: bool = False) -> str:
    #     """这是一个示例函数"""
    #     return f"{a}-{b}-{c}"

    # # 获取函数签名
    # sig = inspect.signature(example)
    # print(sig)                    # (a: int, b: str = 'hello', *, c: bool = False) -> str

    # # 获取所有参数信息
    # for name, param in sig.parameters.items():
    #     print(f"参数名: {name}")
    #     print(f"  类型注解: {param.annotation}")
    #     print(f"  默认值: {param.default}")
    #     print(f"  种类: {param.kind}")   # POSITIONAL_OR_KEYWORD / KEYWORD_ONLY 等

    toolExecutor = ToolExecutor()
    toolExecutor.register_tool(name="search",description="一个基于tavily的实战网页搜索引擎工具。它会智能地解析搜索结果，返回搜索结果。他的参数是query:str",func=search)

    agent = ReActAgent(tool_executor=toolExecutor)
    agent.run()
