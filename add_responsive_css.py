#!/usr/bin/env python3
"""
Add mobile responsive breakpoints to Rainstaff CSS
"""

mobile_css = '''

/* ============================================================================ */
/* Mobile Responsive Breakpoints (Added 19 Ocak 2026) */
/* ============================================================================ */

@media (max-width: 768px) {
  /* Tablet Devices */
  .sidebar {
    position: fixed;
    left: -240px;
    height: 100vh;
    z-index: 1000;
    transition: left 0.3s ease;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }

  body.sidebar-open .sidebar {
    left: 0;
  }

  .content {
    margin-left: 0 !important;
  }

  .topbar {
    flex-wrap: wrap;
    gap: 8px;
  }

  .topbar .sync {
    width: 100%;
    font-size: 12px;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .sidebar-toggle {
    display: block !important;
  }

  .kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;
  }

  .kpi-card {
    padding: 12px;
    font-size: 12px;
  }

  .kpi-card .label {
    font-size: 11px;
  }

  .kpi-card .value {
    font-size: 16px;
    font-weight: 700;
  }

  table {
    font-size: 12px;
  }

  table th,
  table td {
    padding: 8px 4px;
  }

  .table-tools {
    flex-direction: column;
    align-items: stretch;
  }

  .table-tools input,
  .table-tools button {
    width: 100%;
  }

  .panel {
    padding: 12px;
  }

  button,
  .btn {
    padding: 10px 12px;
    font-size: 13px;
    min-height: 40px;
  }

  input,
  select,
  textarea {
    font-size: 16px;
    padding: 10px;
    min-height: 40px;
  }
}

@media (max-width: 480px) {
  /* Small Mobile Devices */
  .topbar {
    padding: 8px;
    flex-direction: column;
  }

  .topbar .brand {
    flex-direction: row;
    gap: 6px;
  }

  .topbar .brand-title {
    font-size: 14px;
  }

  .topbar .brand-sub {
    font-size: 11px;
  }

  .topbar .sync {
    font-size: 11px;
    gap: 4px;
  }

  .sync .status,
  .sync .alert-pill,
  .sync .notify-btn,
  .sync .logout {
    padding: 6px 8px;
    font-size: 11px;
  }

  .content {
    padding: 8px !important;
  }

  .panel {
    padding: 8px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .kpi-card {
    padding: 10px;
  }

  table {
    font-size: 11px;
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  table thead {
    display: none;
  }

  table tbody tr {
    display: block;
    border: 1px solid var(--border);
    margin-bottom: 8px;
    border-radius: 6px;
  }

  table tbody td {
    display: block;
    padding: 8px 0;
    text-align: right;
    position: relative;
    padding-left: 50%;
  }

  table tbody td:before {
    content: attr(data-label);
    position: absolute;
    left: 0;
    font-weight: 600;
    text-align: left;
    width: 45%;
    padding-left: 8px;
    color: var(--muted);
    font-size: 10px;
  }

  .alert-list {
    grid-template-columns: 1fr;
  }

  .report-list {
    grid-template-columns: 1fr;
  }

  input,
  select,
  textarea {
    width: 100%;
    font-size: 16px;
  }

  button,
  .btn {
    width: 100%;
    padding: 12px 8px;
    font-size: 14px;
  }

  .login-card {
    width: 90%;
    max-width: 100%;
  }
}

@media (max-width: 360px) {
  /* Extra Small Devices */
  .topbar {
    padding: 4px;
  }

  .topbar .brand-title {
    font-size: 12px;
  }

  .topbar .sync {
    font-size: 10px;
  }

  table {
    font-size: 10px;
  }

  button,
  .btn {
    padding: 8px 6px;
    font-size: 12px;
  }
}
'''

css_path = r"C:\Users\rainwater\Desktop\puantaj\server\static\style.css"

with open(css_path, "a", encoding="utf-8") as f:
    f.write(mobile_css)

print("✅ Mobile responsive CSS added!")
print("   ├─ 768px breakpoint (tablet)")
print("   ├─ 480px breakpoint (mobile)")
print("   └─ 360px breakpoint (small phone)")
