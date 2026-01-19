# Rainstaff Pro Sidebar Integration Guide

## Overview
This guide explains how to integrate the responsive Pro Sidebar template into your Rainstaff Flask application.

## Files Created

1. **`server/templates/components/_sidebar.html`** - Sidebar component template
2. **`server/static/sidebar.css`** - Complete responsive CSS (4 breakpoints)
3. **`server/static/sidebar.js`** - JavaScript interactions
4. **`server/templates/base.html`** (modify) - Include sidebar in main layout

## Integration Steps

### Step 1: Update Base Template

In `server/templates/base.html`, modify the layout:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Rainstaff{% endblock %}</title>
    
    {# Core CSS #}
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    
    {# Sidebar CSS #}
    <link rel="stylesheet" href="{{ url_for('static', filename='sidebar.css') }}">
    
    {# Remix Icons (for menu icons) #}
    <link href="https://cdnjs.cloudflare.com/ajax/libs/remixicon/3.5.0/remixicon.min.css" rel="stylesheet">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% if current_user.is_authenticated %}
    <div class="layout has-sidebar fixed-sidebar fixed-header">
        {% include 'components/_sidebar.html' %}
        
        <div class="layout">
            <main class="content">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    {% else %}
    {# Login page - no sidebar #}
    {% block content %}{% endblock %}
    {% endif %}

    {# Sidebar JavaScript #}
    <script src="{{ url_for('static', filename='sidebar.js') }}"></script>
    
    {# Optional: Popper.js for advanced tooltip positioning (if needed) #}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/2.11.8/umd/popper.min.js"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Step 2: Update Dashboard Template

In `server/templates/dashboard.html` (or your main content template):

```html
{% extends 'base.html' %}

{% block content %}
<div class="dashboard-container">
    <h1>Hoş Geldiniz</h1>
    <p>Rainstaff Yönetim Paneline hoş geldiniz.</p>
    
    {# Your dashboard content here #}
</div>
{% endblock %}
```

### Step 3: Add Responsive Classes to CSS

Ensure your `style.css` includes responsive adjustments for the main content area:

```css
/* Main content responsive adjustments */
.layout.has-sidebar {
    display: flex;
}

.layout.has-sidebar .content {
    flex: 1;
    overflow-y: auto;
}

@media (max-width: 768px) {
    .layout.has-sidebar {
        flex-direction: column;
    }
    
    .layout.has-sidebar .content {
        margin-top: 60px;
    }
}
```

## Features

### Desktop (> 768px)
- Full sidebar visible (260px width)
- Collapse button to minimize sidebar (60px width)
- Smooth slide animations for submenus
- Hover effects on menu items

### Tablet (768px - 900px)
- Slightly narrower sidebar (240px)
- All collapse functionality preserved

### Mobile (< 768px)
- Sidebar slides from left (hidden by default)
- Hamburger toggle button (top-right)
- Click overlay to close sidebar
- Full-width content area
- Touch-friendly menu items

### Extra Small (< 360px)
- Optimized spacing and font sizes
- Maintains full functionality

## Customization

### Change Sidebar Width
In `sidebar.css`, modify the CSS variable:

```css
:root {
    --sidebar-width: 260px;  /* Change this value */
}
```

### Change Colors
In `sidebar.css`, update color variables:

```css
:root {
    --text-color: #7d84ab;
    --secondary-text-color: #dee2ec;
    --bg-color: #0c1e35;
    --accent-color: #00829f;
    --logo-bg: #ff8100;
}
```

### Add Menu Items
In `_sidebar.html`, add new menu items following the structure:

```html
<li class="menu-item sub-menu">
    <a href="#">
        <span class="menu-icon">
            <i class="ri-icon-name"></i>
        </span>
        <span class="menu-title">Menu Name</span>
    </a>
    <div class="sub-menu-list">
        <ul>
            <li class="menu-item">
                <a href="{{ url_for('route_name') }}">
                    <span class="menu-title">Submenu Item</span>
                </a>
            </li>
        </ul>
    </div>
</li>
```

### Icons
Uses Remix Icon library: https://remixicon.com/

Available icons:
- `ri-dashboard-line` - Dashboard
- `ri-user-line` - Users/Personnel
- `ri-time-line` - Timesheets
- `ri-truck-line` - Vehicles
- `ri-settings-line` - Settings
- `ri-logout-box-line` - Logout

## JavaScript API

The sidebar is automatically initialized when the page loads. Access it via:

```javascript
// Close sidebar programmatically
window.rainstaffSidebar.closeSidebar();

// Set active menu item
window.rainstaffSidebar.setActiveMenu('/dashboard');

// Toggle collapse
window.rainstaffSidebar.toggleCollapse();

// Toggle mobile sidebar
window.rainstaffSidebar.toggleSidebar();
```

## Browser Compatibility

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Notes

- CSS animations use `transform` and `opacity` for smooth GPU acceleration
- JavaScript uses event delegation for efficiency
- Media queries are mobile-first (progressive enhancement)
- No external dependencies required (Remix Icons are optional, can use Font Awesome instead)

## Troubleshooting

### Sidebar appears behind content
Ensure `.layout.has-sidebar` uses `display: flex` and sidebar has appropriate `z-index`.

### Menu items not responsive
Check that `sidebar.js` is loaded after DOM is ready (placed before `</body>`).

### Icons not showing
Verify Remix Icons CDN link is included in `<head>` section.

### Sidebar not toggling on mobile
Check browser console for JavaScript errors. Ensure `btn-toggle` element ID exists.

## Migration Checklist

- [ ] Copy `_sidebar.html` to `server/templates/components/`
- [ ] Copy `sidebar.css` to `server/static/`
- [ ] Copy `sidebar.js` to `server/static/`
- [ ] Update `base.html` with sidebar includes
- [ ] Add Remix Icons CDN link
- [ ] Update Flask route names in sidebar menu links
- [ ] Test on desktop (1920px, 1200px)
- [ ] Test on tablet (768px, 900px)
- [ ] Test on mobile (375px, 480px)
- [ ] Test on very small screens (360px)
- [ ] Verify menu collapse/expand works
- [ ] Verify mobile toggle works
- [ ] Check active menu highlighting

## Support

For issues or customizations, refer to the original Pro Sidebar repository:
https://github.com/azouaoui-med/pro-sidebar-template

---

**Last Updated:** January 19, 2026
**Rainstaff Version:** 1.0
