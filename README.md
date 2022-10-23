[![build](https://github.com/mgcth/mysgen/actions/workflows/github-actions-build.yml/badge.svg?branch=master)](https://github.com/mgcth/mysgen/actions/workflows/github-actions-build.yml)
[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/mgcth/3362178b6b392352d136d87d280e2dbe/raw/mysgen-coverage-badge.json)](https://github.com/mgcth/mysgen/actions/workflows/github-actions-build.yml)
[![lint](https://github.com/mgcth/mysgen/actions/workflows/github-actions-lint.yml/badge.svg?branch=master)](https://github.com/mgcth/mysgen/actions/workflows/github-actions-lint.yml)
![code style](https://img.shields.io/badge/code%20style-black-black)

# mysgen

A very simple static site generator used for [mladen.gibanica.net](https://mladen.gibanica.net) built using Python and Jinja2.

The configuration file should contain the following:
```json
{
    "author": "Name",
    "sitename": "Site name",
    "siteurl": "https://address.com",
    "timezone": "Europe/Stockholm",
    "default_lang": "en-gb",
    "template_path": "path_to_dir",
    "site_path": "path_to_dir",
    "content": "content_path",
    "templates": "templates_path",
    "output": "output_path",
    "home": "home",
    "menuitems": {
        "home": "",
        "archive": "archive"
    },
    "post_url": "{{post_url}}",
    "build_date": "{{update_date}}",
    "thumbnail_size": [300, 300],
    "markdown_extensions": [
        "meta",
        "fenced_code",
        "mdx_math"
    ]
}
```
