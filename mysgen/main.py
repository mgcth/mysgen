"""
mysgen, a simple static site generator.
"""
import os
import shutil
from datetime import datetime
from dataclasses import dataclass
import markdown
from jinja2 import Environment, FileSystemLoader


MYSGEN = 'mysgen'
CONTENT = '../../site/content'
TEMPLATES = '../../site/templates'
OUTPUT = '../../site/output'
INDEXHTML = '/index.html'
ALLTAGS = []
ALLCATEGORIES = []
HOME = 'home'
HOMEMD = 'home.md'
HOME_DATE = '{{DATE_TIME}}'
ARCHIVE = 'archive'
PROJECTS = 'projects'
PERSONAL = 'personal'
POST_URL = '{{POSTURL}}'


base_vars = {
    'AUTHOR': u'Mladen Gibanica',
    'SITENAME': u'mladen.gibanica.net',
    'SITEURL': 'https://mladen.gibanica.net',
    'PATH': 'content',
    'TIMEZONE': 'Europe/Stockholm',
    'DEFAULT_LANG': u'en-gb',
    'MENUITEMS': [
        [HOME, ''],
        [ARCHIVE, '/' + ARCHIVE],
        [PROJECTS, '/' + PROJECTS],
        [PERSONAL, '/' + PERSONAL]
    ]
}


@dataclass
class Item:
    """
    Dataclass holding post and page meta and content.
    """
    meta: dict
    content: str


def parse_metadata(meta):
    """
    Parse metadata.
    """
    for key, value in meta.items():
        if value:
            if key == 'date':
                meta[key] = datetime.strptime(value.pop(), '%Y-%m-%d')
            else:
                meta[key] = value.pop()

                if key == 'tags':
                    meta[key] = meta[key].split(',')
                    ALLTAGS.extend(meta[key])

                if key == 'category':
                    ALLCATEGORIES.append(meta[key])

    return meta


def parse(what, path):
    """
    Parse posts and pages.
    """
    md_pars = markdown.Markdown(extensions=['meta', 'fenced_code', 'mdx_math'])

    for item in os.listdir(os.path.join(CONTENT, path)):
        item_path = os.path.join(os.path.join(CONTENT, path), item)

        with open(item_path, 'r') as file:
            content = md_pars.convert(file.read())
            what[item] = Item(
                meta=parse_metadata(md_pars.Meta),
                content=content
            )
            what[item].meta['path'] = item


def build_menu(pages):
    """
    Build the main menu.
    """
    names = [x[0] for x in base_vars['MENUITEMS']]
    for page in pages:
        name = page.split('.')[0]

        if name not in names:
            base_vars['MENUITEMS'].append([name, '/' + name])


def define_env(template):
    """
    Define the Jinja enviroment.
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        trim_blocks=True,
        lstrip_blocks=True
        )

    for file in os.listdir(TEMPLATES):
        if os.path.isfile(os.path.join(TEMPLATES, file)):
            page_type = file.split('.')[0]
            template[page_type] = env.get_template(file)


def about_date(pages):
    """
    Special about page, plugin.
    """
    for page in pages:
        if page == HOMEMD:
            date = datetime.now().strftime('%Y-%m-%d')
            pages[page].content = pages[page].content.replace(HOME_DATE, date)


def process_posts(posts):
    """
    Process all published posts.
    """
    for post in posts:
        if posts[post].meta['status'] == 'published':
            postpath = '/posts/' + post.split('.')[0]
            posts[post].meta['url'] = postpath

            if posts[post].content.find(POST_URL) > 0:
                posts[post].content = posts[post].content.replace(
                    POST_URL, base_vars['SITEURL'] + postpath
                )

                post_data = posts[post].meta['data'].split(', ')
                for pdata in post_data:
                    cpdata = CONTENT + '/data/' + pdata
                    if os.path.isfile(cpdata):
                        shutil.copyfil(
                            cpdata,
                            OUTPUT + postpath + '/' + pdata
                        )
                    else:
                        shutil.copytree(
                            cpdata,
                            OUTPUT + postpath + '/'
                        )

            os.makedirs(OUTPUT + postpath, exist_ok=True)
            with open(OUTPUT + postpath + INDEXHTML, 'w') as file:
                post_html = template['article'].render(
                    base_vars,
                    articles=posts[post],
                    path=postpath,
                    pages=pages,
                    page=HOME,
                    page_name='index'
                )
                file.write(post_html)

            if posts[post].meta['image']:
                shutil.copyfile(
                    CONTENT + '/images/' + posts[post].meta['image'],
                    OUTPUT + postpath + '/' + posts[post].meta['image'])


def main():
    """
    mysgen main function.
    """
    posts = {}
    parse(posts, 'posts')

    base_vars['ALLTAGS'] = set(ALLTAGS)
    base_vars['ALLCATEGORIES'] = set(ALLCATEGORIES)

    pages = {}
    parse(pages, 'pages')
    about_date(pages)

    build_menu(pages)

    template = {}
    define_env(template)

    process_posts(posts)

    posts_metadata = [post.meta for _, post in posts.items() if post.meta['status'] == 'published']
    posts_metadata = sorted(posts_metadata, key=lambda x: x['date'], reverse=True)
    pages_metadata = [pages[page].meta for page in pages]

    html_pages = {}
    base_vars['pages'] = pages
    for page, link in base_vars['MENUITEMS']:
        pagetype = 'page'
        base_vars['articles'] = posts_metadata

        if page == HOME:
            page = 'index'
            pagetype = page
            base_vars['articles'] = posts[posts_metadata[0]['path']]
            base_vars['path'] = base_vars['articles'].meta['url'].split('.')[0]
        elif page == ARCHIVE:
            pagetype = page

        base_vars['page'] = page + '.md'
        base_vars['page_name'] = page
        html_pages[page] = template[pagetype].render(base_vars)

        file = OUTPUT + INDEXHTML if not link else OUTPUT + link + INDEXHTML
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w') as f:
            f.write(html_pages[page])


def init():
    """
    Entry point to main.
    """
    if __name__ == '__main__':
        main()


init()
