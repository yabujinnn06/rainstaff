import os

templates_dir = r"C:\Users\rainwater\Desktop\puantaj\server\templates"
templates = ["alerts.html", "driver.html", "employee.html", 
             "reports.html", "report_detail.html", "vehicle.html"]

backdrop_div = '    <div class="backdrop" id="sidebarBackdrop"></div>\n\n'

for template_name in templates:
    filepath = os.path.join(templates_dir, template_name)
    if not os.path.exists(filepath):
        print(f"⚠ {template_name} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add after </header> if not exists
    if 'sidebarBackdrop' not in content and '</header>' in content:
        content = content.replace('</header>', '</header>\n' + backdrop_div)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {template_name} - added backdrop")
    elif 'sidebarBackdrop' in content:
        print(f"○ {template_name} - already has backdrop")
    else:
        print(f"✗ {template_name} - no header found")

print("\nDone!")
