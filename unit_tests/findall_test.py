import pytest
from pathlib import Path
from file_re import file_re
import json

ROOT = Path(__file__).parent

file_types = [
    ("simple_file.txt"),
    ("simple_file.txt.gz"),
    ("simple_file.txt.xz"),
]

@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_findall(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    emails = file_re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", simple_file)
    assert len(emails) == 4

    expected_emails = [f"user{i}@example.com" for i in range(1, 5)] 

    assert set(emails) == set(expected_emails)

@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_groups(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    emails = file_re.findall(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+)\.[a-zA-Z0-9-.]+", simple_file)
    assert len(emails) == 4
    assert len(emails[0]) == 2

    expected_emails = [(f"user{i}", "example") for i in range(1, 5)] 

    assert set(emails) == set(expected_emails)


@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_multiline_mode(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    json_matchs = file_re.findall(
        r"\{[^{]+\{[^}]+\}\r?\n\}",
        simple_file,
        multiline=False
    )

    assert len(json_matchs) == 0

    json_matchs = file_re.findall(
        r"\{[^{]+\{[^}]+\}\r?\n\}",
        simple_file,
        multiline=True
    )
    
    assert json_matchs
    assert len(json_matchs) == 2

    json_1, json_2 = json_matchs

    json_dict = json.loads(json_1)
    assert json_dict
    assert json_dict["address"]["street"] == "123 Elm Street"

    json_dict = json.loads(json_2)
    assert json_dict
    assert json_dict["address"]["street"] == "456 Maple Avenue"



