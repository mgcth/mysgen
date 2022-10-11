"""
Functions to test mysgen.
"""
import os
import json
import pytest
from datetime import datetime
from collections import OrderedDict
from distutils.errors import DistutilsFileError
from unittest.mock import patch, mock_open, MagicMock
from mysgen.mysgen import MySGEN, Item, Post, ImagePost, DataPost, Page, build

this_dir = os.path.dirname(os.path.realpath(__file__))


CONFIG_FILE = "fixtures/config.json"


with open(this_dir + "/fixtures/test_config.json", "r") as file:
    test_config = file.read()

with open(this_dir + "/fixtures/content/posts/post.md", "r") as file:
    test_post = file.read()

with open(this_dir + "/fixtures/content/pages/home.md", "r") as file:
    test_page = file.read()


@patch("mysgen.mysgen.__name__", "__main__")
@patch("mysgen.mysgen.MySGEN")
def test_unit_build(mock_mysgen):
    """
    Test init build function.
    """
    build()

    mock_mysgen.assert_called_once()
    mock_mysgen.return_value.build.assert_called_once()


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

    @pytest.mark.parametrize(
        "item_type, files, meta",
        [
            ("unknown", [], {}),
            ("pages", [], {}),
            ("posts", [], {}),
            ("pages", ["file"], {}),
            ("posts", ["file"], {"image": "image"}),
            ("posts", ["file"], {"data": "data"}),
            ("posts", ["file"], {}),
        ],
    )
    @patch("mysgen.mysgen.DataPost")
    @patch("mysgen.mysgen.ImagePost")
    @patch("mysgen.mysgen.Post")
    @patch("mysgen.mysgen.Page")
    @patch("mysgen.mysgen.MySGEN._parse")
    @patch("mysgen.mysgen.glob.glob")
    def test_unit_find_and_parse(
        self,
        mock_glob,
        mock_parse,
        mock_page,
        mock_post,
        mock_imagepost,
        mock_datapost,
        item_type,
        files,
        meta,
    ):
        """
        Test MySGEN find_and_parse method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base = {"site_path": "", "content": "content", "output": "output"}
        mock_glob.return_value = files
        if item_type != "posts" and item_type != "pages":
            with pytest.raises(NotImplementedError):
                mysgen.find_and_parse(item_type)

        elif not files:
            with pytest.raises(FileNotFoundError):
                mysgen.find_and_parse(item_type)
            mock_glob.assert_called_once()

        else:
            mock_parse.return_value = (meta, None)
            mysgen.find_and_parse(item_type)

            if item_type == "pages":
                mock_page.assert_called_once()
            elif "image" in meta:
                mock_imagepost.assert_called_once()
            elif "data" in meta:
                mock_datapost.assert_called_once()
            else:
                mock_post.assert_called_once()

            mock_glob.assert_called_once()

    @pytest.mark.parametrize(
        "item_type, data",
        [
            ("unknown", {}),
            ("pages", {"page": Page({"status": ""}, "", "", "")}),
            ("pages", {"page": Page({"status": "published"}, "", "", "")}),
            ("posts", {"post": Post({"status": ""}, "", "", "")}),
            ("posts", {"post": Post({"status": "published"}, "", "", "")}),
        ],
    )
    @patch("mysgen.mysgen.sorted")
    def test_unit_process(self, mock_sorted, item_type, data):
        """
        Test the parse posts method.
        """
        mock_sorted.return_value = "posts_metadata"
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.pages = "pages"
        mysgen.template = "template"
        if item_type != "posts" and item_type != "pages":
            with pytest.raises(NotImplementedError):
                mysgen.process(item_type)
            return

        if item_type == "posts":
            mysgen.posts = data
            data["post"].process = MagicMock()
            mysgen.process(item_type)
            if data["post"].meta["status"] == "published":
                data["post"].process.assert_called_once_with({}, "template")
        else:
            mysgen.pages = data
            data["page"].process = MagicMock()
            mysgen.process(item_type)
            if data["page"].meta["status"] == "published":
                data["page"].process.assert_called_once_with(
                    {"pages": data, "articles": "posts_metadata"}, "template"
                )
            mock_sorted.assert_called_once()

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
        assert post.from_path is None
        assert post.to_path is None

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
    def test_unit_post_copy(self, mock_copy_tree):
        """
        Unit test of Post _copy method.
        """
        post = Post({}, "content", "src", "build")
        post.from_path = "from"
        post.to_path = "to"
        post.copy()

        mock_copy_tree.assert_called_once_with("from", "to")

    def test_unit_post_copy_raises(self):
        """
        Unit test of Post _copy method when raises exception.
        """
        post = Post({}, "content", "src", "build")
        post.from_path = "/error/"
        post.to_path = "to"
        with pytest.raises(DistutilsFileError):
            post.copy()


class TestUnitImagePost:
    """
    Unit tests of ImagePost class.
    """

    def test_unit_imagepost_init(self):
        """
        Unit test of ImagePost init method.
        """
        meta = {"path": "posts/post"}
        post = ImagePost(meta, "content", "src", "build")

        assert post.meta == meta
        assert post.content == "content"
        assert post.src_path == "src"
        assert post.build_path == "build"
        assert post.from_path == "src/images/post"
        assert post.to_path == "build/posts/post/images"

    @patch("mysgen.mysgen.Post.copy")
    @patch("mysgen.mysgen.Post.process")
    def test_unit_imagepost_process(self, mock_item_process, mock_post_copy):
        """
        Unit test of ImagePost process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        post = ImagePost(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        post.process(mock_base, mock_template)

        mock_item_process.assert_called_once_with(mock_base, mock_template)
        mock_post_copy.assert_called_once()

    @pytest.mark.parametrize(
        "path, small_image_height, glob_return, split_return, small_image",
        [
            (
                "posts/path",
                300,
                ["path/image1.jpg", "path/image2.jpg"],
                [("path", "image1.jpg"), ("path", "image2.jpg")],
                ["image1_small.jpg", "image2_small.jpg"],
            )
        ],
    )
    @patch("mysgen.mysgen.Image.open")
    @patch("mysgen.mysgen.glob.glob")
    @patch("mysgen.mysgen.join")
    def test_unit_imagepost_resize_image(
        self,
        mock_join,
        mock_glob,
        mock_image,
        glob_return,
        path,
        small_image_height,
        split_return,
        small_image,
    ):
        """
        Unit test of ImagePost _resize_image method.
        """
        meta = {"path": path, "small_image_height": small_image_height}
        post = ImagePost(meta, MagicMock(), MagicMock(), MagicMock())
        mock_glob.return_value = (g for g in glob_return)
        post._resize_image()

        mock_glob.assert_called_once()
        assert mock_join.call_count == 5
        assert mock_image.return_value.__enter__.return_value.thumbnail.call_count == 2
        assert post.meta["small_image"] == small_image
        assert mock_image.return_value.__enter__.return_value.save.call_count == 2


class TestUnitDataPost:
    """
    Unit tests of DataPost class.
    """

    def test_unit_datapost_init(self):
        """
        Unit test of DataPost init method.
        """
        meta = {"path": "posts/post"}
        post = DataPost(meta, "content", "src", "build")

        assert post.meta == meta
        assert post.content == "content"
        assert post.src_path == "src"
        assert post.build_path == "build"
        assert post.from_path == "src/data/post"
        assert post.to_path == "build/posts/post/data"

    @patch("mysgen.mysgen.DataPost.copy")
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
        page.process(mock_base, mock_template)

        assert mock_base["path"] == expected
        assert mock_base["page_name"] == mock_meta["type"]
        mock_page_patch_content.assert_called_once_with(
            mock_base["build_date"], datetime.now().strftime("%Y-%m-%d")
        )
        mock_item_process.assert_called_once_with(
            mock_base, mock_template[page.meta["type"]]
        )
