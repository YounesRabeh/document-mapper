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
    with open(locales_dir / "es.json", "r", encoding="utf-8") as handle:
        es_catalog = json.load(handle)
    with open(locales_dir / "fr.json", "r", encoding="utf-8") as handle:
        fr_catalog = json.load(handle)
    with open(locales_dir / "de.json", "r", encoding="utf-8") as handle:
        de_catalog = json.load(handle)
    with open(locales_dir / "ru.json", "r", encoding="utf-8") as handle:
        ru_catalog = json.load(handle)

    assert set(en_catalog) == set(it_catalog)
    assert set(en_catalog) == set(es_catalog)
    assert set(en_catalog) == set(fr_catalog)
    assert set(en_catalog) == set(de_catalog)
    assert set(en_catalog) == set(ru_catalog)
