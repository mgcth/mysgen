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
	"MENUITEMS": [('home', ''), ('archive', '/archive')], #default menu
	"CONTENT": "content/",
	"TEMPLATES": "templates/",
	"OUTPUT": "output",
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
	for item in os.listdir(base_vars["CONTENT"] + "/" + path):
		item_path = os.path.join(base_vars["CONTENT"] + "/" + path, item)

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
	base_vars['MENUITEMS'].append((name, "/" + name ))
	base_vars['pagesAndMenu'].append(name)

# create templates from html files in template folder
template = {}
for file in os.listdir(base_vars["TEMPLATES"]):
	if os.path.isfile(os.path.join(base_vars["TEMPLATES"], file)):
		page_type = file.split(".")[0]
		template[page_type] = env.get_template(file)

# transform some metadata
#tags = [posts[post].meta['tags'] for post in posts_metadata]

# write posts
for post in posts:
	if posts[post].meta["status"] == 'published':
		postpath = post.split(".")[0]
		posts[post].meta['url'] = postpath

		os.makedirs(base_vars["OUTPUT"] + "/posts/" + postpath, exist_ok=True)
		with open(base_vars["OUTPUT"] + "/posts/" + postpath + "/index.html", 'w') as file:
			post_html = template["article"].render(base_vars, article=posts[post],
				path=postpath, tags=posts[post].meta['tags'], pages=pages, page='home', page_name="index")
			file.write(post_html)

		if posts[post].meta["image"]:
			shutil.copyfile('content/images/' + posts[post].meta["image"],
				base_vars["OUTPUT"] + "/posts/" + postpath + '/' + posts[post].meta["image"])

# transform more metadata
posts_metadata = sorted([posts[post].meta for post in posts], key = lambda x: x['date'], reverse=True)
posts_metadata = list(filter(lambda x: x["status"] == "published", posts_metadata))
#post_metadata_projects = list(filter(lambda x: x["category"] == "Projects", posts_metadata))
pages_metadata = [pages[page].meta for page in pages]

common_data = {
	"pages": pages,
	"articles": posts_metadata,
}

# set and write pages, simplify this?
html = {}
html["home"] = template['index'].render(base_vars, article=posts[posts_metadata[0]["path"]],
	path=posts_metadata[0]["path"].split(".")[0], tags=posts_metadata[0]["tags"], pages=pages, page='home.md', page_name="index")
html["archive"]= template['archive'].render(base_vars, articles=posts_metadata, pages=pages, page_name="archive")
html["about"] = template['page'].render(base_vars, articles=posts_metadata, pages=pages, page='about.md', page_name="about")
html["projects"] = template['page'].render(base_vars, articles=posts_metadata, pages=pages, page='projects.md', page_name="projects")

for item in base_vars["MENUITEMS"]:
	folder = base_vars["OUTPUT"] + "/index.html" if not item[1] else base_vars["OUTPUT"] + item[1] + ".html"
	with open(folder, 'w') as file:
		file.write(html[item[0]])
