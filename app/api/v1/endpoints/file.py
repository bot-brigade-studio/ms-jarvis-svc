from fastapi import APIRouter, Depends, UploadFile, File
from app.api.v1.endpoints.deps import CurrentUser, get_current_user
from app.services.file import FileService
from app.utils.response_handler import response
import imghdr
from app.core.exceptions import APIError


router = APIRouter()


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    service: FileService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Validate file size (10MB = 10 * 1024 * 1024 bytes)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)  # Reset file pointer to beginning

    if file_size > MAX_SIZE:
        raise APIError(
            message="File size too large. Maximum size allowed is 10MB",
            status_code=400,
        )

    # Validate file type
    file_type = imghdr.what(None, h=contents)
    valid_image_types = ["jpeg", "jpg", "png", "gif"]

    if not file_type or file_type not in valid_image_types:
        raise APIError(
            message="Invalid file type. Only JPEG, PNG, and GIF images are allowed",
            status_code=400,
        )

    item = await service.upload_image(file)
    return response.success(
        data=item,
        message="Image uploaded successfully",
    )


@router.get("/stream/{file_name}")
async def stream_file(
    file_name: str,
    service: FileService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await service.stream_file(file_name)
