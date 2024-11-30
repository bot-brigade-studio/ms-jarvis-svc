from uuid import UUID
from fastapi import APIRouter, Depends
from app.api.v1.endpoints.deps import CurrentUser, get_current_user
from app.schemas.chat import CreateThreadRequest
from app.utils.debug import debug_print
from app.utils.http_client import NexusClient
from app.utils.response_handler import response

router = APIRouter()


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
