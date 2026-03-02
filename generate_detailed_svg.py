import urllib.request
import json
import os

wigs_dir = 'public/wigs_webp'
os.makedirs(wigs_dir, exist_ok=True)

# Let's try to get a few known open-source transparent images of hair from github or similar
urls = [
    "https://raw.githubusercontent.com/NVlabs/ffhq-dataset/master/thumbnail.png", # not transparent hair
]

# Alternatively, I can use a script to generate a very complex procedural SVG that looks almost like real vector hair (lots of strands)
def create_complex_hair_svg(filename, color1, color2):
    filepath = os.path.join(wigs_dir, filename)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <radialGradient id="hairGrad" cx="50%" cy="30%" r="70%" fx="50%" fy="30%">
      <stop offset="0%" stop-color="{color1}"/>
      <stop offset="100%" stop-color="{color2}"/>
    </radialGradient>
    <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-opacity="0.4"/>
    </filter>
  </defs>
  <path d="M50 130 C30 80 40 20 100 20 C160 20 170 80 150 130 C130 160 160 180 140 190 C120 200 110 150 100 150 C90 150 80 200 60 190 C40 180 70 160 50 130 Z" fill="url(#hairGrad)" filter="url(#dropShadow)"/>
  <path d="M70 40 Q100 25 130 40 Q110 50 100 60 Q90 50 70 40 Z" fill="#ffffff" opacity="0.15"/>
'''
    # Add many strands
    import random
    random.seed(filename)
    for _ in range(40):
        x1 = random.randint(40, 160)
        y1 = random.randint(20, 130)
        x2 = x1 + random.randint(-20, 20)
        y2 = y1 + random.randint(30, 80)
        opacity = random.uniform(0.1, 0.4)
        stroke_width = random.uniform(0.5, 2.5)
        # dark strands
        svg += f'  <path d="M{x1} {y1} Q{x1+10} {(y1+y2)//2} {x2} {y2}" stroke="#000000" stroke-width="{stroke_width}" fill="none" opacity="{opacity}"/>\n'
        # light strands
        x1 += 2
        svg += f'  <path d="M{x1} {y1} Q{x1+10} {(y1+y2)//2} {x2+2} {y2}" stroke="#ffffff" stroke-width="{stroke_width*0.5}" fill="none" opacity="{opacity*0.5}"/>\n'

    svg += "</svg>"
    
    with open(filepath.replace('.webp', '.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)

# Let's generate 10 highly detailed vector hairs
colors = [
    ("#4a3b32", "#1a1210"), # Dark brown
    ("#d9b382", "#8c6239"), # Blonde
    ("#803315", "#331408"), # Auburn
    ("#2b2b2b", "#0a0a0a"), # Black
    ("#e6ceb3", "#a68c72"), # Light Blonde
    ("#594031", "#261912"), # Medium Brown
]

wigs_data = []
for i in range(1, 11):
    c1, c2 = colors[i % len(colors)]
    name = f"Premium Vector Style {i}"
    filename = f"premium-style-{i}.webp" # We will use SVG but pretend it's WebP or just use SVG directly
    create_complex_hair_svg(filename, c1, c2)
    wigs_data.append({
        "id": f"premium-style-{i}",
        "src": f"/wigs_webp/premium-style-{i}.svg",
        "name": name
    })

with open("components/wigs_data.json", "w") as f:
    json.dump(wigs_data, f, indent=2)

print("Generated highly detailed vector wigs")
