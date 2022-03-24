"""
Integration test of mysgen.
"""
import os
from mysgen.main import main


CONFIG_FILE = "tests/fixtures/test_config.json"
known_output = "tests/fixtures/output"
output = "tests/output"


def test_integration_mysgen():
    """
    Integration test for mysgen.
    """

    main(CONFIG_FILE)

    known_files = [
        os.path.join(path, name)
        for path, _, files in os.walk(known_output)
        for name in files
    ]
    test_files = [
        os.path.join(path, name) for path, _, files in os.walk(output) for name in files
    ]

    for true_f, test_f in zip(known_files, test_files):
        with open(true_f, "r") as f:
            true = f.read()

        with open(test_f, "r") as f:
            test = f.read()

        assert test == true
