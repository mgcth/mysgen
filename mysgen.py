# import libraries
import os, shutil
from datetime import datetime
from dataclasses import dataclass
import markdown
from jinja2 import Environment, PackageLoader

## config
base_vars = {
	"AUTHOR": u'Mladen Gibanica',
	"SITENAME": u'mladen.gibanica.net',
	"SITEURL": 'https://mladen.gibanica.net',
	"PATH": 'content',
	"TIMEZONE": 'Europe/Stockholm',
	"DEFAULT_LANG": u'en-gb',

	"MENUITEMS": [('home', ''), ('archive', '/archive')],

	"DISPLAY_PAGES_ON_MENU": True,
	"pagesAndMenu": ["home", "archive"]
}

# define post and page structure as item
@dataclass
class Item:
	meta: dict
	content: str

# read markdown metadata
md_pars = markdown.Markdown(extensions=['meta'])

## some helper functions
def parse_metadata(meta):
	for key, value in meta.items():
		if len(value) == 1:
			if key != "tags":
				meta[key] = value[0]

			if key == 'date':
				meta[key] = datetime.strptime(meta[key], '%Y-%m-%d')

	return meta

## parse posts and pages
def parse(what, path):
	for item in os.listdir('content/' + path):
		item_path = os.path.join('content/' + path, item)

		with open(item_path, 'r') as file:
			content = md_pars.convert(file.read())
			what[item] = Item(meta=parse_metadata(md_pars.Meta), content=content)
			what[item].meta["path"] = item

# parse posts
posts = {}
parse(posts, 'posts')

# parse pages
pages = {}
parse(pages, 'pages')
for k in pages:
	name = k.split(".")[0]
	base_vars['MENUITEMS'].append((name, '/' + name ))
	base_vars['pagesAndMenu'].append(name)

## jinja
env = Environment(loader=PackageLoader('mysgen', 'templates'), trim_blocks=True, lstrip_blocks=True)
home_template = env.get_template('index.html')
post_template = env.get_template('article.html')
page_template = env.get_template('page.html')
archive_template = env.get_template('archive.html')

# transform some metadata
posts_metadata = [posts[post].meta for post in posts]
tags = [post['tags'] for post in posts_metadata]

# write posts
for post in posts:
	if posts[post].meta["status"] == 'published':
		postpath = post.split(".")[0]
		posts[post].meta['url'] = postpath + '/index.html'
		os.makedirs('output/posts/' + postpath, exist_ok=True)
		with open('output/posts/' + posts[post].meta['url'], 'w') as file:
			post_html = post_template.render(base_vars, article=posts[post], path=postpath, tags=tags, pages=pages, page='home', page_name="index")
			file.write(post_html)

		if posts[post].meta["image"]:
			shutil.copyfile('content/images/' + posts[post].meta["image"], 'output/posts/' + postpath + '/' + posts[post].meta["image"])

# transform more metadata
posts_metadata = sorted([posts[post].meta for post in posts], key = lambda i: i['date'], reverse=True)
pages_metadata = [pages[page].meta for page in pages]

home_html = home_template.render(base_vars, article=posts[posts_metadata[0]["path"]], path=posts_metadata[0]["path"].split(".")[0], tags=tags, pages=pages, page='home.md', page_name="index")
about_html = page_template.render(base_vars, pages=pages, page='about.md', page_name="about")
archive_html = archive_template.render(base_vars, articles=posts_metadata, pages=pages, page_name="archive")

# hardcode file output
with open('output/index.html', 'w') as file:
	file.write(home_html)

os.makedirs('output/about', exist_ok=True)
with open('output/about/index.html', 'w') as file:
	file.write(about_html)

os.makedirs('output/archive', exist_ok=True)
with open('output/archive/index.html', 'w') as file:
	file.write(archive_html)
