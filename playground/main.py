# playground/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from playground.module.helper import Pipeline

class QueryRequest(BaseModel):
    query: str
    conversation_id: str = "default"  # Default conversation for POC

class QueryResponse(BaseModel):
    response: str
    route_info: dict
    processing_time: float

app = FastAPI()

# Initialize pipeline with your API keys
pipeline = Pipeline(
    anthropic_api_key="your-anthropic-key",
    openai_api_key="your-openai-key"
)

@app.post("/query")
async def process_query(request: QueryRequest):
    start_time = asyncio.get_event_loop().time()
    
    try:
        response, route_info = await pipeline.process_query(
            query=request.query,
            conversation_id=request.conversation_id
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return QueryResponse(
            response=response,
            route_info=route_info,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))