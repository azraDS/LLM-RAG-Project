"""Factories for the Weaviate and OpenAI clients."""
import weaviate
from openai import OpenAI

from .config import Settings, settings as default_settings


def get_weaviate_client(settings: Settings = default_settings, with_openai_key: bool = True, **kwargs):
    """Weaviate client. The OpenAI key is forwarded so Weaviate can vectorize queries."""
    if with_openai_key:
        kwargs["additional_headers"] = {"X-OpenAI-Api-Key": settings.require_openai_key()}
    return weaviate.Client(settings.weaviate_url, **kwargs)


def get_openai_client(settings: Settings = default_settings) -> OpenAI:
    return OpenAI(api_key=settings.require_openai_key())
