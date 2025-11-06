import pytest


def test_smoke_main():
    from regex_compiler.main import main
    try:
        main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")
