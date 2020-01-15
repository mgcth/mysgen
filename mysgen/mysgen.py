# import libraries
import os
import shutil
from datetime import datetime
from dataclasses import dataclass
import markdown
from jinja2 import Environment, PackageLoader

MYSGEN = "mysgen"
CONTENT = "content"
TEMPLATES = "templates"
OUTPUT = "output"
HOME = "home"
ARCHIVE = "archive"

# config
base_vars = {
	"AUTHOR": u'Mladen Gibanica',
	"SITENAME": u'mladen.gibanica.net',
	"SITEURL": 'https://mladen.gibanica.net',
	"PATH": 'content',
	"TIMEZONE": 'Europe/Stockholm',
	"DEFAULT_LANG": u'en-gb',
	"MENUITEMS": [[HOME, ''], [ARCHIVE, '/' + ARCHIVE]], #default menu
}

# define post and page structure as item
@dataclass
class Item:
	meta: dict
	content: str

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
	# read markdown metadata
	md_pars = markdown.Markdown(extensions=['meta'])

	for item in os.listdir(CONTENT + "/" + path):
		item_path = os.path.join(CONTENT + "/" + path, item)

		with open(item_path, 'r') as file:
			content = md_pars.convert(file.read())
			what[item] = Item(meta=parse_metadata(md_pars.Meta), content=content)
			what[item].meta["path"] = item

def build_menu(pages):
	for page in pages:
		name = page.split(".")[0]
		base_vars['MENUITEMS'].append([name, "/" + name])

def define_env(template):
	# jinja stuff
	env = Environment(loader=PackageLoader(MYSGEN, TEMPLATES), trim_blocks=True, lstrip_blocks=True)

	for file in os.listdir(TEMPLATES):
		if os.path.isfile(os.path.join(TEMPLATES, file)):
			page_type = file.split(".")[0]
			template[page_type] = env.get_template(file)

def main():
	# parse posts
	posts = {}
	parse(posts, 'posts')

	# parse pages
	pages = {}
	parse(pages, 'pages')

	# add pages to menu
	build_menu(pages)

	# create templates from html files in template folder
	template = {}
	define_env(template)

	# write posts
	for post in posts:
		if posts[post].meta["status"] == 'published':
			postpath = post.split(".")[0]
			posts[post].meta['url'] = postpath

			os.makedirs(OUTPUT + "/posts/" + postpath, exist_ok=True)
			with open(OUTPUT + "/posts/" + postpath + "/index.html", 'w') as file:
				post_html = template["article"].render(base_vars, articles=posts[post],
					path=postpath, tags=posts[post].meta['tags'], pages=pages, page=HOME, page_name="index")
				file.write(post_html)

			if posts[post].meta["image"]:
				shutil.copyfile('content/images/' + posts[post].meta["image"],
					OUTPUT + "/posts/" + postpath + '/' + posts[post].meta["image"])

	# transform more metadata
	posts_metadata = sorted([posts[post].meta for post in posts], key = lambda x: x['date'], reverse=True)
	posts_metadata = list(filter(lambda x: x["status"] == "published", posts_metadata))
	#post_metadata_projects = list(filter(lambda x: x["category"] == "Projects", posts_metadata))
	pages_metadata = [pages[page].meta for page in pages]

	# set and write fixed pages
	html_pages = {}
	base_vars["pages"] = pages
	for page, link in base_vars["MENUITEMS"]:
		pagetype = "page"
		base_vars["articles"] = posts_metadata

		if page == HOME:
			page = "index"
			pagetype = page
			base_vars["articles"] = posts[posts_metadata[0]["path"]]
		elif page == ARCHIVE:
			pagetype = page
		
		base_vars["page"] = page + ".md"
		base_vars["page_name"] = page
		html_pages[page] = template[pagetype].render(base_vars)

		file = OUTPUT + "/index.html" if not link else OUTPUT + link + "/index.html"
		os.makedirs(os.path.dirname(file), exist_ok=True)
		with open(file, 'w') as f:
			f.write(html_pages[page])

if __name__ == '__main__':
    main()