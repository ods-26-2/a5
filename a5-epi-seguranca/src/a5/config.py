"""Configuração do A5, lida do ambiente (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="A5_")

    env: str = "development"
    log_level: str = "INFO"

    i9_client: str = "mock"
    s2_client: str = "mock"
    s3_client: str = "mock"
    s4_client: str = "mock"

    # RNF2 / RF-orquestração: faixa de confiança intermediária vira "incerto",
    # nunca ação automática nem silêncio.
    confianca_minima: float = 0.4
    confianca_maxima: float = 0.8


settings = Settings()
