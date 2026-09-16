from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]


def test_generic_interaction_example_executes():
    runpy.run_path(str(ROOT / "examples" / "generic_interactions.py"), run_name="__main__")


def test_pollination_example_executes_only_through_generic_api():
    runpy.run_path(
        str(ROOT / "examples" / "pollination_as_one_example.py"),
        run_name="__main__",
    )
