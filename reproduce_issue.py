
def parse_serial(seri_no):
    print(f"Input: '{seri_no}'")
    if seri_no:
        parts = seri_no.split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit():
            # Logic from test_deneme_excel_fix.py lines 90-94
            if not parts[1].isdigit():
                seri_no = parts[1]
                print(f"  -> Stripped numbering: '{seri_no}'")
            else:
                print(f"  -> DID NOT STRIP because second part is numeric: '{seri_no}'")
    return seri_no

print("--- Test Case 1: Standard Serial ---")
parse_serial("1 ST87088")

print("\n--- Test Case 2: Numeric Serial Issue ---")
result = parse_serial("1 8697236914625")

expected = "8697236914625"
if result == expected:
    print("\n✅ PASSED")
else:
    print(f"\n❌ FAILED: Expected '{expected}', got '{result}'")
