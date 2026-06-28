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

# Komponen Utama: Deteksi Link Barcode dengan Sistem Kunci Memori (Session State)
try:
    # 1. Tangkap parameter dari link barcode (?scan=...)
    params = st.query_parameters
    
    # 2. Jika ada parameter "scan" di link dan belum pernah diproses di sesi ini
    if "scan" in params and "barcode_terproses" not in st.session_state:
        id_dari_link = params["scan"]
        
        # Jalankan fungsi input otomatis ke Google Sheets
        eksekusi_pickup_gspread(id_dari_link)
        
        # Kunci di memori agar tidak menduplikasi input saat halaman me-refresh sendiri
        st.session_state["barcode_terproses"] = id_dari_link
        st.success(f"✅ Barcode {id_dari_link} dari link berhasil di-input otomatis!")
        
    # 3. Tampilan Halaman Utama Web
    if "barcode_terproses" in st.session_state:
        st.info(f"Karung yang terakhir diproses otomatis: **{st.session_state['barcode_terproses']}**")
        # Tombol reset jika ingin melakukan scan link baru tanpa menutup browser
        if st.button("🔄 Siap untuk Scan Selanjutnya"):
            del st.session_state["barcode_terproses"]
            st.rerun()
    else:
        # Jika web dibuka biasa (bukan dari link barcode), tampilkan kotak input manual seperti biasa
        id_dari_scanner = st.text_input("👉 SILAKAN SCAN BARCODE KARUNG DI SINI:", key="scanner_input")
        if id_dari_scanner:
            eksekusi_pickup_gspread(id_dari_scanner)

except Exception as e:
    # Antisipasi aman jika sistem pembacaan URL mengalami kendala internal
    id_dari_scanner = st.text_input("👉 SILAKAN SCAN BARCODE KARUNG DI SINI:", key="scanner_input")
    if id_dari_scanner:
        eksekusi_pickup_gspread(id_dari_scanner)