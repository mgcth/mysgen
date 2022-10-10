"""
Functions to test mysgen.
"""
import os
import json
import pytest
from datetime import datetime
from mysgen.mysgen import MySGEN, Item, Post, ImagePost, DataPost, Page
from collections import OrderedDict
from unittest.mock import patch, mock_open, MagicMock


this_dir = os.path.dirname(os.path.realpath(__file__))


CONFIG_FILE = "fixtures/config.json"


with open(this_dir + "/fixtures/test_config.json", "r") as file:
    test_config = file.read()

with open(this_dir + "/fixtures/content/posts/post.md", "r") as file:
    test_post = file.read()

with open(this_dir + "/fixtures/content/pages/home.md", "r") as file:
    test_page = file.read()


class TestUnitMySGEN:
    """
    Unit tests for MySGEN.
    """

    def test_unit_mysgen_init(self):
        """
        Test MySGEN init method.
        """
        mysgen = MySGEN(CONFIG_FILE)

        assert mysgen.config_file == CONFIG_FILE
        assert mysgen.base == {}
        assert mysgen.template == {}
        assert mysgen.posts == {}
        assert mysgen.pages == {}
        assert mysgen.markdown is None

    @patch("mysgen.mysgen.MySGEN.process")
    @patch("mysgen.mysgen.MySGEN.build_menu")
    @patch("mysgen.mysgen.MySGEN.find_and_parse")
    @patch("mysgen.mysgen.MySGEN.define_environment")
    @patch("mysgen.mysgen.MySGEN.set_base_config")
    def test_unit_mysgen_build(
        self,
        mock_set_base_config,
        mock_define_environment,
        mock_find_and_parse,
        mock_build_menu,
        mock_process,
    ):
        """
        Test MySGEN build method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.build()
        mock_set_base_config.assert_called_once()
        mock_define_environment.assert_called_once()
        assert mock_find_and_parse.call_count == 2
        mock_build_menu.assert_called_once()
        assert mock_process.call_count == 2

    @patch("builtins.open", mock_open(read_data=test_config))
    def test_unit_mysgen_set_base_config(self):
        """
        Test MySGEN set_base_config method.
        """
        with open(test_config, "r") as file:
            base = json.loads(file.read(), object_pairs_hook=OrderedDict)

        # fs.create_file("../../site/test_config.json")

        mysgen = MySGEN(CONFIG_FILE)
        mysgen.set_base_config()

        assert mysgen.base["content"] == os.path.join(
            base["site_path"], base["content"]
        )
        assert mysgen.base["output"] == os.path.join(base["site_path"], base["output"])
        assert mysgen.base["templates"] == os.path.join(
            base["template_path"], base["templates"]
        )
        assert mysgen.base["tags"] == []
        assert mysgen.base["tags"] == []

    def test_unit_build_menu(self):
        """
        Test build menu function.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.pages = ["test_page1", "test_page2"]
        mysgen.base = {"menuitems": {"home": "", "archive": "archive"}}
        mysgen.build_menu()

        assert mysgen.base["menuitems"] == {
            "home": "",
            "archive": "archive",
            "test_page1": "test_page1",
            "test_page2": "test_page2",
        }

    @patch("mysgen.mysgen.os.path.join")
    @patch("mysgen.mysgen.os.path.isfile")
    @patch("mysgen.mysgen.os.listdir")
    @patch("mysgen.mysgen.markdown.Markdown")
    @patch("mysgen.mysgen.Environment")
    @patch("mysgen.mysgen.FileSystemLoader")
    def test_unit_define_environment(
        self,
        mock_filesystemloader,
        mock_environment,
        mock_markdown,
        mock_listdir,
        mock_isfile,
        mock_join,
    ):
        """
        Test MySGEN define environment method.

        Args:
            mock_filesystemloader: mock filesystem loader
            mock_environment: mock environment object
            mock_markdown: mock markdown object
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base = {"templates": "test", "markdown_extensions": ["test"]}
        mysgen.define_environment()

        mock_filesystemloader.assert_called_once()
        mock_environment.assert_called_once()
        mock_markdown.assert_called_once()

        assert mysgen.markdown == mock_markdown.return_value

    @pytest.mark.parametrize("item_type", [("posts"), ("pages"), ("unknown")])
    def test_unit_find_and_parse(self, item_type):
        """
        Test MySGEN find_and_parse method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        if item_type != "posts" and item_type != "pages":
            with pytest.raises(NotImplementedError):
                mysgen.find_and_parse(item_type)

    @pytest.mark.parametrize("item_type", [("posts"), ("pages"), ("unknown")])
    def test_unit_process(self, item_type):
        """
        Test the parse posts method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        if item_type != "posts" and item_type != "pages":
            with pytest.raises(NotImplementedError):
                mysgen.process(item_type)

    @patch.object(os, "listdir")
    @patch.object(MySGEN, "_parse")
    def test_unit_format_metadata(self, mock_parse_pages, mock_listdir):
        """
        Test the parse pages method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base["tags"] = []
        mysgen.base["categories"] = []
        meta = {
            "date": ["2022-01-01"],
            "tags": ["a, b"],
            "category": ["c"],
            "test": "",
        }
        meta_return = mysgen._format_metadata(meta)

        meta_answer = {
            "date": datetime.strptime("2022-01-01", "%Y-%m-%d"),
            "tags": ["a", " b"],
            "category": "c",
            "test": "",
        }
        assert meta_return == meta_answer

    @patch("builtins.open", mock_open(read_data=test_post))
    @patch("mysgen.mysgen.markdown.Markdown")
    @patch("mysgen.mysgen.MySGEN._format_metadata")
    def test_unit_parse(self, mock_format_metadata, mock_markdown):
        """
        Test the parse pages method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base = MagicMock()
        mysgen.markdown = mock_markdown
        meta, content = mysgen._parse(MagicMock())

        assert meta == mock_format_metadata.return_value
        assert content == mock_markdown.convert.return_value


class TestUnitItem:
    """
    Unit tests of Item class.
    """

    def test_unit_item_init(self):
        """
        Unit test of Item init method.
        """
        item = Item({}, "")

        assert item.meta == {}
        assert item.content == ""

    @patch("builtins.open", mock_open(read_data=None))
    @patch("mysgen.mysgen.os.makedirs")
    @patch("mysgen.mysgen.os.path.join")
    def test_unit_item_process(self, mock_os_path_join, mock_os_makedirs):
        """
        Unit test of Item process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        item = Item(MagicMock(), MagicMock())
        item.process(mock_base, mock_template)

        assert mock_os_path_join.call_count == 2
        mock_os_makedirs.assert_called_once()

    def test_unit_item_patch_content(self):
        """
        Unit test of Item _patch_content method.
        """
        item = Item({}, "patch_me")
        item._patch_content("patch", "PATCHED")

        assert item.content == "PATCHED_me"


class TestUnitPost:
    """
    Unit tests of Post class.
    """

    def test_unit_post_init(self):
        """
        Unit test of Post init method.
        """
        post = Post({}, "")

        assert post.meta == {}
        assert post.content == ""

    @patch("mysgen.mysgen.Item.process")
    @patch("mysgen.mysgen.Item._patch_content")
    def test_unit_post_process(self, mock_item_patch_content, mock_item_process):
        """
        Unit test of Post process method.
        """
        input1 = MagicMock()
        input2 = MagicMock()
        mock_base = MagicMock()
        mock_template = MagicMock()
        post = Post(input1, input2)
        post.process(mock_base, mock_template)

        assert post.meta == input1
        assert post.content == input2
        mock_item_patch_content.assert_called_once()
        mock_item_process.assert_called_once_with(mock_base, mock_template["article"])

    @patch("mysgen.mysgen.shutil.copyfile")
    def test_unit_post_copy(self, mock_shutil_copyfile):
        """
        Unit test of Post _copy method.
        """
        post = Post({}, "")
        post._copy("from", "to")

        mock_shutil_copyfile.assert_called_once_with("from", "to")
