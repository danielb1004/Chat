import re

with open('src/index.css', 'r') as f:
    css = f.read()

replacements = {
    '#f3f8ee': '#eff6f0',
    '#dff3d6': '#d5ecd8',
    '#16330d': '#122616',
    '#f7faf5': '#f4f9f5',
    '#243022': '#1f2a22',
    '#1f7d08': '#1b5b27',
    '#f1fee9': '#eaf6ec',
    '#0e1e0a': '#0b1a0d',
    '#1e3c15': '#16361d'
}

for old, new in replacements.items():
    css = css.replace(old, new)

with open('src/index.css', 'w') as f:
    f.write(css)

print("Other greens updated successfully!")
