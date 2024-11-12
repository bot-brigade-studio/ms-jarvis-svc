from enum import Enum
from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field

# core/types.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str

class ConversationHistory(BaseModel):
    messages: List[Message] = []
    
    def add_message(self, role: MessageRole, content: str):
        self.messages.append(Message(role=role, content=content))

class LLMRequest(BaseModel):
    system_prompt: Optional[str] = None
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class InputType(Enum):
    SYSTEM_PROMPT = "system"
    USER_PROMPT = "user"
    APPEND_SYSTEM = "append_system"

class RouteDecision(BaseModel):
    route_id: str
    metadata: Dict[str, Any] = {}
class LLMResponse(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    route_decision: Optional[RouteDecision] = None
class LLMConfig(BaseModel):
    provider: str
    api_key: str
    model: str
    messages: Optional[List[Dict[str, Any]]] = None
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class PromptConfig(BaseModel):
    input_type: InputType
    template: str
    base_system_prompt: Optional[str] = None