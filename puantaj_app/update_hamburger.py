import os
import re

templates_dir = r"C:\Users\rainwater\Desktop\puantaj\server\templates"
templates = ["alerts.html", "driver.html", "employee.html", 
             "reports.html", "report_detail.html", "vehicle.html"]

old_button = '<button class="sidebar-toggle" id="sidebarToggle" aria-label="Menu">Menu</button>'
new_button = '''<button class="sidebar-toggle" id="sidebarToggle" aria-label="Menu">
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
        </button>'''

for template_name in templates:
    filepath = os.path.join(templates_dir, template_name)
    if not os.path.exists(filepath):
        print(f"⚠ {template_name} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old_button in content:
        content = content.replace(old_button, new_button)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {template_name} - updated hamburger icon")
    else:
        print(f"○ {template_name} - no menu button found")

print("\nDone!")
