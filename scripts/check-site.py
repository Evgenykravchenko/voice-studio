#!/usr/bin/env python3
"""Validate the public site's links, translations, metadata and artifact boundary."""

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.meta = {}
        self.links = []
        self.resources = []
        self.ids = set()
        self.h1 = 0
        self.models = set()
        self.title = ""
        self.in_title = False
        self.in_json = False
        self.json_text = ""
        self.schema = []
        self.scripts = []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if "id" in a:
            assert a["id"] not in self.ids, "Duplicate ID: " + a["id"]
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1 += 1
        if tag == "meta":
            self.meta[a.get("name", a.get("property", ""))] = a.get("content", "")
        if tag == "link":
            self.links.append(a)
            if a.get("rel") in ("stylesheet", "icon"):
                self.resources.append(a["href"])
        if tag == "a" and "href" in a:
            self.resources.append(a["href"])
        if tag == "img":
            assert "alt" in a, "Image is missing alt text"
            assert a.get("width") and a.get("height"), "Image dimensions are missing"
            self.resources.append(a["src"])
        if tag == "tr" and "data-model-id" in a:
            self.models.add(a["data-model-id"])
        if tag == "script":
            self.scripts.append(a)
            self.in_json = a.get("type") == "application/ld+json"
            self.json_text = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_json:
            self.schema.append(json.loads(self.json_text))
            self.in_json = False

    def handle_data(self, text):
        if self.in_title:
            self.title += text
        if self.in_json:
            self.json_text += text


def check(output, base_url=None):
    output = Path(output).resolve()
    settings = json.loads((ROOT / "site/site.json").read_text())
    base = (base_url or settings["baseUrl"]).rstrip("/")
    base_parts = urlsplit(base)
    prefix = base_parts.path.rstrip("/")
    routes = {"": ("en", ""), "ru/": ("ru", ""), "models/": ("en", "models/"), "ru/models/": ("ru", "models/")}
    models = {m["id"] for m in json.loads((ROOT / "src/voice_cloner/model-catalog.json").read_text())}
    pages = {route: Page((output / route / "index.html").read_text()) for route in routes}
    titles, descriptions = set(), set()
    links_checked = 0
    for route, p in pages.items():
        lang, kind = routes[route]
        assert p.lang == lang and p.h1 == 1, route
        assert p.title and p.title not in titles, route
        titles.add(p.title)
        assert p.meta["description"] and p.meta["description"] not in descriptions, route
        descriptions.add(p.meta["description"])
        assert "noindex" not in p.meta.get("robots", ""), route
        canonical = [x["href"] for x in p.links if x.get("rel") == "canonical"]
        assert canonical == [base + "/" + route], route
        alternates = {x["hreflang"]: x["href"] for x in p.links if x.get("rel") == "alternate"}
        assert alternates == {"en": base + "/" + kind, "ru": base + "/ru/" + kind, "x-default": base + "/" + kind}, route
        assert p.meta["og:url"] == canonical[0]
        assert p.meta["og:title"] == p.title
        assert p.meta["og:description"] == p.meta["description"]
        assert p.meta["twitter:card"] == "summary_large_image"
        assert len(p.scripts) == 1 and p.scripts[0]["type"] == "application/ld+json", "The site must work without JavaScript"
        assert len(p.schema) == 1
        graph = p.schema[0]["@graph"]
        assert graph[0]["inLanguage"] == lang and graph[0]["url"] == canonical[0]
        assert graph[1]["@type"] == "SoftwareSourceCode"
        assert graph[1]["codeRepository"] == settings["repository"]
        assert not any(key in graph[1] for key in ("offers", "review", "aggregateRating"))
        assert p.models == (models if kind else set()), route
        for address in p.resources + [p.meta["og:image"], p.meta["twitter:image"]]:
            url = urlsplit(address)
            if url.scheme and (url.scheme, url.netloc) != (base_parts.scheme, base_parts.netloc):
                assert url.scheme == "https", address
                continue
            if url.path:
                path = unquote(url.path)
                if path.startswith("/"):
                    assert path.startswith(prefix + "/"), address
                    relative = path[len(prefix) + 1:]
                else:
                    relative = route + path
                dest = (output / relative).resolve()
                assert dest.is_relative_to(output), address
                if dest.is_dir():
                    dest /= "index.html"
            else:
                dest = output / route / "index.html"
            assert dest.is_file(), (route, address)
            if url.fragment and dest.suffix == ".html":
                assert unquote(url.fragment) in Page(dest.read_text()).ids, (route, address)
            links_checked += 1
    sitemap = ET.parse(output / "sitemap.xml").getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
    urls = sitemap.findall("s:url", ns)
    assert {node.find("s:loc", ns).text for node in urls} == {base + "/" + route for route in routes}
    for node in urls:
        p = pages[node.find("s:loc", ns).text[len(base) + 1:]]
        assert {x.get("hreflang"): x.get("href") for x in node.findall("x:link", ns)} == {x["hreflang"]: x["href"] for x in p.links if x.get("rel") == "alternate"}
    expected = {route + "index.html" for route in routes} | {"404.html", "sitemap.xml", ".nojekyll", "assets/site.css", "assets/icon.svg", "assets/en-studio.png", "assets/ru-studio.png"}
    files = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    assert files == expected, {"unexpected": sorted(files - expected), "missing": sorted(expected - files)}
    assert not any(p.is_symlink() for p in output.rglob("*")), "No symlinks may enter the artifact"
    assert "noindex" in Page((output / "404.html").read_text()).meta["robots"]
    print(json.dumps({"status": "passed", "pages": len(pages), "modelEntriesPerLanguage": len(models), "localLinksAndAssets": links_checked, "artifactFiles": len(files), "bytes": sum((output / f).stat().st_size for f in files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/site")
    parser.add_argument("--base-url")
    args = parser.parse_args()
    check(args.output, args.base_url)
