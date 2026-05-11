"""Smoke test — verifies the workspace is wired up and watad is importable."""

from pytest import CaptureFixture

from watad.main import main


def test_main_runs(capsys: CaptureFixture[str]) -> None:
    main()
    assert capsys.readouterr().out.strip() == "Hello from watad!"
