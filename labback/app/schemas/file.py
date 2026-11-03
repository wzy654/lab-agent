from pydantic import BaseModel

class FileResponse(BaseModel):
    origin_name: str
    file_name: str
    size: int
    url: str

