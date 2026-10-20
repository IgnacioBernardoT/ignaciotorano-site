"""Adds 'Famous Tampa Homes' to the Resources dropdown + footer nav on every page,
and adds the 3 new URLs to sitemap.xml and llms.txt. Safe to run more than once. Run from repo root."""
import pathlib, re
root = pathlib.Path('.')
DROP = re.compile(r'(<li><a href="[^"]*/things-to-do/">Things to Do in Tampa</a></li>)')
FOOT = re.compile(r'(<a href="[^"]*/things-to-do/">Things to Do</a>(?:</li>)?)')
changed = 0
for f in root.rglob('*.html'):
    if '.git' in f.parts or 'famous-tampa-homes' in f.parts:
        continue
    s = f.read_text(encoding='utf-8'); o = s
    if '/famous-tampa-homes/' not in s:
        s = DROP.sub(r'\1\n          <li><a href="https://ignaciotorano.com/famous-tampa-homes/">Famous Tampa Homes</a></li>', s, count=1)
        foot = s.find('<footer')
        m = [x for x in FOOT.finditer(s) if foot != -1 and x.start() > foot]
        if m:
            i = m[-1].end()
            if m[-1].group(1).endswith('</li>'):
                s = s[:i] + '\n      <li><a href="https://ignaciotorano.com/famous-tampa-homes/">Famous Tampa Homes</a></li>' + s[i:]
            else:
                s = s[:i] + '\n      <a href="https://ignaciotorano.com/famous-tampa-homes/">Famous Tampa Homes</a>' + s[i:]
    if s != o:
        f.write_text(s, encoding='utf-8'); changed += 1
# parks.html uses bare <a> items in its dropdown
pk = root / 'parks.html'
if pk.exists():
    s = pk.read_text(encoding='utf-8')
    if '/famous-tampa-homes/' not in s:
        s2 = re.sub(r'(\n(\s*)<a href="https://ignaciotorano.com/things-to-do/">Things to Do in Tampa</a>)',
                    r'\1\n\2<a href="https://ignaciotorano.com/famous-tampa-homes/">Famous Tampa Homes</a>', s, count=1)
        if s2 != s:
            pk.write_text(s2, encoding='utf-8'); changed += 1
print(f'nav updated on {changed} pages')
URLS = ['famous-tampa-homes/', 'famous-tampa-homes/captain-william-parker-jackson-house/', 'famous-tampa-homes/peter-o-knight-house/']
sm = root / 'sitemap.xml'
if sm.exists():
    x = sm.read_text(encoding='utf-8')
    if 'famous-tampa-homes' not in x:
        add = ''.join(f'  <url><loc>https://ignaciotorano.com/{u}</loc><lastmod>2026-10-19</lastmod><priority>0.7</priority></url>\n' for u in URLS)
        x = x.replace('</urlset>', add + '</urlset>'); sm.write_text(x, encoding='utf-8'); print('sitemap updated')
ll = root / 'llms.txt'
if ll.exists():
    x = ll.read_text(encoding='utf-8')
    if 'famous-tampa-homes' not in x:
        block = ('## Famous Tampa Homes\n\n'
                 '- [Famous Tampa Homes](https://ignaciotorano.com/famous-tampa-homes/): Series on historic Tampa homes and the people who lived in them\n'
                 '- [Captain William Parker Jackson House](https://ignaciotorano.com/famous-tampa-homes/captain-william-parker-jackson-house/): c. 1885 pioneer farmhouse, Old Seminole Heights\n'
                 '- [Peter O. Knight Cottage](https://ignaciotorano.com/famous-tampa-homes/peter-o-knight-house/): c. 1889 Victorian cottage, Hyde Park\n\n')
        x = x.replace('## Services', block + '## Services', 1) if '## Services' in x else x + '\n' + block
        ll.write_text(x, encoding='utf-8'); print('llms.txt updated')
