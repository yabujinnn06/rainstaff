#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update server templates with modern ERP design"""

import os

base = r'C:\Users\rainwater\Desktop\puantaj\server\templates'

CSS_BASE = """<style>
:root{--primary:#3b82f6;--accent:#06b6d4;--success:#10b981;--warning:#f59e0b;--danger:#ef4444;--bg-dark:#0f172a;--bg-card:#1e293b;--bg-hover:#334155;--text-primary:#f1f5f9;--text-secondary:#94a3b8;--border-color:#334155}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg-dark);color:var(--text-primary);min-height:100vh}
.header{background:var(--bg-card);padding:12px 20px;border-bottom:1px solid var(--border-color);position:sticky;top:0;z-index:100}
.header-content{max-width:1400px;margin:0 auto;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{width:36px;height:36px;background:linear-gradient(135deg,var(--primary),var(--accent));border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;color:white}
.logo-text h1{font-size:16px;font-weight:600}
.header-actions{display:flex;gap:8px}
.btn{padding:10px 16px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:8px;border:none;text-decoration:none}
.btn-primary{background:var(--primary);color:white}
.btn-primary:hover{background:#2563eb}
.main-container{max-width:1400px;margin:0 auto;padding:24px}
.page-header{margin-bottom:24px}
.page-header h2{font-size:24px;font-weight:600}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--bg-card);border-radius:12px;padding:20px;border:1px solid var(--border-color);transition:all .2s}
.card:hover{border-color:var(--primary)}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-title{font-size:16px;font-weight:600}
.badge{padding:4px 10px;border-radius:6px;font-size:11px;font-weight:600}
.badge-success{background:rgba(16,185,129,.15);color:var(--success)}
.badge-warning{background:rgba(245,158,11,.15);color:var(--warning)}
.badge-danger{background:rgba(239,68,68,.15);color:var(--danger)}
.card-info{font-size:13px;color:var(--text-secondary)}
.data-table{width:100%;background:var(--bg-card);border-radius:12px;border:1px solid var(--border-color);overflow:hidden}
.data-table th,.data-table td{padding:14px 16px;text-align:left;border-bottom:1px solid var(--border-color)}
.data-table th{background:var(--bg-hover);font-weight:600;font-size:12px;text-transform:uppercase;color:var(--text-secondary)}
.data-table tr:last-child td{border-bottom:none}
.data-table tr:hover td{background:var(--bg-hover)}
.action-btn{padding:6px 10px;border-radius:6px;background:var(--primary);color:white;border:none;cursor:pointer;font-size:12px;text-decoration:none}
.action-btn:hover{background:#2563eb}
.empty-state{text-align:center;padding:60px 20px;color:var(--text-secondary)}
.empty-state i{font-size:48px;margin-bottom:16px;opacity:.5}
@media(max-width:768px){.header{padding:10px 12px}.main-container{padding:16px}.data-table{display:block;overflow-x:auto}.btn span{display:none}}
</style>"""

HEAD_BASE = """<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Rainstaff ERP</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  {css}
</head>"""

HEADER_NAV = """<body>
  <header class="header">
    <div class="header-content">
      <div class="logo">
        <div class="logo-icon"><i class="fas fa-{icon}"></i></div>
        <div class="logo-text"><h1>{page_title}</h1></div>
      </div>
      <div class="header-actions">
        <a href="/dashboard" class="btn btn-primary"><i class="fas fa-arrow-left"></i><span>Dashboard</span></a>
      </div>
    </div>
  </header>"""

# Vehicle page
vehicle_html = HEAD_BASE.format(title="Araclar", css=CSS_BASE) + HEADER_NAV.format(icon="truck", page_title="Araclar") + """
  <main class="main-container">
    <div class="page-header"><h2>Arac Listesi</h2></div>
    <div class="card-grid">
      {% if vehicles %}
        {% for v in vehicles %}
        <div class="card">
          <div class="card-header">
            <span class="card-title" style="color:var(--primary)">{{ v.plate }}</span>
            <span class="badge badge-success">Aktif</span>
          </div>
          <div class="card-info">{{ v.brand }} {{ v.model }}</div>
        </div>
        {% endfor %}
      {% else %}
        <div class="empty-state">
          <i class="fas fa-truck"></i>
          <p>Arac bulunamadi</p>
        </div>
      {% endif %}
    </div>
  </main>
</body>
</html>"""

# Employee page
employee_html = HEAD_BASE.format(title="Calisanlar", css=CSS_BASE) + HEADER_NAV.format(icon="users", page_title="Calisanlar") + """
  <main class="main-container">
    <div class="page-header"><h2>Calisan Listesi</h2></div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Ad Soyad</th>
          <th>Bolge</th>
          <th>Durum</th>
        </tr>
      </thead>
      <tbody>
        {% if employees %}
          {% for e in employees %}
          <tr>
            <td>{{ e.name }}</td>
            <td>{{ e.region }}</td>
            <td><span class="badge badge-success">Aktif</span></td>
          </tr>
          {% endfor %}
        {% else %}
          <tr>
            <td colspan="3">
              <div class="empty-state">
                <i class="fas fa-users"></i>
                <p>Calisan bulunamadi</p>
              </div>
            </td>
          </tr>
        {% endif %}
      </tbody>
    </table>
  </main>
</body>
</html>"""

# Driver page
driver_html = HEAD_BASE.format(title="Suruculer", css=CSS_BASE) + HEADER_NAV.format(icon="id-card", page_title="Suruculer") + """
  <main class="main-container">
    <div class="page-header"><h2>Surucu Listesi</h2></div>
    <div class="card-grid">
      {% if drivers %}
        {% for d in drivers %}
        <div class="card">
          <div class="card-header">
            <span class="card-title">{{ d.name }}</span>
            <span class="badge badge-success">Aktif</span>
          </div>
          <div class="card-info">Tel: {{ d.phone or '-' }}</div>
        </div>
        {% endfor %}
      {% else %}
        <div class="empty-state">
          <i class="fas fa-id-card"></i>
          <p>Surucu bulunamadi</p>
        </div>
      {% endif %}
    </div>
  </main>
</body>
</html>"""

# Report detail page
report_detail_html = HEAD_BASE.format(title="Rapor Detay", css=CSS_BASE) + HEADER_NAV.format(icon="file-alt", page_title="Rapor Detay") + """
  <main class="main-container">
    <div class="page-header">
      <h2>{{ plate }} - {{ week_start }}</h2>
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Tarih</th>
          <th>Kontrol</th>
          <th>Sonuc</th>
          <th>Not</th>
        </tr>
      </thead>
      <tbody>
        {% if results %}
          {% for r in results %}
          <tr>
            <td>{{ r.date }}</td>
            <td>{{ r.check_item }}</td>
            <td>
              {% if r.result == 'OK' %}
                <span class="badge badge-success">OK</span>
              {% else %}
                <span class="badge badge-danger">FAIL</span>
              {% endif %}
            </td>
            <td>{{ r.note or '-' }}</td>
          </tr>
          {% endfor %}
        {% else %}
          <tr>
            <td colspan="4">
              <div class="empty-state">
                <i class="fas fa-clipboard-list"></i>
                <p>Sonuc bulunamadi</p>
              </div>
            </td>
          </tr>
        {% endif %}
      </tbody>
    </table>
  </main>
</body>
</html>"""

# Write files
templates = {
    'vehicle.html': vehicle_html,
    'employee.html': employee_html,
    'driver.html': driver_html,
    'report_detail.html': report_detail_html,
}

for filename, content in templates.items():
    filepath = os.path.join(base, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated: {filename}")

print("\nAll templates updated successfully!")
