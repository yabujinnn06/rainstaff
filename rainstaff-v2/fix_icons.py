import re

# Fix all icon references in all view files
import glob

for file in glob.glob('frontend/views/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'ft\.icons\.', 'ft.Icons.', content)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed icons in {file}")

print("All view files updated!")
