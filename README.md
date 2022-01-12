# mysgen
A very simple static site generator used for [mladen.gibanica.net](https://mladen.gibanica.net) built using Python and Jinja2.

The configuration file should contain the following:
```
{
    "author": "Name",
    "sitename": "Site name",
    "siteurl": "https://address.com",
    "path": "content_path",
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