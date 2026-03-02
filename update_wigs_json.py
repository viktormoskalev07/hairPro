import json

# Load new categorized wigs
with open('components/categorized_wigs.json', 'r', encoding='utf-8') as f:
    categorized = json.load(f)

# Convert to the format expected by WigEditor, adding category field
new_data = []
for item in categorized:
    new_data.append({
        "id": item['name'].lower().replace(" ", "-"),
        "src": item['src'],
        "name": item['name'],
        "category": item['category'],
        "audit": {
            "ok": item.get('ok', True),
            "reason": item.get('reason', '')
        }
    })

# Load old wigs and assign them to "Other" category if not already there
try:
    with open('components/wigs_data.json', 'r', encoding='utf-8') as f:
        old_data = json.load(f)
        for item in old_data:
            # Check if already added (by src)
            if not any(d['src'] == item['src'] for d in new_data):
                item['category'] = "General"
                new_data.append(item)
except FileNotFoundError:
    pass

# Save merged data
with open('components/wigs_data.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, indent=2)

print(f"Merged {len(new_data)} wigs into components/wigs_data.json")
