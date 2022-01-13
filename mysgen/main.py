"""
mysgen, a simple static site generator in Python.
"""
import os
import shutil
from distutils.dir_util import copy_tree
import json
from datetime import datetime
from dataclasses import dataclass
import markdown
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from collections import OrderedDict


# set config file path
CONFIG_FILE = "../../site/config.json"


@dataclass
class Item:
    """
    Dataclass holding post and page meta and content.
    """

    meta: dict
    content: str


class MySGEN:
    """
    MySGEN class.
    """

    def __init__(self, config_file):
        """
        Initialise MySGEN object.
        """

        self.config_file = config_file
        self.template = {}
        self.posts = {}
        self.pages = {}
        self.date = datetime.now().strftime("%Y-%m-%d")

    def _set_base_config(self):
        """
        Set base configuration.
        """

        with open(self.config_file, "r") as file:
            self.base = json.loads(file.read(), object_pairs_hook=OrderedDict)

        site_path = self.base["site_path"]
        template_path = self.base["template_path"]

        self.base["content"] = os.path.join(site_path, self.base["content"])
        self.base["output"] = os.path.join(site_path, self.base["output"])
        self.base["templates"] = os.path.join(template_path, self.base["templates"])

        self.base["tags"] = []
        self.base["categories"] = []

    def _define_environment(self):
        """
        Define Jinja environment.
        """

        env = Environment(
            loader=FileSystemLoader(self.base["templates"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        for file in os.listdir(self.base["templates"]):
            if os.path.isfile(os.path.join(self.base["templates"], file)):
                page_type = file.split(".")[0]
                self.template[page_type] = env.get_template(file)

        self.md_pars = markdown.Markdown(extensions=["meta", "fenced_code", "mdx_math"])

    def _parse_metadata(self, meta):
        """
        Parse post and page metadata.
        """

        for key, value in meta.items():
            if value:
                if key == "date":
                    meta[key] = datetime.strptime(value.pop(), "%Y-%m-%d")
                else:
                    meta[key] = value.pop()

                    if key == "tags":
                        meta[key] = meta[key].split(",")
                        self.base["tags"].extend(meta[key])

                    if key == "category":
                        self.base["categories"].append(meta[key])

        return meta

    def _parse(self, what, item, path):
        """
        Parse both posts and pages.
        """

        item_path = os.path.join(os.path.join(self.base["content"], path), item)

        with open(item_path, "r") as file:
            content = self.md_pars.convert(file.read())
            what[item] = Item(
                meta=self._parse_metadata(self.md_pars.Meta), content=content
            )
            what[item].meta["path"] = item

    def _parse_posts(self, path="posts"):
        """
        Parse posts.
        """

        for item in os.listdir(os.path.join(self.base["content"], path)):
            self._parse(self.posts, item, path)

    def _parse_pages(self, path="pages"):
        """
        Parse pages.
        """

        for item in os.listdir(os.path.join(self.base["content"], path)):
            self._parse(self.pages, item, path)
            self.base["menuitems"][item.split(".")[0]] = item.split(".")[0]

        self.base["menuitems"]["home"] = ""  # hack for now
        self.base["js_menu"] = list(self.base["menuitems"].keys())

    def _process_posts(self):
        """
        Process all published posts.
        """

        for post in self.posts:
            if self.posts[post].meta["status"] == "published":
                postpath = os.path.join("posts", post.split(".")[0])
                self.posts[post].meta["url"] = postpath
                os.makedirs(os.path.join(self.base["output"], postpath), exist_ok=True)

                self._render_markdown(post, postpath)

                with open(
                    os.path.join(self.base["output"], postpath, self.base["indexhtml"]),
                    "w",
                ) as file:
                    post_html = self.template["article"].render(
                        self.base,
                        articles=self.posts[post],
                        path=postpath,
                        page=self.base["home"],
                        page_name=self.base["indexhtml"].split(".")[0],
                    )
                    file.write(post_html)

                self._copy_post_image(post, postpath)
                self._copy_post_data(post, postpath)

    def _process_pages(self):
        """
        Process all pages.
        """

        self.pages["home.md"].content = self.pages["home.md"].content.replace(
            "{{update_date}}", self.date
        )

        posts_metadata = [
            post.meta
            for _, post in self.posts.items()
            if post.meta["status"] == "published"
        ]
        posts_metadata = sorted(posts_metadata, key=lambda x: x["date"], reverse=True)

        html_pages = {}
        self.base["pages"] = self.pages
        for page, link in self.base["menuitems"].items():
            pagetype = "page"
            self.base["articles"] = posts_metadata

            if page == self.base["home"]:
                page = "index"
                pagetype = page
            elif page == self.base["archive"]:
                pagetype = page

            self.base["page"] = page  # + ".md"
            self.base["page_name"] = page
            html_pages[page] = self.template[pagetype].render(self.base)

            file = (
                os.path.join(self.base["output"], self.base["indexhtml"])
                if not link
                else os.path.join(self.base["output"], link, self.base["indexhtml"])
            )
            os.makedirs(os.path.dirname(file), exist_ok=True)
            with open(file, "w") as file:
                file.write(html_pages[page])

    def _build_menu(self):
        """
        Build the main menu based on pages.
        """

        names = list(self.base["menuitems"].keys())
        for page in self.pages:
            name = page.split(".")[0]

            if name not in names:
                self.base["menuitems"][name] = name

    def _copy_post_data(self, post, postpath):
        """
        Copy post's data to output from contents.
        """

        try:
            post_data = self.posts[post].meta["data"].split(", ")
        except KeyError:
            # don't print error for now
            post_data = None

        if post_data:
            for pdata in post_data:
                cpdata = os.path.join(self.base["content"], "data", pdata)
                if os.path.isfile(cpdata):
                    self._copy(
                        cpdata, os.path.join(self.base["output"], postpath, pdata)
                    )
                else:
                    copy_tree(cpdata, os.path.join(self.base["output"], postpath))

    def _resize_image(self, post, to_file):
        """
        Resize post's image for photo gallery.
        """

        img = Image.open(to_file)
        width, height = img.size
        small_height = self.base["small_image_height"]
        small_width = small_height * width // height
        img = img.resize((small_width, small_height), Image.ANTIALIAS)

        path, file = os.path.split(to_file)
        im_name_split = file.split(".")
        small_name = im_name_split[0] + "_small." + im_name_split[1]

        img.save(os.path.join(path, im_name_split[0] + "_small." + im_name_split[1]))
        self.posts[post].meta["small_image"] = small_name

    def _copy_post_image(self, post, postpath):
        """
        Copy post's image to output from contents.
        """

        if "image" in self.posts[post].meta:
            if self.posts[post].meta["image"]:
                from_file = os.path.join(
                    self.base["content"],
                    "images",
                    self.posts[post].meta["image"],
                )
                to_file = os.path.join(
                    self.base["output"],
                    postpath,
                    self.posts[post].meta["image"],
                )

                self._copy(
                    from_file,
                    to_file,
                )

                # resize images too
                self._resize_image(post, to_file)

    def _copy(self, from_file, to_file):
        """
        Copy files from to.
        """

        shutil.copyfile(
            from_file,
            to_file,
        )

    def _render_markdown(self, post, postpath):
        """
        Some markdown posts contain tags that need replacing.
        """

        if self.posts[post].content.find(self.base["posturl"]) > 0:
            self.posts[post].content = self.posts[post].content.replace(
                self.base["posturl"],
                os.path.join(self.base["siteurl"], postpath),
            )

    def build(self):
        """
        Build site.
        """

        self._set_base_config()
        self._define_environment()
        self._parse_posts()
        self._parse_pages()
        self._build_menu()
        self._process_posts()
        self._process_pages()


def main():
    """
    mysgen main function.
    """

    mysgen = MySGEN(CONFIG_FILE)
    mysgen.build()


def init():
    """
    Entry point to main.
    """

    if __name__ == "__main__":
        main()


init()
