"""
Fix for stock upload when Excel has no header row
Detects if first row is empty and skips it
"""

fix_code = '''
    def _stock_upload_worker(self, file_path, bolge):
        """Process stock file upload in background"""
        try:
            # Read Excel locally first
            rows = load_tabular_file(file_path)
            if not rows:
                self.stock_status_var.set("Dosyada veri bulunamadi!")
                messagebox.showwarning("Uyari", "Dosyada veri bulunamadi.")
                return

            # Check if first row is empty (no headers)
            first_row_empty = all(cell is None or str(cell).strip() == '' for cell in rows[0])
            
            if first_row_empty:
                # No headers - use default column indices
                if self.logger:
                    self.logger.info("Stock upload: No header row detected, using default indices")
                stok_kod_idx = 0
                stok_adi_idx = 1
                seri_no_idx = 2
                seri_sayi_idx = 3
                start_row = 1  # Skip empty first row
            else:
                # Parse headers (flexible)
                headers = [str(h).strip().lower() if h else '' for h in rows[0]]
                
                stok_kod_idx = next((i for i, h in enumerate(headers) if 'stok' in h and 'kod' in h), 0)
                stok_adi_idx = next((i for i, h in enumerate(headers) if 'stok' in h and ('adi' in h or 'ad' in h)), 1)
                seri_no_idx = next((i for i, h in enumerate(headers) if 'seri' in h and 'no' in h), 2)
                seri_sayi_idx = next((i for i, h in enumerate(headers) if 'seri' in h and 'say' in h), 3)
                start_row = 1  # Skip header row

            # Parse nested Excel structure
            # Format: Stok header row followed by seri_no child rows (with empty stok_kod)
            imported = 0
            with db.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM stock_inventory WHERE bolge = ?", (bolge,))

                i = start_row
                while i < len(rows):
                    row = rows[i]

                    # Check if this is a product header (stok_kod not empty)
                    stok_kod = str(row[stok_kod_idx]).strip() if stok_kod_idx < len(row) and row[stok_kod_idx] else ''

                    if stok_kod and stok_kod not in ['', 'nan', 'None', 'None']:
                        # This is a product header
                        stok_adi = str(row[stok_adi_idx]).strip() if stok_adi_idx < len(row) and row[stok_adi_idx] else ''
                        seri_sayi = 0
                        try:
                            seri_sayi = int(row[seri_sayi_idx]) if seri_sayi_idx < len(row) and row[seri_sayi_idx] else 0
                        except (ValueError, TypeError):
                            pass

                        # Collect all following seri_no rows (child rows where stok_kod is empty)
                        i += 1
                        seri_count = 0
                        while i < len(rows):
                            child_row = rows[i]
                            child_stok_kod = str(child_row[stok_kod_idx]).strip() if stok_kod_idx < len(child_row) and child_row[stok_kod_idx] else ''

                            # If stok_kod is empty/nan, this is a seri_no row
                            if not child_stok_kod or child_stok_kod in ['', 'nan', 'None', 'None']:
                                try:
                                    # Seri no is in stok_adi column for child rows
                                    seri_no = str(child_row[stok_adi_idx]).strip() if stok_adi_idx < len(child_row) and child_row[stok_adi_idx] else ''

                                    # Extract actual serial number (remove numbering like "1 ST87088")
                                    if seri_no:
                                        parts = seri_no.split(maxsplit=1)
                                        if len(parts) == 2 and parts[0].isdigit():
                                            seri_no = parts[1]  # "ST87088"

                                    # Skip if seri_no is empty or just a number (serial position)
                                    if seri_no and seri_no not in ['', 'nan', 'None', 'None'] and not seri_no.isdigit():
                                        cursor.execute(
                                            """INSERT INTO stock_inventory
                                               (stok_kod, stok_adi, seri_no, durum, tarih, girdi_yapan, bolge, adet, updated_at)
                                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                            (stok_kod, stok_adi, seri_no, "OK", datetime.now().strftime("%Y-%m-%d"),
                                             "system", bolge, 1, datetime.now().isoformat())
                                        )
                                        imported += 1
                                        seri_count += 1

                                    i += 1
                                except Exception as e:
                                    if self.logger:
                                        self.logger.debug(f"Stock seri row error: {e}")
                                    i += 1
                                    break
                            else:
                                # Next product header found
                                break
                    else:
                        i += 1

            self.stock_status_var.set(f"✓ {imported} kayit yuklendi ({bolge})")
            self._log_action("stock_upload", f"file={os.path.basename(file_path)} region={bolge} count={imported}")

            # Refresh view
            self.refresh_stock_list()
            messagebox.showinfo("Basarili", f"{imported} stok kaydı yüklendi.")

            # Trigger sync
            self.trigger_sync("stock_upload")

        except Exception as e:
            self.stock_status_var.set(f"✗ Hata: {str(e)[:50]}")
            if self.logger:
                self.logger.error(f"Stock upload error: {e}")
            messagebox.showerror("Hata", f"Yukleme basarisiz: {str(e)[:100]}")
'''

print("Fix code ready to apply")
print("\nKey changes:")
print("1. Detect if first row is empty (no headers)")
print("2. If empty, use default column indices (0,1,2,3)")
print("3. Start from row 1 instead of row 0")
print("4. For child rows, read seri_no from stok_adi column (column 1)")
print("5. Add check to skip pure numeric values")
