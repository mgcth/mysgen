"""
mysgen, a simple static site generator in Python.
"""
from __future__ import annotations
import json
import glob
import shutil
import markdown
from PIL import Image
from datetime import datetime
from os import listdir, makedirs
from os.path import join, isfile, split
from distutils.dir_util import copy_tree
from collections import defaultdict, OrderedDict
from jinja2 import Environment, FileSystemLoader


# constants
CONFIG_FILE = "config.json"
INDEX = "index.html"


class Item:
    """
    Item base class.
    """

    def __init__(
        self, meta: dict, content: str, src_path: str, build_path: str
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

    def process(self, base: dict, template: Environment) -> None:
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
        Some markdown posts contain tags that need replacing.

        Args:
            pattern: pattern to search for
            patch: patch to apply in place of pattern
        """
        self.content = self.content.replace(pattern, patch)


class Post(Item):
    """
    Post class.
    """

    def __init__(
        self, meta: defaultdict, content: str, src_path: str, build_path: str
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

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        base["meta"] = self.meta
        base["article_content"] = self.content
        base["page"] = base["home"]
        base["page_name"] = INDEX.split(".")[0]

        self._patch_content(base["post_url"], join("/", self.meta["path"]))
        super().process(base, template["article"])

    def _copy(self, item_type) -> None:
        """
        Copy files from to.

        Args:
            item_type: item type to copy
        """
        from_path = join(self.src_path, item_type, self.meta["path"])
        to_path = join(self.build_path, self.meta["path"], item_type)

        try:
            copy_tree(from_path, to_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                "File {from_path} not found.".format(from_path=from_path)
            )

    def _extract(self, item_type: str):
        """
        Extract data from meta and return from and to paths.

        Args:
            item_type: item to search for data

        Returns:
            list of data

        Raises:
            KeyError
        """
        try:
            post_data = [x.strip() for x in self.meta[item_type].split(",")]
        except KeyError:
            raise KeyError("No data in item.")

        for data in post_data:
            from_file = join(self.src_path, item_type, data)
            to_file = join(self.build_path, self.meta["path"], data)
            yield from_file, to_file


class ImagePost(Post):
    """
    Image post.
    """

    def __init__(
        self, meta: defaultdict, content: str, src_path: str, build_path: str
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

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        super().process(base, template)
        self.meta["small_image_height"] = base["small_image_height"]
        self._copy_image()
        self._resize_image()

    def _copy_image(self) -> None:
        """
        Copy post images to output from contents.
        """
        self._copy("image")

    def _resize_image(self, to_file: str) -> None:
        """
        Resize post images for photo gallery.

        Args:
            to_file: file to resize
        """
        for from_path, to_path in self._extract("image"):
            self._resize_image(to_path)
            with Image.open(to_file) as img:
                width, height = img.size
                small_height = self.meta["small_image_height"]
                small_width = small_height * width // height
                img = img.resize((small_width, small_height), Image.Resampling.LANCZOS)

                path, file_id = split(to_file)
                im_name_split = file_id.split(".")
                small_name = im_name_split[0] + "_small." + im_name_split[1]

                img.save(join(path, im_name_split[0] + "_small." + im_name_split[1]))
                self.meta["small_image"] = small_name


class DataPost(Post):
    """
    Data post.
    """

    def __init__(
        self, meta: defaultdict, content: str, src_path: str, build_path: str
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

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        super().process(base, template)
        self.copy_data()

    def copy_data(self) -> None:
        """
        Copy post's data to output from contents.
        """
        for from_path, to_path in self._extract("data"):
            self._copy(from_path, to_path)


class Page(Item):
    """
    Page class.
    """

    def __init__(
        self, meta: defaultdict, content: str, src_path: str, build_path: str
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
        self, base: dict, template: dict, pages: dict = {}, posts_metadata: dict = {}
    ) -> None:
        """
        Process all pages.

        Args:
            base: base variables, copy
            template: available templates dictionary
            pages: all pages
            posts_metadata: all published posts metadata
        """
        page_path = self.meta["path"].replace("pages/", "")
        page_path = "" if page_path == base["home"] else page_path
        base["path"] = page_path
        base["page_name"] = self.meta["type"]
        base["pages"] = pages
        base["articles"] = posts_metadata

        self._patch_content(base["build_date"], datetime.now().strftime("%Y-%m-%d"))
        super().process(base, template[self.meta["type"]])


class MySGEN:
    """
    MySGEN class.
    """

    def __init__(self, config_file: str = CONFIG_FILE) -> None:
        """
        Initialise MySGEN object.

        Args:
            config_file: path to config file
        """
        self.config_file = config_file
        self.base: dict = {}
        self.template: dict = {}
        self.posts: dict = {}
        self.pages: dict = {}
        self.markdown = None

    def build(self) -> None:
        """
        Build site.
        """
        self.set_base_config()
        self.define_environment()
        self.find_and_parse("posts")
        self.find_and_parse("pages")
        self.build_menu()
        self.process("posts")
        self.process("pages")

    def set_base_config(self) -> None:
        """
        Set base configuration.
        """
        with open(self.config_file, "r") as file:
            self.base = json.loads(file.read(), object_pairs_hook=OrderedDict)

        site_path = self.base["site_path"]
        template_path = self.base["template_path"]
        self.base["content"] = join(site_path, self.base["content"])
        self.base["output"] = join(site_path, self.base["output"])
        self.base["templates"] = join(template_path, self.base["templates"])
        self.base["tags"] = []
        self.base["categories"] = []

    def define_environment(self) -> None:
        """
        Define Jinja environment.
        """
        env = Environment(
            loader=FileSystemLoader(self.base["templates"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        for file in listdir(self.base["templates"]):
            if isfile(join(self.base["templates"], file)):
                page_type = file.split(".")[0]
                self.template[page_type] = env.get_template(file)

        self.markdown = markdown.Markdown(extensions=self.base["markdown_extensions"])

    def build_menu(self) -> None:
        """
        Build the main menu based on pages.
        """
        names = list(self.base["menuitems"].keys())
        for page in self.pages:
            name = page.split(".")[0]

            if name not in names:
                self.base["menuitems"][name] = name

        # self.base["menuitems"]["home"] = ""  # hack for now
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

        try:
            all_item_paths = glob.glob(join(self.base["content"], item_type, "*.md"))
        except FileNotFoundError:
            raise FileNotFoundError(
                "Item {item_type} not found.".format(item_type=item_type)
            )

        for item_path in all_item_paths:
            item = item_path.split("/")[-1]
            meta, content = self._parse(item_path)

            if item_type == "pages":
                self.pages[item] = Page(meta, content)
            elif meta["image"]:
                self.posts[item] = ImagePost(meta, content)
            elif meta["data"]:
                self.posts[item] = DataPost(meta, content)
            else:
                self.posts[item] = Post(meta, content)

    def process(self, item_type: str) -> None:
        """
        Process items based on type.

        Args:
            item_type: type of item to process

        Raises:
            NotImplementedError
        """
        if item_type == "posts":
            data = self.posts
        elif item_type == "pages":
            data = self.pages
        else:
            raise NotImplementedError(
                "Item type {item_type} not implemented.".format(item_type=item_type)
            )

        posts_metadata = [
            post.meta
            for _, post in self.posts.items()
            if post.meta["status"] == "published"
        ]
        posts_metadata = sorted(posts_metadata, key=lambda x: x["date"], reverse=True)

        for _, item_object in data.items():
            if item_object.meta["status"] != "published":
                continue

            if item_type == "posts":
                item_object.process(self.base.copy(), self.template)

            if item_type == "pages":
                item_object.process(
                    self.base.copy(), self.template, self.pages, posts_metadata
                )

    def _format_metadata(self, meta: defaultdict) -> defaultdict:
        """
        Custom formatting of some metadata fields.

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

    def _parse(self, item_path: str) -> tuple[defaultdict, str]:
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
            meta["path"] = item_path.replace(self.base["content"], "")
            meta["path"] = meta["path"].replace(".md", "")
            self.markdown.reset()

        return meta, content


def build():
    """
    Run MySGEN
    """
    if __name__ == "__main__":
        mysgen = MySGEN()
        mysgen.build()


build()
