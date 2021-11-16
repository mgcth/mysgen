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

# set config path based on this directory
CONFIG_PATH = "../../site/config.json"


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
        self.posts = []
        self.pages = []
        self.date = datetime.now().strftime("%Y-%m-%d")

        self.set_base_config()
        self.define_environment()

    def set_base_config(self):
        """
        Set base configuration.
        """
        with open(CONFIG_PATH, "r") as file:
            self.base = json.loads(file.read())

        self.base["TAGS"] = {}
        self.base["CATEGORIES"] = {}

    def define_environment(self):
        """
        Define Jinja enviroment.
        """
        env = Environment(
            loader=FileSystemLoader(self.base.TEMPLATES),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        for file in os.listdir(self.base.TEMPLATES):
            if os.path.isfile(os.path.join(self.base.TEMPLATES, file)):
                page_type = file.split(".")[0]
                self.template[page_type] = env.get_template(file)

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
                        self.base.TAGS.extend(meta[key])

                    if key == "category":
                        self.base.CATEGORIES.append(meta[key])

        return meta

    def parse(self, what, path):
        """
        Parse both posts and pages.
        """
        md_pars = markdown.Markdown(extensions=["meta", "fenced_code", "mdx_math"])

        for item in os.listdir(os.path.join(self.base.CONTENT, path)):
            item_path = os.path.join(os.path.join(self.base.CONTENT, path), item)

            with open(item_path, "r") as file:
                content = md_pars.convert(file.read())

                content = content.replace(self.base.DATE, self.date)  # not efficient

                what[item] = Item(
                    meta=self.parse_metadata(md_pars.Meta), content=content
                )
                what[item].meta["path"] = item

    def process_posts(self):
        """
        Process all published posts.
        """
        for post in self.posts:
            if self.posts[post].meta["status"] == "published":
                postpath = "/posts/" + post.split(".")[0]
                self.posts[post].meta["url"] = postpath

                if self.posts[post].content.find(self.base.POST_URL) > 0:
                    self.posts[post].content = self.posts[post].content.replace(
                        self.base.POST_URL, self.base.SITEURL + postpath
                    )

                    post_data = self.posts[post].meta["data"].split(", ")
                    for pdata in post_data:
                        cpdata = self.base.CONTENT + "/data/" + pdata
                        if os.path.isfile(cpdata):
                            shutil.copyfil(
                                cpdata, self.base.OUTPUT + postpath + "/" + pdata
                            )
                        else:
                            shutil.copytree(cpdata, self.base.OUTPUT + postpath + "/")

                os.makedirs(self.base.OUTPUT + postpath, exist_ok=True)
                with open(
                    self.base.OUTPUT + postpath + self.base.INDEXHTML, "w"
                ) as file:
                    post_html = self.template["article"].render(
                        self.base,
                        articles=self.posts[post],
                        path=postpath,
                        pages=self.pages,
                        page=self.base.HOME,
                        page_name="index",
                    )
                    file.write(post_html)

                if self.posts[post].meta["image"]:
                    shutil.copyfile(
                        self.base.CONTENT + "/images/" + self.posts[post].meta["image"],
                        self.base.OUTPUT
                        + postpath
                        + "/"
                        + self.posts[post].meta["image"],
                    )

    def process_pages(self):
        posts_metadata = [
            post.meta
            for _, post in self.posts.items()
            if post.meta["status"] == "published"
        ]
        posts_metadata = sorted(posts_metadata, key=lambda x: x["date"], reverse=True)
        pages_metadata = [self.pages[page].meta for page in self.pages]

        html_pages = {}
        self.base["pages"] = self.pages
        for page, link in self.base.MENUITEMS:
            pagetype = "page"
            self.base["articles"] = posts_metadata

            if page == self.base.HOME:
                page = "index"
                pagetype = page
                BASE_VARS["articles"] = self.posts[posts_metadata[0]["path"]]
                BASE_VARS["path"] = BASE_VARS["articles"].meta["url"].split(".")[0]
            elif page == ARCHIVE:
                pagetype = page

            BASE_VARS["page"] = page + ".md"
            BASE_VARS["page_name"] = page
            html_pages[page] = template[pagetype].render(BASE_VARS)

            file = (
                self.base.OUTPUT + self.base.INDEXHTML
                if not link
                else self.base.OUTPUT + link + self.base.INDEXHTML
            )
            os.makedirs(os.path.dirname(file), exist_ok=True)
            with open(file, "w") as f:
                f.write(html_pages[page])

    def build_menu(self):
        """
        Build the main menu based on pages.
        """
        names = [x[0] for x in BASE_VARS["MENUITEMS"]]
        for page in self.pages:
            name = page.split(".")[0]

            if name not in names:
                BASE_VARS["MENUITEMS"].append([name, "/" + name])

    def build(self):
        """
        Build site.
        """
        self.parse(self.posts, "posts")
        self.parse(self.pages, "pages")
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
