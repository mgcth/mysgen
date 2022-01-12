# mysgen
A very simple static site generator used for [mladen.gibanica.net](https://mladen.gibanica.net) built using Python, Markdown and Jinja2.

The configuration file should contain the following:
```
{
    "AUTHOR": "Name",
    "SITENAME": "Site name",
    "SITEURL": "https://address.com",
    "PATH": "content_path",
    "TIMEZONE": "Europe/Stockholm",
    "DEFAULT_LANG": "en-gb",
    "CONTENT": "content_path",
    "TEMPLATES": "templates_path",
    "OUTPUT": "output_path",
    "INDEXHTML": "index.html",
    "HOME": "home",
    "ARCHIVE": "archive",
    "MENUITEMS": {"home": "", "archive": "archive"},
    "POST_URL": "{{POSTURL}}",
    "SMALL_IMAGE_HEIGHT": 300
}
```