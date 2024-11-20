# core/types.py

from enum import Enum
from typing import AsyncIterator, Awaitable, Callable, List, Optional, Any, Dict, Union
from pydantic import BaseModel, ConfigDict, Field
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
    system_prompt_additions: Optional[str] = None  # Additional system prompt for next node
    user_input_transform: Optional[str] = None     # Modified user input for next node
    metadata: Dict[str, Any] = {}
    
class NodeContext(BaseModel):
    """Context passed between nodes"""
    original_input: str
    current_input: str
    system_prompt_additions: List[str] = []
    metadata: Dict[str, Any] = {}

class PromptConfig(BaseModel):
    input_type: InputType
    template: str
    base_system_prompt: Optional[str] = None
    

class StreamChunk(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    done: bool = False

class StreamConfig(BaseModel):
    enabled: bool = False
    chunk_size: int = 100
    buffer_size: int = 1024
    callback: Optional[Callable[[StreamChunk], Awaitable[None]]] = None

# Update LLMConfig to include streaming
class LLMConfig(BaseModel):
    provider: str
    api_key: str
    model: str
    messages: Optional[List[Dict[str, Any]]] = None
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    streaming: Optional[StreamConfig] = None

# Update LLMResponse to handle streaming
class LLMResponse(BaseModel):
    """Response from LLM providers"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    content: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    route_decision: Optional[RouteDecision] = None
    stream: Optional[AsyncIterator[StreamChunk]] = None