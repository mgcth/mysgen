# import libraries
import os, shutil
from datetime import datetime
from dataclasses import dataclass

import markdown
from jinja2 import Environment, PackageLoader

MYSGEN = 'mysgen'
CONTENT = 'content'
TEMPLATES = 'templates'
OUTPUT = 'output'
HOME = 'home'
INDEXHTML = '/index.html'
ARCHIVE = 'archive'
ALLTAGS = []
ALLCATEGORIES = []
ABOUT = 'about.md'
ABOUT_DATE = 'DATE_TIME'

# config
base_vars = {
	'AUTHOR': u'Mladen Gibanica',
	'SITENAME': u'mladen.gibanica.net',
	'SITEURL': 'https://mladen.gibanica.net',
	'PATH': 'content',
	'TIMEZONE': 'Europe/Stockholm',
	'DEFAULT_LANG': u'en-gb',
	'MENUITEMS': [[HOME, ''], [ARCHIVE, '/' + ARCHIVE]], #default menu
}

# define post and page structure as item
@dataclass
class Item:
	meta: dict
	content: str

# parse metadata
def parse_metadata(meta):
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

# parse posts and pages
def parse(what, path):
	md_pars = markdown.Markdown(extensions = ['meta', 'fenced_code', 'mdx_math'])

	for item in os.listdir(CONTENT + '/' + path):
		item_path = os.path.join(CONTENT + '/' + path, item)

		with open(item_path, 'r') as file:
			content = md_pars.convert(file.read())
			what[item] = Item(meta=parse_metadata(md_pars.Meta), content=content)
			what[item].meta['path'] = item

def build_menu(pages):
	for page in pages:
		name = page.split('.')[0]
		base_vars['MENUITEMS'].append([name, '/' + name])
		print(name)

def define_env(template):
	env = Environment(
		loader = PackageLoader(MYSGEN, TEMPLATES),
		trim_blocks = True,
		lstrip_blocks = True)

	for file in os.listdir(TEMPLATES):
		if os.path.isfile(os.path.join(TEMPLATES, file)):
			page_type = file.split('.')[0]
			template[page_type] = env.get_template(file)

# plugin, generate date in about page from compilation
def about_date(pages):
	for page in pages:
		if page == ABOUT:
			date = datetime.now().strftime('%Y-%m-%d')
			pages[page].content = pages[page].content.replace(ABOUT_DATE, date)

def main():
	# parse posts
	posts = {}
	parse(posts, 'posts')

	# find unique tags and categories
	base_vars['ALLTAGS'] = set(ALLTAGS)
	base_vars['ALLCATEGORIES'] = set(ALLCATEGORIES)

	# parse pages
	pages = {}
	parse(pages, 'pages')
	about_date(pages)

	# add pages to menu
	build_menu(pages)

	# create templates from html files in template folder
	template = {}
	define_env(template)

	# write posts
	for post in posts:
		if posts[post].meta['status'] == 'published':
			postpath = '/posts/' + post.split('.')[0]
			posts[post].meta['url'] = postpath

			os.makedirs(OUTPUT + postpath, exist_ok = True)
			with open(OUTPUT + postpath + INDEXHTML, 'w') as file:
				post_html = template['article'].render(base_vars, articles=posts[post],
					path=postpath, pages=pages, page=HOME, page_name='index')
				file.write(post_html)

			if posts[post].meta['image']:
				shutil.copyfile(CONTENT + '/images/' + posts[post].meta['image'],
					OUTPUT + postpath + '/' + posts[post].meta['image'])

	# transform more metadata
	posts_metadata = [post.meta for _, post in posts.items() if post.meta['status'] == 'published']#.sort(key = lambda x: x['date'], reverse = True)
	posts_metadata = sorted(posts_metadata, key = lambda x: x['date'], reverse = True)
	pages_metadata = [pages[page].meta for page in pages]

	# set and write fixed pages
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

if __name__ == '__main__':
    main()