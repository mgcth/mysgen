"""
Functions to test mysgen.
"""
import os
import json
from datetime import datetime
from collections import OrderedDict
from unittest.mock import patch, mock_open
from mysgen.main import init, main, MySGEN


this_dir = os.path.dirname(os.path.realpath(__file__))


CONFIG_FILE = "fixtures/config.json"


@patch("mysgen.main.main")
@patch("mysgen.main.__name__", "__main__")
def test_unit_init(mock_main):
    """
    Test init function.
    """
    init(CONFIG_FILE)
    mock_main.assert_called_once()


@patch("mysgen.main.MySGEN")
def test_unit_main(mock_mysgen):
    """
    Test main function.
    """
    main(CONFIG_FILE)
    mock_mysgen.assert_called_once()
    mock_mysgen.return_value.build.assert_called_once()


def test_unit_mysgen_init():
    """
    Test MySGEN init method.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    mysgen = MySGEN(CONFIG_FILE)

    assert mysgen.config_file == CONFIG_FILE
    assert mysgen.template == {}
    assert mysgen.posts == {}
    assert mysgen.pages == {}
    assert mysgen.date == date


@patch.object(MySGEN, "_process_pages")
@patch.object(MySGEN, "_process_posts")
@patch.object(MySGEN, "_build_menu")
@patch.object(MySGEN, "_parse_pages")
@patch.object(MySGEN, "_parse_posts")
@patch.object(MySGEN, "_define_environment")
@patch.object(MySGEN, "_set_base_config")
def test_unit_mysgen_build(
    mock_set_base_config,
    mock_define_environment,
    mock_parse_posts,
    mock_parse_pages,
    mock_build_menu,
    mock_process_posts,
    mock_process_pages,
):
    """
    Test MySGEN build function.
    """
    mysgen = MySGEN(CONFIG_FILE)
    mysgen.build()
    mock_set_base_config.assert_called_once()
    mock_define_environment.assert_called_once()
    mock_parse_posts.assert_called_once()
    mock_parse_pages.assert_called_once()
    mock_build_menu.assert_called_once()
    mock_process_posts.assert_called_once()
    mock_process_pages.assert_called_once()


with open(this_dir + "/fixtures/test_config.json", "r") as file:
    test_config = file.read()


@patch("builtins.open", mock_open(read_data=test_config))
def test_unit_mysgen_set_base_config(fs):
    """
    Test MySGEN set_base_config method.
    """
    with open(test_config, "r") as file:
        base = json.loads(file.read(), object_pairs_hook=OrderedDict)

    fs.create_file("../../site/test_config.json")

    mysgen = MySGEN(CONFIG_FILE)
    mysgen._set_base_config()

    assert mysgen.base["content"] == os.path.join(base["site_path"], base["content"])
    assert mysgen.base["output"] == os.path.join(base["site_path"], base["output"])
    assert mysgen.base["templates"] == os.path.join(
        base["template_path"], base["templates"]
    )
    assert mysgen.base["tags"] == []
    assert mysgen.base["tags"] == []


def test_unit_parse_metadata():
    """
    Test parse function for metadata.

    This does not test the whole function, yet.
    """
    metadata = {
        "author": ["A man has no name"],
        "category": ["Category"],
        "date": ["2021-01-24"],
        "image": ["20210124.jpg"],
        "status": ["published"],
        "tags": ["tag1, tag2"],
        "title": ["Test post"],
        "type": ["photo"],
    }

    mysgen = MySGEN(CONFIG_FILE)
    mysgen.base = {"tags": [], "categories": []}
    meta = mysgen._parse_metadata(metadata)

    assert meta["title"] == metadata["title"]
    assert meta["date"] == metadata["date"]
    assert meta["author"] == metadata["author"]
    assert meta["category"] == metadata["category"]
    assert meta["tags"] == metadata["tags"]
    assert meta["type"] == metadata["type"]
    assert meta["image"] == metadata["image"]
    assert meta["status"] == metadata["status"]

    assert mysgen.base["tags"] == metadata["tags"]
    assert mysgen.base["categories"] == [metadata["category"]]


@patch.object(os, "listdir")
@patch.object(MySGEN, "_parse")
def test_unit_parse_posts(mock_parse_posts, mock_listdir):
    """
    Test the parse posts method.
    """
    expected = ["f1", "f2"]
    mock_listdir.return_value = expected

    mysgen = MySGEN(CONFIG_FILE)
    mysgen.base = {"content": ""}
    mysgen._parse_posts()

    assert mock_parse_posts.call_count == 2


@patch.object(os, "listdir")
@patch.object(MySGEN, "_parse")
def test_unit_parse_pages(mock_parse_pages, mock_listdir):
    """
    Test the parse pages method.
    """
    expected = ["f1.md", "f2.md"]
    mock_listdir.return_value = expected

    mysgen = MySGEN(CONFIG_FILE)
    mysgen.base = {"content": "", "menuitems": {"home": "", "archive": "archive"}}
    mysgen._parse_pages()

    assert mock_parse_pages.call_count == 2
    assert mysgen.base["menuitems"]["home"] == ""
    assert mysgen.base["menuitems"]["f1"] == "f1"
    assert mysgen.base["menuitems"]["f2"] == "f2"
    assert mysgen.base["js_menu"] == list(mysgen.base["menuitems"].keys())


def test_unit_build_menu():
    """
    Test build menu function.
    """
    mysgen = MySGEN(CONFIG_FILE)
    mysgen.pages = ["test_page1", "test_page2"]
    mysgen.base = {"menuitems": {"home": "", "archive": "archive"}}
    mysgen._build_menu()

    assert mysgen.base["menuitems"] == {
        "home": "",
        "archive": "archive",
        "test_page1": "test_page1",
        "test_page2": "test_page2",
    }
