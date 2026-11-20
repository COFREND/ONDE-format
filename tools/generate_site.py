#!/usr/bin/env python3
#
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "pyyaml",
#   "jinja2",
#   "mkdocs-material",
# ]
# ///

"""
Build the multi-version ONDE documentation site, or stamp a pull request preview.

Published site layout (everything is static, so it can be served by GitHub Pages):

    <root>/index.html         redirects to latest/
    <root>/404.html           redirects old flat URLs to latest/, or lists the versions
    <root>/versions.json      list read by the version selector of the Material theme
    <root>/ONDE_fields.csv    copied from the latest release (also robots.txt)
    <root>/latest/            copy of the newest release
    <root>/v0.9.2/            one directory per release tag (v*) merged into main
    <root>/next_minor/        development versions, built from the remote branches
    <root>/next_major/
    <root>/pr-preview/pr-N/   pull request previews, published by a separate workflow

Contract with the other refs: each published ref is built with its own
tools/generate_docs.py, which must leave an MkDocs project in build/docs
(mkdocs.yml and docs/). Releases older than the generator are rendered as they
are, from their Markdown files. The generated project is then built a second
time with a small overlay configuration (mkdocs.site.yml) that adds the version
selector and, for everything except the latest release, a banner saying which
version is shown.

Usage, from the repository root:

    python tools/generate_site.py                    # all versions -> build/site
    python tools/generate_site.py --pr-preview 42    # working tree -> build/docs/site
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

import yaml

# Development branches that are published next to the releases, in this order.
DEV_BRANCHES = ['next_minor', 'next_major']

DEFAULT_REPO_URL = 'https://github.com/COFREND/ONDE-format'

RELEASE_TAG = re.compile(r'^v\d+(\.\d+)*$')

# Built for refs that predate tools/generate_docs.py: render the Markdown files of
# the tree as they are (README.md becomes the index page).
LEGACY_MKDOCS_YML = """\
site_name: ONDE Format Specification
use_directory_urls: false
docs_dir: tree
theme:
  name: material
markdown_extensions:
  - attr_list
  - md_in_html
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.escapeall:
      hardbreak: true
extra_javascript:
  - https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js
validation:
  links:
    absolute_links: relative_to_docs
"""

# Theme override. Only written for builds that show a banner, because the theme
# renders the banner element as soon as the announce block is not empty. All values
# come from extra.onde_site in mkdocs.site.yml and are escaped here.
BANNER_TEMPLATE = """\
{% extends "base.html" %}

{% block extrahead %}
{{ super() }}
{%- set onde = config.extra.onde_site %}
{%- set colors = {
  "outdated": ["#ffff99", "#000000de"],
  "development": ["#ffb300", "#000000de"],
  "pr_preview": ["#d84315", "#ffffff"]
}[onde.kind] %}
<style>
  .md-banner {
    background-color: {{ colors[0] }};
    color: {{ colors[1] }};
  }
  .md-banner .md-banner__inner a,
  .md-banner .md-banner__inner a:hover {
    color: inherit;
    text-decoration: underline;
    font-weight: 700;
  }
  .md-banner .md-banner__inner code {
    color: inherit;
    background-color: transparent;
    padding: 0;
  }
</style>
{% endblock %}

{% block announce %}
{%- set onde = config.extra.onde_site -%}
{%- if onde.kind == "outdated" -%}
You are viewing version <strong>{{ onde.name | e }}</strong> of the ONDE specification.
The latest released version is <a href="{{ base_url }}/../latest/index.html">{{ onde.latest | e }}</a>.
{%- elif onde.kind == "development" -%}
<strong>Development version.</strong> You are viewing the <code>{{ onde.name | e }}</code> branch, a working draft of a future version of the ONDE specification. It has not been approved and may change.
{%- if onde.latest %}
The latest released version is <a href="{{ base_url }}/../latest/index.html">{{ onde.latest | e }}</a>.
{%- endif -%}
{%- elif onde.kind == "pr_preview" -%}
<strong>Pull request preview.</strong> This page previews the changes proposed in <a href="{{ onde.pr_url | e }}">pull request #{{ onde.number | e }}</a>. It is under development and is not part of the approved ONDE specification.
<a href="{{ base_url }}/../../index.html">View the published specification</a>.
{%- endif -%}
{% endblock %}
"""

REDIRECT_PAGE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ONDE Format Specification</title>
<noscript><meta http-equiv="refresh" content="0; url={target_attr}"></noscript>
<script>
window.location.replace({target_js} + window.location.search + window.location.hash);
</script>
</head>
<body>
<p>Redirecting to <a href="{target_attr}">the ONDE Format Specification</a>.</p>
</body>
</html>
"""

# GitHub Pages serves this page at the requested URL, so it cannot use relative
# links: the script finds the site root by looking for versions.json upwards.
NOT_FOUND_PAGE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found - ONDE Format Specification</title>
<style>
  body { font-family: system-ui, sans-serif; line-height: 1.5; max-width: 40rem; margin: 3rem auto; padding: 0 1rem; color: #222; background: #fff; }
  a { color: #1a5fb4; }
  @media (prefers-color-scheme: dark) {
    body { color: #ddd; background: #1e1e1e; }
    a { color: #8ab4f8; }
  }
</style>
</head>
<body>
<h1>Page not found</h1>
<p>The requested page does not exist in the ONDE Format Specification.</p>
<div id="versions"></div>
<script>
(async function () {
  // Walk up from the requested directory until a versions.json is found.
  async function findSite() {
    var dir = location.pathname.replace(/[^\\/]*$/, '');
    while (true) {
      try {
        var response = await fetch(dir + 'versions.json');
        if (response.ok) {
          var versions = await response.json();
          if (Array.isArray(versions)) return { root: dir, versions: versions };
        }
      } catch (e) { /* not found here, try the parent */ }
      var parent = dir.replace(/[^\\/]+\\/$/, '');
      if (dir === '/' || parent === dir) return null;
      dir = parent;
    }
  }

  var site = await findSite();
  if (!site) return;

  var known = ['pr-preview'];
  site.versions.forEach(function (v) {
    known.push(v.version);
    (v.aliases || []).forEach(function (a) { known.push(a); });
  });
  var rest = location.pathname.substring(site.root.length);
  var first = rest.split('/')[0];

  // Links from before the site had versions point into the root: send them to the
  // latest release. A miss there is not redirected again because "latest" is known.
  if (first && known.indexOf(first) === -1 && known.indexOf('latest') !== -1) {
    location.replace(site.root + 'latest/' + rest + location.search + location.hash);
    return;
  }

  var container = document.getElementById('versions');
  var intro = document.createElement('p');
  intro.textContent = 'Available versions:';
  var list = document.createElement('ul');
  site.versions.forEach(function (v) {
    var link = document.createElement('a');
    link.href = site.root + encodeURIComponent(v.version) + '/index.html';
    link.textContent = v.title || v.version;
    var item = document.createElement('li');
    item.appendChild(link);
    list.appendChild(item);
  });
  container.appendChild(intro);
  container.appendChild(list);
})();
</script>
</body>
</html>
"""


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True,
                          text=True).stdout


def ref_exists(ref):
    result = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', ref + '^{commit}'],
                            capture_output=True)
    return result.returncode == 0


def release_key(tag):
    return tuple(int(n) for n in tag[1:].split('.'))


def discover_versions(remote):
    """Return the versions to publish: releases newest first, then development branches."""
    main_ref = f'refs/remotes/{remote}/main'
    if not ref_exists(main_ref):
        sys.exit(f"Error: {main_ref} not found. Fetch the remote '{remote}' first "
                 "(or pass --remote).")

    tags = [t for t in git('tag', '--list', 'v*', '--merged', main_ref).split()
            if RELEASE_TAG.match(t)]
    tags.sort(key=release_key, reverse=True)
    versions = [{'version': t, 'ref': f'refs/tags/{t}', 'release': True} for t in tags]

    for branch in DEV_BRANCHES:
        ref = f'refs/remotes/{remote}/{branch}'
        if ref_exists(ref):
            versions.append({'version': branch, 'ref': ref, 'release': False})
        else:
            print(f"Note: {ref} not found, skipping {branch}.")

    if not versions:
        sys.exit("Error: no release tags and no development branches found.")
    return versions


def export_tree(ref, dest):
    """Extract the tree of a git ref into dest."""
    os.makedirs(dest)
    archive = dest + '.tar'
    subprocess.check_call(['git', 'archive', '--format=tar', '-o', archive, ref])
    with tarfile.open(archive) as tar:
        if hasattr(tarfile, 'data_filter'):
            tar.extractall(dest, filter='data')
        else:
            tar.extractall(dest)
    os.remove(archive)


def banner_for(version, latest):
    """Banner data for a published version, None for the latest release."""
    if version['release']:
        if version['version'] == latest:
            return None
        return {'kind': 'outdated', 'name': version['version'], 'latest': latest}
    banner = {'kind': 'development', 'name': version['version']}
    if latest:
        banner['latest'] = latest
    return banner


def build_site(project_dir, output_dir, banner=None, published=False):
    """Build an MkDocs project with the overlay configuration.

    The overlay inherits the generated mkdocs.yml, so the project itself is left
    untouched. published enables the version selector, banner adds the banner.
    """
    overlay = {'INHERIT': 'mkdocs.yml'}
    extra = {}
    if published:
        extra['version'] = {'provider': 'mike', 'alias': True}
    if banner:
        extra['onde_site'] = banner
        overlay['theme'] = {'custom_dir': 'site_overrides'}
        override_dir = os.path.join(project_dir, 'site_overrides')
        os.makedirs(override_dir, exist_ok=True)
        with open(os.path.join(override_dir, 'main.html'), 'w', encoding='utf-8') as f:
            f.write(BANNER_TEMPLATE)
    if extra:
        overlay['extra'] = extra

    with open(os.path.join(project_dir, 'mkdocs.site.yml'), 'w', encoding='utf-8') as f:
        yaml.safe_dump(overlay, f, sort_keys=False)

    subprocess.check_call([sys.executable, '-m', 'mkdocs', 'build',
                           '-f', 'mkdocs.site.yml', '-d', os.path.abspath(output_dir)],
                          cwd=project_dir)


def build_version(version, latest, work_dir, output_dir):
    name = version['version']
    print(f"\n=== Building {name} ({version['ref']}) ===", flush=True)
    base = os.path.join(work_dir, name)
    tree = os.path.join(base, 'tree')
    export_tree(version['ref'], tree)

    if os.path.isfile(os.path.join(tree, 'tools', 'generate_docs.py')):
        subprocess.check_call([sys.executable, os.path.join('tools', 'generate_docs.py')],
                              cwd=tree)
        project_dir = os.path.join(tree, 'build', 'docs')
    else:
        print(f"{name} has no tools/generate_docs.py, rendering its Markdown files as they are.",
              flush=True)
        with open(os.path.join(base, 'mkdocs.yml'), 'w', encoding='utf-8') as f:
            f.write(LEGACY_MKDOCS_YML)
        project_dir = base

    build_site(project_dir, os.path.join(output_dir, name),
               banner=banner_for(version, latest), published=True)


def write_root_files(output_dir, versions, latest):
    """Write versions.json, the redirect page and the 404 page; copy the CSV."""
    entries = []
    for v in versions:
        name = v['version']
        entries.append({
            'version': name,
            'title': name if v['release'] else f'{name} (development)',
            'aliases': ['latest'] if name == latest else [],
        })
    with open(os.path.join(output_dir, 'versions.json'), 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2)
        f.write('\n')

    target = 'latest/index.html' if latest else f"{versions[0]['version']}/index.html"
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(REDIRECT_PAGE.format(target_attr=html.escape(target),
                                     target_js=json.dumps(target)))

    with open(os.path.join(output_dir, '404.html'), 'w', encoding='utf-8') as f:
        f.write(NOT_FOUND_PAGE)

    # Keeps the long-standing link to the CSV of the latest release working.
    if latest:
        for name in ('ONDE_fields.csv', 'robots.txt'):
            src = os.path.join(output_dir, latest, name)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(output_dir, name))


def check_output_dir(output_dir):
    # The output directory is emptied, so refuse the obvious mistakes.
    out = os.path.abspath(output_dir)
    inside = (os.getcwd() + os.sep).startswith(out.rstrip(os.sep) + os.sep)
    if inside or os.path.exists(os.path.join(out, '.git')):
        sys.exit(f"Error: refusing to empty {out}, choose another --output directory.")


def build_all(remote, output_dir):
    versions = discover_versions(remote)
    releases = [v['version'] for v in versions if v['release']]
    latest = releases[0] if releases else None
    print("Versions to build: " + ", ".join(v['version'] for v in versions))

    check_output_dir(output_dir)
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir)

    with tempfile.TemporaryDirectory() as work_dir:
        for v in versions:
            build_version(v, latest, work_dir, output_dir)

    if latest:
        shutil.copytree(os.path.join(output_dir, latest), os.path.join(output_dir, 'latest'))
    write_root_files(output_dir, versions, latest)

    print(f"\nBuilt versions: {', '.join(v['version'] for v in versions)}")
    if latest:
        print(f"Latest release: {latest}")
    print(f"Site written to {os.path.join(output_dir, 'index.html')}")


def build_pr_preview(number, repo_url):
    """Build the working tree as a pull request preview (no version selector)."""
    subprocess.check_call([sys.executable, os.path.join('tools', 'generate_docs.py')])
    banner = {
        'kind': 'pr_preview',
        'number': str(number),
        'pr_url': f"{repo_url.rstrip('/')}/pull/{number}",
    }
    build_site(os.path.join('build', 'docs'), os.path.join('build', 'docs', 'site'),
               banner=banner)
    print(f"Preview for pull request #{number} written to "
          f"{os.path.join('build', 'docs', 'site', 'index.html')}")


def default_repo_url():
    server = os.environ.get('GITHUB_SERVER_URL')
    repository = os.environ.get('GITHUB_REPOSITORY')
    if server and repository:
        return f'{server}/{repository}'
    return DEFAULT_REPO_URL


def main():
    parser = argparse.ArgumentParser(
        description='Build the multi-version ONDE documentation site, '
                    'or a pull request preview. Run from the repository root.')
    parser.add_argument('--output', default=os.path.join('build', 'site'),
                        help='directory for the multi-version site (default: build/site)')
    parser.add_argument('--remote', default='origin',
                        help='remote whose main, next_minor and next_major branches '
                             'are published (default: origin)')
    parser.add_argument('--pr-preview', type=int, metavar='N',
                        help='build the working tree as a preview of pull request N '
                             'into build/docs/site instead of the multi-version site')
    parser.add_argument('--repo-url', default=default_repo_url(),
                        help='repository URL for the pull request link (default: from '
                             'GITHUB_SERVER_URL and GITHUB_REPOSITORY, else '
                             + DEFAULT_REPO_URL + ')')
    args = parser.parse_args()

    if args.pr_preview is not None:
        build_pr_preview(args.pr_preview, args.repo_url)
    else:
        build_all(args.remote, args.output)


if __name__ == '__main__':
    main()
