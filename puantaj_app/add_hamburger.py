import os

templates_dir = r"C:\Users\rainwater\Desktop\puantaj\server\templates"
templates = ["alerts.html", "driver.html", "employee.html", 
             "reports.html", "report_detail.html", "vehicle.html"]

hamburger_button = '''        <button class="sidebar-toggle" id="sidebarToggle" aria-label="Menu">
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
        </button>
'''

for template_name in templates:
    filepath = os.path.join(templates_dir, template_name)
    if not os.path.exists(filepath):
        print(f"⚠ {template_name} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find: <div class="brand"> and add button after it
    if '<div class="brand">' in content and 'sidebar-toggle' not in content:
        content = content.replace(
            '<div class="brand">',
            '<div class="brand">\n' + hamburger_button
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {template_name} - added hamburger button")
    elif 'sidebar-toggle' in content:
        print(f"○ {template_name} - already has button")
    else:
        print(f"✗ {template_name} - no brand div found")

print("\nDone!")
