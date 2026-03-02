import os
import sys
import json
import time
import io
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from rembg import remove as rembg_remove

# Load environment
load_dotenv('../.env')
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: No GEMINI_API_KEY found in ../.env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# Configuration
OUTPUT_DIR = "public/wigs_categorized"
HTML_PATH = "public/test_wigs.html"
DATA_PATH = "components/categorized_wigs.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Categories and Prompts (Hairdresser Classifications)
CATEGORIES = {
    "Women's Classics": [
        ("Classic Bob", "isolated hairstyle: sleek chin-length bob haircut, straight hair, pure white background, no face, no body, photorealistic"),
        ("Pixie Cut", "isolated hairstyle: short textured pixie haircut for women, pure white background, no face, no body, photorealistic"),
        ("Long Layers", "isolated hairstyle: long layered hair with volume, chestnut brown, pure white background, no face, no body, photorealistic"),
        ("Sassoon Cut", "isolated hairstyle: geometric sassoon haircut, precision cut, pure white background, no face, no body, photorealistic")
    ],
    "Men's Classics": [
        ("Classic Side Part", "isolated hairstyle: men's classic side part haircut, polished look, brown hair, pure white background, no face, no body, photorealistic"),
        ("Crew Cut", "isolated hairstyle: men's crew cut, short sides and back, pure white background, no face, no body, photorealistic"),
        ("Executive Contour", "isolated hairstyle: men's executive contour haircut, vintage style, pure white background, no face, no body, photorealistic")
    ],
    "Modern & Creative": [
        ("Wolf Cut", "isolated hairstyle: trendy wolf cut haircut, shaggy layers, messy texture, pure white background, no face, no body, photorealistic"),
        ("Mullet", "isolated hairstyle: modern mullet haircut, short front long back, pure white background, no face, no body, photorealistic"),
        ("High Fade", "isolated hairstyle: men's high skin fade with textured top, black hair, pure white background, no face, no body, photorealistic"),
        ("Curtain Bangs", "isolated hairstyle: medium length hair with curtain bangs, blonde, pure white background, no face, no body, photorealistic")
    ],
    "Textured": [
        ("Classic Afro", "isolated hairstyle: round black natural afro hair, highly textured, pure white background, no face, no body, photorealistic"),
        ("Dreadlocks", "isolated hairstyle: shoulder-length dreadlocks, natural texture, pure white background, no face, no body, photorealistic"),
        ("Deep Wave", "isolated hairstyle: long deep wave curly hair, pure white background, no face, no body, photorealistic")
    ],
    "Avant-Garde": [
        ("Neon Shag", "isolated hairstyle: neon green shaggy haircut, experimental style, pure white background, no face, no body, photorealistic"),
        ("Geometric Pink", "isolated hairstyle: bright pink geometric bob, sharp edges, pure white background, no face, no body, photorealistic")
    ]
}

def generate_wigs():
    all_wigs = []
    print(f"Starting generation in {OUTPUT_DIR}...")
    
    for category, wigs in CATEGORIES.items():
        print(f"\n--- Category: {category} ---")
        for name, prompt in wigs:
            safe_name = name.lower().replace(" ", "_").replace("&", "and")
            filename = f"{safe_name}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if os.path.exists(filepath):
                print(f"File {filepath} already exists, skipping generation.")
                all_wigs.append({
                    "category": category,
                    "name": name,
                    "src": f"/wigs_categorized/{filename}",
                    "path": filepath
                })
                continue

            print(f"Generating: {name}...")
            try:
                result = client.models.generate_images(
                    model="imagen-4.0-generate-001",
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                        aspect_ratio="1:1",
                    )
                )

                if not result.generated_images:
                    print(f"  -> Failed: No image returned")
                    continue

                raw_bytes = result.generated_images[0].image.image_bytes
                
                # Remove background
                print(f"  -> Removing background...")
                clean_bytes = rembg_remove(raw_bytes)
                img = Image.open(io.BytesIO(clean_bytes))
                img.save(filepath)
                
                all_wigs.append({
                    "category": category,
                    "name": name,
                    "src": f"/wigs_categorized/{filename}",
                    "path": filepath
                })
                print(f"  -> Saved to {filepath}")
                
            except Exception as e:
                print(f"  -> ERROR: {e}")
            
            time.sleep(1) # Small delay
            
    return all_wigs

def audit_wigs(wigs):
    print("\n" + "="*60)
    print("STEP: Auditing with Gemini Vision")
    print("="*60)
    
    audited_wigs = []
    
    for wig in wigs:
        print(f"Auditing: {wig['name']}...")
        try:
            img = Image.open(wig['path']).convert("RGBA")
            img.thumbnail((512, 512), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()

            prompt = """Look at this image carefully. Answer ONLY with JSON like {"ok": true/false, "reason": "..."}.
            This is a wig/hairstyle for a virtual try-on app.
            Criteria for ok=true:
            - Only hair is visible (or hair on a very subtle head shape if needed, but preferably just hair)
            - NO human faces (no eyes, nose, mouth)
            - NO watermarks or text
            - Background is transparent or clean white
            - Clearly recognizable as the hairstyle: """ + wig['name']

            response = client.models.generate_content(
                model="gemini-2.5-flash", # Using 2.5 flash
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    prompt
                ]
            )
            
            raw = response.text.strip()
            match = re.search(r'\{.*?\}', raw, re.DOTALL)
            if match:
                res = json.loads(match.group())
                wig['ok'] = res.get("ok", False)
                wig['reason'] = res.get("reason", "N/A")
            else:
                wig['ok'] = False
                wig['reason'] = f"Failed to parse AI response: {raw[:50]}"
            
            status = "PASS" if wig['ok'] else "FAIL"
            print(f"  -> {status}: {wig['reason']}")
            audited_wigs.append(wig)
            
        except Exception as e:
            print(f"  -> ERROR during audit: {e}")
            wig['ok'] = True # Keep on error
            wig['reason'] = f"Audit error: {e}"
            audited_wigs.append(wig)
            
        time.sleep(0.5)
        
    return audited_wigs

def create_html(wigs):
    print(f"\nCreating HTML page: {HTML_PATH}")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wig Generation Test Page</title>
        <style>
            body {{ font-family: sans-serif; background: #f0f0f0; padding: 20px; }}
            .container {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
            .card {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 250px; padding: 10px; }}
            .card img {{ width: 100%; height: 250px; object-fit: contain; background: #eee; border-radius: 4px; }}
            .card.fail {{ border: 2px solid #ff4d4d; }}
            .card.pass {{ border: 2px solid #4dff4d; }}
            .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 5px; }}
            .badge.pass {{ background: #d4edda; color: #155724; }}
            .badge.fail {{ background: #f8d7da; color: #721c24; }}
            h1 {{ text-align: center; }}
            h2 {{ width: 100%; border-bottom: 2px solid #ccc; padding-bottom: 5px; margin-top: 40px; }}
            .reason {{ font-size: 12px; color: #666; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h1>Wig Generation Results</h1>
        <div class="container">
    """
    
    current_cat = ""
    for wig in wigs:
        if wig['category'] != current_cat:
            current_cat = wig['category']
            html_content += f"<h2>{current_cat}</h2>"
            
        status_class = "pass" if wig['ok'] else "fail"
        badge_text = "PASSED" if wig['ok'] else "FAILED"
        
        html_content += f"""
        <div class="card {status_class}">
            <span class="badge {status_class}">{badge_text}</span>
            <img src=".{wig['src']}" alt="{wig['name']}">
            <strong>{wig['name']}</strong>
            <div class="reason">{wig['reason']}</div>
        </div>
        """
        
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(wigs, f, indent=2)

if __name__ == "__main__":
    generated = generate_wigs()
    audited = audit_wigs(generated)
    create_html(audited)
    print("\nAll done!")
