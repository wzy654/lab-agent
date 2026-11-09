#配置类
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOUR: int = 24
    LLM_API_KEY: str
    LLM_API_URL: str
    LLM_API_MODEL: str

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env",env_file_encoding="utf-8")


settings = Settings()

#文件目录
UPLOAD_DIR = BASE_DIR / "uploads"
#创建上传目录
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 1024 * 1024 * 100 # 100MB max

#上传文件类型
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx", ".xlsx", ".xls", ".txt", ".doc",
                      ".zip"
                      }
