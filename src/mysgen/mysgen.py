"""mysgen, a simple static site generator in Python."""
from __future__ import annotations
import os
import json
import glob
import boto3
import markdown
from PIL import Image
from typing import Any
from datetime import datetime
from os import scandir, makedirs
from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError
from os.path import join, isfile, split, relpath
from collections import defaultdict, OrderedDict
from jinja2 import Environment, FileSystemLoader, Template


# constants
CONFIG_FILE = "config.json"
TEMPLATES = "templates"
INDEX = "index.html"
TODAY = datetime.now()


class Item:
    """Item base class."""

    def __init__(
        self, meta: defaultdict[str, Any], content: str, src_path: str, build_path: str
    ) -> None:
        """
        Initialise item object.

        Args:
            meta: meta dictionary
            content: content string
            src_path: src path of item
            build_path: build path of item
        """
        self.meta = meta
        self.content = content
        self.src_path = src_path
        self.build_path = build_path
        self.from_path: str = ""
        self.to_path: str = ""

    def abstract_process(
        self,
        base: dict[str, Any],
        template: Template,
    ) -> None:
        """
        Process item.

        Args:
            base: base variables
            template: selected template
        """
        item_html = template.render(base)
        path = join(self.build_path, self.meta["path"])
        html_file = join(path, INDEX)

        makedirs(path, exist_ok=True)
        with open(html_file, "w") as file:
            file.write(item_html)

    def _patch_content(self, pattern: str, patch: str) -> None:
        """
        Patch markdown posts contain tags that need replacing.

        Args:
            pattern: pattern to search for
            patch: patch to apply in place of pattern
        """
        self.content = self.content.replace(pattern, patch)

    def copy(self) -> None:
        """Copy files from to."""
        try:
            copy_tree(self.from_path, self.to_path)
        except DistutilsFileError:
            raise DistutilsFileError(
                "File {from_path} not found.".format(from_path=self.from_path)
            )


class Post(Item):
    """Post class."""

    def __init__(
        self, meta: defaultdict[str, Any], content: str, src_path: str, build_path: str
    ) -> None:
        """
        Initialise post object.

        Args:
            meta: meta dictionary
            content: content string
            src_path: src path of item
            build_path: build path of item
        """
        super().__init__(meta, content, src_path, build_path)

    def process(
        self,
        base: dict[str, Any],
        template: dict[str, Template],
    ) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        base["meta"] = self.meta
        self._patch_content(base["post_url"], join("/", self.meta["path"]))
        base["article_content"] = self.content
        base["page"] = base["home"]
        base["page_name"] = INDEX.split(".")[0]

        super().abstract_process(base, template["article"])


class ImagePost(Post):
    """Image post."""

    def __init__(
        self, meta: defaultdict[str, Any], content: str, src_path: str, build_path: str
    ) -> None:
        """
        Initialise post object.

        Args:
            meta: meta dictionary
            content: content string
            src_path: src path of item
            build_path: build path of item
        """
        super().__init__(meta, content, src_path, build_path)
        path = self.meta["path"].replace("posts/", "")
        self.from_path = join(self.src_path, "images", path)
        self.to_path = join(self.build_path, self.meta["path"], "images")

    def process(
        self,
        base: dict[str, Any],
        template: dict[str, Template],
    ) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        self.copy()
        self.meta["thumbnail_size"] = base["thumbnail_size"]
        self.meta["thumbnails"] = []
        self.meta["image_paths"] = []
        for to_image in glob.glob(join(self.to_path, "*.*")):
            if not isfile(to_image):
                continue

            self.meta["image_paths"].append(split(to_image)[-1])
            self._resize_image(to_image)

        super().process(base, template)

    def _resize_image(self, image: str) -> None:
        """
        Resize post images for photo gallery.

        Args:
            image: image path
        """
        with Image.open(image) as img:
            if max(img.size) > min(self.meta["thumbnail_size"]):
                img.thumbnail(
                    self.meta["thumbnail_size"],
                    resample=Image.Resampling.LANCZOS,
                )

                path, file_id = split(image)
                im_name_split = file_id.split(".")
                image = im_name_split[0] + "_small." + im_name_split[1]
                img.save(join(path, image), quality=95)

            self.meta["thumbnails"].append(image)


class DataPost(Post):
    """Data post."""

    def __init__(
        self, meta: defaultdict[str, Any], content: str, src_path: str, build_path: str
    ) -> None:
        """
        Initialise post object.

        Args:
            meta: meta dictionary
            content: content string
            src_path: src path of item
            build_path: build path of item
        """
        super().__init__(meta, content, src_path, build_path)
        path = self.meta["path"].replace("posts/", "")
        self.from_path = join(self.src_path, "data", path)
        self.to_path = join(self.build_path, self.meta["path"], "data")

    def process(
        self,
        base: dict[str, Any],
        template: dict[str, Template],
    ) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        self.copy()
        super().process(base, template)


class Page(Item):
    """Page class."""

    def __init__(
        self, meta: defaultdict[str, Any], content: str, src_path: str, build_path: str
    ) -> None:
        """
        Initialise page object.

        Args:
            meta: meta dictionary
            content: content string
            src_path: src path of item
            build_path: build path of item
        """
        super().__init__(meta, content, src_path, build_path)

    def process(
        self,
        base: dict[str, Any],
        template: dict[str, Template],
    ) -> None:
        """
        Process all pages.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        base["page_name"] = self.meta["path"].split("/")[-1].split(".")[0]
        page_path = self.meta["path"].replace("pages/", "")
        page_path = "" if page_path == base["home"] else page_path
        self.meta["path"] = page_path

        self._patch_content(base["build_date_template"], str(base["build_date"]))
        super().abstract_process(base, template[self.meta["type"]])


class DataPage(Page):
    """Data page."""

    def __init__(
        self, meta: defaultdict[str, Any], content: str, src_path: str, build_path: str
    ) -> None:
        """
        Initialise page object.

        Args:
            meta: meta dictionary
            content: content string
            src_path: src path of item
            build_path: build path of item
        """
        super().__init__(meta, content, src_path, build_path)
        path = self.meta["path"].replace("pages/", "")
        self.from_path = join(self.src_path, "data", path)
        self.to_path = join(self.build_path, self.meta["path"], "data")

    def process(
        self,
        base: dict[str, Any],
        template: dict[str, Template],
    ) -> None:
        """
        Process all published pages.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        self.copy()
        super().process(base, template)


class MySGEN:
    """MySGEN class."""

    def __init__(self, config_file: str = CONFIG_FILE) -> None:
        """
        Initialise MySGEN object.

        Args:
            config_file: path to config file
        """
        self.config_file = config_file
        self.base: dict[str, Any] = {}
        self.template: dict[str, Template] = {}
        self.posts: dict[str, Any] = {}
        self.pages: dict[str, Any] = {}
        self.markdown: Any = None

    def build(self) -> None:
        """Build site."""
        self.set_base_config()

        if self.base["s3-bucket"]:
            self.copy_s3()

        self.define_environment()
        self.find_and_parse("posts")
        self.find_and_parse("pages")
        self.build_menu()
        self.process("posts")
        self.process("pages")

    def set_base_config(self) -> None:
        """Set base configuration."""
        with open(self.config_file, "r") as file:
            self.base = json.loads(file.read(), object_pairs_hook=OrderedDict)

        self.base["tags"] = []
        self.base["categories"] = []
        self.base["build_date"] = datetime(TODAY.year, TODAY.month, TODAY.day)

    def define_environment(self) -> None:
        """Define Jinja environment."""
        templates_path = join(self.base["theme_path"], TEMPLATES)
        env = Environment(  # nosec
            loader=FileSystemLoader(templates_path),  # nosec
            trim_blocks=True,  # nosec
            lstrip_blocks=True,  # nosec
        )  # nosec

        for file in scandir(templates_path):
            if file.is_file() and ".html" in file.name:
                page_type, _ = file.name.split(".")
                self.template[page_type] = env.get_template(file.name)

        self.markdown = markdown.Markdown(extensions=self.base["markdown_extensions"])

    def build_menu(self) -> None:
        """Build the main menu based on pages."""
        names = list(self.base["menuitems"].keys())
        for page in self.pages:
            name = page.split(".")[0]

            if name not in names:
                self.base["menuitems"][name] = name

        self.base["js_menu"] = list(self.base["menuitems"].keys())

    def find_and_parse(self, item_type: str) -> None:
        """
        Find and parse items.

        Args:
            item_type: type of item to process

        Raises:
            NotImplementedError
            FileNotFoundError
        """
        if item_type != "posts" and item_type != "pages":
            raise NotImplementedError(
                "Item type {item_type} not implemented.".format(item_type=item_type)
            )

        src_path = self.base["src_path"]
        build_path = self.base["build_path"]
        all_item_paths = glob.glob(join(src_path, item_type, "*.md"))
        if not all_item_paths:
            raise FileNotFoundError(
                "Item {item_type} not found.".format(item_type=item_type)
            )

        for item_path in all_item_paths:
            item = item_path.split("/")[-1]
            meta, content = self._parse(item_path)

            if item_type == "pages":
                if "data" in meta:
                    self.pages[item] = DataPage(meta, content, src_path, build_path)
                else:
                    self.pages[item] = Page(meta, content, src_path, build_path)
            else:
                if "image" in meta:
                    self.posts[item] = ImagePost(meta, content, src_path, build_path)
                elif "data" in meta:
                    self.posts[item] = DataPost(meta, content, src_path, build_path)
                else:
                    self.posts[item] = Post(meta, content, src_path, build_path)

    def process(self, item_type: str) -> None:
        """
        Process items based on type.

        Args:
            item_type: type of item to process

        Raises:
            NotImplementedError
        """
        base = self.base.copy()

        if item_type == "posts":
            data = self.posts
        elif item_type == "pages":
            data = self.pages
            posts_metadata = [
                p.meta for _, p in self.posts.items() if p.meta["status"] == "published"
            ]
            posts_metadata = sorted(
                posts_metadata, key=lambda x: x["date"], reverse=True  # type: ignore
            )
            base["pages"] = self.pages
            base["articles"] = posts_metadata
        else:
            raise NotImplementedError(
                "Item type {item_type} not implemented.".format(item_type=item_type)
            )

        for _, item_object in data.items():
            if item_object.meta["status"] == "published":
                item_object.process(base, self.template)

    def copy_s3(self) -> None:
        """Copy files from s3 in one go."""
        bucket = self.base["s3-bucket"]
        client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("S3_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET"),
            endpoint_url=os.getenv("S3_URL"),
        )
        files = client.list_objects(Bucket=bucket)

        for path in files["Contents"]:
            f = path["Key"]
            makedirs(join(*f.split("/")[:-1]), exist_ok=True)
            client.download_file(bucket, f, f)

    def _format_metadata(self, meta: defaultdict[str, Any]) -> defaultdict[str, Any]:
        """
        Format some metadata fields.

        Args:
            meta: dictionary of metadata

        Returns:
            meta: formatted metadata dictionary
        """
        for key, value in meta.items():
            if value == "":
                continue

            if key == "date":
                meta[key] = datetime.strptime(value.pop(), "%Y-%m-%d")
                continue

            meta[key] = value.pop()

            if key == "tags":
                meta[key] = meta[key].split(",")
                self.base["tags"].extend(meta[key])

            if key == "category":
                self.base["categories"].append(meta[key])

        return meta

    def _parse(self, item_path: str) -> tuple[defaultdict[str, Any], str]:
        """
        Parse items.

        Args:
            item_path: path of item to parse

        Returns:
            meta: metadata of item
            content: content of item as string
        """
        with open(item_path, "r") as file:
            content = self.markdown.convert(file.read())
            meta = self._format_metadata(defaultdict(lambda: "", self.markdown.Meta))
            meta["path"] = relpath(item_path, self.base["src_path"])
            meta["path"] = meta["path"].replace(".md", "")
            self.markdown.reset()

        return meta, content


def build() -> None:
    """Run MySGEN."""
    if __name__ == "__main__":
        mysgen = MySGEN()
        mysgen.build()


build()
