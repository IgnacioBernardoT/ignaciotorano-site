"""Adds/updates the Famous Tampa Homes series in sitemap.xml and llms.txt. Safe to run more than once. Run from repo root."""
import pathlib, re
root=pathlib.Path('.')
URLS=['https://ignaciotorano.com/famous-tampa-homes/', 'https://ignaciotorano.com/famous-tampa-homes/captain-william-parker-jackson-house/', 'https://ignaciotorano.com/famous-tampa-homes/peter-o-knight-house/', 'https://ignaciotorano.com/famous-tampa-homes/tc-taliaferro-house/', 'https://ignaciotorano.com/famous-tampa-homes/jackson-rooming-house/', 'https://ignaciotorano.com/famous-tampa-homes/stovall-house/', 'https://ignaciotorano.com/famous-tampa-homes/dorchester-house-901-bayshore/', 'https://ignaciotorano.com/famous-tampa-homes/dp-davis-house/', 'https://ignaciotorano.com/famous-tampa-homes/plant-hatton-house/', 'https://ignaciotorano.com/famous-tampa-homes/george-guida-house/', 'https://ignaciotorano.com/famous-tampa-homes/1801-bayshore-boulevard/']
sm=root/'sitemap.xml'
x=sm.read_text(encoding='utf-8')
for url in URLS:
    if url not in x:
        x=x.replace('</urlset>', f'  <url><loc>{url}</loc><lastmod>2026-10-20</lastmod><priority>0.7</priority></url>\n</urlset>')
sm.write_text(x,encoding='utf-8')
ll=root/'llms.txt'
x=ll.read_text(encoding='utf-8')
heading='## Famous Tampa Homes'
lines='- [Captain William Parker Jackson House](https://ignaciotorano.com/famous-tampa-homes/captain-william-parker-jackson-house/): c. 1885, 800 E. Lambright St., Old Seminole Heights\n- [The Peter O. Knight Cottage](https://ignaciotorano.com/famous-tampa-homes/peter-o-knight-house/): 1890, 245 S. Hyde Park Ave., Hyde Park\n- [The T.C. Taliaferro House](https://ignaciotorano.com/famous-tampa-homes/tc-taliaferro-house/): 1890, 305 S. Hyde Park Ave., Hyde Park\n- [The Jackson Rooming House](https://ignaciotorano.com/famous-tampa-homes/jackson-rooming-house/): c. 1900, 851 E. Zack St., Downtown\n- [The Stovall House](https://ignaciotorano.com/famous-tampa-homes/stovall-house/): 1909, 4621 Bayshore Blvd., Bayshore Beautiful\n- [The Dorchester House](https://ignaciotorano.com/famous-tampa-homes/dorchester-house-901-bayshore/): 1912, 901 Bayshore Blvd., Bayshore / Hyde Park\n- [The D.P. Davis House](https://ignaciotorano.com/famous-tampa-homes/dp-davis-house/): 1925, 116 W. Davis Blvd., Davis Islands\n- [The Plant-Hatton House](https://ignaciotorano.com/famous-tampa-homes/plant-hatton-house/): c. 1926, 4505 W. Beachway Dr., Beach Park\n- [The George Guida Sr. House](https://ignaciotorano.com/famous-tampa-homes/george-guida-house/): 1952, 1516 N. Renfrew St., West Tampa\n- [1801 Bayshore Boulevard](https://ignaciotorano.com/famous-tampa-homes/1801-bayshore-boulevard/): Modern Era, 1801 Bayshore Blvd., Bayshore'
block=heading+'\n'+lines+'\n'
if heading in x:
    x=re.sub(r'## Famous Tampa Homes\n.*?(?=\n## |\Z)',block.rstrip(),x,flags=re.S)
else:
    x=x.rstrip()+'\n\n'+block
ll.write_text(x,encoding='utf-8')
print('Famous Tampa Homes sitemap and llms.txt entries updated.')
