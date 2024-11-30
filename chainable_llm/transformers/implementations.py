import json
from typing import Any
from chainable_llm.transformers.base import DataTransformer
from chainable_llm.core.exceptions import TransformerError


class JSONTransformer(DataTransformer):
    async def transform(self, data: Any) -> str:
        try:
            if isinstance(data, str):
                # Validate JSON string
                json.loads(data)
                return data
            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            raise TransformerError(f"JSON transformation error: {str(e)}")


class TextNormalizer(DataTransformer):
    async def transform(self, data: Any) -> str:
        try:
            text = str(data)
            # Basic text normalization
            text = " ".join(text.split())
            return text.strip()
        except Exception as e:
            raise TransformerError(f"Text normalization error: {str(e)}")
