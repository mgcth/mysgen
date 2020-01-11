# import libraries
import os
import shutil
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

## jinja stuff
env = Environment(loader=PackageLoader('mysgen', 'templates'), trim_blocks=True, lstrip_blocks=True)

# create templates
template = {}
template['home'] = env.get_template('index.html')
template['post'] = env.get_template('article.html')
template['page'] = env.get_template('page.html')
template['archive'] = env.get_template('archive.html')

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

# add pages to menu
for page in pages:
	name = page.split(".")[0]
	base_vars['MENUITEMS'].append((name, '/' + name ))
	base_vars['pagesAndMenu'].append(name)

# transform some metadata
#tags = [posts[post].meta['tags'] for post in posts_metadata]

# write posts
for post in posts:
	if posts[post].meta["status"] == 'published':
		postpath = post.split(".")[0]
		posts[post].meta['url'] = postpath

		os.makedirs('output/posts/' + postpath, exist_ok=True)
		with open('output/posts/' + postpath + '/index.html', 'w') as file:
			post_html = template['post'].render(base_vars, article=posts[post],
				path=postpath, tags=posts[post].meta['tags'], pages=pages, page='home', page_name="index")
			file.write(post_html)

		if posts[post].meta["image"]:
			shutil.copyfile('content/images/' + posts[post].meta["image"],
				'output/posts/' + postpath + '/' + posts[post].meta["image"])

# transform more metadata
posts_metadata = sorted([posts[post].meta for post in posts], key = lambda i: i['date'], reverse=True)
post_metadata_projects = list(filter(lambda x: x["category"] == "Projects", posts_metadata))
pages_metadata = [pages[page].meta for page in pages]

# set pages
home_html = template['home'].render(base_vars, article=posts[posts_metadata[0]["path"]],
	path=posts_metadata[0]["path"].split(".")[0], tags=posts_metadata[0]["tags"], pages=pages, page='home.md', page_name="index")

about_html = template['page'].render(base_vars, articles=posts_metadata, pages=pages, page='about.md', page_name="about")
projects_html = template['page'].render(base_vars, articles=post_metadata_projects, pages=pages, page='projects.md', page_name="projects")
archive_html = template['archive'].render(base_vars, articles=posts_metadata, pages=pages, page_name="archive")

with open('output/index.html', 'w') as file:
	file.write(home_html)

os.makedirs('output/about', exist_ok=True)
with open('output/about/index.html', 'w') as file:
	file.write(about_html)

os.makedirs('output/archive', exist_ok=True)
with open('output/archive/index.html', 'w') as file:
	file.write(archive_html)

os.makedirs('output/projects', exist_ok=True)
with open('output/projects/index.html', 'w') as file:
	file.write(projects_html)
