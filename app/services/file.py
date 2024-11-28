from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from app.utils.debug import debug_print
from app.utils.http_client import SanctumClient
from app.core.config import settings
from uuid_extensions import uuid7


class FileService:
    def __init__(self):
        self.sanctum_client = SanctumClient()
        self.bucket_name = settings.BUCKET_NAME

    async def upload_image(self, file: UploadFile) -> str:
        try:
            file_type = file.filename.split(".")[-1]
            file_uuid = str(uuid7())
            file_name = f"{file_uuid}.{file_type}"

            files = {"file": (file_name, file.file, file.content_type)}
            response = await self.sanctum_client.put(
                f"api/v1/objects/{self.bucket_name}/{file_name}",
                files=files,
            )

            return response.json()
        except Exception as e:
            debug_print(f"Error uploading image: {e}")
            raise e

    async def stream_file(self, file_name: str) -> StreamingResponse:

        response = await self.sanctum_client.get(
            f"api/v1/objects/{self.bucket_name}/{file_name}"
        )

        return StreamingResponse(
            response.aiter_bytes(),
            media_type=response.headers["content-type"],
            headers={
                key: value
                for key, value in response.headers.items()
                if key.lower() != "content-length"
            },
        )
