import os
import re

templates_dir = r"C:\Users\rainwater\Desktop\puantaj\server\templates"
templates = ["alerts.html", "dashboard.html", "driver.html", "employee.html", 
             "reports.html", "report_detail.html", "stock.html", "vehicle.html"]

script_tag = '    <script src="{{ url_for(\'static\', filename=\'app.js\') }}"></script>\n'

for template_name in templates:
    filepath = os.path.join(templates_dir, template_name)
    if not os.path.exists(filepath):
        print(f"Skipping {template_name} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if script is already added
    if "app.js" in content:
        print(f"✓ {template_name} - already has app.js")
        continue
    
    # Add script before </body>
    if '</body>' in content:
        # Try different indentation patterns
        if '    </body>' in content:
            content = content.replace('    </body>', f'{script_tag}    </body>')
        elif '  </body>' in content:
            script_tag_2space = '  <script src="{{ url_for(\'static\', filename=\'app.js\') }}"></script>\n'
            content = content.replace('  </body>', f'{script_tag_2space}  </body>')
        else:
            content = content.replace('</body>', f'{script_tag}</body>')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {template_name} - added app.js")
    else:
        print(f"✗ {template_name} - no </body> tag found")

print("\nDone!")
