"""Update Famous Tampa Homes entries in sitemap.xml and llms.txt. Run from repo root."""
from pathlib import Path
import re

ROOT = Path(".")
URLS = ['https://ignaciotorano.com/famous-tampa-homes/captain-william-parker-jackson-house/', 'https://ignaciotorano.com/famous-tampa-homes/peter-o-knight-house/', 'https://ignaciotorano.com/famous-tampa-homes/tc-taliaferro-house/', 'https://ignaciotorano.com/famous-tampa-homes/jackson-rooming-house/', 'https://ignaciotorano.com/famous-tampa-homes/stovall-house/', 'https://ignaciotorano.com/famous-tampa-homes/dorchester-house-901-bayshore/', 'https://ignaciotorano.com/famous-tampa-homes/dp-davis-house/', 'https://ignaciotorano.com/famous-tampa-homes/plant-hatton-house/', 'https://ignaciotorano.com/famous-tampa-homes/george-guida-house/']
RETIRED = "https://ignaciotorano.com/famous-tampa-homes/1801-bayshore-boulevard/"
BLOCK = '## Famous Tampa Homes\n- [Famous Tampa Homes](https://ignaciotorano.com/famous-tampa-homes/): interactive map and sourced history series\n- [Captain William Parker Jackson House](https://ignaciotorano.com/famous-tampa-homes/captain-william-parker-jackson-house/)\n- [Peter O. Knight Cottage](https://ignaciotorano.com/famous-tampa-homes/peter-o-knight-house/)\n- [T.C. Taliaferro House](https://ignaciotorano.com/famous-tampa-homes/tc-taliaferro-house/)\n- [Jackson Rooming House](https://ignaciotorano.com/famous-tampa-homes/jackson-rooming-house/)\n- [Stovall House](https://ignaciotorano.com/famous-tampa-homes/stovall-house/)\n- [Dorchester House at 901 Bayshore](https://ignaciotorano.com/famous-tampa-homes/dorchester-house-901-bayshore/)\n- [House at 116 West Davis Boulevard](https://ignaciotorano.com/famous-tampa-homes/dp-davis-house/)\n- [Plant-Hatton House](https://ignaciotorano.com/famous-tampa-homes/plant-hatton-house/)\n- [George Guida Sr. House](https://ignaciotorano.com/famous-tampa-homes/george-guida-house/)\n'

sm = ROOT / "sitemap.xml"
text = sm.read_text(encoding="utf-8")
text = re.sub(r"\s*<url><loc>" + re.escape(RETIRED) + r"</loc>.*?</url>\s*", "\n", text, flags=re.S)
for url in URLS:
    if url not in text:
        text = text.replace("</urlset>", f"  <url><loc>{url}</loc><lastmod>2026-10-20</lastmod><priority>0.7</priority></url>\n</urlset>")
sm.write_text(text, encoding="utf-8")
print("sitemap.xml updated")

ll = ROOT / "llms.txt"
if ll.exists():
    text = ll.read_text(encoding="utf-8")
    text = "\n".join(line for line in text.splitlines() if "1801-bayshore-boulevard" not in line) + "\n"
    if "## Famous Tampa Homes" in text:
        text = re.sub(r"## Famous Tampa Homes.*?(?=\n## |\Z)", BLOCK.rstrip(), text, flags=re.S)
    else:
        text += "\n" + BLOCK
    ll.write_text(text, encoding="utf-8")
    print("llms.txt updated")
