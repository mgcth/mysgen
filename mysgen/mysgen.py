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

    def __init__(self, meta: dict, content: str) -> None:
        """
        Initialise item object.

        Args:
            meta: meta dictionary
            content: content string
            settings: settings dictionary
        """
        self.meta = meta
        self.content = content

    def process(self, base: dict, template: Environment) -> None:
        """
        Process item.

        Args:
            base: base variables
            template: selected template
        """
        item_html = template.render(base)
        path = join(base["output"], base["path"])
        makedirs(path, exist_ok=True)
        with open(join(path, INDEX), "w") as file:
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

    def __init__(self, meta: defaultdict, content: str) -> None:
        """
        Initialise post object.

        Args:
            meta: meta dictionary
            content: content string
        """
        super().__init__(meta, content)

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        base["meta"] = self.meta
        base["article_content"] = self.content
        base["path"] = self.meta["path"]
        base["page"] = base["home"]
        base["page_name"] = INDEX.split(".")[0]

        self._patch_content(base["post_url"], join("/", self.meta["path"]))
        super().process(base, template["article"])

    def _copy(self, from_path, to_path) -> None:
        """
        Copy files from to.

        Args:
            from_path: from file path
            to_path: to file path
        """
        try:
            if isfile(from_path):
                shutil.copyfile(from_path, to_path)
            else:
                copy_tree(from_path, to_path)
        except KeyError:
            raise KeyError("File {from_path} not found.".format(from_path=from_path))


class ImagePost(Post):
    """
    Image post.
    """

    def __init__(self, meta: defaultdict, content: str) -> None:
        """
        Initialise post object.

        Args:
            meta: meta dictionary
            content: content string
        """
        super().__init__(meta, content)

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        super().process(base, template)
        self._copy_image(base)

    def _copy_image(self, base: dict) -> None:
        """
        Copy post's image to output from contents.

        Args:
            base: base variables

        Raises:
            FileNotFoundError
        """
        from_file = join(base["content"], "images", self.meta["image"])
        to_file = join(base["output"], base["path"], self.meta["image"])
        self._copy(from_file, to_file)
        self._resize_image(base, to_file)

    def _resize_image(self, base: dict, to_file: str) -> None:
        """
        Resize post's image for photo gallery.

        Args:
            base: base variables
            to_file: file to resize
        """
        try:
            img = Image.open(to_file)
        except FileNotFoundError:
            raise FileNotFoundError("File {0} not found".format(to_file))

        width, height = img.size
        small_height = base["small_image_height"]
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

    def __init__(self, meta: defaultdict, content: str) -> None:
        """
        Initialise post object.

        Args:
            meta: meta dictionary
            content: content string
        """
        super().__init__(meta, content)

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        super().process(base, template)
        self._copy_data(base)

    def _copy_data(self, base: dict) -> None:
        """
        Copy post's data to output from contents.

        Args:
            base: base variables

        Raises:
            KeyError
        """
        try:
            post_data = self.meta["data"].split(", ")
        except KeyError:
            raise KeyError("No data in post.")

        for data in post_data:
            from_path = join(base["content"], "data", data)
            to_path = join(base["output"], base["path"])
            to_path = join(to_path, data) if isfile(from_path) else to_path
            self._copy(from_path, to_path)


class Page(Item):
    """
    Page class.
    """

    def __init__(self, meta: defaultdict, content: str) -> None:
        """
        Initialise page object.

        Args:
            meta: meta dictionary
            content: content string
        """
        self.meta = meta
        self.content = content

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
        base["pages"] = pages
        base["page_name"] = self.meta["type"]
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
