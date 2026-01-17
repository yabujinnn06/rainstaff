"""
Test Flet Tab API in version 0.80.2
"""

import flet as ft
import sys

def main(page: ft.Page):
    page.title = "Flet Tab API Test"
    
    # Test 1: Try basic Tab with text parameter
    test_results = []
    
    # Test different Tab parameter combinations
    tests = [
        ("text= parameter", lambda: ft.Tab(text="Test")),
        ("tab_text= parameter", lambda: ft.Tab(tab_text="Test")),
        ("label= parameter", lambda: ft.Tab(label="Test")),
        ("content= parameter", lambda: ft.Tab(content=ft.Text("Test"))),
        ("text + content", lambda: ft.Tab(text="Test", content=ft.Text("Content"))),
        ("icon parameter", lambda: ft.Tab(text="Test", icon=ft.Icons.INBOX)),
    ]
    
    for test_name, test_func in tests:
        try:
            tab = test_func()
            test_results.append(ft.Row([
                ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN),
                ft.Text(f"✓ {test_name}", color=ft.Colors.GREEN)
            ]))
        except TypeError as e:
            test_results.append(ft.Row([
                ft.Icon(ft.Icons.CLOSE, color=ft.Colors.RED),
                ft.Text(f"✗ {test_name}: {str(e)[:50]}", color=ft.Colors.RED)
            ]))
    
    # Also test Tabs structure
    try:
        tabs = ft.Tabs(
            tabs=[
                ft.Tab(text="Tab 1"),
                ft.Tab(text="Tab 2"),
            ]
        )
        test_results.append(ft.Row([
            ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN),
            ft.Text("✓ Tabs with Tab objects", color=ft.Colors.GREEN)
        ]))
    except Exception as e:
        test_results.append(ft.Row([
            ft.Icon(ft.Icons.CLOSE, color=ft.Colors.RED),
            ft.Text(f"✗ Tabs structure: {str(e)[:50]}", color=ft.Colors.RED)
        ]))
    
    page.add(
        ft.Column([
            ft.Text("Flet 0.80.2 Tab API Test Results", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(test_results, spacing=10),
            ft.Divider(),
            ft.Text(f"Flet version: {ft.__version__}", size=12, color=ft.Colors.GREY),
        ], spacing=15, padding=20)
    )

if __name__ == "__main__":
    ft.app(target=main)
