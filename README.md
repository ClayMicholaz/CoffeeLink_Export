# CoffeeLink Export

Aplikasi CRUD berbasis Python Flask untuk mengelola rantai pasok dan ekspor kopi lokal ke pembeli internasional.

## Fitur
- Login dan registrasi (role admin, buyer, farmer)
- Dashboard ringkasan data
- Master data petani, pembeli, dan produk kopi
- Transaksi pesanan ekspor
- Pengurangan stok otomatis saat pesanan dibuat
- Pengelolaan status pesanan dan pengiriman
- Laporan transaksi dan tombol cetak
- SQLite untuk lokal; PostgreSQL melalui `DATABASE_URL` untuk deployment

## Menjalankan di Windows
1. Install Python 3.10 atau lebih baru.
2. Buka folder project di VS Code / terminal.
3. Buat virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependency:
   ```powershell
   pip install -r requirements.txt
   ```
5. Jalankan:
   ```powershell
   python app.py
   ```
6. Buka `http://127.0.0.1:5000`.

## Akun demo
- Email: `admin@coffeelink.test`
- Password: `admin123`

Ganti password dan `SECRET_KEY` sebelum aplikasi dipublikasikan.

## Hosting gratis (Render)
1. Upload project ke repository GitHub.
2. Buat PostgreSQL database gratis pada penyedia yang mendukung PostgreSQL, lalu salin connection string internal.
3. Di Render, buat Web Service dari repository tersebut.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Tambahkan environment variables:
   - `SECRET_KEY`: string acak yang kuat
   - `DATABASE_URL`: connection string PostgreSQL
7. Deploy. Pastikan paket database gratis yang dipilih masih tersedia dan memperhatikan masa berlaku/limit paketnya.

Catatan: SQLite lokal cocok untuk demonstrasi. Untuk hosting, gunakan PostgreSQL persisten karena filesystem layanan web gratis dapat bersifat sementara.

## Struktur data
- User: akun dan role.
- Farmer: master petani.
- Buyer: master pembeli internasional.
- CoffeeProduct: master produk, stok, harga, dan petani pemasok.
- ExportOrder: transaksi ekspor.
- Shipment: detail logistik yang terhubung ke pesanan.

## Catatan ruang lingkup tugas
Aplikasi ini adalah prototipe akademik. Fitur pembayaran internasional, dokumen bea cukai, sertifikat fitosanitari, sinkronisasi tracking carrier, kurs valuta asing real-time, dan proses kepabeanan belum diintegrasikan.
