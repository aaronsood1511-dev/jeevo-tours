#!/usr/bin/env python3
"""Marks every translatable string on the site with a data-i18n key.

The site used to translate the interface only - nav, headings, buttons - and
left the itineraries in English. For an inbound operator selling to French,
Italian and Spanish agents that defeats the point, so this walks every page,
tags every piece of visible text and every translatable attribute, and writes
the English source out as a translation table.

Keys are a hash of the English string, so a string that appears on twenty
pages is translated once and reused, and keys survive content being reordered.

Two things it is careful about, both of which bit on the first attempt:
  - An element whose only child is text gets the attribute itself. A <span>
    is only introduced where the text sits beside other markup, because a
    span inside <title> renders as literal angle brackets.
  - Entities are folded in before splitting, so "Temples &amp; Trails" stays
    one string instead of becoming two that no language can reorder.

    python3 tools/i18n_wire.py             # report only
    python3 tools/i18n_wire.py --apply     # rewrite the HTML + emit the table
"""
import glob, hashlib, html, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = sorted(glob.glob(os.path.join(ROOT, 'tours', '*.html'))) + [
    os.path.join(ROOT, p) for p in
    ('privacy.html', 'terms.html', 'disclaimer.html', 'photo-credits.html')
]

SKIP_TAGS = {'script', 'style', 'noscript', 'textarea'}
VOID      = {'area','base','br','col','embed','hr','img','input','link','meta',
             'param','source','track','wbr'}
ATTR_KEYS = ('alt', 'title', 'aria-label', 'placeholder')

# Never translated: the brand, the logo wordmark, contact details, and
# anything that is only punctuation or digits. City and country names are
# handled by leaving them inside the sentences that carry them.
LITERAL = {
    'Jeevo', 'jeev', 'Jeevo Tours and Travels', 'Jeevo Tours & Travels',
    'jeevo.co.in', 'www.jeevo.co.in', 'jeevotoursandtravels@gmail.com',
    '@jeevotoursandtravels', 'Jazz S',
}
ONLY_PUNCT = re.compile(r'^[\s\W\d]+$')

def translatable(s):
    s = s.strip()
    if not s or s in LITERAL:            return False
    if ONLY_PUNCT.match(s):              return False
    if not re.search(r'[A-Za-z]{2}', s): return False
    return True

def key_for(s):
    return 's.' + hashlib.sha1(s.encode('utf-8')).hexdigest()[:10]

def esc(s):
    """Back to markup. &nbsp; is restored by name so the bytes stay familiar."""
    return html.escape(s, quote=False).replace('\xa0', '&nbsp;')

# --------------------------------------------------------------- tree build
class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {'tag': None, 'children': [], 'parent': None}
        self.cur = self.root

    def _add(self, node):
        node['parent'] = self.cur
        self.cur['children'].append(node)
        return node

    def handle_starttag(self, tag, attrs):
        n = self._add({'kind': 'elem', 'tag': tag, 'raw': self.get_starttag_text(),
                       'attrs': dict(attrs), 'children': [], 'end': ''})
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self._add({'kind': 'elem', 'tag': tag, 'raw': self.get_starttag_text(),
                   'attrs': dict(attrs), 'children': [], 'end': '', 'selfclose': True})

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n['tag'] != tag:
            n = n['parent']
        if n is self.root:
            self._add({'kind': 'raw', 'raw': '</%s>' % tag})   # stray close tag
            return
        n['end'] = '</%s>' % tag
        self.cur = n['parent']

    def handle_data(self, d):     self._add({'kind': 'text', 'raw': d})
    def handle_comment(self, d):  self._add({'kind': 'raw', 'raw': '<!--%s-->' % d})
    def handle_decl(self, d):     self._add({'kind': 'raw', 'raw': '<!%s>' % d})
    def handle_pi(self, d):       self._add({'kind': 'raw', 'raw': '<?%s>' % d})
    def unknown_decl(self, d):    self._add({'kind': 'raw', 'raw': '<![%s]>' % d})

# ------------------------------------------------------------------- rewrite
class Rewriter(object):
    def __init__(self):
        self.found = {}

    def note(self, s):
        s = ' '.join(s.split())
        self.found[s] = key_for(s)
        return self.found[s]

    def attr_tag(self, node):
        """Add data-i18n-attr for alt / title / aria-label / placeholder / meta."""
        raw, d = node['raw'], node['attrs']
        if 'data-i18n-attr' in raw:
            return raw
        adds = []
        for a in ATTR_KEYS:
            v = d.get(a)
            if v and translatable(v):
                adds.append('%s:%s' % (a, self.note(v)))
        if node['tag'] == 'meta' and d.get('name') == 'description' and d.get('content'):
            if translatable(d['content']):
                adds.append('content:%s' % self.note(d['content']))
        if not adds:
            return raw
        close = '/>' if raw.rstrip().endswith('/>') else '>'
        stem = raw.rstrip()[:-len(close)].rstrip()
        return '%s data-i18n-attr="%s"%s' % (stem, ';'.join(adds), close)

    def walk(self, node, skipping=False):
        out = []
        kids = node.get('children', [])
        skip_here = skipping or node.get('tag') in SKIP_TAGS

        # An element whose only content is one run of text gets the attribute
        # itself - no span, so the DOM and any CSS built on it stay as they were.
        solo = None
        if not skip_here and node.get('tag') and node.get('end'):
            real = [c for c in kids if c['kind'] != 'text' or c['raw'].strip()]
            if len(real) == 1 and real[0]['kind'] == 'text' and translatable(real[0]['raw']):
                solo = real[0]

        for c in kids:
            if c['kind'] == 'text':
                if skip_here or not translatable(c['raw']) or c is solo:
                    out.append(esc(c['raw']))
                else:
                    lead = c['raw'][:len(c['raw']) - len(c['raw'].lstrip())]
                    tail = c['raw'][len(c['raw'].rstrip()):]
                    body = c['raw'].strip()
                    out.append('%s<span data-i18n="%s">%s</span>%s'
                               % (lead, self.note(body), esc(body), tail))
            elif c['kind'] == 'elem':
                # walk first: the child patches its own start tag when its
                # content turns out to be a single run of text
                inner = self.walk(c, skip_here)
                raw = c['raw'] if skip_here else self.attr_tag(c)
                out.append(raw)
                out.append(inner)
                out.append(c['end'])
            else:
                out.append(c['raw'])

        if solo is not None:
            k = self.note(solo['raw'])
            raw = node['raw']
            if 'data-i18n=' not in raw:
                close = '/>' if raw.rstrip().endswith('/>') else '>'
                stem = raw.rstrip()[:-len(close)].rstrip()
                node['raw'] = '%s data-i18n="%s"%s' % (stem, k, close)
        return ''.join(out)

def wire(path, apply=False):
    src = open(path, encoding='utf-8').read()
    t = Tree(); t.feed(src); t.close()
    r = Rewriter()
    # the document's own children, then patch the root's element raws
    body = r.walk(t.root)
    if apply:
        open(path, 'w', encoding='utf-8').write(body)
    return r.found, body

V = '20261022-all'

HEAD_LINK = '    <link rel="stylesheet" href="%sassets/jeevo-i18n.css?v=%s">\n'
FOOT = ('    <script src="%sassets/jeevo-i18n-data.js?v=%s"></script>\n'
        '    <script src="%sassets/i18n/%s.js?v=%s"></script>\n'
        '    <script src="%sassets/jeevo-i18n.js?v=%s" defer></script>\n')

def slug_for(path):
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    return rel[:-5]                       # drop .html

def install(path):
    """Put the language switcher on a page that never had it."""
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    up  = '../' if '/' in rel else ''
    src = open(path, encoding='utf-8').read()
    if 'jeevo-i18n.js' in src:
        return False
    src = src.replace('</head>', HEAD_LINK % (up, V) + '</head>', 1)
    foot = FOOT % (up, V, up, slug_for(path), V, up, V)
    i = src.rfind('</body>')
    src = src[:i] + foot + src[i:]
    open(path, 'w', encoding='utf-8').write(src)
    return True

def main():
    apply = '--apply' in sys.argv
    allstrings, manifest = {}, {}
    for p in PAGES:
        found, _ = wire(p, apply=apply)
        allstrings.update(found)
        manifest[slug_for(p)] = sorted(set(found.values()))
    print('pages: %d   unique strings: %d   words: %d'
          % (len(PAGES), len(allstrings), sum(len(s.split()) for s in allstrings)))
    if not apply:
        return
    out = os.path.join(ROOT, 'assets', 'i18n-source.json')
    json.dump({v: k for k, v in sorted(allstrings.items(), key=lambda kv: kv[1])},
              open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    man = os.path.join(ROOT, 'assets', 'i18n-manifest.json')
    json.dump(manifest, open(man, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = sum(1 for p in PAGES if install(p))
    print('wrote assets/i18n-source.json and assets/i18n-manifest.json')
    print('language switcher installed on %d page(s)' % n)

if __name__ == '__main__':
    main()
