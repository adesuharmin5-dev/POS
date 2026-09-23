<?php
/**
 * =========================================================================
 * KONFIGURASI DATABASE TERAS MANIS / AURORA CAFE POS (INFINITYFREE / CPANEL)
 * =========================================================================
 * 
 * Cara mengisi konfigurasi ini dari Akun InfinityFree Anda:
 * 1. Login ke panel InfinityFree (https://app.infinityfree.com)
 * 2. Masuk ke Akun Hosting Anda -> klik "Control Panel"
 * 3. Buka menu "MySQL Databases"
 * 4. Buat database baru (misal: "cafe" atau "pos")
 * 5. Salin data berikut dan masukkan ke konfigurasi di bawah:
 *    - MySQL Hostname : contoh "sql105.infinityfree.com"
 *    - MySQL Username : contoh "epiz_12345678"
 *    - MySQL Password : password akun cPanel InfinityFree Anda
 *    - Database Name  : contoh "epiz_12345678_cafe"
 * 
 * CATATAN PENTING:
 * Jika data MySQL belum diisi, sistem API akan otomatis berjalan menggunakan
 * fallback data lokal (SQLite / Demo Mock) sehingga aplikasi tetap bisa dibuka
 * dan digunakan secara langsung!
 */

// Hostname MySQL (Ganti dengan hostname dari cPanel InfinityFree)
define('DB_HOST', 'localhost');

// Username MySQL (Ganti dengan username cPanel InfinityFree Anda)
define('DB_USER', 'root');

// Password MySQL (Ganti dengan password akun cPanel Anda)
define('DB_PASS', '');

// Nama Database MySQL (Ganti dengan nama database lengkap di cPanel)
define('DB_NAME', 'aurora_cafe');

// Port MySQL default
define('DB_PORT', '3306');

// Path Fallback SQLite jika MySQL offline/belum dikonfigurasi
define('SQLITE_FALLBACK_PATH', __DIR__ . '/../data/aurora_cafe.db');
