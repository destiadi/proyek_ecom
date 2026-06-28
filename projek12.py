import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.title("📦 Sistem Verifikasi Master Barcode (Gspread)")
st.subheader("Manajemen Pick-Up Paket Gudang")
st.write("---")

try:
    credentials = st.secrets["gspread_creds"]
    # Login ke Google Sheets menggunakan gspread
    gc = gspread.service_account_from_dict(credentials)
    
    # Buka spreadsheet berdasarkan URL-nya
    URL_SHEET = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = gc.open_by_url(URL_SHEET)
    worksheet = sh.get_worksheet(0) # Membuka sheet pertama
    
    # Konversi data Google Sheets menjadi Pandas DataFrame untuk ditampilkan
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error("❌ Gagal terhubung ke Google Sheets: Batas kuota permintaan (Rate Limit) terlampaui atau server sedang sibuk. Silakan tunggu 1-2 menit lalu refresh kembali halaman ini.")
    st.stop()

# Tampilkan data saat ini di layar web
st.write("🔍 **Data Terdeteksi di Google Sheets:**")
st.dataframe(df)

def eksekusi_pickup_gspread(id_karung_scan):
    # Cari tahu di baris mana ID_Karung tersebut berada
    try:
        # Mencari sel yang berisi ID_Karung yang cocok
        cell_list = worksheet.findall(str(id_karung_scan), in_column=3) # Angka 3 artinya kolom ke-3 (ID_Karung)
        
        if not cell_list:
            st.warning(f"⚠️ Barcode '{id_karung_scan}' tidak ditemukan di database!")
            return
            
        zona_wib = ZoneInfo("Asia/Jakarta")
        waktu_sekarang = datetime.now(zona_wib).strftime("%Y-%m-%d %H:%M:%S")
        
        # Lakukan update massal langsung ke baris Google Sheets asli secara real-time
        for cell in cell_list:
            row_num = cell.row
            worksheet.update_cell(row_num, 4, 'Sudah di-Pickup') # Kolom 4 = Status
            worksheet.update_cell(row_num, 5, waktu_sekarang)    # Kolom 5 = Waktu_Pickup
            
        st.success(f"🎉 Sukses! {len(cell_list)} paket di dalam {id_karung_scan} berhasil diperbarui di Google Sheets asli!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Gagal memperbarui data: {e}")

# Komponen Scanner URL Parameter - Auto Input Aktif
# Komponen Scanner URL Parameter - Auto Input & Auto Submit Aktif
try:
    query_parameters = st.query_parameters
    if "scan" in query_parameters:
        id_scan = query_parameters["scan"]
        if isinstance(id_scan, list):
            id_scan = id_scan[0]
        eksekusi_pickup_gspread(id_scan)
    else:
        # Menggunakan parameter on_change agar langsung mengeksekusi fungsi begitu scanner mengisi teks
        id_dari_scanner = st.text_input(
            "👉 SILAKAN SCAN BARCODE KARUNG DI SINI:", 
            key="scanner_input",
            on_change=lambda: eksekusi_pickup_gspread(st.session_state.scanner_input) if st.session_state.scanner_input else None
        )
except Exception as e:
    id_dari_scanner = st.text_input(
        "👉 SILAKAN SCAN BARCODE KARUNG DI SINI:", 
        key="scanner_input",
        on_change=lambda: eksekusi_pickup_gspread(st.session_state.scanner_input) if st.session_state.scanner_input else None
    )