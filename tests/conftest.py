from types import SimpleNamespace

import pandas as pd
import pytest

from fashion_rag.assistant import FashionAssistant
from fashion_rag.config import Settings


class FakeOpenAI:
    """Mimics ``client.chat.completions.create`` and records every call."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.replies.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeWeaviate:
    """Mimics the v3 fluent ``query.get(...).with_hybrid(...).with_limit(...).do()`` chain."""

    def __init__(self, products):
        self.products = products
        self.query = self

    def get(self, *args, **kwargs):
        return self

    def with_hybrid(self, **kwargs):
        return self

    def with_limit(self, n):
        return self

    def do(self):
        return {"data": {"Get": {"Product": self.products}}}


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "category": ["Clothing and Accessories", "Footwear"],
            "sub_category": ["Bottomwear", "Sports Shoes"],
            "product_category": ["Jeans", "Running Shoes"],
        }
    )


@pytest.fixture
def settings(tmp_path):
    info = tmp_path / "info.txt"
    info.write_text("Returns accepted within 30 days.")
    return Settings(
        openai_api_key="test-key",
        model_name="test-model",
        weaviate_url="http://example:8080",
        raw_data_path=tmp_path / "raw.json",
        modified_data_path=tmp_path / "mod.json",
        website_info_path=info,
    )


@pytest.fixture
def make_assistant(df, settings):
    def _make(openai_replies=(), products=()):
        openai_client = FakeOpenAI(openai_replies)
        assistant = FashionAssistant(
            df,
            weaviate_client=FakeWeaviate(list(products)),
            openai_client=openai_client,
            settings=settings,
        )
        return assistant, openai_client

    return _make
