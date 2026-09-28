import sys
sys.path.insert(0, '.')
from qf_script import template_script
from qf_visuals.copy import build_copy, STYLES, choose_style

topics = ['Chai tapri sunrise regulars', 'Mechanical keyboard custom build', 'Maggi instant noodles review']
for topic in topics:
    s = template_script(topic)
    style = choose_style(topic)
    out_path = f'storage/comps/test3_{topic[:8]}'
    out = build_copy(s, out_path, style=style)
    print(f"Topic: {topic}")
    print(f"  Style: {style}")
    print(f"  Output: {out_path}/index.html ({len(out)} chars)")