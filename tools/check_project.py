"""Verifica referencias locales del HTML y la sintaxis JavaScript si hay Node."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        for name in ('src', 'href', 'data-full'):
            value = data.get(name, '')
            url = urlsplit(value)
            if value and not url.scheme and not value.startswith(('#', '/')):
                self.paths.append(unquote(url.path))


for html in (ROOT / 'dist').glob('*.html'):
    parser = Assets()
    parser.feed(html.read_text(encoding='utf-8'))
    for path in parser.paths:
        assert (html.parent / path).is_file(), f'Recurso ausente: {html.name}: {path}'
node = shutil.which('node')
if node:
    for script in (ROOT / 'dist').glob('*.js'):
        subprocess.run([node, '--check', str(script)], check=True)
else:
    print('Node no disponible: se omitió la revisión opcional de sintaxis JavaScript.')
print('Recursos locales y comprobaciones disponibles: correctos.')
