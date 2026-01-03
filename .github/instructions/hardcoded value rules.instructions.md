---
applyTo: '**'
---

# Larangan Penggunaan Hardcoded Values sebagai Fallback

1. DILARANG menggunakan hardcoded values sebagai fallback dalam kode apapun.
2. DILARANG menetapkan nilai default secara langsung di dalam kode untuk menangani error atau exception.
3. DILARANG menyimpan konfigurasi penting seperti API key, URL, path, atau credential secara hardcoded.
4. DILARANG menggunakan hardcoded values untuk pengaturan environment (development, staging, production).
5. DILARANG menggunakan hardcoded values untuk pengaturan database connection string.
6. DILARANG menggunakan hardcoded values untuk pengaturan timeout, limit, atau threshold.
7. DILARANG menggunakan hardcoded values untuk pesan error, notifikasi, atau response user.
8. DILARANG menggunakan hardcoded values untuk pengaturan fitur toggle atau flag aplikasi.
9. DILARANG menggunakan hardcoded values untuk pengaturan bahasa, regional, atau currency.
10. DILARANG menggunakan hardcoded values sebagai solusi sementara atau permanen untuk menghindari error, karena akan menyulitkan migrasi dan update sistem.