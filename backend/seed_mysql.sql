USE aurora_cafe;
SET FOREIGN_KEY_CHECKS = 0;

-- Data for brands
INSERT INTO `brands` (`id`, `name`, `logo`, `description`, `created_at`) VALUES (1, 'TERAS MANIS', '/static/img/coffee.jpg', 'Cafe & Resto Modern Santai dan Nyaman', '2026-09-18 12:11:46');

-- Data for outlets
INSERT INTO `outlets` (`id`, `brand_id`, `name`, `address`, `phone`, `email`, `is_active`, `created_at`) VALUES (1, 1, 'TERAS MANIS - Outlet Rancaekek', 'Jl Cipasir, Gg. Pancasila, RT.03/RW.09, Linggar, Kec. Rancaekek, Bandung', '08123456789', 'admin@terasmanis.com', 1, '2026-09-18 12:11:46');
INSERT INTO `outlets` (`id`, `brand_id`, `name`, `address`, `phone`, `email`, `is_active`, `created_at`) VALUES (2, 1, 'Teras Manis 2', 'Jl Cipasir, Gg. Pancasila, RT.03/RW.09, Linggar, Kec. Rancaekek, Kabupaten Bandung, Jawa Barat 40394', '022-7205678', '-', 1, '2026-09-18 12:11:46');

-- Data for settings
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (1, 1, 'receipt_footer', 'Terima kasih atas kunjungan Anda! Follow IG: @terasmanis.cafe', 'Pesan di struk kasir');
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (2, 1, 'auto_print_receipt', 'true', 'Cetak struk otomatis saat pembayaran sukses');
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (3, 1, 'receipt_header', 'TERAS MANIS CAFE & ROASTERY', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (5, 1, 'show_logo', 'true', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (6, 1, 'show_wifi', 'true', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (7, 1, 'wifi_ssid', 'TerasManis_Guest', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (8, 1, 'wifi_password', 'kopiterasmanis', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (9, 1, 'tax_id', '01.892.481.0-421.000', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (10, 1, 'instagram', '@terasmanis.cafe', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (19, 1, 'tax_enabled', 'false', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (20, 1, 'tax_rate', '0.0', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (21, 1, 'tax_name', 'Bebas Pajak', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (22, 1, 'show_tax_on_receipt', 'true', NULL);
INSERT INTO `settings` (`id`, `outlet_id`, `setting_key`, `setting_value`, `description`) VALUES (23, 1, 'paper_width', '58mm', NULL);

-- Data for billing_plans
INSERT INTO `billing_plans` (`id`, `brand_id`, `plan_name`, `status`, `billing_cycle`, `start_date`, `end_date`, `price`) VALUES (1, 1, 'Pro Enterprise Multi-Outlet', 'active', 'yearly', '2026-09-18', '2027-09-18', 2400000.0);

-- Data for roles
INSERT INTO `roles` (`id`, `name`, `description`, `permissions`) VALUES (1, 'Owner / Admin', 'Akses penuh ke semua fitur dan laporan', '["all"]');
INSERT INTO `roles` (`id`, `name`, `description`, `permissions`) VALUES (2, 'Store Manager', 'Manajemen stok, shift, dan laporan penjualan', '["pos", "inventory", "reports", "shift"]');
INSERT INTO `roles` (`id`, `name`, `description`, `permissions`) VALUES (3, 'Cashier / Barista', 'Operasional POS kasir, order dan update status meja', '["pos", "table", "shift_open_close"]');

-- Data for users
INSERT INTO `users` (`id`, `brand_id`, `email`, `password_hash`, `full_name`, `role_id`, `phone`, `is_active`, `created_at`, `username`) VALUES (1, 1, 'admin@auroracafe.com', '54d7ae936b4de00f$b35664125c03e0418dff00d87622e6ce1f9fb59b4f739f20e404e34f5bbbdd9c', 'Ade Suharmin (Owner)', 1, '081234567890', 1, '2026-09-22 04:59:22', 'admin');
INSERT INTO `users` (`id`, `brand_id`, `email`, `password_hash`, `full_name`, `role_id`, `phone`, `is_active`, `created_at`, `username`) VALUES (2, 1, 'kasir@auroracafe.com', '874953f5275a6d55$94aee7a75b9ea572d95bd23b7b5f471a57171f104f77109c878bbd5c793fd519', 'Kasir Utama Aurora', 2, '081233334444', 1, '2026-09-22 04:59:22', 'kasir');

-- Data for employees
INSERT INTO `employees` (`id`, `outlet_id`, `user_id`, `name`, `pin`, `role_id`, `phone`, `is_active`, `created_at`) VALUES (1, 1, NULL, 'Ade Suharmin', '1122', 2, '081234567890', 1, '2026-09-18 12:11:46');
INSERT INTO `employees` (`id`, `outlet_id`, `user_id`, `name`, `pin`, `role_id`, `phone`, `is_active`, `created_at`) VALUES (2, 1, NULL, 'Risa Aprilia Wahyudi', '1234', 3, '081233334444', 1, '2026-09-18 12:11:46');
INSERT INTO `employees` (`id`, `outlet_id`, `user_id`, `name`, `pin`, `role_id`, `phone`, `is_active`, `created_at`) VALUES (3, 1, NULL, 'Asep Setiawan (Kasir Sore)', '5678', 3, '081255556666', 1, '2026-09-18 12:11:46');

-- Data for employee_slots
INSERT INTO `employee_slots` (`id`, `outlet_id`, `max_slots`, `used_slots`) VALUES (1, 1, 10, 3);
INSERT INTO `employee_slots` (`id`, `outlet_id`, `max_slots`, `used_slots`) VALUES (2, 2, 5, 1);

-- Data for categories
INSERT INTO `categories` (`id`, `brand_id`, `name`, `description`, `is_active`) VALUES (1, 1, 'Signature Coffee', 'Kopi racikan khas Aurora dengan cita rasa unik', 1);
INSERT INTO `categories` (`id`, `brand_id`, `name`, `description`, `is_active`) VALUES (2, 1, 'Manual Brew & Espresso', 'Kopi murni single origin nusantara', 1);
INSERT INTO `categories` (`id`, `brand_id`, `name`, `description`, `is_active`) VALUES (3, 1, 'Non-Coffee & Tea', 'Minuman segar susu, matcha, dan teh artisan', 1);
INSERT INTO `categories` (`id`, `brand_id`, `name`, `description`, `is_active`) VALUES (4, 1, 'Bakery & Pastry', 'Kue fresh baked setiap hari', 1);
INSERT INTO `categories` (`id`, `brand_id`, `name`, `description`, `is_active`) VALUES (5, 1, 'Main Course', 'Makanan berat untuk santap siang dan malam', 1);

-- Data for items
INSERT INTO `items` (`id`, `category_id`, `name`, `description`, `sku`, `price`, `cost_price`, `image_url`, `is_active`) VALUES (1, 1, 'Kopi Susu Gula Aren', 'Espresso, fresh milk, and premium palm sugar', 'KPS-001', 28000.0, 14000.0, '/static/img/coffee.jpg', 1);
INSERT INTO `items` (`id`, `category_id`, `name`, `description`, `sku`, `price`, `cost_price`, `image_url`, `is_active`) VALUES (2, 2, 'Espresso Double Shot', 'Double shot extracted from house blend arabica', 'ESP-002', 18000.0, 4000.0, '/static/img/coffee.jpg', 1);
INSERT INTO `items` (`id`, `category_id`, `name`, `description`, `sku`, `price`, `cost_price`, `image_url`, `is_active`) VALUES (3, 3, 'Matcha Green Tea Latte', 'Pure uji ceremonial matcha with steamed milk', 'MTC-003', 26000.0, 9500.0, '/static/img/coffee.jpg', 1);
INSERT INTO `items` (`id`, `category_id`, `name`, `description`, `sku`, `price`, `cost_price`, `image_url`, `is_active`) VALUES (4, 4, 'Butter Croissant French', 'Flaky butter croissant baked to golden perfection', 'CRS-004', 22000.0, 10000.0, '/static/img/pastry.jpg', 1);
INSERT INTO `items` (`id`, `category_id`, `name`, `description`, `sku`, `price`, `cost_price`, `image_url`, `is_active`) VALUES (5, 5, 'Nasi Goreng Spesial Aurora', 'Fried rice with chicken satay, egg, and kerupuk', 'NAS-005', 35000.0, 14000.0, '/static/img/pastry.jpg', 1);

-- Data for modifiers
INSERT INTO `modifiers` (`id`, `brand_id`, `name`, `min_selection`, `max_selection`, `is_active`) VALUES (1, 1, 'Level Gula (Sugar Level)', 1, 1, 1);
INSERT INTO `modifiers` (`id`, `brand_id`, `name`, `min_selection`, `max_selection`, `is_active`) VALUES (2, 1, 'Extra Topping & Add-ons', 0, 3, 1);
INSERT INTO `modifiers` (`id`, `brand_id`, `name`, `min_selection`, `max_selection`, `is_active`) VALUES (3, 1, 'Pilihan Ukuran (Size)', 1, 1, 1);

-- Data for modifier_options
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (1, 1, 'Normal Sugar (100%)', 0.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (2, 1, 'Less Sugar (50%)', 0.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (3, 1, 'No Sugar (0%)', 0.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (4, 2, 'Extra Espresso Shot', 5000.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (5, 2, 'Grass Jelly (Cincau)', 4000.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (6, 2, 'Ganti Susu Oat (Oatmilk)', 7000.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (7, 3, 'Regular (Standar)', 0.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (8, 3, 'Large (+Rp 5.000)', 5000.0);
INSERT INTO `modifier_options` (`id`, `modifier_id`, `name`, `additional_price`) VALUES (9, 3, 'Jumbo / Extra (+Rp 8.000)', 8000.0);

-- Data for item_modifiers
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (1, 1);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (1, 2);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (3, 1);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (1, 3);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (2, 3);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (3, 3);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (4, 3);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (5, 3);
INSERT INTO `item_modifiers` (`item_id`, `modifier_id`) VALUES (3, 2);

-- Data for bundle_packages
INSERT INTO `bundle_packages` (`id`, `brand_id`, `name`, `price`, `description`, `is_active`) VALUES (1, 1, 'Paket Ngopi Pagi (Morning Booster)', 38000.0, '1 Kopi Susu Gula Aren + 1 Butter Croissant French', 1);

-- Data for bundle_items
INSERT INTO `bundle_items` (`id`, `bundle_id`, `item_id`, `quantity`) VALUES (1, 1, 1, 1);
INSERT INTO `bundle_items` (`id`, `bundle_id`, `item_id`, `quantity`) VALUES (2, 1, 4, 1);

-- Data for ingredient_categories
INSERT INTO `ingredient_categories` (`id`, `brand_id`, `name`, `description`) VALUES (1, 1, 'Biji Kopi (Coffee Beans)', 'Biji kopi sangrai specialty');
INSERT INTO `ingredient_categories` (`id`, `brand_id`, `name`, `description`) VALUES (2, 1, 'Dairy & Pemanis', 'Susu cair, kental manis, sirup gula');
INSERT INTO `ingredient_categories` (`id`, `brand_id`, `name`, `description`) VALUES (3, 1, 'Powder & Teh', 'Bubuk matcha, cokelat, teh artisan');
INSERT INTO `ingredient_categories` (`id`, `brand_id`, `name`, `description`) VALUES (4, 1, 'Bahan Dapur & Bakery', 'Adonan kue dan bahan masakan');

-- Data for ingredients
INSERT INTO `ingredients` (`id`, `category_id`, `name`, `unit`, `cost_per_unit`, `min_stock_alert`, `is_active`) VALUES (1, 1, 'Biji Kopi Arabika House Blend', 'gr', 250.0, 1000.0, 1);
INSERT INTO `ingredients` (`id`, `category_id`, `name`, `unit`, `cost_per_unit`, `min_stock_alert`, `is_active`) VALUES (2, 2, 'Fresh Milk UHT Full Cream', 'ml', 18.0, 5000.0, 1);
INSERT INTO `ingredients` (`id`, `category_id`, `name`, `unit`, `cost_per_unit`, `min_stock_alert`, `is_active`) VALUES (3, 2, 'Gula Aren Cair Premium', 'ml', 35.0, 1000.0, 1);
INSERT INTO `ingredients` (`id`, `category_id`, `name`, `unit`, `cost_per_unit`, `min_stock_alert`, `is_active`) VALUES (4, 3, 'Matcha Powder Ceremonial', 'gr', 500.0, 250.0, 1);
INSERT INTO `ingredients` (`id`, `category_id`, `name`, `unit`, `cost_per_unit`, `min_stock_alert`, `is_active`) VALUES (5, 4, 'Adonan Croissant Beku', 'pcs', 10000.0, 20.0, 1);
INSERT INTO `ingredients` (`id`, `category_id`, `name`, `unit`, `cost_per_unit`, `min_stock_alert`, `is_active`) VALUES (6, 4, 'Beras Organik Pandan Wangi', 'gr', 15.0, 5000.0, 1);

-- Data for outlet_ingredient_stocks
INSERT INTO `outlet_ingredient_stocks` (`id`, `outlet_id`, `ingredient_id`, `current_stock`, `updated_at`) VALUES (1, 1, 1, 14658.0, '2026-09-21 12:13:15');
INSERT INTO `outlet_ingredient_stocks` (`id`, `outlet_id`, `ingredient_id`, `current_stock`, `updated_at`) VALUES (2, 1, 2, 57300.0, '2026-09-21 12:13:15');
INSERT INTO `outlet_ingredient_stocks` (`id`, `outlet_id`, `ingredient_id`, `current_stock`, `updated_at`) VALUES (3, 1, 3, 11550.0, '2026-09-21 12:13:15');
INSERT INTO `outlet_ingredient_stocks` (`id`, `outlet_id`, `ingredient_id`, `current_stock`, `updated_at`) VALUES (4, 1, 4, 3000.0, '2026-09-18 12:11:46');
INSERT INTO `outlet_ingredient_stocks` (`id`, `outlet_id`, `ingredient_id`, `current_stock`, `updated_at`) VALUES (5, 1, 5, 91.0, '2026-09-21 12:13:15');
INSERT INTO `outlet_ingredient_stocks` (`id`, `outlet_id`, `ingredient_id`, `current_stock`, `updated_at`) VALUES (6, 1, 6, 25000.0, '2026-09-18 12:11:46');

-- Data for recipes
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (1, 1, 1, 18.0, 'gr');
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (2, 1, 2, 150.0, 'ml');
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (3, 1, 3, 25.0, 'ml');
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (4, 2, 1, 18.0, 'gr');
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (5, 3, 4, 15.0, 'gr');
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (6, 3, 2, 200.0, 'ml');
INSERT INTO `recipes` (`id`, `item_id`, `ingredient_id`, `quantity_used`, `unit`) VALUES (7, 4, 5, 1.0, 'pcs');

-- Data for suppliers
INSERT INTO `suppliers` (`id`, `brand_id`, `name`, `contact_person`, `phone`, `email`, `address`, `is_active`) VALUES (1, 1, 'PT Roastery Kopi Nusantara', 'Hendra Wijaya', '08119876543', 'order@roasterynusantara.com', 'Kawasan Industri Cimahi No. 8', 1);
INSERT INTO `suppliers` (`id`, `brand_id`, `name`, `contact_person`, `phone`, `email`, `address`, `is_active`) VALUES (2, 1, 'CV Sumber Dairy Segar', 'Dewi Susanti', '08128877665', 'dairy@sumbersusu.co.id', 'Lembang No. 42, Bandung Barat', 1);

-- Data for table_groups
INSERT INTO `table_groups` (`id`, `outlet_id`, `name`, `description`) VALUES (1, 1, 'Main Hall (Indoor AC)', 'Ruang utama bebas rokok ber-AC cocok untuk WFC');
INSERT INTO `table_groups` (`id`, `outlet_id`, `name`, `description`) VALUES (2, 1, 'Garden Patio (Outdoor)', 'Area taman terbuka untuk santai dan merokok');

-- Data for tables
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (1, 1, 1, 'Meja 01', 2, 50.0, 50.0, 'available', NULL);
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (2, 1, 1, 'Meja 02', 4, 150.0, 50.0, 'occupied', 12);
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (3, 1, 1, 'Meja 03', 4, 250.0, 50.0, 'available', NULL);
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (4, 1, 1, 'Meja 04 (Sofa)', 6, 50.0, 180.0, 'available', NULL);
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (5, 1, 1, 'Meja 05 (VIP)', 8, 200.0, 180.0, 'available', NULL);
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (6, 2, 1, 'Outdoor 01', 4, 50.0, 320.0, 'available', NULL);
INSERT INTO `tables` (`id`, `group_id`, `outlet_id`, `table_number`, `capacity`, `pos_x`, `pos_y`, `status`, `current_transaction_id`) VALUES (7, 2, 1, 'Outdoor 02', 4, 150.0, 320.0, 'available', NULL);

-- Data for taxes
INSERT INTO `taxes` (`id`, `outlet_id`, `name`, `rate_percent`, `is_inclusive`, `is_active`) VALUES (1, 1, 'Bebas Pajak', 0.0, 0, 0);

-- Data for gratuities
INSERT INTO `gratuities` (`id`, `outlet_id`, `name`, `rate_percent`, `is_active`) VALUES (1, 1, 'Service Charge', 5.0, 1);

-- Data for bank_accounts
INSERT INTO `bank_accounts` (`id`, `outlet_id`, `bank_name`, `account_number`, `account_holder`, `is_active`) VALUES (1, 1, 'Bank Central Asia (BCA)', '8420192831', 'PT AURORA CAFE NUSANTARA', 1);
INSERT INTO `bank_accounts` (`id`, `outlet_id`, `bank_name`, `account_number`, `account_holder`, `is_active`) VALUES (2, 1, 'Bank Mandiri', '1310029381290', 'PT AURORA CAFE NUSANTARA', 1);

-- Data for qris_configs
INSERT INTO `qris_configs` (`id`, `outlet_id`, `merchant_name`, `merchant_id`, `nmid`, `api_key`, `is_active`) VALUES (1, 1, 'Aurora Coffee Martadinata', 'MID-AURORA-001', 'ID1020023456789', NULL, 1);

-- Data for customers
INSERT INTO `customers` (`id`, `brand_id`, `name`, `phone`, `email`, `loyalty_points`, `total_spent`, `created_at`) VALUES (1, 1, 'Dimas Aditya', '081299887766', 'dimas@gmail.com', 139, 1436370.0, '2026-09-18 12:11:46');
INSERT INTO `customers` (`id`, `brand_id`, `name`, `phone`, `email`, `loyalty_points`, `total_spent`, `created_at`) VALUES (2, 1, 'Clarissa Putri', '085712345678', 'clarissa@yahoo.com', 28, 280000.0, '2026-09-18 12:11:46');

-- Data for discounts
INSERT INTO `discounts` (`id`, `brand_id`, `name`, `discount_type`, `value`, `min_order_amount`, `is_active`) VALUES (1, 1, 'Diskon Mahasiswa 10%', 'percentage', 10.0, 30000.0, 1);
INSERT INTO `discounts` (`id`, `brand_id`, `name`, `discount_type`, `value`, `min_order_amount`, `is_active`) VALUES (2, 1, 'Potongan Rp 15.000', 'fixed', 15000.0, 60000.0, 1);

-- Data for promos
INSERT INTO `promos` (`id`, `brand_id`, `name`, `promo_code`, `discount_type`, `discount_value`, `start_date`, `end_date`, `quota`, `used_count`, `is_active`) VALUES (1, 1, 'Promo Hemat Mantap', 'AURORAPAS', 'fixed', 10000.0, NULL, NULL, 500, 0, 1);

-- Data for campaigns
INSERT INTO `campaigns` (`id`, `brand_id`, `name`, `target_audience`, `message`, `start_date`, `end_date`, `status`) VALUES (1, 1, 'Promo Coffee Week 2026', 'Semua Pelanggan Terdaftar', 'Dapatkan cashback poin 2x lipat setiap pembelian Kopi Susu!', '2026-09-18', '2026-10-02', 'active');

-- Data for sales_types
INSERT INTO `sales_types` (`id`, `outlet_id`, `name`, `is_active`) VALUES (1, 1, 'Dine In (Makan di Tempat)', 1);
INSERT INTO `sales_types` (`id`, `outlet_id`, `name`, `is_active`) VALUES (2, 1, 'Take Away (Bungkus)', 1);
INSERT INTO `sales_types` (`id`, `outlet_id`, `name`, `is_active`) VALUES (3, 1, 'Delivery Online (GoFood / Grab)', 1);

-- Data for shifts
INSERT INTO `shifts` (`id`, `outlet_id`, `employee_id`, `start_time`, `end_time`, `initial_cash`, `expected_cash`, `actual_cash`, `difference`, `notes`, `status`) VALUES (1, 1, 2, '2026-09-18 12:11:46', NULL, 200000.0, 1303340.0, NULL, NULL, NULL, 'open');

-- Data for gofood_integrations
INSERT INTO `gofood_integrations` (`id`, `outlet_id`, `store_id`, `is_integrated`, `auto_accept_order`, `last_sync_at`) VALUES (1, 1, 'GOFOOD-BDG', 1, 1, NULL);

-- Data for partners
INSERT INTO `partners` (`id`, `brand_id`, `partner_name`, `partner_type`, `api_key`, `webhook_url`, `status`) VALUES (1, 1, 'GoFood Indonesia', 'delivery', NULL, NULL, 'active');
INSERT INTO `partners` (`id`, `brand_id`, `partner_name`, `partner_type`, `api_key`, `webhook_url`, `status`) VALUES (2, 1, 'GrabFood Merchant', 'delivery', NULL, NULL, 'active');
INSERT INTO `partners` (`id`, `brand_id`, `partner_name`, `partner_type`, `api_key`, `webhook_url`, `status`) VALUES (3, 1, 'ShopeePay & QRIS', 'payment', NULL, NULL, 'active');

SET FOREIGN_KEY_CHECKS = 1;
