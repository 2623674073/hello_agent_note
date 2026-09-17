"""消息系统"""


from typing import Literal,Dict,Any,Optional
from datetime import datetime
from pydantic import BaseModel


MessageRole = Literal["user","assistant","system","tool"]

class Message(BaseModel):
    """消息类"""

    content:str
    role:MessageRole
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __init__(self, content: str, role: MessageRole, **kwargs):
        super().__init__(
            content=content,
            role=role,
            timestamp=kwargs.get('timestamp', datetime.now()),
            metadata=kwargs.get('metadata', {})
        )
    def to_dict(self)->Dict[str, Any]:
        """转换为字典格式（Openai API格式）"""
        return {
            "role":self.role,
            "content":self.content
        }
    def __str__(self) -> str:
        return f"[{self.role}]: {self.content}"


if __name__ == "__main__":
    msg = Message(content="你好",role="user")

    res = msg.to_dict()

    print(msg)
    print(f"{type(res)}  : {res}")