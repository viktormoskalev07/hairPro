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

try:
    client = genai.Client(api_key=api_key)
    print("Testing image generation...")
    
    result = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt='a photorealistic high quality wig, hair piece on a pure solid white background, isolated, high resolution, hair only',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            output_mime_type="image/jpeg",
            aspect_ratio="1:1"
        )
    )
    
    for i, image in enumerate(result.generated_images):
        print(f"Got image {i}")
        with open(f"test_image_{i}.jpeg", "wb") as f:
            f.write(image.image.image_bytes)
            
    print("Success")
except Exception as e:
    print(f"Failed: {e}")
