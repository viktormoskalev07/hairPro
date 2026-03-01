import os
import json
from PIL import Image, ImageDraw, ImageFilter

wigs_dir = 'public/wigs_webp'
os.makedirs(wigs_dir, exist_ok=True)

wigs_list = []
# Realistic hair colors
colors = [
    (9, 8, 6), (44, 34, 43), (59, 48, 36), (78, 67, 63), 
    (80, 68, 68), (106, 78, 66), (167, 133, 106), (151, 121, 97),
    (220, 206, 177), (184, 151, 120), (165, 107, 70), (145, 85, 61), 
    (83, 61, 50), (113, 99, 90)
]
styles = ['fade', 'crew', 'pompadour', 'long', 'slick', 'buzz']

for i in range(1, 51):
    style = styles[i % len(styles)]
    color = colors[i % len(colors)]
    filename = f'male-wig-{i}.webp'
    filepath = os.path.join(wigs_dir, filename)
    
    # Create a transparent image
    img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a shape resembling hair
    # Simple curve using ellipse/polygon
    if style == 'long':
        draw.ellipse([30, 20, 170, 180], fill=color)
    elif style == 'pompadour':
        draw.polygon([(50, 100), (40, 30), (100, 10), (160, 30), (150, 100)], fill=color)
    else:
        draw.ellipse([40, 20, 160, 120], fill=color)
    
    # Apply a slight blur to simulate softness/anti-aliasing
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    
    # Save as WebP
    img.save(filepath, 'WEBP', lossless=True)
    
    wigs_list.append({
        'id': f'wig-{i}',
        'src': f'/wigs_webp/{filename}',
        'name': f'Style {i} ({style})'
    })

with open('components/wigs_data.json', 'w', encoding='utf-8') as f:
    json.dump(wigs_list, f, indent=2)

print("Created 50 WebP wigs")
