import os
import sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv('../.env')

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("No API key found in ../.env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

wigs_dir = 'public/wigs_real'
os.makedirs(wigs_dir, exist_ok=True)

# Loading existing wigs if any
try:
    with open("components/wigs_data.json", "r") as f:
        wigs_data = json.load(f)
except:
    wigs_data = []

existing_ids = [w['id'] for w in wigs_data]

new_styles = [
    ("cyberpunk neon-streaked black undercut, isolated on white background, photorealistic", "Neon Undercut"),
    ("platinum blonde braided viking hair style, isolated on white background, photorealistic", "Viking Braids"),
    ("pink pastel wavy long hair, isolated on white background, photorealistic", "Pastel Pink Waves"),
    ("men's top knot with shaved sides, dark hair, isolated on white background, photorealistic", "Top Knot"),
    ("emerald green short bob, isolated on white background, photorealistic", "Emerald Bob"),
    ("purple ombre long curly hair, isolated on white background, photorealistic", "Purple Ombre"),
    ("vibrant blue mohawk hairstyle, isolated on white background, photorealistic", "Blue Mohawk"),
    ("rose gold middle part long hair, isolated on white background, photorealistic", "Rose Gold Long"),
    ("white wolf cut hairstyle, isolated on white background, photorealistic", "White Wolf Cut"),
    ("rainbow dyed buzz cut, isolated on white background, photorealistic", "Rainbow Buzz")
]

start_index = len(wigs_data) + 1

print(f"Starting generation of 10 more cool wigs (starting from index {start_index})...")

for i, (prompt, name) in enumerate(new_styles):
    idx = start_index + i
    filename = f"real-wig-{idx}.png"
    filepath = os.path.join(wigs_dir, filename)
    print(f"Generating wig {idx}: {name}")
    
    try:
        result = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/png",
                aspect_ratio="1:1"
            )
        )
        
        for image in result.generated_images:
            with open(filepath, "wb") as f:
                f.write(image.image.image_bytes)
            
            wigs_data.append({
                "id": f"real-wig-{idx}",
                "src": f"/wigs_real/{filename}",
                "name": name
            })
            print(f" -> Saved to {filepath}")
            
    except Exception as e:
        print(f"Failed to generate wig {idx}: {e}")

with open("components/wigs_data.json", "w") as f:
    json.dump(wigs_data, f, indent=2)

print(f"Done! Updated wigs_data.json with {len(wigs_data)} total wigs.")
