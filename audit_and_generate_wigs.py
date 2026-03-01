"""
Step 1: Audit all wigs with Gemini Vision — remove bad ones (watermarks, faces, random photos)
Step 2: Generate fresh proper wig images with Imagen
"""

import os, sys, json, time, base64, io
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv('../.env')
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: No GEMINI_API_KEY found in ../.env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

WIGS_DATA_PATH = "components/wigs_data.json"
WIGS_DIR = "public/wigs_real"

# ──────────────────────────────────────────────
# STEP 1: AUDIT EXISTING WIGS
# ──────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Auditing existing wigs with Gemini Vision")
print("=" * 60)

with open(WIGS_DATA_PATH) as f:
    wigs = json.load(f)

kept = []
removed = []

for wig in wigs:
    path = "public" + wig["src"]
    if not os.path.exists(path):
        print(f"  [MISSING] {wig['name']} -> {path}")
        removed.append(wig)
        continue

    # Load image and convert to base64 for Gemini
    img = Image.open(path).convert("RGBA")
    # Resize to max 512px for faster API calls
    img.thumbnail((512, 512), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    prompt = """Look at this image carefully. Answer ONLY with JSON like {"ok": true/false, "reason": "..."}.

This image is supposed to be a HAIRSTYLE / WIG for a virtual hair try-on app.
A GOOD image (ok=true) must:
- Show ONLY hair/hairstyle isolated on a transparent or clean white background
- Have NO watermarks, logos, or text overlays
- Have NO human faces visible
- Not be a random photo, product shot, or unrelated image
- Hair should be clearly visible and recognizable as a hairstyle

Answer ok=false if the image has watermarks, shows a full person/face, has text overlays, is a random photo, or is clearly not a wig/hairstyle image."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt
            ]
        )
        raw = response.text.strip()
        # Extract JSON from response
        import re
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            ok = result.get("ok", False)
            reason = result.get("reason", "")
        else:
            ok = False
            reason = f"Could not parse response: {raw[:100]}"

        status = "OK  " if ok else "BAD "
        print(f"  [{status}] {wig['name']:30s} | {reason[:70]}")

        if ok:
            kept.append(wig)
        else:
            removed.append(wig)
            # Delete the file
            try:
                os.remove(path)
                print(f"           -> Deleted: {path}")
            except Exception as e:
                print(f"           -> Could not delete: {e}")

    except Exception as e:
        print(f"  [ERR ] {wig['name']:30s} | API error: {e}")
        kept.append(wig)  # Keep on error to be safe

    time.sleep(0.3)  # Rate limit

print(f"\nAudit done: {len(kept)} kept, {len(removed)} removed")

# Save cleaned JSON
with open(WIGS_DATA_PATH, "w") as f:
    json.dump(kept, f, indent=2)
print(f"Saved cleaned wigs_data.json ({len(kept)} wigs)")

# ──────────────────────────────────────────────
# STEP 2: GENERATE NEW QUALITY WIGS
# ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Generating new wig images with Imagen")
print("=" * 60)

# These prompts are crafted specifically for transparent-bg hair images
new_wigs_to_generate = [
    ("Natural Black Straight",     "isolated hairstyle: sleek long straight black hair, top view of hair only, pure white background, no face, no body, photorealistic hair texture, professional product shot"),
    ("Auburn Wavy Bob",            "isolated hairstyle: auburn reddish-brown wavy bob haircut, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Platinum Blonde Pixie",      "isolated hairstyle: platinum blonde pixie cut short hair, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Chestnut Curly Long",        "isolated hairstyle: chestnut brown long curly hair, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Ash Grey Bob",               "isolated hairstyle: ash grey silver short bob haircut, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Honey Blonde Layers",        "isolated hairstyle: honey blonde layered medium hair, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Jet Black Undercut",         "isolated hairstyle: men's jet black undercut fade haircut, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Copper Red Waves",           "isolated hairstyle: copper red wavy medium length hair, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Dark Brown Pompadour",       "isolated hairstyle: men's dark brown pompadour hairstyle, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Lavender Lob",               "isolated hairstyle: pastel lavender shoulder length lob haircut, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Bleached Textured Crop",     "isolated hairstyle: men's bleached blonde textured crop haircut, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Dark Chocolate Braid",       "isolated hairstyle: dark chocolate brown single thick braid, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Rose Gold Curtain Bangs",    "isolated hairstyle: rose gold hair with curtain bangs, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Salt and Pepper Quiff",      "isolated hairstyle: men's salt and pepper quiff hairstyle, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Teal Blue Shag",             "isolated hairstyle: teal blue shag haircut with layers, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Caramel Balayage Long",      "isolated hairstyle: caramel balayage long wavy hair, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Burgundy Wolf Cut",          "isolated hairstyle: burgundy dark red wolf cut haircut, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Blonde Beach Waves",         "isolated hairstyle: natural blonde beach waves medium hair, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Navy Blue Mohawk",           "isolated hairstyle: navy blue mohawk hairstyle spiky, pure white background, no face, no body, only hair visible, photorealistic"),
    ("Classic Black Afro",         "isolated hairstyle: classic round black natural afro hair, pure white background, no face, no body, only hair visible, photorealistic"),
]

from rembg import remove as rembg_remove

generated = []
start_idx = len(kept) + 1

for i, (name, prompt) in enumerate(new_wigs_to_generate):
    idx = start_idx + i
    filename = f"gen-wig-{idx}.png"
    filepath = os.path.join(WIGS_DIR, filename)

    print(f"  Generating [{i+1}/{len(new_wigs_to_generate)}]: {name}...")

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
            print(f"    -> No image returned, skipping")
            continue

        raw_bytes = result.generated_images[0].image.image_bytes

        # Remove background with rembg
        print(f"    -> Removing background...")
        clean_bytes = rembg_remove(raw_bytes)
        img = Image.open(io.BytesIO(clean_bytes))

        img.save(filepath)
        print(f"    -> Saved: {filepath} | mode={img.mode}")

        generated.append({
            "id": f"gen-wig-{idx}",
            "src": f"/wigs_real/{filename}",
            "name": name
        })

    except Exception as e:
        print(f"    -> ERROR: {e}")

    time.sleep(1)

print(f"\nGenerated {len(generated)} new wigs")

# Combine and save
all_wigs = kept + generated
with open(WIGS_DATA_PATH, "w") as f:
    json.dump(all_wigs, f, indent=2)

print(f"\nDone! Total wigs in collection: {len(all_wigs)}")
print(f"  - Kept from audit: {len(kept)}")
print(f"  - Removed as bad: {len(removed)}")
print(f"  - Newly generated: {len(generated)}")
