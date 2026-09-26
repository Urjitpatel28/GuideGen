from __future__ import annotations

import json
from pathlib import Path

import pytest

from guidegen_engine.config.models import Config
from guidegen_engine.context import Ctx
from guidegen_engine.drivers.fake import FakeDriver
from guidegen_engine.masking import clear_secrets
from guidegen_engine.paths import init_out_dir

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _clean_secrets():
    clear_secrets()
    yield
    clear_secrets()


@pytest.fixture
def ctx(tmp_path: Path) -> Ctx:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "Orders.xaml").write_text("<Page/>", encoding="utf-8")
    (repo / "src" / "Home.xaml").write_text("<Page/>", encoding="utf-8")
    c = Ctx(repo=repo, out=repo / "guidegen-out")
    init_out_dir(c.out)
    return c


def base_config(**over) -> Config:
    data = {
        "app": {"kind": "web", "url": "http://localhost:5173", "start": "npm run dev"},
        "brand": {"productName": "Acme Quote", "primaryColor": "#1F4E79", "accentColor": "#F29F05", "version": "2.3.0"},
    }
    data.update(over)
    return Config.model_validate(data)


@pytest.fixture
def cfg() -> Config:
    return base_config()


def write_config(c: Ctx, cfg: Config) -> None:
    c.config_path.write_text(json.dumps(cfg.dump(), indent=2), encoding="utf-8")


FAKE_VIEWS = {
    "home": {"elements": {
        "Orders": {"rect": [10, 40, 80, 24], "role": "link", "goes": "orders"},
        "Customers": {"rect": [100, 40, 90, 24], "role": "link", "goes": "customers"},
        "support@acme.test": {"rect": [10, 260, 150, 20], "role": "text", "text": "support@acme.test"},
    }},
    "orders": {"elements": {
        "New Order": {"rect": [10, 80, 100, 28], "role": "button", "goes": "new-order"},
        "Delete": {"rect": [120, 80, 70, 28], "role": "button", "goes": "orders"},
        "Home": {"rect": [300, 10, 60, 20], "role": "link", "goes": "home"},
    }},
    "new-order": {"elements": {
        "Customer": {"rect": [10, 60, 200, 24], "role": "textbox"},
        "Email": {"rect": [10, 100, 200, 24], "role": "textbox"},
        "Password": {"rect": [10, 140, 200, 24], "role": "password"},
        "Save": {"rect": [10, 200, 80, 28], "role": "button", "goes": "orders"},
    }},
    "customers": {"elements": {"Home": {"rect": [300, 10, 60, 20], "role": "link", "goes": "home"}}},
}


@pytest.fixture
def fake() -> FakeDriver:
    d = FakeDriver(FAKE_VIEWS)
    d.launch()
    return d
