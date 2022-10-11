"""
mysgen, a simple static site generator in Python.
"""
from __future__ import annotations
import json
import glob
import markdown
from PIL import Image
from datetime import datetime
from os import listdir, makedirs
from os.path import join, isfile, split
from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError
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
        self.from_path = None
        self.to_path = None

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

    def copy(self) -> None:
        """
        Copy files from to.

        Args:
            item_type: item type to copy
        """
        try:
            copy_tree(self.from_path, self.to_path)
        except DistutilsFileError:
            raise DistutilsFileError(
                "File {from_path} not found.".format(from_path=self.from_path)
            )


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
        path = self.meta["path"].replace("posts/", "")
        self.from_path = join(self.src_path, "images", path)
        self.to_path = join(self.build_path, self.meta["path"], "images")

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        super().process(base, template)
        self.meta["small_image_height"] = base["small_image_height"]
        self.copy()
        self._resize_image()

    def _resize_image(self) -> None:
        """
        Resize post images for photo gallery.
        """
        self.meta["small_image"] = []
        for to_image in glob.glob(join(self.to_path)):
            with Image.open(to_image) as img:
                img.thumbnail(
                    self.meta["small_image_height"], resample=Image.Resampling.LANCZOS
                )

                path, file_id = split(to_image)
                im_name_split = file_id.split(".")
                thumbnail = im_name_split[0] + "_small." + im_name_split[1]
                self.meta["small_image"].append(thumbnail)
                img.save(join(path, thumbnail))


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
        path = self.meta["path"].replace("posts/", "")
        self.from_path = join(self.src_path, "data", path)
        self.to_path = join(self.build_path, self.meta["path"], "data")

    def process(self, base: dict, template: dict) -> None:
        """
        Process all published posts.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        super().process(base, template)
        self.copy()


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

    def process(self, base: dict, template: dict) -> None:
        """
        Process all pages.

        Args:
            base: base variables, copy
            template: available templates dictionary
        """
        page_path = self.meta["path"].replace("pages/", "")
        page_path = "" if page_path == base["home"] else page_path
        base["path"] = page_path
        base["page_name"] = self.meta["type"]

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

        template_path = self.base["template_path"]
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

        all_item_paths = glob.glob(join(self.base["content"], item_type, "*.md"))
        if not all_item_paths:
            raise FileNotFoundError(
                "Item {item_type} not found.".format(item_type=item_type)
            )

        site_path = self.base["site_path"]
        src_path = join(site_path, self.base["content"])
        build_path = join(site_path, self.base["output"])

        for item_path in all_item_paths:
            item = item_path.split("/")[-1]
            meta, content = self._parse(item_path)

            if item_type == "pages":
                self.pages[item] = Page(meta, content, src_path, build_path)
            elif "image" in meta:
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

        Returns:
            None

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
                posts_metadata, key=lambda x: x["date"], reverse=True
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
