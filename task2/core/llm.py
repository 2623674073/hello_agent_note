"""
用来封装llm，尽可能多适配各种模型
"""
from typing import Optional, Dict, Any, List, Iterator
import os

from dotenv import load_dotenv
from openai import OpenAI

# from hello_agents import HelloAgentsLLM
load_dotenv()

class LLM:
    def __init__(self, 
                base_url : Optional[str] = None, 
                model : Optional[str] = None, 
                api_key : Optional[str] = None, 
                provider : Optional[str] = "auto",
                temperature: float = 0.5,
                max_tokens: Optional[int] = None,
                timeout: Optional[int] = None,
                **kwargs
                ):

        self.base_url = base_url or os.getenv("BASE_URL","http://k8s-new-api.deepi.tech")
        self.model = model or os.getenv("MODEL","deepseek-v4-flash")
        self.api_key = api_key or os.getenv("API_KEY")
        self.temperature = temperature or os.getenv("TEMPERATURE")
        self.max_tokens = max_tokens or os.getenv("MAX_TOKRNS")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))
        self.kwargs = kwargs


        # 创建OpenAI客户端
        self._client = self._create_client()
            
    def _create_client(self):

        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=3
            )

    def think(self, messages:list[dict[str, str]], temperature:Optional[float]=None)->Iterator[str]:
        """
                调用大语言模型进行思考，并返回流式响应。
                这是主要的调用方法，默认使用流式响应以获得更好的用户体验。
        
                Args:
                    messages: 消息列表
                    temperature: 温度参数，如果未提供则使用初始化时的值
        
                Yields:
                    str: 流式响应的文本片段
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=temperature if temperature is not None else self.temperature,
                            max_tokens=self.max_tokens,
                            stream=True,
                        )

            print(f"大模型响应成功：")
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                if content:
                    # print(content,end="",flush=True) # end 就是结束的符号，默认时换行，flush就是不缓存，有内容立即输出
                    yield content
            print() # 在流式输出结束后换行
        except Exception as e:
            print(f"调用大模型失败：{e}")
            raise BaseException(f"LLM调用失败: {str(e)}")

    def invoke(self, messages:list[dict[str, str]], **kwargs)->str:
        """
                非流式调用LLM，返回完整响应。
                适用于不需要流式输出的场景。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=kwargs.get('temperature', self.temperature),
                            max_tokens=kwargs.get('max_tokens', self.max_tokens),
                            **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
                        )
            print(f"大模型响应成功：")
            return response.choices[0].message.content
        except Exception as e:
                    print(f"调用大模型失败：{e}")
                    raise BaseException(f"LLM调用失败: {str(e)}")

    def stream_invoke(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
            """
            流式调用LLM的别名方法，与think方法功能相同。
            保持向后兼容性。
            """
            temperature = kwargs.get('temperature')
            # yield from self.think(messages, temperature)  # 等同于下面的
            for content in self.think(messages, temperature):
                yield content
        

if __name__ == "__main__":

    llm = LLM()

    messages = [
         {
              "role":"user",
              "content":"hello,介绍一下你自己"
         }
    ]
    # 只调用 stream_invoke() 不会立即请求模型：
    #
    # stream = llm.stream_invoke(messages=messages)
    #
    # 因为 stream_invoke() 内部使用了 yield，所以它是“生成器函数”。
    # 调用生成器函数只会创建并返回 generator 对象，函数体此时还没有执行。
    # 必须使用 next(stream)、list(stream) 或 for 循环消费生成器，
    # 请求模型和 yield 返回文本片段的代码才会真正开始执行。

    # for 循环会持续消费生成器；chunk 是每次 yield 出来的一段模型文本。
    for chunk in llm.stream_invoke(messages=messages):
        # 当前 think() 内部已经调用 print() 输出文本，所以这里写 pass
        # 仍会看到回答；但是 chunk 本身会被丢弃，调用者没有处理返回值。
        print(chunk,end="",flush=True) # pass

        # 如果删掉 think() 内部的 print()，就应该在这里负责输出：
        # print(chunk, end="", flush=True)

    # 建议只选择一层负责打印：
    # 1. think() 内部打印，调用者使用 pass；写法简单，但复用性较差。
    # 2. think() 只负责 yield，调用者打印 chunk；职责更清晰，更推荐。
