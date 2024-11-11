# playground/prompts/user_prompts.py
from typing import Optional


class UserPrompts:
    @staticmethod
    def fingerprint(query: str, context: Optional[str] = None) -> str:
        context_str = f"\nPrevious Context:\n{context}" if context else ""
        return f"""Please analyze the following query:{context_str}

Query: {query}

Determine the appropriate processing route based on query complexity and requirements."""

    @staticmethod
    def route_1(query: str, context: Optional[str] = None) -> str:
        context_str = f"\nContext:\n{context}" if context else ""
        return f"""Please provide a direct response to this query:{context_str}

Query: {query}"""

    @staticmethod
    def route_2(query: str, guidance: str, context: Optional[str] = None) -> str:
        context_str = f"\nContext:\n{context}" if context else ""
        return f"""Please respond to this query following the specific guidance:{context_str}

Guidance:
{guidance}

Query: {query}"""

    @staticmethod
    def route_3(query: str, context: Optional[str] = None) -> str:
        context_str = f"\nContext:\n{context}" if context else ""
        return f"""Please provide a comprehensive response to this query:{context_str}

Query: {query}"""