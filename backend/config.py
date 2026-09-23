from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "EduGenius"
    DATABASE_URL: str = "sqlite:///./edugenius.db"
    GOOGLE_API_KEY: str = ""
    JWT_SECRET: str = "edugenius-hackathon-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"

settings = Settings()
