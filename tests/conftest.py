from collections.abc import Iterator
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from magic_link.config import reset_settings_cache


@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "test-secret")
    reset_settings_cache()
    yield
    reset_settings_cache()
