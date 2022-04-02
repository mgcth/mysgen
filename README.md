[![Unit tests](https://github.com/mgcth/mysgen/actions/workflows/github-actions-unit-tests-mgcth.yml/badge.svg?branch=master)](https://github.com/mgcth/mysgen/actions/workflows/github-actions-unit-tests-mgcth.yml)
# mysgen
A very simple static site generator used for [mladen.gibanica.net](https://mladen.gibanica.net) built using Python and Jinja2.

The configuration file should contain the following:
```
{
    "author": "Name",
    "sitename": "Site name",
    "siteurl": "https://address.com",
    "template_path": "path_to_dir",
    "site_path": "path_to_dir",
    "timezone": "Europe/Stockholm",
    "default_lang": "en-gb",
    "content": "content_path",
    "templates": "templates_path",
    "output": "output_path",
    "indexhtml": "index.html",
    "home": "home",
    "archive": "archive",
    "menuitems": {
        "home": "",
        "archive": "archive"
    },
    "posturl": "{{POSTURL}}",
    "small_image_height": 300
}
```