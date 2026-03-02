"""
1. Аудит всех существующих париков — удалить те, где видно лицо или вид сзади
2. Сгенерировать 40 новых мужских париков (вид спереди, только волосы)
3. Аудит новых
4. Сохранить wigs_data.json
"""

import os, sys, json, time, re, io
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv('../.env')
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: No GEMINI_API_KEY"); sys.exit(1)

client = genai.Client(api_key=API_KEY)
WIGS_DIR  = "public/wigs_real"
DATA_FILE = "components/wigs_data.json"

# ─────────────────────────────────────────────────────────────────────
# AUDIT PROMPT (strict: no face, no back view)
# ─────────────────────────────────────────────────────────────────────
AUDIT_PROMPT = """Look at this image. Answer ONLY with JSON: {"ok": true/false, "reason": "..."}

This must be a HAIRSTYLE image for a virtual try-on overlay app.
ok=true ONLY if ALL conditions are met:
- Shows ONLY hair / hairstyle shape, isolated on white or transparent background
- NO human face, eyes, nose, mouth visible
- NOT a back/rear view of the head - must be front-facing or 3/4 view
- NO body, neck skin, ears clearly visible
- NO text, watermarks, logos
- Hairstyle is clearly recognizable and professionally rendered

ok=false if: face is visible, it's a back view, has watermarks, random photo, empty image, or shows significant body parts."""

def audit_image(path: str) -> tuple[bool, str]:
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail((512, 512), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                AUDIT_PROMPT,
            ]
        )
        raw = resp.text.strip()
        m = re.search(r'\{.*?\}', raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"ok": False, "reason": raw[:80]}
        return result.get("ok", False), result.get("reason", "")[:80]
    except Exception as e:
        return True, f"audit error: {e}"  # keep on error

# ─────────────────────────────────────────────────────────────────────
# STEP 1: Re-audit all existing wigs (strict: remove faces & back views)
# ─────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Строгий аудит существующих париков")
print("=" * 60)

with open(DATA_FILE, encoding="utf-8") as f:
    wigs = json.load(f)

kept, removed = [], []
for w in wigs:
    path = "public" + w["src"]
    if not os.path.exists(path):
        print(f"  [MISS ] {w['name']}")
        removed.append(w)
        continue
    ok, reason = audit_image(path)
    status = "OK  " if ok else "BAD "
    print(f"  [{status}] {w.get('category','?'):20s} | {w['name']:35s} | {reason}")
    if ok:
        kept.append(w)
    else:
        removed.append(w)
        try: os.remove(path)
        except: pass
    time.sleep(0.5)

print(f"\nАудит: {len(kept)} OK, {len(removed)} удалено")

# ─────────────────────────────────────────────────────────────────────
# STEP 2: Генерация 40 новых мужских париков (только волосы, вид спереди)
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Генерация 40 новых мужских париков")
print("=" * 60)

from rembg import remove as rembg_remove

# Промпты специально для мужских, вид спереди, только форма волос
MEN_PROMPTS = [
    # men-classic (10)
    ("Classic Pompadour",       "men-classic",   "isolated men hairstyle, front facing view, classic pompadour with volume on top, dark hair, clean white background, no face, hair shape only, studio photo"),
    ("Hard Side Part",          "men-classic",   "isolated men hairstyle, front facing view, hard side part with slick finish, brunette, white background, no face, hair shape only, photorealistic"),
    ("Ivy League Preppy",       "men-classic",   "isolated men hairstyle, front facing view, ivy league preppy haircut, sandy brown hair, white background, no face, hair shape only"),
    ("Slick Back Dark",         "men-classic",   "isolated men hairstyle, front facing view, slicked back hair, jet black, glossy finish, white background, no face, hair silhouette only"),
    ("Classic Quiff",           "men-classic",   "isolated men hairstyle, front facing view, classic quiff hairstyle, light brown hair, white background, no face, hair shape only"),
    ("Military Crew Cut",       "men-classic",   "isolated men hairstyle, front facing view, military crew cut very short hair, dark brown, white background, no face, hair shape only"),
    ("Business Cut Short",      "men-classic",   "isolated men hairstyle, front facing view, neat business side part cut, medium brown, white background, no face, hair only"),
    ("Retro Pompadour",         "men-classic",   "isolated men hairstyle, front facing view, retro 50s pompadour, jet black hair, white background, no face, hair shape only"),
    ("Executive Contour",       "men-classic",   "isolated men hairstyle, front facing view, executive contour cut, salt and pepper hair, white background, no face, hair only"),
    ("Classic Comb Over",       "men-classic",   "isolated men hairstyle, front facing view, classic comb over, dark hair, white background, no face, hair silhouette only"),
    # men-fade (10)
    ("High Fade Flat Top",      "men-fade",      "isolated men hairstyle, front facing view, high fade with flat top, dark hair, white background, no face, hair shape only, photorealistic"),
    ("Mid Fade Quiff",          "men-fade",      "isolated men hairstyle, front facing view, mid fade with quiff on top, brunette, white background, no face, hair shape only"),
    ("Low Taper Fade",          "men-fade",      "isolated men hairstyle, front facing view, low taper fade clean cut, dark brown hair, white background, no face, hair only"),
    ("Bald Fade Comb Over",     "men-fade",      "isolated men hairstyle, front facing view, bald skin fade with comb over top, black hair, white background, no face, hair only"),
    ("Temp Fade Edgar",         "men-fade",      "isolated men hairstyle, front facing view, temp fade edgar cut straight fringe, dark hair, white background, no face, hair shape"),
    ("Drop Fade Waves",         "men-fade",      "isolated men hairstyle, front facing view, drop fade with 360 waves on top, black hair, white background, no face, hair only"),
    ("High Fade Spiky",         "men-fade",      "isolated men hairstyle, front facing view, high fade with spiky textured top, brown hair, white background, no face, hair shape only"),
    ("Burst Fade Mohawk",       "men-fade",      "isolated men hairstyle, front facing view, burst fade with mohawk strip, dark hair, white background, no face, hair shape"),
    ("Shadow Fade Curls",       "men-fade",      "isolated men hairstyle, front facing view, shadow fade with curly top, natural black hair, white background, no face, hair only"),
    ("Skin Fade Pompadour",     "men-fade",      "isolated men hairstyle, front facing view, skin fade with pompadour top, brunette, white background, no face, hair shape only"),
    # men-textured (10)
    ("Shaggy Wolf Cut",         "men-textured",  "isolated men hairstyle, front facing view, shaggy wolf cut with curtain bangs, dark brunette, white background, no face, hair shape only"),
    ("Messy Textured Crop",     "men-textured",  "isolated men hairstyle, front facing view, messy textured crop top, light brown, white background, no face, hair only"),
    ("Curly Fringe Men",        "men-textured",  "isolated men hairstyle, front facing view, curly fringe medium length, dark brown, white background, no face, hair shape"),
    ("Tousled Bedhead",         "men-textured",  "isolated men hairstyle, front facing view, tousled bedhead textured look, dirty blonde, white background, no face, hair only"),
    ("French Crop Textured",    "men-textured",  "isolated men hairstyle, front facing view, French crop with textured top, brunette, white background, no face, hair shape only"),
    ("Surfer Shag",             "men-textured",  "isolated men hairstyle, front facing view, surfer shag medium wavy hair, golden blonde, white background, no face, hair only"),
    ("Curly Edgar Cut",         "men-textured",  "isolated men hairstyle, front facing view, curly hair edgar blunt fringe, black hair, white background, no face, hair shape"),
    ("Wavy Curtain Bangs Men",  "men-textured",  "isolated men hairstyle, front facing view, wavy curtain bangs medium, light brown, white background, no face, hair silhouette"),
    ("Afro Textured Fade",      "men-textured",  "isolated men hairstyle, front facing view, afro textured hair with fade, natural dark, white background, no face, hair only"),
    ("Modern Mullet Shag",      "men-textured",  "isolated men hairstyle, front facing view, modern mullet shaggy layers, brunette, white background, no face, hair shape"),
    # men-long (10)
    ("Long Straight Men",       "men-long",      "isolated men hairstyle, front facing view, long straight hair shoulder length, dark brunette, white background, no face, hair shape only"),
    ("Curtain Hair Long",       "men-long",      "isolated men hairstyle, front facing view, long curtain hair center parted, brown, white background, no face, hair only"),
    ("Man Bun Top Knot",        "men-long",      "isolated men hairstyle, front facing view, man bun top knot pulled up, dark hair, white background, no face, hair shape"),
    ("Viking Long Wavy",        "men-long",      "isolated men hairstyle, front facing view, viking warrior long wavy hair, dirty blonde, white background, no face, hair only"),
    ("Samurai Knot",            "men-long",      "isolated men hairstyle, front facing view, samurai top knot bun, jet black hair, white background, no face, hair shape"),
    ("Rock Long Layers",        "men-long",      "isolated men hairstyle, front facing view, long layered rock hair, dark brunette, white background, no face, hair silhouette"),
    ("Ponytail Low Men",        "men-long",      "isolated men hairstyle, front facing view, low ponytail men's hair, brown, white background, no face, hair only"),
    ("Half Up Long Men",        "men-long",      "isolated men hairstyle, front facing view, half up bun long flowing hair, brunette, white background, no face, hair shape"),
    ("Wavy Shoulder Curtains",  "men-long",      "isolated men hairstyle, front facing view, wavy shoulder length curtain hair, auburn, white background, no face, hair only"),
    ("Dreadlocks Mid Men",      "men-long",      "isolated men hairstyle, front facing view, medium dreadlocks shoulder length, dark brown, white background, no face, hair shape"),
]

existing_names = {w["name"] for w in kept}
gen_idx = max(
    (int(re.sub(r"[^0-9]", "", w["id"])) for w in (kept + removed) if re.sub(r"[^0-9]", "", w["id"])),
    default=97
)

new_wigs = []
for name, cat_id, prompt in MEN_PROMPTS:
    if name in existing_names:
        print(f"  [SKIP] {name} (уже есть)")
        continue

    gen_idx += 1
    filename = f"cat-wig-{gen_idx}.png"
    filepath = os.path.join(WIGS_DIR, filename)

    print(f"  [{cat_id}] Генерирую: {name} ...")
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
            print("    -> пустой ответ, пропускаю")
            continue

        raw = result.generated_images[0].image.image_bytes
        clean = rembg_remove(raw)
        Image.open(io.BytesIO(clean)).save(filepath)

        new_wigs.append({
            "id": f"cat-wig-{gen_idx}",
            "src": f"/wigs_real/{filename}",
            "name": name,
            "category": cat_id,
        })
        print(f"    -> OK: {filepath}")
    except Exception as e:
        print(f"    -> ERROR: {e}")
    time.sleep(1.0)

print(f"\nСгенерировано {len(new_wigs)} новых мужских париков")

# ─────────────────────────────────────────────────────────────────────
# STEP 3: Аудит новых
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Аудит новых мужских париков")
print("=" * 60)

audited_new = []
for w in new_wigs:
    path = "public" + w["src"]
    ok, reason = audit_image(path)
    status = "OK  " if ok else "BAD "
    print(f"  [{status}] {w['name']:35s} | {reason}")
    if ok:
        audited_new.append(w)
    else:
        try: os.remove(path)
        except: pass
    time.sleep(0.5)

print(f"\nНовых прошло аудит: {len(audited_new)} из {len(new_wigs)}")

# ─────────────────────────────────────────────────────────────────────
# STEP 4: Сохранить wigs_data.json
# ─────────────────────────────────────────────────────────────────────
final = kept + audited_new

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(final, f, indent=2, ensure_ascii=False)

print(f"\nwigs_data.json сохранён: {len(final)} париков")

from collections import Counter
print("\nСтатистика по категориям:")
for cat, n in sorted(Counter(w.get("category","?") for w in final).items()):
    print(f"  {cat:30s}  {n:3d}")
