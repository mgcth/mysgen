"""
mysgen, a simple static site generator in Python.
"""
import os
import shutil
import json
from datetime import datetime
from dataclasses import dataclass
import markdown
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from collections import OrderedDict


# set config path based on this directory
TEMPLATE_PATH = "../"
CONTENT_PATH = "../../site"
CONFIG_PATH = os.path.join(CONTENT_PATH, "config.json")


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

    def __init__(self):
        """
        Initialise MySGEN object.
        """

        self.template = {}
        self.posts = {}
        self.pages = {}
        self.date = datetime.now().strftime("%Y-%m-%d")

        self.set_base_config()
        self.define_environment()

    def set_base_config(self):
        """
        Set base configuration.
        """

        with open(CONFIG_PATH, "r") as file:
            self.base = json.loads(file.read(), object_pairs_hook=OrderedDict)

        self.base["CONTENT"] = os.path.join(CONTENT_PATH, self.base["CONTENT"])
        self.base["OUTPUT"] = os.path.join(CONTENT_PATH, self.base["OUTPUT"])
        self.base["TEMPLATES"] = os.path.join(TEMPLATE_PATH, self.base["TEMPLATES"])

        self.base["TAGS"] = []
        self.base["CATEGORIES"] = []

    def define_environment(self):
        """
        Define Jinja enviroment.
        """

        env = Environment(
            loader=FileSystemLoader(self.base["TEMPLATES"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        for file in os.listdir(self.base["TEMPLATES"]):
            if os.path.isfile(os.path.join(self.base["TEMPLATES"], file)):
                page_type = file.split(".")[0]
                self.template[page_type] = env.get_template(file)

        self.md_pars = markdown.Markdown(extensions=["meta", "fenced_code", "mdx_math"])

    def parse_metadata(self, meta):
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
                        self.base["TAGS"].extend(meta[key])

                    if key == "category":
                        self.base["CATEGORIES"].append(meta[key])

        return meta

    def parse(self, what, item, path):
        """
        Parse both posts and pages.
        """

        item_path = os.path.join(os.path.join(self.base["CONTENT"], path), item)

        with open(item_path, "r") as file:
            content = self.md_pars.convert(file.read())
            what[item] = Item(
                meta=self.parse_metadata(self.md_pars.Meta), content=content
            )
            what[item].meta["path"] = item

    def parse_posts(self, path="posts"):
        """
        Parse posts.
        """

        for item in os.listdir(os.path.join(self.base["CONTENT"], path)):
            self.parse(self.posts, item, path)

    def parse_pages(self, path="pages"):
        """
        Parse pages.
        """

        for item in os.listdir(os.path.join(self.base["CONTENT"], path)):
            self.parse(self.pages, item, path)
            self.base["MENUITEMS"][item.split(".")[0]] = item.split(".")[0]

        self.base["MENUITEMS"]["home"] = ""  # hack for now
        self.base["JS_MENU"] = list(self.base["MENUITEMS"].keys())

    def process_posts(self):
        """
        Process all published posts.
        """

        for post in self.posts:
            if self.posts[post].meta["status"] == "published":
                postpath = os.path.join("posts", post.split(".")[0])
                self.posts[post].meta["url"] = postpath

                if self.posts[post].content.find(self.base["POST_URL"]) > 0:
                    self.posts[post].content = self.posts[post].content.replace(
                        self.base["POST_URL"],
                        os.path.join(self.base["SITEURL"], postpath),
                    )

                    post_data = self.posts[post].meta["data"].split(", ")
                    for pdata in post_data:
                        cpdata = os.path.join(self.base["CONTENT"], "data", pdata)
                        if os.path.isfile(cpdata):
                            shutil.copyfil(
                                cpdata,
                                os.path.join(self.base["OUTPUT"], postpath, pdata),
                            )
                        else:
                            shutil.copytree(
                                cpdata, os.path.join(self.base["OUTPUT"], postpath)
                            )

                os.makedirs(os.path.join(self.base["OUTPUT"], postpath), exist_ok=True)
                with open(
                    os.path.join(self.base["OUTPUT"], postpath, self.base["INDEXHTML"]),
                    "w",
                ) as file:
                    post_html = self.template["article"].render(
                        self.base,
                        articles=self.posts[post],
                        path=postpath,
                        pages=self.pages,
                        page=self.base["HOME"],
                        page_name="index",
                    )
                    file.write(post_html)

                if "image" in self.posts[post].meta:
                    if self.posts[post].meta["image"]:
                        from_file = os.path.join(
                            self.base["CONTENT"],
                            "images",
                            self.posts[post].meta["image"],
                        )
                        to_file = os.path.join(
                            self.base["OUTPUT"],
                            postpath,
                            self.posts[post].meta["image"],
                        )

                        shutil.copyfile(
                            from_file,
                            to_file,
                        )

                    # resize images too
                    self.resize_images(post, to_file)

    def process_pages(self):
        """
        Process all pages.
        """

        self.pages["home.md"].content = self.pages["home.md"].content.replace(
            "{{UPDATE_DATE}}", self.date
        )

        posts_metadata = [
            post.meta
            for _, post in self.posts.items()
            if post.meta["status"] == "published"
        ]
        posts_metadata = sorted(posts_metadata, key=lambda x: x["date"], reverse=True)
        # pages_metadata = [self.pages[page].meta for page in self.pages]

        html_pages = {}
        self.base["pages"] = self.pages
        for page, link in self.base["MENUITEMS"].items():
            pagetype = "page"
            self.base["articles"] = posts_metadata

            if page == self.base["HOME"]:
                page = "index"
                pagetype = page
                #self.base["articles"] = self.posts[posts_metadata[0]["path"]]
                #self.base["path"] = self.base["articles"].meta["url"].split(".")[0]
            elif page == self.base["ARCHIVE"]:
                pagetype = page

            self.base["page"] = page  # + ".md"
            self.base["page_name"] = page
            html_pages[page] = self.template[pagetype].render(self.base)

            file = (
                os.path.join(self.base["OUTPUT"], self.base["INDEXHTML"])
                if not link
                else os.path.join(self.base["OUTPUT"], link, self.base["INDEXHTML"])
            )
            os.makedirs(os.path.dirname(file), exist_ok=True)
            with open(file, "w") as file:
                file.write(html_pages[page])

    def build_menu(self):
        """
        Build the main menu based on pages.
        """

        names = list(
            self.base["MENUITEMS"].keys()
        )  # [x[0] for x in self.base["MENUITEMS"]]
        for page in self.pages:
            name = page.split(".")[0]

            if name not in names:
                self.base["MENUITEMS"][name] = name

    def resize_images(self, post, to_file):
        img = Image.open(to_file)
        width, height = img.size
        small_height = self.base["SMALL_IMAGE_HEIGHT"]
        small_width = small_height * width // height
        img = img.resize((small_width, small_height), Image.ANTIALIAS)

        path, file = os.path.split(to_file)
        im_name_split = file.split(".")
        small_name = im_name_split[0] + "_small." + im_name_split[1]

        img.save(os.path.join(path, im_name_split[0] + "_small." + im_name_split[1]))
        self.posts[post].meta["small_image"] = small_name

    def build(self):
        """
        Build site.
        """

        self.parse_posts()
        self.parse_pages()
        self.build_menu()
        self.process_posts()
        self.process_pages()


def main():
    """
    mysgen main function.
    """

    mysgen = MySGEN()
    mysgen.build()


def init():
    """
    Entry point to main.
    """

    if __name__ == "__main__":
        main()


init()
