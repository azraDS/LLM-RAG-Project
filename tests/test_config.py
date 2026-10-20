import pytest

from fashion_rag import config
from fashion_rag.config import PROJECT_ROOT, load_settings


def test_defaults(monkeypatch, tmp_path):
    for name in ("WEAVIATE_URL", "MODEL_NAME", "DATA_PATH", "MODIFIED_DATA_PATH", "WEBSITE_INFO_PATH"):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/balanced_data.json").touch()
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    s = load_settings()
    assert s.weaviate_url == "http://localhost:8080"
    assert s.model_name == "gpt-3.5-turbo"
    assert s.modified_data_path == tmp_path / "data/modified_balanced_data.json"


def test_falls_back_to_committed_sample_without_full_dataset(monkeypatch, tmp_path):
    for name in ("DATA_PATH", "MODIFIED_DATA_PATH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    s = load_settings()
    assert s.raw_data_path == tmp_path / "data/sample/sample_products.json"
    assert s.modified_data_path == tmp_path / "data/modified_sample.json"


def test_env_overrides_and_relative_paths_resolve_to_project_root(monkeypatch):
    monkeypatch.setenv("WEAVIATE_URL", "http://weaviate:8080")
    monkeypatch.setenv("MODIFIED_DATA_PATH", "somewhere/else.json")
    s = load_settings()
    assert s.weaviate_url == "http://weaviate:8080"
    assert s.modified_data_path == PROJECT_ROOT / "somewhere/else.json"


def test_absolute_paths_are_kept(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_PATH", str(tmp_path / "raw.json"))
    assert load_settings().raw_data_path == tmp_path / "raw.json"


def test_missing_key_raises_helpful_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        load_settings().require_openai_key()


def test_module_level_settings_exist():
    assert config.settings.weaviate_url
