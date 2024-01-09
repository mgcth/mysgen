<h1 align="center">mysgen</h1>

<p align="center">
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-test.yml">
        <img src="https://github.com/mgcth/mysgen/actions/workflows/github-action-test.yml/badge.svg?branch=main" alt="test" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-test.yml">
        <img src="https://img.shields.io/endpoint?logo=github&labelColor=%23333a41&logoColor=%23959da5&url=https://gist.githubusercontent.com/mgcth/3362178b6b392352d136d87d280e2dbe/raw/mysgen-coverage-badge.json" alt="coverage" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-lint.yml">
        <img src="https://github.com/mgcth/mysgen/actions/workflows/github-action-lint.yml/badge.svg?branch=main" alt="lint" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-type.yaml">
        <img src="https://github.com/mgcth/mysgen/actions/workflows/github-action-type.yaml/badge.svg?branch=main" alt="type" style="max-width: 100%;">
    </a>
</p>

<p align="center">
    <a href="https://www.python.org">
        <img src="https://img.shields.io/badge/Python-3.8%20|%203.9%20|%203.10%20|%203.11-blue" alt="Python 3.8 - 3.11" style="max-width: 100%;">
    </a>
    <a href="https://pytest.org">
        <img src="https://img.shields.io/badge/Testing_framework-pytest-a04000" alt="Testing framework: pytest" style="max-width: 100%;">
    </a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/badge/Linter-ruff-black" alt="Linter and formatter: ruff" style="max-width: 100%;">
    </a>
    <a href="http://mypy-lang.org">
        <img src="https://img.shields.io/badge/Type_checker-mypy-1674b1" alt="Type checker: mypy" style="max-width: 100%;">
    </a>
</p>

A very simple static site generator used for [mladen.gibanica.net](https://mladen.gibanica.net) built using Python and Jinja2.

The configuration file `config.json` should contain the following

```json
{
    "author": "Name",
    "sitename": "Site name",
    "siteurl": "https://address.com",
    "timezone": "Europe/Stockholm",
    "default_lang": "en-gb",
    "theme_path": "path_to_theme",
    "src_path": "path_to_content",
    "build_path": "path_to_build",
    "home": "home",
    "menuitems": {
        "home": "",
        "archive": "archive"
    },
    "post_url": "{{post_url}}",
    "build_date_template": "{{update_date}}",
    "thumbnail_size": [300, 300],
    "markdown_extensions": [
        "meta",
        "fenced_code",
        "mdx_math"
    ],
    "s3-bucket": "bucket"
}
```

Such a configuration assumes the following folder structure

```text
root/
├─ config.json
├─ path_to_content/
│  ├─ data/
│  ├─ images/
│  ├─ pages/
│  │  ├─ home.md
│  │  ├─ archive.md
│  ├─ posts/
├─ path_to_theme/
│  ├─ css/
│  ├─ js/
│  ├─ templates/
├─ path_to_build/
```
