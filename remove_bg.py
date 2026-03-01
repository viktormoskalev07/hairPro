import os
import json
from PIL import Image

wigs_dir = 'public/wigs_real'

print("Making backgrounds transparent...")

for i in range(10):
    filename = f"real-wig-{i+1}.png"
    filepath = os.path.join(wigs_dir, filename)
    
    if os.path.exists(filepath):
        img = Image.open(filepath).convert("RGBA")
        datas = img.getdata()
        
        newData = []
        # tolerance for white
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
                
        img.putdata(newData)
        # Save over as webp to be fast
        webp_filepath = filepath.replace(".png", ".webp")
        img.save(webp_filepath, "WEBP")
        # Remove original png
        os.remove(filepath)
        print(f"Made transparent and saved as {webp_filepath}")

# Update json to point to webp
with open("components/wigs_data.json", "r") as f:
    wigs_data = json.load(f)

for wig in wigs_data:
    wig["src"] = wig["src"].replace(".png", ".webp")

with open("components/wigs_data.json", "w") as f:
    json.dump(wigs_data, f, indent=2)

print("Done! All real wigs now have transparent backgrounds and are compressed as WebP.")
