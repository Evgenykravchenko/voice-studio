# Project website and search

**English** · [Русский](discovery.ru.md) · [Documentation](README.md)

The [public project website](https://evgenykravchenko.github.io/voice-studio/)
introduces the studio and lists its models in English and Russian. GitHub Pages
hosts static documentation; users install the actual application locally.
Pages is currently included for public repositories on GitHub Free, subject to
[GitHub's limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
No custom domain, paid server or always-on Mac is required for this site.

## What is configured

- Repository description, relevant topics and a website link for GitHub discovery.
- A README that names the supported tasks and model families.
- Four static pages: home and model catalog, each in English and Russian.
- Unique titles and descriptions, self-canonical URLs and reciprocal `hreflang` links.
- An XML sitemap, social sharing metadata, local screenshots and an icon.
- `WebPage` and `SoftwareSourceCode` JSON-LD describing the visible project and repository. This does not promise a Google rich result or a star rating.

The website works without JavaScript, downloads no models and uses no analytics
or advertising scripts. The deployment artifact includes only the validated
HTML, CSS, icon, two anonymous screenshots and sitemap.

## Update the site

Edit `site/content.json` for both languages. The catalog comes directly from
`src/voice_cloner/model-catalog.json`; do not maintain a second list of models.
Local builds use only Python's standard library:

```sh
./.venv/bin/python scripts/build-site.py
./.venv/bin/python scripts/check-site.py
```

Output goes to ignored `.runtime/site/`. The check rejects unexpected artifact
files, broken internal links, missing metadata, inconsistent language links and
catalog mismatches. The Pages workflow runs the same checks before publishing
changes to site source, model data or screenshots on `main`.

## Optional Google Search Console setup

1. In [Search Console](https://search.google.com/search-console/welcome), add a **URL-prefix** property: `https://evgenykravchenko.github.io/voice-studio/`.
2. Choose **HTML tag** verification. Set `googleSiteVerification` in `site/site.json` to the tag's `content` value, then publish the site. This is a public verification value, not a Google password or API key.
3. After the tag appears on the live homepage, click **Verify** in Search Console. Keep the tag in future deployments.
4. Submit `https://evgenykravchenko.github.io/voice-studio/sitemap.xml` in **Sitemaps**. Inspect the homepage and catalog if you want to request indexing.

Verification and sitemap submission require the owner's Google account; deploying
the website does not complete them. The site can still be discovered without
Search Console. [Google's verification guide](https://support.google.com/webmasters/answer/9008080?hl=en)
explains the ownership step.

There is no project-folder `robots.txt`: crawlers read that file at the hostname
root, outside `/voice-studio/`. The site emits indexable HTML and a linked sitemap.
Do not add a subfolder robots file and describe it as controlling Googlebot.

## Measure results honestly

GitHub's [repository search](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)
uses name, description and topics by default; README searches use `in:readme`.
Try `user:Evgenykravchenko topic:voice-cloning` or
`user:Evgenykravchenko Qwen3-TTS in:readme` to check relevant matches after indexing.

Use Search Console for Google impressions, clicks, queries and indexing status.
A `site:` query is only a rough check, not a complete index report. A sitemap
helps discovery but does not guarantee indexing, ranking, traffic or stars.
[Google describes these limits](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl).
Useful releases, audio demonstrations and genuine community feedback can provide
more evidence for prospective users. Submit announcements only with the owner's authorization.
