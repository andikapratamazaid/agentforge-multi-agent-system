# Roadmap AgentForge Menuju Produk SaaS

Dokumen ini menjabarkan jalan pengembangan AgentForge dari MVP open
source di repo ini menjadi produk SaaS berbayar. Setiap fase berisi
ruang lingkup, kebutuhan teknis, dan metrik keberhasilan. Angka harga
di bagian akhir bersifat indikatif untuk pasar Indonesia dan Asia
Tenggara, bukan janji komersial.

## Fase 1: MVP (Repo Ini)

Ruang lingkup:
- Orchestration Engine deterministik dengan rencana langkah, retry,
  log run lengkap, dan siklus revisi berbasis skor Reviewer.
- Lima agent: Conductor, Research, Data, Writer, Reviewer.
- Model Router OpenRouter dengan model per agent, rantai fallback,
  dan perhitungan biaya per run. Mode demo deterministik tanpa API
  key dan mode live dengan satu API key.
- Tiga workflow contoh: pipeline konten, pipeline laporan data, dan
  pipeline triase support.
- CLI, dashboard statis, riwayat run SQLite, test suite, dan harness
  evaluasi benchmark.

Kebutuhan teknis:
- Python standard library, SQLite, file konfigurasi JSON.
- Satu proses, satu pengguna, tanpa server wajib.

Metrik keberhasilan:
- Test suite lulus 100 persen.
- Benchmark evaluasi: seluruh tugas menyelesaikan workflow dengan
  skor Reviewer mencapai ambang.
- Biaya per run tercatat dan dapat diaudit dari log.

## Fase 2: Multi-Tenant

Ruang lingkup:
- Workspace sebagai unit isolasi: setiap workspace punya anggota,
  konfigurasi model, API key OpenRouter sendiri (atau key platform),
  dan riwayat run terpisah.
- Akun pengguna dengan peran pemilik, admin, dan anggota.
- Kuota per workspace: batas run per bulan, batas token per bulan,
  dan batas pengguna bersamaan.
- API resmi (REST) di atas Orchestration Engine agar workflow dapat
  dipicu dari sistem lain, lengkap dengan webhook hasil run.

Kebutuhan teknis:
- Migrasi penyimpanan dari SQLite ke PostgreSQL dengan skema
  multi-tenant (kolom workspace_id di semua tabel run).
- Lapisan autentikasi (email dan kata sandi plus OAuth Google),
  manajemen sesi, dan rate limiting per workspace.
- Antrian pekerjaan (queue) agar run panjang tidak memblokir API,
  misalnya dengan worker terpisah dan Redis atau layanan antrian
  setara.
- Pemisahan rahasia per workspace dengan enkripsi at rest.

Metrik keberhasilan:
- Isolasi data antar workspace lolos uji keamanan dasar (tidak ada
  run yang dapat dibaca lintas workspace).
- P95 latensi API di bawah 500 ms untuk operasi baca riwayat.
- Onboarding workspace baru selesai di bawah 10 menit tanpa bantuan
  tim.

## Fase 3: Penagihan dan Langganan

Ruang lingkup:
- Langganan per agent aktif per bulan: workspace membayar untuk
  agent yang diaktifkan (misalnya Writer dan Reviewer sebagai paket
  dasar, Data dan Research sebagai tambahan).
- Meteran per run di atas kuota paket: setiap run mencatat token dan
  biaya model, lalu ditagihkan sebagai pemakaian tambahan dengan
  markup platform yang transparan.
- Masa coba gratis terbatas kuota, halaman tagihan, riwayat invoice,
  dan pemberitahuan ambang pemakaian.

Kebutuhan teknis:
- Integrasi payment gateway yang umum di Indonesia (misalnya
  Midtrans atau Xendit) untuk kartu, transfer bank, dan e-wallet,
  plus opsi gateway internasional untuk pelanggan luar negeri.
- Mesin meteran (metering) yang membaca log run dari Fase 1 dan 2,
  mengagregasi per workspace per periode tagihan.
- Penanganan pembayaran gagal: masa tenggang, penurunan paket
  otomatis, dan penguncian fitur berbayar tanpa menghapus data.

Metrik keberhasilan:
- Selisih antara catatan meteran internal dan tagihan gateway di
  bawah 0,5 persen per periode.
- Konversi masa coba ke berbayar minimal 5 persen pada kohort awal.
- Waktu rekonsiliasi tagihan bulanan di bawah 1 hari kerja.

## Fase 4: Marketplace Agent dan Workflow

Ruang lingkup:
- Katalog agent pihak ketiga dan paket workflow siap pakai
  (misalnya agent untuk ringkasan rapat, klasifikasi dokumen hukum,
  atau laporan keuangan berkala) yang dapat dipasang ke workspace
  dalam sekali klik.
- Halaman profil penerbit, ulasan pengguna, dan versi paket workflow.
- Bagi hasil antara platform dan penerbit paket berbayar.

Kebutuhan teknis:
- Format paket workflow yang terstandar (manifest JSON: langkah,
  agent, prompt, kebutuhan input) dengan validasi otomatis sebelum
  diterbitkan.
- Sandbox eksekusi untuk paket pihak ketiga: batas token, batas
  waktu, dan larangan akses jaringan di luar daftar yang diizinkan.
- Sistem versi dan rollback untuk paket yang sudah terpasang.

Metrik keberhasilan:
- Minimal 20 paket workflow terbit dalam 6 bulan pertama marketplace.
- Kurang dari 1 persen run marketplace gagal karena kesalahan paket.
- Penerbit eksternal menyumbang minimal 15 persen run berbayar.

## Fase 5: Enterprise

Ruang lingkup:
- Single sign-on (SSO) SAML dan OIDC, provisioner pengguna (SCIM),
  dan kebijakan kata sandi per organisasi.
- Audit log lengkap yang tidak dapat diubah (siapa menjalankan apa,
  model apa yang dipakai, dan berapa biayanya), dengan ekspor untuk
  tim kepatuhan.
- Pilihan residensi data dan mode dedicated tenant untuk pelanggan
  besar, termasuk opsi membawa API key dan model sendiri.
- SLA tertulis dengan target uptime dan waktu tanggap dukungan.

Kebutuhan teknis:
- Pemisahan control plane dan data plane, pencadangan otomatis, dan
  uji pemulihan berkala.
- Observabilitas penuh: metrik per agent, per model, dan per
  workspace; peringatan otomatis untuk lonjakan biaya model.
- Peninjauan keamanan berkala dan uji penetrasi tahunan.

Metrik keberhasilan:
- Uptime bulanan minimal 99,9 persen sesuai SLA.
- Lolos audit keamanan pelanggan enterprise pertama tanpa temuan
  kritis terbuka.
- Waktu tanggap dukungan prioritas di bawah 4 jam kerja.

## Skema Harga Indikatif

Angka berikut contoh indikatif dalam rupiah per workspace per bulan,
disusun mengikuti model langganan per agent ditambah meteran per run.
Angka final wajib diuji ke pasar dan disesuaikan dengan biaya model
yang berubah dari waktu ke waktu.

- Starter: gratis sampai 50 run per bulan, 2 agent aktif (Writer dan
  Reviewer), 1 anggota. Untuk mencoba dan portofolio.
- Growth: Rp 299.000 per bulan, 5 agent aktif, 500 run termasuk,
  5 anggota, riwayat run 90 hari. Kelebihan run dikenakan Rp 750 per
  run di luar biaya model yang diteruskan apa adanya.
- Business: Rp 999.000 per bulan, semua agent, 2.500 run termasuk,
  anggota tanpa batas wajar, kuota dan laporan biaya per anggota,
  dukungan prioritas.
- Enterprise: harga negosiasi mulai sekitar Rp 7.500.000 per bulan,
  mencakup SSO, audit log penuh, SLA, dan opsi dedicated tenant.

Catatan: biaya model dari OpenRouter selalu diteruskan secara
transparan di semua paket berbayar, agar pelanggan dapat memilih
model murah atau model kuat sesuai kebutuhan tiap agent.
