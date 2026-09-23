/**
 * TERAS • MANIS: ROTI THAILAND & SUSU MURNI
 * State Management, Jar-Cards, Bottom Sheet, Cart & Checkout
 */

const TM_DATA = {
  roti: [
    {
      id: 'roti-srikaya',
      name: 'Srikaya Pandan Wangi',
      desc: 'Selai srikaya daun pandan asli yang lumer gurih manis lembut khas Thailand.',
      icon: '🌿',
      badge: 'Best Seller',
      priceSmall: 15000,
      priceLarge: 22000
    },
    {
      id: 'roti-cokelat',
      name: 'Cokelat Lumer Belgia',
      desc: 'Cokelat premium pekat yang meleleh saat roti dipanggang hangat.',
      icon: '🍫',
      badge: 'Favorit',
      priceSmall: 16000,
      priceLarge: 24000
    },
    {
      id: 'roti-keju',
      name: 'Keju Susu Gurih',
      desc: 'Parutan keju cheddar melimpah dipadu susu kental manis gurih sedap.',
      icon: '🧀',
      badge: 'Populer',
      priceSmall: 16000,
      priceLarge: 24000
    },
    {
      id: 'roti-choco-crunchy',
      name: 'Choco Crunchy Krenyes',
      desc: 'Pasta cokelat malt dengan butiran cruncy garing yang renyah tiap gigitan.',
      icon: '🍪',
      badge: 'Renyah',
      priceSmall: 17000,
      priceLarge: 25000
    },
    {
      id: 'roti-thai-tea',
      name: 'Thai Tea Cream',
      desc: 'Krim seduhan teh Thailand wangi aroma khas dipadu kelembutan roti.',
      icon: '🧋',
      badge: 'Autentik',
      priceSmall: 16000,
      priceLarge: 23000
    },
    {
      id: 'roti-matcha',
      name: 'Matcha Green Tea',
      desc: 'Ekstrak teh hijau jepang dengan rasa manis lembut dan wangi aromatik.',
      icon: '🍵',
      badge: 'Spesial',
      priceSmall: 17000,
      priceLarge: 25000
    },
    {
      id: 'roti-biscoff',
      name: 'Lotus Biscoff Caramel',
      desc: 'Selai karamel biskuit Lotus khas eropa dengan remahan biskuit karamel.',
      icon: '🍯',
      badge: 'Premium',
      priceSmall: 18000,
      priceLarge: 26000
    },
    {
      id: 'roti-taro',
      name: 'Taro Milk Cream',
      desc: 'Krim ubi ungu taro manis legit beraroma wangi lembut memanjakan lidah.',
      icon: '🍠',
      badge: 'Unik',
      priceSmall: 16000,
      priceLarge: 23000
    },
    {
      id: 'roti-strawberry',
      name: 'Strawberry Jam Segar',
      desc: 'Selai stroberi segar dengan bulir buah asli berpadu kelembutan mentega.',
      icon: '🍓',
      badge: 'Segar',
      priceSmall: 15000,
      priceLarge: 22000
    },
    {
      id: 'roti-tiramisu',
      name: 'Tiramisu Melt',
      desc: 'Krim tiramisu wangi kopi lembut dan taburan kakao nikmat lumer di mulut.',
      icon: '☕',
      badge: 'Lumer',
      priceSmall: 17000,
      priceLarge: 25000
    }
  ],
  susu: [
    {
      id: 'susu-original',
      name: 'Susu Murni Segar Original',
      desc: 'Susu sapi murni segar tanpa pengawet. Tersedia Dingin / Hangat.',
      icon: '🥛',
      badge: 'Murni 100%',
      priceSmall: 12000,
      priceLarge: 18000
    },
    {
      id: 'susu-cokelat',
      name: 'Susu Murni Cokelat',
      desc: 'Susu segar berpadu cokelat manis creamy menyegarkan.',
      icon: '🍫',
      badge: 'Favorit',
      priceSmall: 14000,
      priceLarge: 20000
    },
    {
      id: 'susu-strawberry',
      name: 'Susu Murni Strawberry',
      desc: 'Susu murni segar beraroma stroberi manis lembut.',
      icon: '🍓',
      badge: 'Segar',
      priceSmall: 14000,
      priceLarge: 20000
    },
    {
      id: 'susu-karamel',
      name: 'Susu Murni Karamel',
      desc: 'Susu murni gurih dengan sirup karamel bakar wangi legit.',
      icon: '🍯',
      badge: 'Legit',
      priceSmall: 14000,
      priceLarge: 20000
    }
  ],
  toppings: [
    { id: 'top-keju', name: 'Extra Keju Parut', price: 3000 },
    { id: 'top-cokelat', name: 'Cokelat Serut Belgia', price: 3000 },
    { id: 'top-almond', name: 'Almond Slice Panggang', price: 4000 },
    { id: 'top-lotus', name: 'Remahan Biskuit Lotus', price: 4000 },
    { id: 'top-skm', name: 'Extra Susu Kental Manis', price: 2000 }
  ]
};

// Application State
const tmState = {
  currentTab: 'menu',
  globalSize: 'small', // 'small' or 'large'
  cart: [],
  sheetItem: null,
  sheetSize: 'small',
  sheetQty: 1,
  sheetSelectedToppings: []
};

// Format Rupiah
function formatRp(num) {
  return 'Rp ' + Number(num).toLocaleString('id-ID');
}

// ------------------------------------------------------------
// INITIALIZATION
// ------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  renderMenuGrid();
  updateCartBadge();
  setupEventListeners();
});

function setupEventListeners() {
  // Tutup bottom sheet jika klik di backdrop gelap
  const backdrop = document.getElementById('tm-bottom-sheet-backdrop');
  if (backdrop) {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        closeBottomSheet();
      }
    });
  }

  // Keyboard Escape untuk tutup bottom sheet
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeBottomSheet();
    }
  });
}

// ------------------------------------------------------------
// TAB NAVIGATION (3 TABS)
// ------------------------------------------------------------
function switchTab(tabName) {
  tmState.currentTab = tabName;

  // Sembunyikan semua tab view
  document.querySelectorAll('.tab-view').forEach(view => {
    view.classList.remove('active');
  });

  // Tampilkan tab view aktif
  const targetView = document.getElementById(`tab-view-${tabName}`);
  if (targetView) targetView.classList.add('active');

  // Update status tombol bottom nav
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.tab === tabName) {
      btn.classList.add('active');
    }
  });

  // Jika buka tab keranjang, render keranjang
  if (tabName === 'cart') {
    renderCartPage();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ------------------------------------------------------------
// GLOBAL SIZE TOGGLE (Small / Large)
// ------------------------------------------------------------
function toggleGlobalSize(size) {
  tmState.globalSize = size;

  // Update tombol pill di header
  const btnSmall = document.getElementById('btn-size-small');
  const btnLarge = document.getElementById('btn-size-large');

  if (btnSmall && btnLarge) {
    if (size === 'small') {
      btnSmall.classList.add('active');
      btnLarge.classList.remove('active');
    } else {
      btnLarge.classList.add('active');
      btnSmall.classList.remove('active');
    }
  }

  // Render ulang harga di kartu toples
  renderMenuGrid();
  showToast(`Ukuran Roti disetel ke: ${size.toUpperCase()}`);
}

// ------------------------------------------------------------
// RENDER MENU (JAR-CARDS GRID)
// ------------------------------------------------------------
function renderMenuGrid() {
  const container = document.getElementById('tm-jar-grid');
  if (!container) return;

  const size = tmState.globalSize;

  container.innerHTML = TM_DATA.roti.map(item => {
    const currentPrice = size === 'small' ? item.priceSmall : item.priceLarge;
    const sizeLabel = size === 'small' ? 'Porsi Small' : 'Porsi Large';

    return `
      <article class="jar-card" onclick="openBottomSheet('${item.id}')" title="Klik untuk pilih rasa ${item.name}">
        <div class="jar-lid"></div>
        <div class="jar-body">
          <span class="jar-badge-tag">${item.badge}</span>
          <div class="jar-icon-wrap">${item.icon}</div>
          <h3 class="jar-name">${item.name}</h3>
          <p class="jar-desc">${item.desc}</p>
          <div class="jar-footer">
            <div class="jar-price-box">
              <span class="jar-price-label">${sizeLabel}</span>
              <span class="jar-price-value">${formatRp(currentPrice)}</span>
            </div>
            <button type="button" class="btn-jar-add" onclick="event.stopPropagation(); openBottomSheet('${item.id}');" title="Pilih ${item.name}">
              +
            </button>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

// ------------------------------------------------------------
// BOTTOM SHEET (KUSTOMISASI ITEM)
// ------------------------------------------------------------
function openBottomSheet(itemId) {
  // Cari di data roti atau susu
  let item = TM_DATA.roti.find(r => r.id === itemId);
  if (!item) {
    item = TM_DATA.susu.find(s => s.id === itemId);
  }
  if (!item) return;

  tmState.sheetItem = item;
  tmState.sheetSize = tmState.globalSize;
  tmState.sheetQty = 1;
  tmState.sheetSelectedToppings = [];

  // Isi data header item
  document.getElementById('sheet-icon').textContent = item.icon;
  document.getElementById('sheet-name').textContent = item.name;
  document.getElementById('sheet-desc').textContent = item.desc;

  // Ukuran radio buttons
  document.getElementById('sheet-size-small-price').textContent = formatRp(item.priceSmall);
  document.getElementById('sheet-size-large-price').textContent = formatRp(item.priceLarge);
  updateSheetSizeSelection();

  // Reset Stepper
  document.getElementById('sheet-stepper-qty').textContent = tmState.sheetQty;

  // Render Checkbox Toppings
  renderSheetToppings();

  // Update harga total di tombol
  updateSheetTotalPrice();

  // Buka Sheet
  const backdrop = document.getElementById('tm-bottom-sheet-backdrop');
  if (backdrop) backdrop.classList.add('active');
}

function closeBottomSheet() {
  const backdrop = document.getElementById('tm-bottom-sheet-backdrop');
  if (backdrop) backdrop.classList.remove('active');
  tmState.sheetItem = null;
}

function selectSheetSize(size) {
  tmState.sheetSize = size;
  updateSheetSizeSelection();
  updateSheetTotalPrice();
}

function updateSheetSizeSelection() {
  const cardSmall = document.getElementById('sheet-size-small-card');
  const cardLarge = document.getElementById('sheet-size-large-card');
  if (cardSmall && cardLarge) {
    if (tmState.sheetSize === 'small') {
      cardSmall.classList.add('active');
      cardLarge.classList.remove('active');
    } else {
      cardLarge.classList.add('active');
      cardSmall.classList.remove('active');
    }
  }
}

function renderSheetToppings() {
  const listEl = document.getElementById('sheet-toppings-list');
  if (!listEl) return;

  listEl.innerHTML = TM_DATA.toppings.map(t => {
    const isChecked = tmState.sheetSelectedToppings.includes(t.id);
    return `
      <label class="topping-item-row" onclick="toggleSheetTopping('${t.id}')">
        <div class="topping-left">
          <input type="checkbox" class="topping-checkbox" ${isChecked ? 'checked' : ''} onchange="toggleSheetTopping('${t.id}')" />
          <span class="topping-name">${t.name}</span>
        </div>
        <span class="topping-price">+${formatRp(t.price)}</span>
      </label>
    `;
  }).join('');
}

function toggleSheetTopping(toppingId) {
  const index = tmState.sheetSelectedToppings.indexOf(toppingId);
  if (index > -1) {
    tmState.sheetSelectedToppings.splice(index, 1);
  } else {
    tmState.sheetSelectedToppings.push(toppingId);
  }
  renderSheetToppings();
  updateSheetTotalPrice();
}

function changeSheetQty(delta) {
  tmState.sheetQty += delta;
  if (tmState.sheetQty < 1) tmState.sheetQty = 1;
  document.getElementById('sheet-stepper-qty').textContent = tmState.sheetQty;
  updateSheetTotalPrice();
}

function calculateSheetItemPrice() {
  if (!tmState.sheetItem) return 0;
  const basePrice = tmState.sheetSize === 'small' ? tmState.sheetItem.priceSmall : tmState.sheetItem.priceLarge;
  
  let toppingsPrice = 0;
  tmState.sheetSelectedToppings.forEach(tId => {
    const topping = TM_DATA.toppings.find(t => t.id === tId);
    if (topping) toppingsPrice += topping.price;
  });

  return (basePrice + toppingsPrice) * tmState.sheetQty;
}

function updateSheetTotalPrice() {
  const total = calculateSheetItemPrice();
  document.getElementById('sheet-total-btn-text').textContent = `Tambah ke Keranjang (${formatRp(total)})`;
}

// ------------------------------------------------------------
// ADD TO CART & CART MANAGEMENT
// ------------------------------------------------------------
function addSheetItemToCart() {
  if (!tmState.sheetItem) return;

  const item = tmState.sheetItem;
  const size = tmState.sheetSize;
  const basePrice = size === 'small' ? item.priceSmall : item.priceLarge;

  const chosenToppings = tmState.sheetSelectedToppings.map(tId => {
    return TM_DATA.toppings.find(t => t.id === tId);
  }).filter(Boolean);

  let toppingsExtra = 0;
  chosenToppings.forEach(t => toppingsExtra += t.price);
  const unitPrice = basePrice + toppingsExtra;

  // Cek apakah ada item yang sama persis di keranjang (id, size, dan topping sama)
  const toppingsKey = chosenToppings.map(t => t.id).sort().join(',');
  const existingIndex = tmState.cart.findIndex(c => c.id === item.id && c.size === size && c.toppingsKey === toppingsKey);

  if (existingIndex > -1) {
    tmState.cart[existingIndex].qty += tmState.sheetQty;
    tmState.cart[existingIndex].subtotal = tmState.cart[existingIndex].qty * unitPrice;
  } else {
    tmState.cart.push({
      id: item.id,
      name: item.name,
      icon: item.icon,
      size: size,
      unitPrice: unitPrice,
      qty: tmState.sheetQty,
      subtotal: tmState.sheetQty * unitPrice,
      toppings: chosenToppings,
      toppingsKey: toppingsKey
    });
  }

  showToast(`${item.name} (${size.toUpperCase()}) masuk keranjang!`);
  closeBottomSheet();
  updateCartBadge();
}

// Fungsi cepat pesan Susu Murni dari banner
function quickAddSusuBanner() {
  openBottomSheet('susu-original');
}

function updateCartBadge() {
  const totalItems = tmState.cart.reduce((sum, item) => sum + item.qty, 0);
  const badge = document.getElementById('nav-cart-badge');
  if (badge) {
    badge.textContent = totalItems;
    if (totalItems > 0) {
      badge.classList.add('visible');
    } else {
      badge.classList.remove('visible');
    }
  }
}

// ------------------------------------------------------------
// HALAMAN KERANJANG
// ------------------------------------------------------------
function renderCartPage() {
  const emptyBox = document.getElementById('cart-empty-box');
  const contentBox = document.getElementById('cart-content-box');
  const listEl = document.getElementById('cart-items-list');

  if (!emptyBox || !contentBox || !listEl) return;

  if (tmState.cart.length === 0) {
    emptyBox.style.display = 'block';
    contentBox.style.display = 'none';
    return;
  }

  emptyBox.style.display = 'none';
  contentBox.style.display = 'block';

  listEl.innerHTML = tmState.cart.map((item, index) => {
    const toppingText = item.toppings.length > 0
      ? `+ Topping: ${item.toppings.map(t => t.name).join(', ')}`
      : 'Tanpa Topping Tambahan';

    return `
      <article class="cart-item-card">
        <div class="cart-item-icon">${item.icon}</div>
        <div class="cart-item-details">
          <h4 class="cart-item-title">${item.name}</h4>
          <div class="cart-item-meta">Porsi: <strong>${item.size.toUpperCase()}</strong></div>
          <div class="cart-item-meta">${toppingText}</div>
          <div class="cart-item-price">${formatRp(item.subtotal)}</div>
        </div>
        <div class="cart-item-actions">
          <button type="button" class="btn-remove-item" onclick="removeCartItem(${index})" title="Hapus item">
            ✕
          </button>
          <div class="cart-item-stepper">
            <button type="button" onclick="changeCartItemQty(${index}, -1)">-</button>
            <span>${item.qty}</span>
            <button type="button" onclick="changeCartItemQty(${index}, 1)">+</button>
          </div>
        </div>
      </article>
    `;
  }).join('');

  // Hitung total
  const subtotal = tmState.cart.reduce((sum, item) => sum + item.subtotal, 0);
  const packagingFee = 2000; // Dus toples ramah lingkungan
  const grandTotal = subtotal + packagingFee;

  document.getElementById('cart-subtotal').textContent = formatRp(subtotal);
  document.getElementById('cart-packaging').textContent = formatRp(packagingFee);
  document.getElementById('cart-grand-total').textContent = formatRp(grandTotal);
}

function changeCartItemQty(index, delta) {
  if (!tmState.cart[index]) return;
  tmState.cart[index].qty += delta;

  if (tmState.cart[index].qty <= 0) {
    tmState.cart.splice(index, 1);
  } else {
    tmState.cart[index].subtotal = tmState.cart[index].qty * tmState.cart[index].unitPrice;
  }

  updateCartBadge();
  renderCartPage();
}

function removeCartItem(index) {
  if (!tmState.cart[index]) return;
  const removedName = tmState.cart[index].name;
  tmState.cart.splice(index, 1);
  updateCartBadge();
  renderCartPage();
  showToast(`${removedName} dihapus dari keranjang`);
}

// ------------------------------------------------------------
// CHECKOUT VIA WHATSAPP / KASIR
// ------------------------------------------------------------
function handleCheckout() {
  if (tmState.cart.length === 0) {
    showToast('Keranjang Anda masih kosong!');
    return;
  }

  const nameInput = document.getElementById('cart-customer-name');
  const noteInput = document.getElementById('cart-customer-note');

  const customerName = (nameInput && nameInput.value.trim()) ? nameInput.value.trim() : 'Pelanggan Teras Manis';
  const notes = (noteInput && noteInput.value.trim()) ? noteInput.value.trim() : '-';

  const subtotal = tmState.cart.reduce((sum, item) => sum + item.subtotal, 0);
  const packagingFee = 2000;
  const grandTotal = subtotal + packagingFee;

  // Format Pesan WhatsApp
  let msg = `Halo *Teras • Manis*, saya ingin memesan Roti Thailand:\n\n`;
  msg += `👤 *Nama Pemesan:* ${customerName}\n`;
  msg += `📝 *Catatan:* ${notes}\n\n`;
  msg += `*DAFTAR PESANAN:*\n`;

  tmState.cart.forEach((item, idx) => {
    msg += `${idx + 1}. ${item.name} (${item.size.toUpperCase()}) x ${item.qty} = ${formatRp(item.subtotal)}\n`;
    if (item.toppings.length > 0) {
      msg += `   └ Topping: ${item.toppings.map(t => t.name).join(', ')}\n`;
    }
  });

  msg += `\nSubtotal: ${formatRp(subtotal)}\n`;
  msg += `Biaya Dus & Kemasan: ${formatRp(packagingFee)}\n`;
  msg += `*TOTAL BAYAR: ${formatRp(grandTotal)}*\n\n`;
  msg += `Mohon konfirmasi ketersediaan dan nomor antrean pesanan. Terima kasih!`;

  const encodedMsg = encodeURIComponent(msg);
  const waNumber = '6281234567890'; // Nomor WhatsApp Toko Teras Manis

  // Buka WhatsApp
  window.open(`https://wa.me/${waNumber}?text=${encodedMsg}`, '_blank');
  showToast('Membuka WhatsApp untuk mengirim pesanan...');
}

// ------------------------------------------------------------
// TOAST NOTIFICATION
// ------------------------------------------------------------
let toastTimer = null;
function showToast(text) {
  const toast = document.getElementById('tm-toast');
  const msg = document.getElementById('tm-toast-msg');
  if (!toast || !msg) return;

  msg.textContent = text;
  toast.classList.add('show');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}
