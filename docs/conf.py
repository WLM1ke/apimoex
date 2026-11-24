import sys
import tomllib
from pathlib import Path

_package_name = "apimoex"

_route_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_route_path))
with (_route_path / "pyproject.toml").open("rb") as file:
    _version = tomllib.load(file)["project"]["version"]

version = ".".join(_version.split(".")[:2])
release = _version

extensions = ["sphinx.ext.autodoc", "sphinx.ext.githubpages"]
autodoc_member_order = "bysource"
toc_object_entries = False
templates_path = ["templates"]
html_static_path = []

source_suffix = ".rst"
master_doc = "index"
project = _package_name
copyright = "2019-2026, Mikhail Korotkov aka WLMike"
author = "Mikhail Korotkov aka WLMike"
language = "ru"
exclude_patterns = ["build"]
highlight_language = "default"
html_theme = "aiohttp_theme"

html_theme_options = {
    "logo": "",
    "description": "MOEX ISS API",
    "canonical_url": "https://wlm1ke.github.io/apimoex",
    "github_user": "WLM1ke",
    "github_repo": "apimoex",
    "github_button": False,
    "github_type": "",
    "github_banner": True,
    "travis_button": False,
    "badges": [
        {
            "image": "https://github.com/WLM1ke/apimoex/workflows/tests/badge.svg",
            "target": "https://github.com/WLM1ke/apimoex/actions",
            "height": "20",
            "alt": "Tests status",
        },
        {
            "image": "https://badge.fury.io/py/apimoex.svg",
            "target": "https://badge.fury.io/py/apimoex",
            "height": "20",
            "alt": "Latest PyPI package version",
        },
    ],
    "sidebar_collapse": False,
}

html_sidebars = {"**": ["about.html", "navigation.html"]}
