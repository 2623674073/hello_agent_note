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


from typing import Any

from openai import OpenAI


class LLM:
    """
    为Agent提供大脑llm
    兼容所有支持openai接口的服务，默认流式响应
    """

    def __int__(self,
                base_url:str,
                api_key:str,
                model:str,
                temperature: float,
                ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
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


class Tool:
    
