import json
import os
import requests
from io import BytesIO
from PIL import Image
import uuid

data_file = 'components/wigs_data.json'
output_dir = 'public/wigs_webp'
os.makedirs(output_dir, exist_ok=True)

valid_wigs = []

for i in range(1, 11):
    src = f"https://picsum.photos/seed/{uuid.uuid4()}/200/200"
    name = f"Real Hairstyle {i}"
    wig_id = f"real-style-{i}"
    print(f"Processing: {name} ({src})")

    img_data = None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(src, headers=headers, timeout=10)
        if response.status_code == 200:
            img_data = response.content
        else:
            print(f"  -> Failed: HTTP {response.status_code}")
            continue
    except Exception as e:
        print(f"  -> Error fetching remote URL: {e}")
        continue
            
    if not img_data or len(img_data) == 0:
        print("  -> Failed: File size is 0 bytes")
        continue

    try:
        img = Image.open(BytesIO(img_data))
        new_filename = f"{wig_id}.webp"
        new_filepath = os.path.join(output_dir, new_filename)
        img.save(new_filepath, 'WEBP', lossless=True)
        
        if os.path.getsize(new_filepath) == 0:
             print("  -> Failed: WebP size is 0 bytes")
             os.remove(new_filepath)
             continue
             
        print(f"  -> Success: Saved as {new_filepath}")
        
        valid_wigs.append({
            'id': wig_id,
            'src': f'/wigs_webp/{new_filename}',
            'name': name
        })
        
    except Exception as e:
        print(f"  -> Failed: Image processing error: {e}")
        continue

with open(data_file, 'w', encoding='utf-8') as f:
    json.dump(valid_wigs, f, indent=2)

print(f"\nProcessing complete! Kept {len(valid_wigs)} wigs.")
