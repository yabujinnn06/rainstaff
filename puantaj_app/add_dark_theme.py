#!/usr/bin/env python3
"""Add dark-theme class to all templates - safe method that doesn't touch Jinja"""

import os
import re

TEMPLATES_DIR = r'C:\Users\rainwater\Desktop\puantaj\server\templates'

# Templates to update (exclude stock.html which already has modern design)
TEMPLATES = [
    'login.html',
    'dashboard.html',
    'alerts.html',
    'reports.html',
    'report_detail.html',
    'vehicle.html',
    'employee.html',
    'driver.html',
]

def add_dark_theme_class(filepath):
    """Add dark-theme class to body tag without touching Jinja code"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has dark-theme
    if 'dark-theme' in content:
        print(f"  SKIP: {os.path.basename(filepath)} - already has dark-theme")
        return False
    
    # Pattern to match body tag with existing class
    # <body class="admin"> -> <body class="admin dark-theme">
    pattern1 = r'<body\s+class="([^"]*)"'
    if re.search(pattern1, content):
        content = re.sub(pattern1, r'<body class="\1 dark-theme"', content)
        print(f"  OK: {os.path.basename(filepath)} - added to existing class")
    else:
        # Pattern to match body tag without class
        # <body> -> <body class="dark-theme">
        pattern2 = r'<body>'
        if re.search(pattern2, content):
            content = re.sub(pattern2, '<body class="dark-theme">', content)
            print(f"  OK: {os.path.basename(filepath)} - added new class")
        else:
            print(f"  WARN: {os.path.basename(filepath)} - no body tag found")
            return False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    print("Adding dark-theme class to templates...\n")
    
    updated = 0
    for template in TEMPLATES:
        filepath = os.path.join(TEMPLATES_DIR, template)
        if os.path.exists(filepath):
            if add_dark_theme_class(filepath):
                updated += 1
        else:
            print(f"  MISS: {template} - file not found")
    
    print(f"\n✓ Updated {updated}/{len(TEMPLATES)} templates")

if __name__ == '__main__':
    main()
