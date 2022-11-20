# mysgen

<p style="text-align: center;">
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-actions-build.yml">
        <img src="https://github.com/mgcth/mysgen/actions/workflows/github-actions-build.yml/badge.svg?branch=main" alt="build" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-actions-build.yml">
        <img src="https://img.shields.io/endpoint?logo=github&labelColor=%23333a41&logoColor=%23959da5&url=https://gist.githubusercontent.com/mgcth/3362178b6b392352d136d87d280e2dbe/raw/mysgen-coverage-badge.json" alt="coverage" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-actions-lint.yml">
        <img src="https://github.com/mgcth/mysgen/actions/workflows/github-actions-lint.yml/badge.svg?branch=main" alt="lint" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-type.yaml">
        <img src="https://github.com/mgcth/mysgen/actions/workflows/github-action-type.yaml/badge.svg?branch=main" alt="type" style="max-width: 100%;">
    </a>
</p>

<p style="text-align: center;">
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-actions-lint.yml">
        <img src="https://img.shields.io/badge/Linter-flake8-red" alt="linter: flake8" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-lint.yaml">
        <img src="https://img.shields.io/badge/Security-bandit-yellow.svg" alt="security: bandit" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-actions-lint.yml">
        <img src="https://img.shields.io/badge/Code_style-black-black" alt="code style: black" style="max-width: 100%;">
    </a>
    <a href="https://github.com/mgcth/mysgen/actions/workflows/github-action-type.yaml">
        <img src="https://img.shields.io/badge/Type_checker-mypy-blue" alt="type checker: mypy" style="max-width: 100%;">
    </a>
</p>

A very simple static site generator used for [mladen.gibanica.net](https://mladen.gibanica.net) built using Python and Jinja2.

The configuration file should contain the following:

```json
{
    "author": "Name",
    "sitename": "Site name",
    "siteurl": "https://address.com",
    "timezone": "Europe/Stockholm",
    "default_lang": "en-gb",
    "theme_path": "path_to_theme",
    "src_path": "pth_to_content",
    "build_path": "path_to_build",
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
    ],
    "s3-bucket": "bucket"
}
```
