#!/usr/bin/env python3
"""Build the public project site using only the Python standard library.

Only explicit public assets are copied. No app builds, runtimes or user data
are included in the GitHub Pages artifact.
"""

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent, register_namespace


ROOT = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value), quote=True)


def build(output, base_url=None):
    settings = json.loads((ROOT / "site/site.json").read_text())
    content = json.loads((ROOT / "site/content.json").read_text())
    models = json.loads((ROOT / "src/voice_cloner/model-catalog.json").read_text())
    base = (base_url or settings["baseUrl"]).rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("The public base URL must be an absolute HTTPS URL without credentials or a query")
    repository = settings["repository"].rstrip("/")
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected a public GitHub repository URL")
    prefix = parsed.path.rstrip("/")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Write only known files; never delete the caller's output directory.
    asset_dir = output / "assets"
    asset_dir.mkdir(exist_ok=True)
    for name in ("site.css", "icon.svg"):
        shutil.copyfile(ROOT / "site/assets" / name, asset_dir / name)
    for lang in content:
        for name in ("studio",):
            shutil.copyfile(ROOT / f"docs/images/{lang}/{name}.png", asset_dir / f"{lang}-{name}.png")

    counts = {
        "total": len(models),
        "synthesis": sum(m["task"] == "synthesis" for m in models),
        "transcription": sum(m["task"] == "transcription" for m in models),
        "tools": sum(m["task"] not in ("synthesis", "transcription") for m in models),
    }

    def route(lang, page="home"):
        return ("ru/" if lang == "ru" else "") + ("models/" if page == "models" else "")

    def href(path=""):
        return prefix + "/" + path.lstrip("/")

    def doc(lang, name):
        return repository + "/blob/main/docs/" + name + (".ru.md" if lang == "ru" else ".md")

    def page_shell(lang, page, body):
        c = content[lang]
        other = "ru" if lang == "en" else "en"
        current = base + "/" + route(lang, page)
        title = c["catalogTitle"] if page == "models" else c["title"]
        description = c["catalogDescription"] if page == "models" else c["description"]
        alternates = "\n".join(
            f'<link rel="alternate" hreflang="{code}" href="{esc(base + "/" + route(code, page))}">'
            for code in ("en", "ru")
        )
        alternates += f'\n<link rel="alternate" hreflang="x-default" href="{esc(base + "/" + route("en", page))}">'
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "WebPage", "@id": current + "#page", "url": current,
                 "name": title, "description": description, "inLanguage": lang,
                 "mainEntity": {"@id": base + "/#source"}},
                {"@type": "SoftwareSourceCode", "@id": base + "/#source",
                 "name": "Voice Studio", "codeRepository": repository, "url": base + "/",
                 "license": repository + "/blob/main/LICENSE",
                 "programmingLanguage": ["TypeScript", "Java", "Python"],
                 "runtimePlatform": "macOS 14+ on Apple Silicon",
                 "description": content["en"]["description"]},
            ],
        }
        verification = settings.get("googleSiteVerification", "")
        verification_tag = f'<meta name="google-site-verification" content="{esc(verification)}">' if verification else ""
        return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="color-scheme" content="dark light">
<link rel="canonical" href="{esc(current)}">
{alternates}
{verification_tag}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Voice Studio">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(current)}">
<meta property="og:locale" content="{'ru_RU' if lang == 'ru' else 'en_US'}">
<meta property="og:locale:alternate" content="{'en_US' if lang == 'ru' else 'ru_RU'}">
<meta property="og:image" content="{esc(base)}/assets/{lang}-studio.png">
<meta property="og:image:width" content="1440">
<meta property="og:image:height" content="820">
<meta property="og:image:alt" content="{esc(c['studioAlt'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(base)}/assets/{lang}-studio.png">
<meta name="twitter:image:alt" content="{esc(c['studioAlt'])}">
<link rel="icon" type="image/svg+xml" href="{href('assets/icon.svg')}">
<link rel="stylesheet" href="{href('assets/site.css')}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace('<', chr(92) + 'u003c')}</script>
</head>
<body>
<a class="skip" href="#main">{esc(c['skip'])}</a>
<header class="site-header"><div class="container header-inner">
<a class="brand" href="{href(route(lang))}"><img src="{href('assets/icon.svg')}" width="28" height="28" alt="">Voice Studio</a>
<nav aria-label="{'Main navigation' if lang == 'en' else 'Основная навигация'}">
<a href="{href(route(lang, 'models'))}"{' aria-current="page"' if page == 'models' else ''}>{esc(c['navModels'])}</a>
<a href="{doc(lang, 'guide')}">{esc(c['navGuide'])}</a>
<a lang="{other}" hreflang="{other}" href="{href(route(other, page))}">{esc(c['otherLanguage'])}</a>
</nav></div></header>
<main id="main" class="container">{body}</main>
<footer class="container site-footer"><p>{esc(c['footerText'])}</p><nav aria-label="{'Project links' if lang == 'en' else 'Ссылки проекта'}">
<a href="{repository}">GitHub</a><a href="{repository}/discussions">{esc(c['feedback'])}</a>
<a href="{doc(lang, 'roadmap')}">{esc(c['roadmap'])}</a><a href="{doc(lang, 'status')}">{esc(c['status'])}</a>
<a href="{doc(lang, 'troubleshooting')}">{esc(c['navHelp'])}</a><a href="{href('sitemap.xml')}">Sitemap</a>
</nav></footer>
</body></html>'''

    for lang, c in content.items():
        rows = "".join(f'<div class="work-row"><h3>{esc(title)}</h3><p>{esc(text)}</p></div>' for title, text in c["work"])
        steps = "".join(
            f'<li><h3>{esc(title)}</h3><p>{esc(text)}</p>'
            + (f'<pre><code>./scripts/studio.sh</code></pre><p>{esc(c["openLocal"])}</p>' if i == 1 else "")
            + '</li>' for i, (title, text) in enumerate(c["steps"])
        )
        faq = "".join(f'<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>' for question, answer in c["faq"])
        body = f'''
<section class="hero" aria-labelledby="hero-title"><h1 id="hero-title">{esc(c['headline'])}</h1>
<p class="lead">{esc(c['intro'])}</p><div class="actions"><a class="button primary" href="#install">{esc(c['install'])}</a>
<a class="button" href="{repository}">{esc(c['github'])}</a></div><p class="note">{esc(c['platform'])}</p></section>
<figure class="studio"><img src="{href('assets/' + lang + '-studio.png')}" width="1440" height="820" fetchpriority="high" alt="{esc(c['studioAlt'])}"><figcaption>{esc(c['studioCaption'])}</figcaption></figure>
<section class="section" aria-labelledby="work-title"><h2 id="work-title">{esc(c['workTitle'])}</h2><div class="work-list">{rows}</div></section>
<section class="section model-summary" aria-labelledby="models-title"><h2 id="models-title">{esc(c['modelsTitle'])}</h2>
<p>{esc(c['modelsText'].format(**counts))}</p><a class="text-link" href="{href(route(lang, 'models'))}">{esc(c['modelsLink'])}</a><p class="note">{esc(c['modelsCaveat'])}</p></section>
<section id="install" class="section" aria-labelledby="install-title"><h2 id="install-title">{esc(c['installTitle'])}</h2>
<ol class="steps">{steps}</ol><a class="text-link" href="{doc(lang, 'setup')}">{esc(c['setupLink'])}</a></section>
<section class="section faq" aria-labelledby="faq-title"><h2 id="faq-title">{esc(c['faqTitle'])}</h2>{faq}</section>'''
        target = output / route(lang) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_shell(lang, "home", body), encoding="utf-8")

        tables = []
        for task in ("synthesis", "transcription", "audio"):
            selection = [m for m in models if (m["task"] == task if task != "audio" else m["task"] not in ("synthesis", "transcription"))]
            model_rows = []
            for m in selection:
                # Normalize punctuation in the published copy, without altering the app catalog.
                name = m["name"].replace(" — ", " ")
                license_name = m["license"].replace(" — ", "; ")
                modes = [c["modes"][f] for f in m["features"] if f in c["modes"]]
                languages = m.get("languages", [])
                short_languages = [c["languages"].get(code, code) for code in languages[:10]]
                if len(languages) > 10:
                    # Keep the useful Russian/English signal visible without listing hundreds of codes.
                    ordered = list(dict.fromkeys([code for code in ("ru", "en") if code in languages] + languages))
                    short_languages = [c["languages"].get(code, code) for code in ordered[:6]]
                    short_languages.append(c["otherLanguages"].format(count=len(languages) - 6))
                size = m.get("sizeBytes", sum(f.get("size", 0) for f in m.get("files", []))) / 1_000_000_000
                description = m.get("description", {}).get(lang, "")
                model_rows.append(f'''<tr id="{esc(m['id'])}" data-model-id="{esc(m['id'])}"><th scope="row"><a href="{esc(m['sourceUrl'])}">{esc(name)}</a><span class="format">{esc(m['format'])}</span><p>{esc(description)}</p></th>
<td>{esc('; '.join(modes))}</td><td>{esc('; '.join(short_languages))}</td><td>{size:.2f} GB<span class="license">{esc(license_name)}</span></td></tr>''')
            headings = "".join(f'<th scope="col">{esc(x)}</th>' for x in c["columns"])
            tables.append(f'<section class="catalog-section"><h2 id="{task}">{esc(c["tasks"][task])} ({len(selection)})</h2><div class="table-scroll" tabindex="0" role="region" aria-label="{esc(c["tasks"][task])}"><table><caption>{esc(c["tasks"][task])}</caption><thead><tr>{headings}</tr></thead><tbody>{"".join(model_rows)}</tbody></table></div></section>')
        jump = "".join(f'<a href="#{task}">{esc(label)}</a>' for task, label in c["tasks"].items())
        body = f'''<nav class="breadcrumb" aria-label="{'Breadcrumb' if lang == 'en' else 'Путь страницы'}"><a href="{href(route(lang))}">{esc(c['home'])}</a></nav>
<section class="catalog-intro"><h1>{esc(c['catalogHeadline'])}</h1><p class="lead">{esc(c['catalogIntro'])}</p><a class="text-link" href="{doc(lang, 'models')}">{esc(c['catalogGuide'])}</a><nav class="catalog-jump" aria-label="{'Model categories' if lang == 'en' else 'Разделы каталога'}">{jump}</nav><details><summary>{esc(c['catalogNotesTitle'])}</summary><p>{esc(c['catalogSource'])}</p><p>{esc(c['catalogNote'])}</p></details><p class="note">{esc(c['tableHint'])}</p></section>{''.join(tables)}'''
        target = output / route(lang, "models") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_shell(lang, "models", body), encoding="utf-8")

    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    register_namespace("", namespace)
    sitemap = Element(f"{{{namespace}}}urlset")
    for page in ("home", "models"):
        for lang in ("en", "ru"):
            node = SubElement(sitemap, f"{{{namespace}}}url")
            SubElement(node, f"{{{namespace}}}loc").text = base + "/" + route(lang, page)
    # HTML already declares reciprocal hreflang links. Keep the sitemap in the
    # base protocol so it also validates with the standalone official XSD.
    indent(sitemap, space="  ")
    ElementTree(sitemap).write(output / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (output / ".nojekyll").write_text("")
    (output / "404.html").write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Page not found | Voice Studio</title><link rel="stylesheet" href="{href("assets/site.css")}"><main class="container section"><h1>Page not found</h1><p><a href="{href()}">Voice Studio home</a></p><p><a lang="ru" href="{href("ru/")}">Главная на русском</a></p></main></html>', encoding="utf-8")
    print(json.dumps({"output": str(output), "baseUrl": base, "pages": 4, "models": len(models), "assets": 4}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/site")
    parser.add_argument("--base-url", help="Override the public URL, for example from configure-pages")
    args = parser.parse_args()
    build(args.output, args.base_url)
