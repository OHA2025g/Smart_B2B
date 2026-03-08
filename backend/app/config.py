from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 5000
    node_env: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017/smartb2b"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_expires_in: str = "7d"
    cors_origin: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore", "populate_by_name": True}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origin.split(",") if o.strip()]


settings = Settings()
