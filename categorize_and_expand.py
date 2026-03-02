"""
Pipeline:
  1. Классифицировать существующие парики по профессиональным категориям парикмахеров
  2. Генерировать новые парики для каждой категории (Imagen 4.0)
  3. Собрать HTML-превью со всеми картинками
  4. Отправить каждую картинку в Gemini Vision — проверить качество
  5. Удалить плохие, сохранить wigs_data.json с полем category
"""

import os, sys, json, time, re, io, base64
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
WIGS_DIR   = "public/wigs_real"
DATA_FILE  = "components/wigs_data.json"
HTML_FILE  = "public/wig_preview.html"

# ─────────────────────────────────────────────────────────────────────
# ПРОФЕССИОНАЛЬНЫЕ КАТЕГОРИИ (классификация парикмахеров)
# ─────────────────────────────────────────────────────────────────────
CATEGORIES = {
    "women-classic": {
        "label": "Женские · Классика",
        "desc":  "Боб, лоб, каре, прямые — вечная классика",
        "keywords": ["bob","lob","straight","classic","blunt","fringe","sleek","sassoon"],
        "generate": [
            ("Classic A-Line Bob",    "isolated hairstyle only: classic A-line bob haircut, dark brown hair, angled longer in front, white background, no face, photorealistic"),
            ("Sleek Lob",             "isolated hairstyle only: sleek straight lob shoulder length hair, warm brunette, white background, no face, photorealistic"),
            ("Blunt Cut Bob",         "isolated hairstyle only: blunt cut chin-length bob, jet black hair, white background, no face, photorealistic"),
            ("French Crop Bob",       "isolated hairstyle only: French crop bob with wispy fringe, ash blonde, white background, no face, photorealistic"),
            ("Italian Bob",           "isolated hairstyle only: voluminous Italian bob, chestnut hair, slight inward curl, white background, no face, photorealistic"),
        ],
    },
    "women-long": {
        "label": "Женские · Длинные",
        "desc":  "Длинные локоны, слои, каскад",
        "keywords": ["long","wavy","cascade","layers","flowing","balayage","ombre"],
        "generate": [
            ("Cascading Layers",      "isolated hairstyle only: long cascading layers hair, honey blonde, flowing, white background, no face, photorealistic"),
            ("Mermaid Waves",         "isolated hairstyle only: long mermaid waves hair, dark auburn, glossy, white background, no face, photorealistic"),
            ("Straight Silk",         "isolated hairstyle only: very long straight silky hair, jet black, white background, no face, photorealistic"),
            ("Balayage Curtains",     "isolated hairstyle only: long hair with curtain bangs and caramel balayage, white background, no face, photorealistic"),
        ],
    },
    "women-curly": {
        "label": "Женские · Кудри и волны",
        "desc":  "Кудрявые, волнистые, пружинистые",
        "keywords": ["curl","curly","wave","ringlet","coil","frizz","bouncy"],
        "generate": [
            ("Tight Ringlets",        "isolated hairstyle only: tight springy ringlet curls, natural black hair, white background, no face, photorealistic"),
            ("Loose Beach Curls",     "isolated hairstyle only: loose beachy curls, golden blonde, white background, no face, photorealistic"),
            ("Coily Natural",         "isolated hairstyle only: natural 4C coily hair, dark brown, voluminous, white background, no face, photorealistic"),
            ("Romantic Waves",        "isolated hairstyle only: romantic soft waves, chestnut, white background, no face, photorealistic"),
        ],
    },
    "women-short": {
        "label": "Женские · Короткие",
        "desc":  "Пикси, стрижки под мальчика, шапочка",
        "keywords": ["pixie","short","crop","buzz","undercut","mushroom"],
        "generate": [
            ("Textured Pixie",        "isolated hairstyle only: textured pixie cut, brunette with highlights, white background, no face, photorealistic"),
            ("Sleek Pixie",           "isolated hairstyle only: sleek glossy pixie cut, platinum blonde, white background, no face, photorealistic"),
            ("Undercut Pixie",        "isolated hairstyle only: pixie cut with side undercut, copper red hair, white background, no face, photorealistic"),
            ("Mushroom Cut",          "isolated hairstyle only: rounded mushroom bowl cut, dark brunette, white background, no face, photorealistic"),
        ],
    },
    "women-updo": {
        "label": "Женские · Причёски вверх",
        "desc":  "Пучки, плетения, косы, updo",
        "keywords": ["bun","updo","braid","braided","knot","ponytail","chignon"],
        "generate": [
            ("French Twist",          "isolated hairstyle only: elegant French twist updo, dark brunette, white background, no face, photorealistic"),
            ("Low Chignon",           "isolated hairstyle only: low chignon bun with loose strands, ash brown, white background, no face, photorealistic"),
            ("Fishtail Braid",        "isolated hairstyle only: long fishtail braid, honey blonde, white background, no face, photorealistic"),
            ("Dutch Crown Braid",     "isolated hairstyle only: Dutch crown braid, auburn, white background, no face, photorealistic"),
        ],
    },
    "women-colored": {
        "label": "Женские · Цветные",
        "desc":  "Яркие цвета, фантазийные оттенки",
        "keywords": ["neon","pink","blue","purple","teal","rainbow","ombre","pastel","rose gold","lavender","emerald"],
        "generate": [
            ("Cotton Candy Pink",     "isolated hairstyle only: cotton candy pastel pink long wavy hair, white background, no face, photorealistic"),
            ("Sapphire Blue Bob",     "isolated hairstyle only: vivid sapphire blue bob cut, white background, no face, photorealistic"),
            ("Purple Haze Long",      "isolated hairstyle only: deep purple violet long straight hair, white background, no face, photorealistic"),
            ("Sunset Ombre",          "isolated hairstyle only: sunset orange to pink ombre long hair, white background, no face, photorealistic"),
        ],
    },
    "men-classic": {
        "label": "Мужские · Классика",
        "desc":  "Зачёс, пробор, помпадур, боксёрская",
        "keywords": ["pompadour","quiff","side part","classic","slick","executive","crew","box"],
        "generate": [
            ("Hard Part Quiff",       "isolated men's hairstyle only: hard side part quiff, dark brown hair, white background, no face, photorealistic"),
            ("Classic Pompadour",     "isolated men's hairstyle only: classic pompadour hairstyle, black hair, glossy, white background, no face, photorealistic"),
            ("Ivy League Cut",        "isolated men's hairstyle only: ivy league preppy haircut, sandy blonde, white background, no face, photorealistic"),
            ("Slick Back",            "isolated men's hairstyle only: slicked back hair with medium fade, dark brunette, white background, no face, photorealistic"),
            ("Crew Cut",              "isolated men's hairstyle only: military crew cut, dark hair, white background, no face, photorealistic"),
        ],
    },
    "men-fade": {
        "label": "Мужские · Фейды и андеркаты",
        "desc":  "Skin fade, mid fade, undercut, taper",
        "keywords": ["fade","undercut","taper","high fade","mid fade","skin fade"],
        "generate": [
            ("Skin Fade Mohawk",      "isolated men's hairstyle only: skin fade with mohawk strip on top, dark hair, white background, no face, photorealistic"),
            ("High Fade Comb Over",   "isolated men's hairstyle only: high fade comb over, brunette, white background, no face, photorealistic"),
            ("Mid Fade Crop",         "isolated men's hairstyle only: mid fade textured crop, light brown hair, white background, no face, photorealistic"),
            ("Undercut Disconnected", "isolated men's hairstyle only: disconnected undercut, black hair on top, white background, no face, photorealistic"),
            ("Taper Fade Low",        "isolated men's hairstyle only: low taper fade clean cut, brown hair, white background, no face, photorealistic"),
        ],
    },
    "men-textured": {
        "label": "Мужские · Текстурные",
        "desc":  "Вольф-кат, шэг, мессенджер, кёрлы",
        "keywords": ["textured","wolf","shag","messy","curly","wavy","mullet"],
        "generate": [
            ("Wolf Cut Men",          "isolated men's hairstyle only: wolf cut shaggy layers, dark brunette, white background, no face, photorealistic"),
            ("Curly Top Fade",        "isolated men's hairstyle only: curly hair on top with low fade, natural black, white background, no face, photorealistic"),
            ("Messy Fringe",          "isolated men's hairstyle only: messy textured fringe forward, light brown, white background, no face, photorealistic"),
            ("Wavy Surfer Hair",      "isolated men's hairstyle only: wavy surfer style medium hair, dirty blonde, white background, no face, photorealistic"),
        ],
    },
    "men-long": {
        "label": "Мужские · Длинные",
        "desc":  "Длинные мужские: манбун, хвост, распущенные",
        "keywords": ["man bun","man-bun","long","ponytail","viking","braid","dread"],
        "generate": [
            ("Man Bun Undercut",      "isolated men's hairstyle only: man bun with shaved sides undercut, dark hair, white background, no face, photorealistic"),
            ("Long Flowing Men",      "isolated men's hairstyle only: long straight flowing men's hair, dark brown, white background, no face, photorealistic"),
            ("Half Up Man Bun",       "isolated men's hairstyle only: half up half down man bun, brunette, white background, no face, photorealistic"),
            ("Norse Braid",           "isolated men's hairstyle only: Norse Viking warrior braids, dirty blonde, white background, no face, photorealistic"),
        ],
    },
    "unisex-natural": {
        "label": "Унисекс · Натуральные",
        "desc":  "Афро, локи, натуральные текстуры",
        "keywords": ["afro","dread","dreads","locs","natural","coil","twist"],
        "generate": [
            ("Big Afro",              "isolated hairstyle only: large round natural afro, dark black hair, white background, no face, photorealistic"),
            ("Freeform Locs",         "isolated hairstyle only: freeform dreadlocks medium length, dark brown, white background, no face, photorealistic"),
            ("Twist Out",             "isolated hairstyle only: defined twist out natural hair, medium length, dark, white background, no face, photorealistic"),
        ],
    },
    "unisex-alternative": {
        "label": "Унисекс · Альтернатива",
        "desc":  "Ирокез, цветные, экспериментальные",
        "keywords": ["mohawk","rainbow","neon","shaved","punk","alt","alternative","buzz","geometric"],
        "generate": [
            ("Liberty Spikes",        "isolated hairstyle only: liberty spikes punk mohawk, bleached white hair, white background, no face, photorealistic"),
            ("Geometric Color Block", "isolated hairstyle only: geometric color block haircut, half black half white, white background, no face, photorealistic"),
            ("Neon Buzz Cut",         "isolated hairstyle only: neon green buzz cut, very short, white background, no face, photorealistic"),
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────
# STEP 1: Классифицировать существующие парики
# ─────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Классификация существующих париков")
print("=" * 60)

with open(DATA_FILE) as f:
    existing = json.load(f)

def classify_wig(name: str) -> str:
    name_l = name.lower()
    for cat_id, cat in CATEGORIES.items():
        for kw in cat["keywords"]:
            if kw in name_l:
                return cat_id
    # Эвристика по полу/длине
    if any(w in name_l for w in ["blonde","long","curl","wave","bun","braid","rose","lavender","pink","updo","lob","bob","pixie","ombre","balayage","highlight"]):
        return "women-classic"
    if any(w in name_l for w in ["fade","undercut","pompadour","quiff","crop","taper","crew"]):
        return "men-fade"
    if any(w in name_l for w in ["dread","afro","coil","loc"]):
        return "unisex-natural"
    return "women-classic"  # fallback

for w in existing:
    if "category" not in w:
        w["category"] = classify_wig(w["name"])
    print(f"  {w['category']:25s} | {w['name']}")

print(f"\n{len(existing)} париков классифицированы")

# ─────────────────────────────────────────────────────────────────────
# STEP 2: Генерация новых париков по категориям
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Генерация новых париков через Imagen 4.0")
print("=" * 60)

from rembg import remove as rembg_remove

existing_names = {w["name"] for w in existing}
new_wigs = []
gen_idx = max((int(re.sub(r"[^0-9]", "", w["id"])) for w in existing if re.sub(r"[^0-9]", "", w["id"])), default=49)

for cat_id, cat in CATEGORIES.items():
    for name, prompt in cat["generate"]:
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

print(f"\nСгенерировано {len(new_wigs)} новых париков")

# Объединяем
all_wigs = existing + new_wigs

# ─────────────────────────────────────────────────────────────────────
# STEP 3: HTML превью
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Создание HTML превью")
print("=" * 60)

# Группируем по категории
from collections import defaultdict
by_cat = defaultdict(list)
for w in all_wigs:
    by_cat[w.get("category", "?")].append(w)

html_parts = ["""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Wig Preview — все категории</title>
<style>
  body { font-family: system-ui, sans-serif; background: #111; color: #eee; padding: 20px; }
  h1   { color: #a78bfa; }
  h2   { color: #818cf8; margin-top: 40px; border-bottom: 1px solid #333; padding-bottom: 8px; }
  .desc { color: #6b7280; font-size: 13px; margin: 4px 0 16px; }
  .grid { display: flex; flex-wrap: wrap; gap: 12px; }
  .card { background: #1f2937; border-radius: 12px; padding: 8px; width: 160px; text-align: center; }
  .card img { width: 144px; height: 144px; object-fit: contain; border-radius: 8px; background: #fff; }
  .card p { font-size: 11px; margin: 6px 0 2px; color: #d1d5db; }
  .card small { font-size: 10px; color: #6b7280; }
  .ok  { border: 2px solid #22c55e; }
  .bad { border: 2px solid #ef4444; opacity: 0.5; }
  .unk { border: 2px solid #374151; }
</style>
</head>
<body>
<h1>HairStudio Pro — Превью всех париков по категориям</h1>
"""]

for cat_id, cat_info in CATEGORIES.items():
    wigs_in_cat = by_cat.get(cat_id, [])
    if not wigs_in_cat:
        continue
    html_parts.append(f'<h2>{cat_info["label"]} <span style="font-size:14px;color:#6b7280">({len(wigs_in_cat)} шт.)</span></h2>')
    html_parts.append(f'<p class="desc">{cat_info["desc"]}</p>')
    html_parts.append('<div class="grid">')
    for w in wigs_in_cat:
        path = "public" + w["src"]
        exists = os.path.exists(path)
        css = "unk" if exists else "bad"
        html_parts.append(f'''
  <div class="card {css}" id="{w["id"]}">
    <img src="{w["src"]}" alt="{w["name"]}" loading="lazy">
    <p>{w["name"]}</p>
    <small>{w["id"]}</small>
  </div>''')
    html_parts.append('</div>')

# Некатегоризированные
uncategorized = [w for w in all_wigs if w.get("category") not in CATEGORIES]
if uncategorized:
    html_parts.append(f'<h2>Без категории ({len(uncategorized)})</h2><div class="grid">')
    for w in uncategorized:
        html_parts.append(f'<div class="card unk"><img src="{w["src"]}"><p>{w["name"]}</p></div>')
    html_parts.append('</div>')

html_parts.append("</body></html>")

html = "\n".join(html_parts)
with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML сохранён: {HTML_FILE}  ({len(all_wigs)} париков)")

# ─────────────────────────────────────────────────────────────────────
# STEP 4: Аудит каждого изображения через Gemini Vision
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Аудит изображений через Gemini 2.5 Flash Vision")
print("=" * 60)

AUDIT_PROMPT = """Посмотри на это изображение. Ответь ТОЛЬКО JSON: {"ok": true/false, "reason": "..."}

Это должен быть ПАРИК / ПРИЧЁСКА для приложения виртуальной примерки.
ok=true если:
- Видны ТОЛЬКО волосы / причёска, изолированные на белом или прозрачном фоне
- НЕТ человеческого лица, тела, текста, водяных знаков, логотипов
- Причёска чётко узнаваема и выглядит профессионально

ok=false если есть лицо, тело, водяной знак, текст, случайное фото, пустое изображение."""

kept, removed = [], []

for w in all_wigs:
    path = "public" + w["src"]
    if not os.path.exists(path):
        print(f"  [MISS ] {w['name']}")
        removed.append(w)
        continue

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
        ok = result.get("ok", False)

        status = "OK  " if ok else "BAD "
        print(f"  [{status}] {w.get('category','?'):20s} | {w['name']:35s} | {result.get('reason','')[:60]}")

        if ok:
            kept.append(w)
        else:
            removed.append(w)
            try: os.remove(path)
            except: pass

    except Exception as e:
        print(f"  [ERR ] {w['name']:35s} | {e}")
        kept.append(w)

    time.sleep(0.3)

print(f"\nАудит: {len(kept)} ОК, {len(removed)} удалено")

# ─────────────────────────────────────────────────────────────────────
# STEP 5: Обновить HTML с результатами аудита
# ─────────────────────────────────────────────────────────────────────
kept_ids = {w["id"] for w in kept}
html_final = html
for w in removed:
    html_final = html_final.replace(f'id="{w["id"]}"', f'id="{w["id"]}" data-removed="1"')
    html_final = html_final.replace(f'class="card unk" id="{w["id"]}"', f'class="card bad" id="{w["id"]}"')
    html_final = html_final.replace(f'class="card ok" id="{w["id"]}"',  f'class="card bad" id="{w["id"]}"')

# Пометим прошедшие аудит
for w in kept:
    html_final = html_final.replace(f'class="card unk" id="{w["id"]}"', f'class="card ok" id="{w["id"]}"')

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(html_final)

# ─────────────────────────────────────────────────────────────────────
# STEP 6: Сохранить финальный wigs_data.json
# ─────────────────────────────────────────────────────────────────────
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(kept, f, indent=2, ensure_ascii=False)

print(f"\n✓ wigs_data.json обновлён: {len(kept)} париков в {len(CATEGORIES)} категориях")
print(f"✓ HTML превью: {HTML_FILE}")

# Статистика по категориям
by_cat_final = defaultdict(list)
for w in kept:
    by_cat_final[w.get("category","?")].append(w)

print("\nСтатистика по категориям:")
for cat_id, cat_info in CATEGORIES.items():
    n = len(by_cat_final.get(cat_id, []))
    print(f"  {cat_info['label']:35s} {n:3d} шт.")
