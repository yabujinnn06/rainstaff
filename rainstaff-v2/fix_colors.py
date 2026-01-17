import re

# Fix login.py
with open('frontend/views/login.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'ft\.colors\.', 'ft.Colors.', content)
with open('frontend/views/login.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Fix dashboard.py
with open('frontend/views/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'ft\.colors\.', 'ft.Colors.', content)
with open('frontend/views/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed colors in login.py and dashboard.py")
