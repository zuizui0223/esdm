from pathlib import Path


def test_runtime_source_contains_no_pollination_specific_logic():
    source_root = Path(__file__).resolve().parents[1] / "src" / "esdm"
    forbidden = ("pollination", "pollen", "proboscis", "flower", "bee")
    offenders: list[tuple[str, str]] = []
    for path in source_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            if token in text:
                offenders.append((str(path.relative_to(source_root)), token))
    assert offenders == []
