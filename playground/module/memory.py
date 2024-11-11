# src/memory.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Interaction:
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    route_info: Dict

class MemoryStore:
    def __init__(self, max_history: int = 10):
        self.conversations: Dict[str, List[Interaction]] = {}
        self.max_history = max_history

    def add_interaction(
        self,
        conversation_id: str,
        role: str,
        content: str,
        route_info: Dict
    ):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append(
            Interaction(
                timestamp=datetime.now(),
                role=role,
                content=content,
                route_info=route_info
            )
        )
        
        # Keep only recent history
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id].pop(0)

    def get_context(self, conversation_id: str) -> List[Interaction]:
        return self.conversations.get(conversation_id, [])