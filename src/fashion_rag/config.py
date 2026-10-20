"""Central configuration: every path, URL and secret is resolved here.

Values come from environment variables (optionally loaded from a ``.env`` file in
the project root). Relative paths are resolved against the project root, so
scripts behave the same no matter which directory they are launched from.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT") or Path(__file__).resolve().parents[2])
load_dotenv(PROJECT_ROOT / ".env")


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


SAMPLE_DATA = "data/sample/sample_products.json"


def _default_data_paths() -> tuple[str, str]:
    """Full dataset if present (git-ignored), otherwise the committed 60-product sample."""
    if (PROJECT_ROOT / "data/balanced_data.json").exists():
        return "data/balanced_data.json", "data/modified_balanced_data.json"
    return SAMPLE_DATA, "data/modified_sample.json"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    model_name: str
    weaviate_url: str
    raw_data_path: Path
    modified_data_path: Path
    website_info_path: Path

    def require_openai_key(self) -> str:
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it in the .env file in the project root "
                "or as an environment variable."
            )
        return self.openai_api_key


def load_settings() -> Settings:
    default_raw, default_modified = _default_data_paths()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
        weaviate_url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
        raw_data_path=_resolve(os.getenv("DATA_PATH", default_raw)),
        modified_data_path=_resolve(
            os.getenv("MODIFIED_DATA_PATH", default_modified)
        ),
        website_info_path=_resolve(
            os.getenv("WEBSITE_INFO_PATH", "data/Fashionista_Website_Info.txt")
        ),
    )


settings = load_settings()
