from scripts.check_commit_msg import is_valid_subject


def test_accepts_conventional_commit_subject() -> None:
    assert is_valid_subject("feat(supplier-matching): add catalog filter")


def test_accepts_fixup_subject() -> None:
    assert is_valid_subject("fixup! feat(api): add health check")


def test_rejects_non_conventional_subject() -> None:
    assert not is_valid_subject("WIP update stuff")
