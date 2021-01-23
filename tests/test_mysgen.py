"""
Functions to test mysgen.
"""
from unittest.mock import patch


from mysgen.main import init


@patch("mysgen.main.main")
@patch("mysgen.main.__name__", "__main__")
def test_init(mock_main):
    init()
    mock_main.assert_called_once()