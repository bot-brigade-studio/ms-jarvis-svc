import json
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends
from app.api.v1.endpoints.deps import CurrentUser, get_current_user
from app.schemas.chat import CreateMessageRequest, CreateThreadRequest
from app.services.conversation_service import ConversationService
from app.utils.debug import debug_print
from app.utils.http_client import NexusClient
from app.utils.response_handler import response
from chainable_llm.core.types import StreamChunk
from sse_starlette import EventSourceResponse
from app.core.exceptions import APIError

router = APIRouter()


@router.post(
    "/{bot_id}/thread/{thread_id}/messages",
    response_model=Any,
)
async def create_user_message(
    bot_id: UUID,
    thread_id: UUID,
    schema: CreateMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(),
):
    try:
        # await service.process_user_message(
        #     bot_id=bot_id,
        #     thread_id=thread_id,
        #     schema=schema,
        #     stream=True,
        # )

        # return response.success(message="Message created successfully")

        async def event_generator():
            stream_iterator = await service.process_user_message(
                bot_id=bot_id,
                thread_id=thread_id,
                schema=schema,
                stream=True,
            )

            async for token in stream_iterator:
                if isinstance(token, StreamChunk):
                    yield format_sse_data(json.dumps(token.model_dump()))
                else:
                    yield format_sse_data(json.dumps({"content": str(token)}))

        return EventSourceResponse(event_generator())
    except Exception as e:
        raise APIError(message=str(e), status_code=500)


@router.post("/{bot_id}/thread")
async def create_thread(
    bot_id: UUID,
    schema: CreateThreadRequest,
    nexus_client: NexusClient = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    debug_print("current_user", current_user)
    schema_dict = schema.model_dump()
    schema_dict["group_by"] = str(bot_id)
    schema_dict["user_identifier"] = current_user.id

    res = await nexus_client.post(
        f"api/v1/threads",
        json=schema_dict,
    )

    item = res.json()
    return response.success(
        data=item.get("data"),
        message="Thread created successfully",
    )


@router.get("/{bot_id}/thread")
async def get_thread(
    bot_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    nexus_client: NexusClient = Depends(),
):
    res = await nexus_client.get(
        f"api/v1/threads",
        params={"group_by": str(bot_id)},
    )

    item = res.json()
    return response.success(data=item.get("data"))


def format_sse_data(data: str) -> str:
    """Format data for Server-Sent Events"""
    return f"data: {data}\n\n"
