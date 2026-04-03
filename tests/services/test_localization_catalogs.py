from __future__ import annotations

import json

from core.util.app_paths import AppPaths


def test_localization_catalogs_expose_the_same_keys():
    locales_dir = AppPaths.locales_dir()
    assert locales_dir is not None

    with open(locales_dir / "en.json", "r", encoding="utf-8") as handle:
        en_catalog = json.load(handle)
    with open(locales_dir / "it.json", "r", encoding="utf-8") as handle:
        it_catalog = json.load(handle)

    assert set(en_catalog) == set(it_catalog)
