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
    print("Generating a fictional guy's face...")
    result = client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt='front facing portrait of a handsome fictional man with no hair, bald, plain background, photorealistic, high quality, symmetrical face',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            output_mime_type="image/png",
            aspect_ratio="1:1"
        )
    )
    
    filepath = "public/test-face.png"
    for image in result.generated_images:
        with open(filepath, "wb") as f:
            f.write(image.image.image_bytes)
    print(f"Success! Saved face to {filepath}")
except Exception as e:
    print(f"Failed: {e}")
