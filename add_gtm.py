"""
add_gtm.py — run from the root of the ignaciotorano-site folder:
    python add_gtm.py

For every .html file (recursively):
  1. Removes old hard-coded GA4 gtag, Meta Pixel, and Microsoft Clarity blocks
  2. Adds the GTM <script> right after <head> if not already present
  3. Adds the GTM <noscript> right after <body ...> if not already present
Prints a summary. Safe to re-run.
"""
import re, pathlib

GTM_ID = "GTM-WDDVB6SD"
GA4_ID = "G-XBTLFZ7QLY"

GTM_HEAD = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');</script>
<!-- End Google Tag Manager -->
"""

GTM_BODY = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""

# Patterns for old tracker blocks (DOTALL so they span lines)
OLD_BLOCKS = [
    # GA4 gtag loader + config (with optional comment)
    re.compile(r'(<!--\s*Google tag \(gtag\.js\)\s*-->\s*)?<script async src="https://www\.googletagmanager\.com/gtag/js\?id=' + GA4_ID + r'"></script>\s*<script>.*?gtag\(\'config\',\s*\'' + GA4_ID + r'\'\);?\s*</script>\s*', re.S),
    # Meta Pixel (commented block)
    re.compile(r'<!--\s*Meta Pixel Code\s*-->.*?<!--\s*End Meta Pixel Code\s*-->\s*', re.S),
    # Meta Pixel (bare script, in case no comments)
    re.compile(r'<script[^>]*>\s*!function\(f,b,e,v,n,t,s\).*?fbevents\.js.*?</script>\s*(<noscript>.*?facebook\.com/tr\?.*?</noscript>\s*)?', re.S),
    # Clarity (commented or bare)
    re.compile(r'(<!--\s*Microsoft Clarity\s*-->\s*)?<script[^>]*>\s*\(function\(c,l,a,r,i,t,y\).*?clarity\.ms/tag/.*?</script>\s*', re.S),
    # Delayed loader Claude added to homepage earlier (if present)
    re.compile(r'<!-- Meta Pixel \+ Microsoft Clarity: loaded after first interaction.*?</script>\s*', re.S),
]

root = pathlib.Path(".")
files = [p for p in root.rglob("*.html") if "node_modules" not in p.parts and ".git" not in p.parts]
added_head = added_body = stripped = 0

for p in files:
    orig = p.read_text(encoding="utf-8", errors="ignore")
    s = orig
    for pat in OLD_BLOCKS:
        s, n = pat.subn("", s)
        stripped += n
    if GTM_ID not in s.split("<body", 1)[0]:  # not in head yet
        s = re.sub(r"(<head[^>]*>\s*)", r"\1" + GTM_HEAD.replace("\\", "\\\\"), s, count=1)
        added_head += 1
    if "ns.html?id=" + GTM_ID not in s:
        s = re.sub(r"(<body[^>]*>\s*)", r"\1" + GTM_BODY.replace("\\", "\\\\"), s, count=1)
        added_body += 1
    if s != orig:
        p.write_text(s, encoding="utf-8")

print(f"Files scanned: {len(files)}")
print(f"GTM head snippets added: {added_head}")
print(f"GTM noscript snippets added: {added_body}")
print(f"Old tracker blocks removed: {stripped}")
