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

    @patch("mysgen.mysgen.join")
    @patch("mysgen.mysgen.isfile")
    @patch("mysgen.mysgen.listdir")
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
        item = Item({}, "content", "src", "build")

        assert item.meta == {}
        assert item.content == "content"
        assert item.src_path == "src"
        assert item.build_path == "build"

    @patch("builtins.open", mock_open(read_data=None))
    @patch("mysgen.mysgen.makedirs")
    @patch("mysgen.mysgen.join")
    def test_unit_item_process(self, mock_os_path_join, mock_os_makedirs):
        """
        Unit test of Item process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        item = Item(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        item.process(mock_base, mock_template)

        assert mock_os_path_join.call_count == 2
        mock_os_makedirs.assert_called_once()

    def test_unit_item_patch_content(self):
        """
        Unit test of Item _patch_content method.
        """
        item = Item({}, "patch_me", "src", "build")
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
        post = Post({}, "content", "src", "build")

        assert post.meta == {}
        assert post.content == "content"
        assert post.src_path == "src"
        assert post.build_path == "build"

    @pytest.mark.parametrize(
        "meta, content, base, template",
        [
            (
                {"path": "path"},
                "content",
                {"home": "home", "post_url": "post_url"},
                MagicMock(),
            ),
        ],
    )
    @patch("mysgen.mysgen.Item.process")
    @patch("mysgen.mysgen.Item._patch_content")
    def test_unit_post_process(
        self, mock_item_patch_content, mock_item_process, meta, content, base, template
    ):
        """
        Unit test of Post process method.
        """
        post = Post(meta, content, "src", "build")
        post.process(base, template)

        assert base["meta"] == meta
        assert base["article_content"] == content
        assert base["page"] == base["home"]
        assert base["page_name"] == "index"
        mock_item_patch_content.assert_called_once()
        mock_item_process.assert_called_once_with(base, template["article"])

    @patch("mysgen.mysgen.copy_tree")
    @patch("mysgen.mysgen.shutil.copyfile")
    def test_unit_post_copy(self, mock_shutil_copyfile, mock_copy_tree):
        """
        Unit test of Post _copy method.
        """
        post = Post({}, "content", "src", "build")
        post._copy("from", "to")

        mock_shutil_copyfile.assert_called_once_with("from", "to")

    @pytest.mark.parametrize(
        "meta, content, src, build, item, expect",
        [
            (
                {"data": "data_1, data_2", "path": "path"},
                "content",
                "content",
                "output",
                "data",
                [
                    ("content/data/data_1", "output/path/data"),
                    ("content/data/data_2", "output/path/data"),
                ],
            ),
            (
                {"data": "data_1", "path": "path"},
                "content",
                "content",
                "output",
                "data",
                [("content/data/data_1", "output/path/data")],
            ),
            (
                {"data": "  data_1, ", "path": "path"},
                "content",
                "content",
                "output",
                "data",
                [("content/data/data_1", "output/path/data")],
            ),
        ],
    )
    def test_unit_post_extract(self, meta, content, src, build, item, expect):
        """
        Unit test of Post _extract method.
        """
        post = Post(meta, content, src, build)
        for i, (from_path, to_path) in enumerate(post._extract(item)):
            assert from_path == expect[i][0]
            assert to_path == expect[i][1]


class TestUnitImagePost:
    """
    Unit tests of ImagePost class.
    """

    def test_unit_imagepost_init(self):
        """
        Unit test of ImagePost init method.
        """
        post = ImagePost({}, "content", "src", "build")

        assert post.meta == {}
        assert post.content == "content"
        assert post.src_path == "src"
        assert post.build_path == "build"

    @patch("mysgen.mysgen.ImagePost.copy_image")
    @patch("mysgen.mysgen.Post.process")
    def test_unit_imagepost_process(self, mock_item_process, mock_imagepost_copy_image):
        """
        Unit test of ImagePost process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        post = ImagePost(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        post.process(mock_base, mock_template)

        mock_item_process.assert_called_once_with(mock_base, mock_template)
        mock_imagepost_copy_image.assert_called_once_with()

    @pytest.mark.parametrize(
        "src, build, item, from_path, to_path",
        [
            ("content", "output", "image", "content/image/data_1", "output/path"),
        ],
    )
    @patch("mysgen.mysgen.ImagePost._resize_image")
    @patch("mysgen.mysgen.Post._copy")
    @patch("mysgen.mysgen.Post._extract")
    def test_unit_imagepost_copy_image(
        self,
        mock_extract,
        mock_copy,
        mock_resize_image,
        src,
        build,
        item,
        from_path,
        to_path,
    ):
        """
        Unit test of ImagePost copy_image method.
        """
        post = ImagePost(MagicMock(), MagicMock(), src, build)
        mock_extract.return_value = [(from_path, to_path)]
        post.copy_image()

        mock_extract.assert_called_once_with(item)
        mock_copy.assert_called_once_with(from_path, to_path)
        mock_resize_image.assert_called_once_with(to_path)

    def test_unit_imagepost_resize_image(self):
        """
        Unit test of ImagePost _resize_image method.
        """
        pass


class TestUnitDataPost:
    """
    Unit tests of DataPost class.
    """

    def test_unit_datapost_init(self):
        """
        Unit test of DataPost init method.
        """
        post = DataPost({}, "content", "src", "build")

        assert post.meta == {}
        assert post.content == "content"
        assert post.src_path == "src"
        assert post.build_path == "build"

    @patch("mysgen.mysgen.DataPost.copy_data")
    @patch("mysgen.mysgen.Post.process")
    def test_unit_datapost_process(self, mock_post_process, mock_datapost_copy_data):
        """
        Unit test of DataPost process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        post = DataPost(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        post.process(mock_base, mock_template)

        mock_post_process.assert_called_once_with(mock_base, mock_template)
        mock_datapost_copy_data.assert_called_once_with()

    @pytest.mark.parametrize(
        "src, build, item, from_path, to_path",
        [
            ("content", "output", "data", "content/data/data_1", "output/path"),
        ],
    )
    @patch("mysgen.mysgen.Post._copy")
    @patch("mysgen.mysgen.Post._extract")
    def test_unit_datapost_copy_data(
        self, mock_extract, mock_copy, src, build, item, from_path, to_path
    ):
        """
        Unit test of DataPost copy_data method.
        """
        post = DataPost(MagicMock(), MagicMock(), src, build)
        mock_extract.return_value = [(from_path, to_path)]
        post.copy_data()

        mock_extract.assert_called_once_with(item)
        mock_copy.assert_called_once_with(from_path, to_path)


class TestUnitPage:
    """
    Unit tests of Page class.
    """

    def test_unit_page_init(self):
        """
        Unit test of Page init method.
        """
        page = Page({}, "content", "src", "build")

        assert page.meta == {}
        assert page.content == "content"
        assert page.src_path == "src"
        assert page.build_path == "build"

    @pytest.mark.parametrize(
        "path, expected", [("pages/home", ""), ("pages/archive", "archive")]
    )
    @patch("mysgen.mysgen.Item.process")
    @patch("mysgen.mysgen.Page._patch_content")
    def test_unit_page_process(
        self, mock_page_patch_content, mock_item_process, path, expected
    ):
        """
        Unit test of Page process method.
        """
        mock_meta = {"path": path, "type": "index"}
        mock_base = {"home": "home", "build_date": "build_date"}
        mock_template = MagicMock()
        page = Page(mock_meta, MagicMock(), MagicMock(), MagicMock())
        page.process(mock_base, mock_template, "pages", "posts")

        assert mock_base["path"] == expected
        assert mock_base["page_name"] == mock_meta["type"]
        assert mock_base["pages"] == "pages"
        assert mock_base["articles"] == "posts"
        mock_page_patch_content.assert_called_once_with(
            mock_base["build_date"], datetime.now().strftime("%Y-%m-%d")
        )
        mock_item_process.assert_called_once_with(
            mock_base, mock_template[page.meta["type"]]
        )
