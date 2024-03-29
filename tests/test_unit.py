"""
Functions to test mysgen.
"""
import os
import json
import pytest
import hashlib
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
from distutils.errors import DistutilsFileError
from unittest.mock import patch, mock_open, MagicMock
from mysgen.mysgen import MySGEN, Item, Post, ImagePost, DataPost, Page, DataPage, build

this_dir = os.path.dirname(os.path.realpath(__file__))


CONFIG_FILE = "fixtures/config.json"
TODAY = datetime.now()


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

    @pytest.mark.parametrize("s3_bucket", [("bucket"), (False), (None)])
    @patch("mysgen.mysgen.MySGEN.copy_s3")
    @patch("mysgen.mysgen.MySGEN.process")
    @patch("mysgen.mysgen.MySGEN.build_menu")
    @patch("mysgen.mysgen.MySGEN.find_and_parse")
    @patch("mysgen.mysgen.MySGEN.define_environment")
    @patch("mysgen.mysgen.MySGEN.set_base_config")
    @patch("mysgen.mysgen.MySGEN.copy_assets")
    def test_unit_mysgen_build(
        self,
        mock_copy_assets,
        mock_set_base_config,
        mock_define_environment,
        mock_find_and_parse,
        mock_build_menu,
        mock_process,
        mock_copy_s3,
        s3_bucket,
    ):
        """
        Test MySGEN build method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base["s3-bucket"] = s3_bucket
        mysgen.build()

        mock_set_base_config.assert_called_once()
        if s3_bucket:
            mock_copy_s3.assert_called_once()
        mock_define_environment.assert_called_once()
        assert mock_find_and_parse.call_count == 2
        mock_build_menu.assert_called_once()
        assert mock_process.call_count == 2
        mock_copy_assets.assert_called_once()

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

        assert mysgen.base["src_path"] == base["src_path"]
        assert mysgen.base["build_path"] == base["build_path"]
        assert mysgen.base["tags"] == []
        assert mysgen.base["tags"] == []
        assert mysgen.base["build_date"] == str(
            datetime(TODAY.year, TODAY.month, TODAY.day).strftime("%Y-%m-%d")
        )

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

    @patch("mysgen.mysgen.scandir")
    @patch("mysgen.mysgen.markdown.Markdown")
    @patch("mysgen.mysgen.Environment")
    @patch("mysgen.mysgen.FileSystemLoader")
    def test_unit_define_environment(
        self,
        mock_filesystemloader,
        mock_environment,
        mock_markdown,
        mock_scandir,
    ):
        """
        Test MySGEN define environment method.

        Args:
            mock_filesystemloader: mock filesystem loader
            mock_environment: mock environment object
            mock_markdown: mock markdown object
            mock_scandir: mock of scandir
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base = {"theme_path": "test", "markdown_extensions": ["test"]}
        mysgen.define_environment()

        mock_filesystemloader.assert_called_once()
        mock_environment.assert_called_once()
        mock_markdown.assert_called_once()
        mock_scandir.assert_called_once()

        assert mysgen.markdown == mock_markdown.return_value

    @pytest.mark.parametrize(
        "item_type, files, meta",
        [
            (Path("unknown"), [], {}),
            (Path("pages"), [], {}),
            (Path("posts"), [], {}),
            (Path("pages"), ["file"], {}),
            (Path("pages"), ["file"], {"data": "data"}),
            (Path("pages"), ["file"], {"data": False}),
            (Path("posts"), ["file"], {"image": "image"}),
            (Path("posts"), ["file"], {"image": False}),
            (Path("posts"), ["file"], {"data": "data"}),
            (Path("posts"), ["file"], {"data": False}),
            (Path("posts"), ["file"], {}),
        ],
    )
    @patch("mysgen.mysgen.DataPage")
    @patch("mysgen.mysgen.DataPost")
    @patch("mysgen.mysgen.ImagePost")
    @patch("mysgen.mysgen.Post")
    @patch("mysgen.mysgen.Page")
    @patch("mysgen.mysgen.MySGEN._parse")
    @patch("mysgen.mysgen.Path.glob")
    def test_unit_find_and_parse(
        self,
        mock_glob,
        mock_parse,
        mock_page,
        mock_post,
        mock_imagepost,
        mock_datapost,
        mock_datapage,
        item_type,
        files,
        meta,
    ):
        """
        Test MySGEN find_and_parse method.
        """
        mysgen = MySGEN(CONFIG_FILE)
        mysgen.base = {
            "src_path": Path("content"),
            "build_path": Path("output"),
        }
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
                if "data" in meta and meta["data"] is not False:
                    mock_datapage.assert_called_once()
                else:
                    mock_page.assert_called_once()
            else:
                if "image" in meta and meta["image"] is not False:
                    mock_imagepost.assert_called_once()
                elif "data" in meta and meta["data"] is not False:
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
                    {"pages": data, "articles": "posts_metadata", "all_posts": {}},
                    "template",
                )
            mock_sorted.assert_called_once()

    @patch("mysgen.mysgen.makedirs")
    @patch("mysgen.mysgen.boto3.client")
    def test_unit_copy_s3(self, mock_client, mock_makedirs):
        """
        Test the copy s3 method.
        """
        mysgen = MySGEN()
        mysgen.base["s3-bucket"] = "bucket"
        mock_client.return_value.list_objects.return_value = {
            "Contents": [
                {"Key": "1/2/3.file"},
                {"Key": "1/2/3.file"},
            ]
        }
        mysgen.copy_s3()

        mock_client.assert_called_once()
        mock_client.return_value.list_objects.assert_called_once()
        assert mock_makedirs.call_count == 2
        assert mock_client.return_value.download_file.call_count == 2

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
            "data": "false",
            "image": "false",
        }
        meta_return = mysgen._format_metadata(meta)

        meta_answer = {
            "date": datetime.strptime("2022-01-01", "%Y-%m-%d"),
            "tags": ["a", " b"],
            "category": "c",
            "test": "",
            "data": False,
            "image": False,
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
        mysgen.base = {"src_path": "tests/fixtures/"}
        mysgen.markdown = mock_markdown
        meta, content = mysgen._parse(Path("tests/fixtures/content/posts/post.md"))

        assert meta == mock_format_metadata.return_value
        assert content == mock_markdown.convert.return_value

    @patch("mysgen.mysgen.copy_tree")
    def test_unit_copy_assets(self, mock_copy_tree):
        """
        Unit test of MySGEN copy_assets method.

        Args:
            mock_copy_tree: mock of copy_tree
        """
        mysgen = MySGEN("tests/fixtures/test_config.json")
        mysgen.set_base_config()
        mysgen.copy_assets()

        assert mock_copy_tree.call_count == 2


class TestUnitItem:
    """
    Unit tests of Item class.
    """

    def test_unit_item_init(self):
        """
        Unit test of Item init method.
        """
        item = Item({}, "content", Path("src"), Path("build"))

        assert item.meta == {}
        assert item.content == "content"
        assert item.src_path == Path("src")
        assert item.build_path == Path("build")
        assert item.from_path == Path()
        assert item.to_path == Path()

    @patch("builtins.open", mock_open(read_data=None))
    @patch("mysgen.mysgen.makedirs")
    def test_unit_item_abstract_process(self, mock_os_makedirs):
        """
        Unit test of Item abstract_process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        item = Item(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        item.abstract_process(mock_base, mock_template)

        mock_os_makedirs.assert_called_once()

    def test_unit_item_patch_content(self):
        """
        Unit test of Item _patch_content method.
        """
        item = Item({}, "patch_me", "src", "build")
        item._patch_content("patch", "PATCHED")

        assert item.content == "PATCHED_me"

    @patch("mysgen.mysgen.copy_tree")
    def test_unit_item_copy(self, mock_copy_tree):
        """
        Unit test of Item _copy method.

        Args:
            mock_copy_tree: mock of copy_tree
        """
        post = Item({}, "content", "src", "build")
        post.from_path = "from"
        post.to_path = "to"
        post.copy()

        mock_copy_tree.assert_called_once_with("from", "to")


class TestUnitPost:
    """
    Unit tests of Post class.
    """

    def test_unit_post_init(self):
        """
        Unit test of Post init method.
        """
        post = Post({}, "content", Path("src"), Path("build"))

        assert post.meta == {}
        assert post.content == "content"
        assert post.src_path == Path("src")
        assert post.build_path == Path("build")

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
    @patch("mysgen.mysgen.Item.abstract_process")
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
        meta = {"path": Path("posts/post")}
        post = ImagePost(meta, "content", Path("src"), Path("build"))

        assert post.meta == meta
        assert post.content == "content"
        assert post.src_path == Path("src")
        assert post.build_path == Path("build")
        assert post.from_path == Path("src/images/post")
        assert post.to_path == Path("build/posts/post/images")

    @pytest.mark.parametrize(
        "isfile, mangle_image_name", [(True, False), (False, False), (True, True)]
    )
    @patch("mysgen.mysgen.shutil.move")
    @patch("mysgen.mysgen.ImagePost._resize_image")
    @patch("mysgen.mysgen.isfile")
    @patch("mysgen.mysgen.Path.glob")
    @patch("mysgen.mysgen.Post.copy")
    @patch("mysgen.mysgen.Post.process")
    def test_unit_imagepost_process(
        self,
        mock_item_process,
        mock_post_copy,
        mock_glob,
        mock_isfile,
        mock_resize_image,
        mock_move,
        isfile,
        mangle_image_name,
    ):
        """
        Unit test of ImagePost process method.
        """
        mock_base = {"mangle_image_name": mangle_image_name, "thumbnail_size": 0}
        mock_template = MagicMock()
        post = ImagePost(
            {"path": Path("posts/post1.md")}, MagicMock(), MagicMock(), MagicMock()
        )
        mock_glob.return_value = (
            Path(g) for g in ["path/image2.jpg", "path/image1.jpg"]
        )
        mock_isfile.return_value = isfile
        post.process(mock_base, mock_template)

        assert post.meta["thumbnail_size"] == mock_base["thumbnail_size"]
        assert post.meta["thumbnails"] == []
        assert mock_isfile.call_count == 2
        mock_glob.assert_called_once()
        mock_post_copy.assert_called_once()

        if isfile:
            assert mock_resize_image.call_count == 2
            mock_item_process.assert_called_once_with(mock_base, mock_template)

            if mangle_image_name:
                assert post.meta["image_paths"] == [
                    "0-"
                    + hashlib.sha256(bytearray("image1", "utf-8")).hexdigest()[:7]
                    + ".jpg",
                    "1-"
                    + hashlib.sha256(bytearray("image2", "utf-8")).hexdigest()[:7]
                    + ".jpg",
                ]
            else:
                assert post.meta["image_paths"] == ["image2.jpg", "image1.jpg"]
        else:
            assert mock_resize_image.call_count == 0
            assert post.meta["image_paths"] == []
            mock_item_process.call_count == 0

    @pytest.mark.parametrize(
        "path, image_size, thumbnail_size, thumbnails",
        [
            (
                Path("posts/path/images/image1.jpg"),
                (400, 400),
                [300, 300],
                Path("image1_small.jpg"),
            )
        ],
    )
    @patch("mysgen.mysgen.Image.open")
    def test_unit_imagepost_resize_image(
        self,
        mock_image,
        path,
        image_size,
        thumbnail_size,
        thumbnails,
    ):
        """
        Unit test of ImagePost _resize_image method.
        """
        meta = {"path": path, "thumbnails": [], "thumbnail_size": thumbnail_size}
        post = ImagePost(meta, MagicMock(), MagicMock(), MagicMock())
        mock_image.return_value.__enter__.return_value.size = image_size
        post._resize_image(path)

        assert post.meta["thumbnails"] == [thumbnails]


class TestUnitDataPost:
    """
    Unit tests of DataPost class.
    """

    def test_unit_datapost_init(self):
        """
        Unit test of DataPost init method.
        """
        meta = {"path": Path("posts/post")}
        post = DataPost(meta, "content", Path("src"), Path("build"))

        assert post.meta == meta
        assert post.content == "content"
        assert post.src_path == Path("src")
        assert post.build_path == Path("build")
        assert post.from_path == Path("src/data/post")
        assert post.to_path == Path("build/posts/post/data")

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
        mock_datapost_copy_data.assert_called_once()


class TestUnitPage:
    """
    Unit tests of Page class.
    """

    def test_unit_page_init(self):
        """
        Unit test of Page init method.
        """
        page = Page({}, "content", Path("src"), Path("build"))

        assert page.meta == {}
        assert page.content == "content"
        assert page.src_path == Path("src")
        assert page.build_path == Path("build")

    @pytest.mark.parametrize(
        "path, expected_path, expected_page_name",
        [
            (Path("pages/home"), Path(""), "home"),
            (Path("pages/archive"), Path("archive"), "archive"),
        ],
    )
    @patch("mysgen.mysgen.Item.abstract_process")
    @patch("mysgen.mysgen.Page._patch_content")
    def test_unit_page_process(
        self,
        mock_page_patch_content,
        mock_item_process,
        path,
        expected_path,
        expected_page_name,
    ):
        """
        Unit test of Page process method.
        """
        mock_date = datetime.now().strftime("%Y-%m-%d")
        mock_meta = {"path": path, "type": "index"}
        mock_base = {
            "home": "home",
            "build_date": mock_date,
            "build_date_template": "build_date",
        }
        mock_template = MagicMock()
        page = Page(mock_meta, MagicMock(), MagicMock(), MagicMock())
        page.process(mock_base, mock_template)

        assert page.meta["path"] == expected_path
        assert mock_base["page_name"] == expected_page_name
        mock_page_patch_content.assert_called_once_with(
            mock_base["build_date_template"], mock_date
        )
        mock_item_process.assert_called_once_with(
            mock_base, mock_template[page.meta["type"]]
        )


class TestUnitDataPage:
    """
    Unit tests of DataPage class.
    """

    def test_unit_datapage_init(self):
        """
        Unit test of DataPage init method.
        """
        meta = {"path": Path("pages/page")}
        page = DataPage(meta, "content", Path("src"), Path("build"))

        assert page.meta == meta
        assert page.content == "content"
        assert page.src_path == Path("src")
        assert page.build_path == Path("build")
        assert page.from_path == Path("src/data/page")
        assert page.to_path == Path("build/page/data")

    @patch("mysgen.mysgen.DataPage.copy")
    @patch("mysgen.mysgen.Page.process")
    def test_unit_datapage_process(self, mock_page_process, mock_datapage_copy_data):
        """
        Unit test of DataPage process method.
        """
        mock_base = MagicMock()
        mock_template = MagicMock()
        page = DataPage(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        page.process(mock_base, mock_template)

        mock_page_process.assert_called_once_with(mock_base, mock_template)
        mock_datapage_copy_data.assert_called_once()
