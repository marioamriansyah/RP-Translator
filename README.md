# PRORP Translator

Aplikasi translator desktop modern bertema **Pro Dark Utility** untuk GTA Roleplay (RP). Menerjemahkan kalimat Bahasa Indonesia ke Bahasa Inggris dalam berbagai gaya RP (*LA Street, Cartel Mexico, Mafia Italy, British Formal, American Formal*) dengan kamus slang lokal instan dan AI Groq (`qwen/qwen3.8-27b`).

---

## Fitur Utama

### 1. Desain Modern Pro Utility (Tanpa Emoji & Bersih)
- Desain gelap profesional dengan palet warna rapi, tipografi presisi, dan kartu jawaban terisolasi.
- **Tanpa Emoji**: Seluruh tombol, status, dan label menggunakan ikon teks bersih (*Snip Area, Guide Box, Settings, Translate, Copy*).
- **Tanpa Suara Mengganggu**: Hotkey berjalan hening tanpa memicu bunyi *system chime* Windows.
- **In-Game OSD (On-Screen Display)**: Tampilan melayang transparan berkecepatan tinggi tanpa border langsung di atas layar game.

### 2. Dual OCR: Input Bar & Chatlog Terbaru
- **`F4` (Input Bar - Apa Yang Kita Ketik)**: Khusus membaca baris pengetikan Anda (saat menekan tombol `T` di game). Dilengkapi pembersihan otomatis kursor berkedip (`|`, `_`) dan prefix command (`/me`, `/do`, `say:`). Riwayat chat lama tidak akan ikut terambil.
- **`F3` (Chatlog History - Pesan Masuk)**: Khusus membaca chat yang dikirim pemain lain di area riwayat chat, dan **hanya mengambil kalimat paling baru** sehingga Anda tidak perlu menerjemahkan puluhan baris chat lama sekaligus.
- **`Snip Input (F4)` & `Snip Chat (F3)`**: Tombol di toolbar untuk menandai masing-masing area secara visual.
- **`Guide Boxes`**: Menampilkan frame visual untuk kedua area tangkap yang bisa digeser (*drag*) dan diubah ukurannya (*resize*) langsung di layar.

### 3. Draggable In-Game OSD (Bisa Digeser Bebas)
- **Klik & Geser Langsung**: OSD overlay di layar game kini bisa diklik dan digeser ke posisi mana pun yang nyaman (pojok atas, samping map, dll).
- **Otomatis Tersimpan**: Koordinat OSD otomatis tersimpan saat mouse dilepas.
- **Tombol `Position OSD`**: Klik tombol ini di aplikasi kapan saja untuk menampilkan OSD dan mengatur posisinya dengan mudah tanpa perlu sedang bermain.

### 4. Slang Library Lokal (1.000+ Frasa) & AI Groq
- **0 ms Delay**: Kalimat yang terdaftar di kamus langsung menghasilkan 3 variasi tanpa kuota API.
- **Groq AI Fallback**: Menerjemahkan kalimat secara kontekstual sesuai aturan gaya RP dengan filter proper noun GTA (*Los Santos, LSPD, FIB, dll.*).

### 5. Global Hotkeys

| Shortcut | Fungsi |
|---|---|
| **`F4`** | Tangkap baris apa yang **kita ketik** via OCR lalu terjemahkan |
| **`F3`** | Tangkap pesan **chat masuk terbaru** dari pemain lain via OCR |
| **`F5`** | Tangkap teks dari clipboard lalu otomatis terjemahkan |
| **`Ctrl + 1`** | Salin opsi terjemahan **Option 1** ke clipboard |
| **`Ctrl + 2`** | Salin opsi terjemahan **Option 2** ke clipboard |
| **`Ctrl + 3`** | Salin opsi terjemahan **Option 3** ke clipboard |
| **`Insert`** | Sembunyikan / Tampilkan jendela aplikasi (*toggle*) |
| **`Page Up` / `Page Down`** | Scroll teks panjang di OSD overlay in-game |

---

## Cara Menjalankan Tanpa Membuka Terminal / CMD

Anda **tidak perlu membuka terminal atau CMD sama sekali**:

1. **Melalui Desktop Shortcut**:
   Klik ganda shortcut **`PRORP Translator`** di Desktop Anda.
2. **Melalui File Launcher VBS**:
   Klik ganda **`PRORP Translator.vbs`** di folder `d:\REA`.
3. **Melalui Shortcut Folder**:
   Klik ganda **`PRORP Translator.lnk`** di folder `d:\REA`.

Aplikasi akan langsung terbuka seperti aplikasi Windows biasa tanpa jendela hitam terminal di belakangnya.
