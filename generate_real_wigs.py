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

wigs_data = []

styles = [
    "long wavy blonde hair, isolated on pure white background, photorealistic",
    "short black afro, isolated on pure white background, photorealistic",
    "men's slicked back brown hair, isolated on pure white background, photorealistic",
    "shoulder length red curly hair, isolated on pure white background, photorealistic",
    "men's modern fade haircut, black hair, isolated on pure white background, photorealistic",
    "long straight brown hair, isolated on pure white background, photorealistic",
    "short pixie cut blonde hair, isolated on pure white background, photorealistic",
    "messy bun brown hair, isolated on pure white background, photorealistic",
    "men's messy textured crop haircut, blonde, isolated on pure white background, photorealistic",
    "elegant silver grey bob haircut, isolated on pure white background, photorealistic"
]

names = [
    "Long Wavy Blonde",
    "Black Afro",
    "Slicked Back Brown",
    "Red Curls",
    "Modern Fade",
    "Long Straight Brown",
    "Blonde Pixie",
    "Messy Bun",
    "Textured Crop",
    "Silver Bob"
]

print("Starting generation of 10 real wigs...")

for i in range(10):
    prompt = styles[i]
    filename = f"real-wig-{i+1}.png"
    filepath = os.path.join(wigs_dir, filename)
    print(f"Generating wig {i+1}: {names[i]}")
    
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
                "id": f"real-wig-{i+1}",
                "src": f"/wigs_real/{filename}",
                "name": names[i]
            })
            print(f" -> Saved to {filepath}")
            
    except Exception as e:
        print(f"Failed to generate wig {i+1}: {e}")

with open("components/wigs_data.json", "w") as f:
    json.dump(wigs_data, f, indent=2)

print(f"Done! Successfully generated {len(wigs_data)} real wigs.")
