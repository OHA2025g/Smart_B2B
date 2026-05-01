from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    port: int = 5000
    node_env: str = "development"
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017/smartb2b",
        validation_alias=AliasChoices("MONGODB_URI", "MONGO_URL", "DATABASE_URL"),
    )
    db_name: str | None = Field(default=None, validation_alias=AliasChoices("DB_NAME", "MONGO_DB_NAME"))
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_expires_in: str = "7d"
    cors_origin: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("CORS_ORIGIN", "CORS_ORIGINS", "ALLOWED_ORIGINS"),
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origin.split(",") if o.strip()]


settings = Settings()


