import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv('../.env')

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("No API key found in ../.env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

try:
    print("Generating Spider-Man wallpaper...")
    result = client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt='Spider-Man cinematic wallpaper, high resolution, 4k, vertical orientation for tablet, action pose, city background',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            output_mime_type="image/png",
            aspect_ratio="9:16"
        )
    )
    
    filepath = "public/spiderman_wallpaper.png"
    for image in result.generated_images:
        with open(filepath, "wb") as f:
            f.write(image.image.image_bytes)
    print(f"Success! Saved wallpaper to {filepath}")
except Exception as e:
    print(f"Failed: {e}")
