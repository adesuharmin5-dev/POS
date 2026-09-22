// ==========================================================================
// Aurora Cafe & Roastery - Main Application Controller
// Tactile POS & High-Comfort Visual Theme System
// ==========================================================================

let state = {
  activeView: 'view-pos',
  activeOutletId: 1,
  activeBrandId: 1,
  brand: null,
  outlet: null,
  outlets: [],
  currentUser: null,
  pinInput: '',
  employees: [],
  selectedEmployee: null,
  currentShift: null,
  categories: [],
  items: [],
  selectedCategory: 'all',
  searchQuery: '',
  cart: [],
  selectedTableId: null,
  appliedPromo: null,
  activeItemForModifier: null,
  tables: [],
  ingredients: [],
  activePaymentMethod: 'Cash',
  cashReceived: 0,
  theme: 'dark', // 'dark' (Warm Dark Roast) or 'light' (Clean Warm Latte)
  activeMasterTab: 'kategori',
  masterSearchQuery: '',
  activeSettingTab: 'toko',
  activeAttendanceTab: 'cards',
  storeSettings: null,
  receiptSettings: null,
  accountUser: null,
  accountToken: null
};

// ==========================================================================
// SPA Routing & Navigation State Persistence System
// ==========================================================================
const VIEW_ROUTES = {
  'view-pos': { hash: 'pos', title: 'Kasir POS' },
  'view-dashboard': { hash: 'dashboard', title: 'Dashboard' },
  'view-tables': { hash: 'tables', title: 'Denah Meja' },
  'view-inventory': { hash: 'inventory', title: 'Stok & Resep' },
  'view-shifts': { hash: 'shifts', title: 'Shift & Riwayat' },
  'view-attendance': { hash: 'attendance', title: 'Absensi Karyawan' },
  'view-master': { hash: 'master', title: 'Master Data' },
  'view-settings': { hash: 'settings', title: 'Pengaturan' }
};

const HASH_TO_VIEW = {
  'pos': 'view-pos',
  'kasir': 'view-pos',
  'view-pos': 'view-pos',
  'dashboard': 'view-dashboard',
  'view-dashboard': 'view-dashboard',
  'tables': 'view-tables',
  'meja': 'view-tables',
  'view-tables': 'view-tables',
  'inventory': 'view-inventory',
  'stok': 'view-inventory',
  'resep': 'view-inventory',
  'view-inventory': 'view-inventory',
  'shifts': 'view-shifts',
  'shift': 'view-shifts',
  'riwayat': 'view-shifts',
  'view-shifts': 'view-shifts',
  'attendance': 'view-attendance',
  'absensi': 'view-attendance',
  'view-attendance': 'view-attendance',
  'master': 'view-master',
  'master-data': 'view-master',
  'view-master': 'view-master',
  'settings': 'view-settings',
  'pengaturan': 'view-settings',
  'toko': 'view-settings',
  'view-settings': 'view-settings'
};

function getViewHash(viewId, subTab = null) {
  const route = VIEW_ROUTES[viewId];
  if (!route) return '#pos';
  if (subTab && (viewId === 'view-master' || viewId === 'view-settings' || viewId === 'view-attendance')) {
    return `#${route.hash}/${subTab}`;
  }
  return `#${route.hash}`;
}

function getSavedSubTabForView(viewId) {
  if (viewId === 'view-master') {
    return sessionStorage.getItem('aurora_master_subtab') || localStorage.getItem('aurora_master_subtab') || state.activeMasterTab || 'kategori';
  }
  if (viewId === 'view-settings') {
    return sessionStorage.getItem('aurora_settings_subtab') || localStorage.getItem('aurora_settings_subtab') || state.activeSettingTab || 'toko';
  }
  if (viewId === 'view-attendance') {
    return sessionStorage.getItem('aurora_attendance_subtab') || localStorage.getItem('aurora_attendance_subtab') || state.activeAttendanceTab || 'cards';
  }
  return null;
}

function parseRouteFromHashOrStorage() {
  const rawHash = (window.location.hash || '').replace(/^#\/?/, '').trim();
  if (rawHash) {
    const parts = rawHash.split(/[\/:]/);
    const mainKey = (parts[0] || '').toLowerCase();
    const subTab = parts[1] ? parts[1].toLowerCase() : null;

    if (HASH_TO_VIEW[mainKey]) {
      const vId = HASH_TO_VIEW[mainKey];
      return {
        viewId: vId,
        subTab: subTab || getSavedSubTabForView(vId)
      };
    }
  }

  const savedView = sessionStorage.getItem('aurora_current_view') || localStorage.getItem('aurora_last_view');
  if (savedView && VIEW_ROUTES[savedView]) {
    return {
      viewId: savedView,
      subTab: getSavedSubTabForView(savedView)
    };
  }

  return { viewId: 'view-pos', subTab: null };
}

function applyViewUI(viewId, subTab = null) {
  if (!viewId) return;

  const sections = document.querySelectorAll('.view-section');
  const allNavBtns = document.querySelectorAll('.sidebar-item, .nav-btn');

  // Deactivate all sections and nav buttons
  sections.forEach(s => s.classList.remove('active'));
  allNavBtns.forEach(b => b.classList.remove('active'));

  // Activate target section
  const section = document.getElementById(viewId);
  if (section) section.classList.add('active');

  // Activate matching sidebar item
  const targetBtns = document.querySelectorAll(`.sidebar-item[data-target="${viewId}"], .nav-btn[data-target="${viewId}"]`);
  targetBtns.forEach(b => b.classList.add('active'));

  // Master Data sidebar button & submenu synchronization
  const isMaster = (viewId === 'view-master');
  const masterToggle = document.getElementById('sidebar-master-toggle');
  if (masterToggle) masterToggle.classList.toggle('active', isMaster);
  const legacyMaster = document.getElementById('nav-btn-master');
  if (legacyMaster) legacyMaster.classList.toggle('active', isMaster);

  const sub = document.getElementById('sidebar-master-sub');
  const chevron = document.getElementById('master-chevron');
  if (isMaster) {
    if (sub) sub.classList.add('open');
    if (chevron) chevron.style.transform = 'rotate(180deg)';
    if (masterToggle) masterToggle.classList.add('submenu-open');
  }

  // Update topbar title
  const titleEl = document.getElementById('topbar-page-title');
  if (titleEl && VIEW_ROUTES[viewId]) {
    titleEl.textContent = VIEW_ROUTES[viewId].title;
  }
}

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  setupNavigation();
  setupEventListeners();

  const isAccountLoggedIn = checkAccountSession();

  if (isAccountLoggedIn) {
    // Early UI restoration to prevent flicker back to POS cashier on refresh
    const initialRoute = parseRouteFromHashOrStorage();
    if (initialRoute && initialRoute.viewId) {
      applyViewUI(initialRoute.viewId, initialRoute.subTab);
    }

    await loadInitialData();
    await initAuth(false); // Langsung ke aplikasi POS, jangan buka tampilan kunci

    // Restore page and trigger view data loader
    if (initialRoute && initialRoute.viewId) {
      navigateToView(initialRoute.viewId, initialRoute.subTab, false, true);
    }
  } else {
    // Preload catalog & settings in background for instant ready upon login
    loadInitialData().catch(e => console.warn('Preload warning:', e));
  }
});

// ==========================================================================
// 0. Landing Page & Store Account Authentication (Layer 1)
// ==========================================================================
function checkAccountSession() {
  const token = localStorage.getItem('aurora_account_token') || sessionStorage.getItem('aurora_account_token');
  const userJson = localStorage.getItem('aurora_account_user') || sessionStorage.getItem('aurora_account_user');

  if (token && userJson) {
    try {
      const user = JSON.parse(userJson);
      state.accountUser = user;
      state.accountToken = token;
      showAppShell();
      updateAccountHeaderUI();

      // Pastikan layar kunci tidak muncul saat sesi akun masih aktif
      const overlay = document.getElementById('login-overlay');
      if (overlay) overlay.classList.add('hidden');

      return true;
    } catch (e) {
      console.warn('Gagal membaca sesi akun:', e);
    }
  }

  // Not logged in -> Show Landing Page
  showLandingPage();
  return false;
}

function showLandingPage() {
  const landing = document.getElementById('landing-page-wrapper');
  const shell = document.getElementById('app-shell');
  const overlay = document.getElementById('login-overlay');

  if (landing) landing.style.display = 'flex';
  if (shell) shell.style.display = 'none';
  if (overlay) overlay.classList.add('hidden');
}

function showAppShell() {
  const landing = document.getElementById('landing-page-wrapper');
  const shell = document.getElementById('app-shell');

  if (landing) landing.style.display = 'none';
  if (shell) shell.style.display = 'flex';
}

function updateAccountHeaderUI() {
  const user = state.accountUser;
  if (!user) return;

  const pinAccEl = document.getElementById('pin-account-name');
  if (pinAccEl) {
    pinAccEl.textContent = `Sesi Toko: ${user.name} (${user.role || 'Admin'})`;
  }
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
    btn.title = 'Sembunyikan password';
  } else {
    input.type = 'password';
    btn.textContent = '👁️';
    btn.title = 'Tampilkan password';
  }
}

function fillLandingCredentials(username, password) {
  const userInput = document.getElementById('landing-username');
  const passInput = document.getElementById('landing-password');
  const errBox = document.getElementById('landing-error-box');

  if (userInput) userInput.value = username;
  if (passInput) passInput.value = password;
  if (errBox) errBox.style.display = 'none';

  api.showToast(`Akun '${username}' siap, silakan klik tombol Masuk`, 'info');
}

async function handleLandingLogin(e) {
  if (e) e.preventDefault();

  const userInput = document.getElementById('landing-username');
  const passInput = document.getElementById('landing-password');
  const rememberCheckbox = document.getElementById('landing-remember-me');
  const errBox = document.getElementById('landing-error-box');
  const errMsg = document.getElementById('landing-error-msg');
  const btnSubmit = document.getElementById('btn-landing-submit');
  const btnText = document.getElementById('btn-landing-text');
  const btnLoader = document.getElementById('btn-landing-loader');

  const username = userInput ? userInput.value.trim() : '';
  const password = passInput ? passInput.value : '';
  const remember = rememberCheckbox ? rememberCheckbox.checked : true;

  if (!username || !password) {
    if (errBox && errMsg) {
      errMsg.textContent = 'Username dan password wajib diisi';
      errBox.style.display = 'flex';
    }
    return;
  }

  // Set loading state
  if (btnSubmit) btnSubmit.disabled = true;
  if (btnText) btnText.style.display = 'none';
  if (btnLoader) btnLoader.style.display = 'inline-flex';
  if (errBox) errBox.style.display = 'none';

  try {
    const res = await api.loginAccount(username, password);

    if (res.success && res.token && res.user) {
      state.accountUser = res.user;
      state.accountToken = res.token;

      // Persist session
      const storage = remember ? localStorage : sessionStorage;
      storage.setItem('aurora_account_token', res.token);
      storage.setItem('aurora_account_user', JSON.stringify(res.user));

      // Reset opposite storage
      if (remember) {
        sessionStorage.removeItem('aurora_account_token');
        sessionStorage.removeItem('aurora_account_user');
      } else {
        localStorage.removeItem('aurora_account_token');
        localStorage.removeItem('aurora_account_user');
      }

      updateAccountHeaderUI();

      // Langsung ke tampilan aplikasi POS
      showAppShell();

      // Pastikan katalog & data master terisi
      if (!state.items || state.items.length === 0) {
        await loadInitialData();
      }

      // Muat daftar petugas kasir
      await loadEmployeesForLogin();

      // Pilih otomatis petugas kasir yang sesuai akun login atau petugas pertama
      let activeCashier = null;
      if (state.employees && state.employees.length > 0) {
        activeCashier = state.employees.find(e => 
          (res.user.username && e.name.toLowerCase().includes(res.user.username.toLowerCase())) || 
          (res.user.name && e.name.toLowerCase().includes(res.user.name.split(' ')[0].toLowerCase()))
        ) || state.employees[0];
      }

      if (activeCashier) {
        state.currentUser = activeCashier;
        state.selectedEmployee = activeCashier;
        sessionStorage.setItem('aurora_pos_user', JSON.stringify(activeCashier));
        updateCashierBadgeUI(activeCashier);
      }

      // Pastikan layar kunci TETAP TERTUTUP (langsung ke aplikasi POS tanpa layar kunci)
      const overlay = document.getElementById('login-overlay');
      if (overlay) {
        overlay.classList.add('hidden');
      }

      // Pastikan view Kasir POS aktif
      navigateToView('view-pos', null, true);

      api.showToast(`Login berhasil! Selamat datang, ${res.user.name}`, 'success');
    } else {
      throw new Error(res.message || 'Login gagal, periksa kredensial');
    }
  } catch (err) {
    console.error('Landing login error:', err);
    if (errBox && errMsg) {
      errMsg.textContent = err.message || 'Username atau password salah';
      errBox.style.display = 'flex';
    }
    api.showToast(err.message || 'Login gagal', 'error');
  } finally {
    if (btnSubmit) btnSubmit.disabled = false;
    if (btnText) btnText.style.display = 'inline';
    if (btnLoader) btnLoader.style.display = 'none';
  }
}

async function logoutAccountToLanding() {
  if (!confirm('Apakah Anda yakin ingin keluar dari akun toko dan kembali ke landing page?')) {
    return;
  }

  try {
    await api.logoutAccount();
  } catch (e) {
    console.warn('Logout API note:', e);
  }

  // Clear storage
  localStorage.removeItem('aurora_account_token');
  localStorage.removeItem('aurora_account_user');
  sessionStorage.removeItem('aurora_account_token');
  sessionStorage.removeItem('aurora_account_user');
  sessionStorage.removeItem('aurora_pos_user');
  sessionStorage.removeItem('aurora_current_view');
  sessionStorage.removeItem('aurora_master_subtab');
  sessionStorage.removeItem('aurora_settings_subtab');
  sessionStorage.removeItem('aurora_attendance_subtab');
  localStorage.removeItem('aurora_last_view');
  localStorage.removeItem('aurora_master_subtab');
  localStorage.removeItem('aurora_settings_subtab');
  localStorage.removeItem('aurora_attendance_subtab');

  try {
    window.history.replaceState(null, '', window.location.pathname);
  } catch (e) {
    window.location.hash = '';
  }

  state.accountUser = null;
  state.accountToken = null;
  state.currentUser = null;
  state.activeView = 'view-pos';

  // Clear landing password field
  const passInput = document.getElementById('landing-password');
  if (passInput) passInput.value = '';

  showLandingPage();
  api.showToast('Anda telah keluar dari akun toko', 'info');
}

// ==========================================================================
// Authentication & Fast PIN Lock System (Layer 2)
// ==========================================================================
async function initAuth(shouldLock = false) {
  await loadEmployeesForLogin();
  const overlay = document.getElementById('login-overlay');

  updateAccountHeaderUI();

  // Layar kunci hanya tampil jika diminta secara eksplisit (misal saat klik tombol Kunci)
  if (overlay) {
    if (shouldLock) {
      overlay.classList.remove('hidden');
    } else {
      overlay.classList.add('hidden');
    }
  }

  // Jika ada sesi kasir sebelumnya, pilih kasir tersebut
  const savedUser = sessionStorage.getItem('aurora_pos_user');
  if (savedUser) {
    try {
      const user = JSON.parse(savedUser);
      state.currentUser = user;
      state.selectedEmployee = user;
      updateCashierBadgeUI(user);
      if (user && user.id) {
        selectLoginEmployee(user.id);
      }
    } catch (e) {
      console.warn('Session parse warning:', e);
    }
  } else if (state.employees && state.employees.length > 0) {
    state.currentUser = state.employees[0];
    state.selectedEmployee = state.employees[0];
    sessionStorage.setItem('aurora_pos_user', JSON.stringify(state.employees[0]));
    updateCashierBadgeUI(state.employees[0]);
  }

  clearPin();
}

async function loadEmployeesForLogin() {
  try {
    const emps = await api.getEmployees(state.activeOutletId);
    state.employees = emps;
    
    // Isi Dropdown Petugas Kasir di Layar Kunci
    const select = document.getElementById('login-employee-select');
    if (select) {
      if (!emps || emps.length === 0) {
        select.innerHTML = '<option value="">(Tidak ada data petugas)</option>';
      } else {
        select.innerHTML = emps.map(emp => {
          const isSelected = state.selectedEmployee ? (state.selectedEmployee.id === emp.id) : false;
          const roleText = emp.role_name || 'Petugas Kasir';
          return `<option value="${emp.id}" ${isSelected ? 'selected' : ''}>👤 ${emp.name} (${roleText})</option>`;
        }).join('');

        if (!state.selectedEmployee && emps.length > 0) {
          state.selectedEmployee = emps[0];
          select.value = emps[0].id;
        } else if (state.selectedEmployee) {
          select.value = state.selectedEmployee.id;
        }
      }
    }

    // Dukungan kontainer list jika ada
    const container = document.getElementById('login-employee-list');
    if (container && emps && emps.length > 0) {
      container.innerHTML = emps.map((emp, idx) => {
        const isSelected = state.selectedEmployee ? (state.selectedEmployee.id === emp.id) : (idx === 0);
        const initial = emp.name ? emp.name.charAt(0).toUpperCase() : '👤';
        const roleText = emp.role_name || 'Petugas Kasir';
        return `
          <div class="login-emp-pill ${isSelected ? 'selected' : ''}" onclick="selectLoginEmployee(${emp.id})" id="emp-pill-${emp.id}" title="Pilih ${emp.name}">
            <div class="login-emp-avatar">${initial}</div>
            <div class="login-emp-info">
              <div class="login-emp-name">${emp.name}</div>
              <div class="login-emp-role">${roleText}</div>
            </div>
            <div class="login-emp-radio">
              <span class="radio-check">✓</span>
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (e) {
    console.warn('Error loading employees for login:', e);
  }
}

function handleSelectEmployeeChange(empId) {
  if (empId) {
    selectLoginEmployee(parseInt(empId));
  }
}

function selectLoginEmployee(empId) {
  const emp = state.employees.find(e => e.id === empId);
  if (!emp) return;
  state.selectedEmployee = emp;

  // Sinkronisasi nilai Dropdown
  const select = document.getElementById('login-employee-select');
  if (select && select.value != empId) {
    select.value = empId;
  }

  // Sinkronisasi pill list jika ada
  document.querySelectorAll('.login-emp-pill').forEach(p => p.classList.remove('selected'));
  const pill = document.getElementById(`emp-pill-${empId}`);
  if (pill) pill.classList.add('selected');

  clearPin();
  focusPinInput();
}

function focusPinInput() {
  const input = document.getElementById('pin-hidden-input');
  if (input) {
    try { input.focus(); } catch (e) {}
  }
}

function syncHiddenPinInput(val) {
  const clean = val.replace(/\D/g, '').slice(0, 4);
  state.pinInput = clean;
  updatePinDots();
  if (clean.length === 4) {
    setTimeout(() => submitPinLogin(), 120);
  }
}

function handlePinDigit(digit) {
  if (state.pinInput.length >= 4) return;
  state.pinInput += digit;
  const input = document.getElementById('pin-hidden-input');
  if (input) input.value = state.pinInput;
  updatePinDots();

  if (state.pinInput.length === 4) {
    setTimeout(() => submitPinLogin(), 120);
  }
}

function updatePinDots() {
  for (let i = 0; i < 4; i++) {
    const dot = document.getElementById(`pdot-${i}`);
    if (dot) {
      if (i < state.pinInput.length) {
        dot.classList.add('filled');
      } else {
        dot.classList.remove('filled');
      }
    }
  }
}

function clearPin() {
  state.pinInput = '';
  const input = document.getElementById('pin-hidden-input');
  if (input) input.value = '';
  updatePinDots();
}

function backspacePin() {
  if (state.pinInput.length > 0) {
    state.pinInput = state.pinInput.slice(0, -1);
    const input = document.getElementById('pin-hidden-input');
    if (input) input.value = state.pinInput;
    updatePinDots();
  }
}

function quickFillPin(empId, pin) {
  selectLoginEmployee(empId);
  state.pinInput = String(pin).trim();
  const input = document.getElementById('pin-hidden-input');
  if (input) input.value = state.pinInput;
  updatePinDots();
  setTimeout(() => submitPinLogin(), 100);
}

async function submitPinLogin() {
  if (state.pinInput.length < 4) {
    api.showToast('Masukkan 4-digit PIN lengkap', 'info');
    return;
  }

  const outletId = state.activeOutletId || 1;
  const employeeId = state.selectedEmployee ? state.selectedEmployee.id : null;

  try {
    const res = await api.verifyPin(outletId, state.pinInput, employeeId);
    if (res.success && res.employee) {
      state.currentUser = res.employee;
      sessionStorage.setItem('aurora_pos_user', JSON.stringify(res.employee));
      updateCashierBadgeUI(res.employee);

      const overlay = document.getElementById('login-overlay');
      if (overlay) overlay.classList.add('hidden');

      api.showToast(`Selamat datang, ${res.employee.name}!`, 'success');
      clearPin();
    }
  } catch (err) {
    console.error('Login PIN error:', err);
    const card = document.getElementById('login-card');
    if (card) {
      card.classList.add('shake');
      setTimeout(() => card.classList.remove('shake'), 400);
    }
    const msg = err.message && err.message !== 'Terjadi kesalahan sistem' ? err.message : 'PIN tidak valid! Silakan periksa kembali.';
    api.showToast(msg, 'error');
    clearPin();
  }
}

function updateCashierBadgeUI(user) {
  if (!user) return;
  const initial = user.name ? user.name.charAt(0).toUpperCase() : '?';
  const role = user.role_name || user.role || 'Kasir';

  // Topbar cashier profile badge
  const topbarInitial = document.getElementById('topbar-user-initial');
  if (topbarInitial) topbarInitial.textContent = initial;
  const topbarName = document.getElementById('topbar-cashier-name');
  if (topbarName) topbarName.textContent = user.name;
  const topbarRole = document.getElementById('topbar-cashier-role');
  if (topbarRole) topbarRole.textContent = role;

  // Sidebar cashier card
  const sidebarInitial = document.getElementById('sidebar-user-initial');
  if (sidebarInitial) sidebarInitial.textContent = initial;
  const sidebarName = document.getElementById('sidebar-cashier-name');
  if (sidebarName) sidebarName.textContent = user.name;
  const sidebarRole = document.getElementById('sidebar-cashier-role');
  if (sidebarRole) sidebarRole.textContent = role;

  // Legacy badges
  const nameEl = document.getElementById('cashier-name-badge');
  const roleEl = document.getElementById('cashier-role-badge');
  if (nameEl) nameEl.innerText = user.name;
  if (roleEl) roleEl.innerText = role;
}

function lockPOS() {
  const overlay = document.getElementById('login-overlay');
  if (overlay) {
    updateAccountHeaderUI();
    overlay.classList.remove('hidden');
    clearPin();
    if (state.currentUser) {
      selectLoginEmployee(state.currentUser.id);
    } else if (state.employees && state.employees.length > 0) {
      selectLoginEmployee(state.employees[0].id);
    }
    focusPinInput();
  }
}

// ==========================================================================
// Theme Management (Putih Susu + Biru Hijau ⇋ Deep Forest Emerald)
// ==========================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('aurora_cafe_theme') || 'light';
  applyTheme(savedTheme);
}

function toggleTheme() {
  const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  const themeName = nextTheme === 'light' ? 'Putih Susu + Biru Hijau' : 'Deep Forest Emerald';
  api.showToast(`Tampilan beralih ke mode ${themeName}`, 'info');
}

function applyTheme(theme) {
  state.theme = theme;
  localStorage.setItem('aurora_cafe_theme', theme);

  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }

  const iconEl = document.getElementById('theme-icon');
  if (iconEl) {
    iconEl.innerText = theme === 'dark' ? '☀️' : '🌙';
  }
  const landingIconEl = document.getElementById('landing-theme-icon');
  if (landingIconEl) {
    landingIconEl.innerText = theme === 'dark' ? '☀️' : '🌙';
  }
  // Update sidebar theme hint if present
  const textEl = document.getElementById('theme-text');
  if (textEl) {
    textEl.innerText = theme === 'dark' ? 'Mode Putih' : 'Mode Gelap';
  }
}

// ==========================================================================
// Tab Navigation & View Management
// ==========================================================================
function setupNavigation() {
  const navBtns = document.querySelectorAll('.nav-btn[data-target], .sidebar-item[data-target]');

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      if (!targetId) return;
      navigateToView(targetId, null, true);
    });
  });

  // Legacy dropdown outside click handler (kept for compatibility)
  document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('master-dropdown-menu');
    const dropdownBtn = document.getElementById('nav-btn-master');
    if (dropdown && dropdownBtn && !dropdownBtn.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });

  // Listen to browser Back / Forward buttons
  window.addEventListener('hashchange', () => {
    const token = localStorage.getItem('aurora_account_token') || sessionStorage.getItem('aurora_account_token');
    if (token) {
      const route = parseRouteFromHashOrStorage();
      if (route && route.viewId) {
        navigateToView(route.viewId, route.subTab, false);
      }
    }
  });
}

function navigateToView(targetId, subTab = null, updateHash = true, forceLoad = false) {
  const viewId = targetId.startsWith('view-') ? targetId : `view-${targetId}`;
  if (!VIEW_ROUTES[viewId]) return;

  // Apply UI active classes immediately
  applyViewUI(viewId, subTab);

  // Close mobile sidebar after navigation
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.remove('mobile-open');

  // Save active view state
  state.activeView = viewId;
  sessionStorage.setItem('aurora_current_view', viewId);
  localStorage.setItem('aurora_last_view', viewId);

  // Sub-tab handling & storage
  if (viewId === 'view-master' && subTab) {
    state.activeMasterTab = subTab;
    sessionStorage.setItem('aurora_master_subtab', subTab);
    localStorage.setItem('aurora_master_subtab', subTab);
  } else if (viewId === 'view-settings' && subTab) {
    state.activeSettingTab = subTab;
    sessionStorage.setItem('aurora_settings_subtab', subTab);
    localStorage.setItem('aurora_settings_subtab', subTab);
  } else if (viewId === 'view-attendance' && subTab) {
    state.activeAttendanceTab = subTab;
    sessionStorage.setItem('aurora_attendance_subtab', subTab);
    localStorage.setItem('aurora_attendance_subtab', subTab);
  }

  // Update URL hash
  if (updateHash) {
    const hash = getViewHash(viewId, subTab);
    if (window.location.hash !== hash) {
      try {
        window.history.replaceState(null, '', hash);
      } catch (e) {
        window.location.hash = hash;
      }
    }
  }

  // Load view data
  loadViewData(viewId, subTab, forceLoad);
}

function loadViewData(viewId, subTab = null, forceLoad = false) {
  if (viewId === 'view-dashboard') {
    loadDashboard();
  } else if (viewId === 'view-tables') {
    loadFloorMap();
  } else if (viewId === 'view-inventory') {
    loadInventory();
  } else if (viewId === 'view-shifts') {
    loadShiftsAndHistory();
  } else if (viewId === 'view-attendance') {
    loadAttendance().then(() => {
      const tab = subTab || state.activeAttendanceTab || sessionStorage.getItem('aurora_attendance_subtab') || 'cards';
      switchAttendanceTab(tab, false);
    }).catch(e => console.warn('Attendance load note:', e));
  } else if (viewId === 'view-master') {
    const tab = subTab || state.activeMasterTab || sessionStorage.getItem('aurora_master_subtab') || 'kategori';
    openMasterTab(tab, false);
  } else if (viewId === 'view-settings') {
    const tab = subTab || state.activeSettingTab || sessionStorage.getItem('aurora_settings_subtab') || 'toko';
    openSettingsTab(tab, false);
  }
}

// ==========================================================================
// Initial Data Loader
// ==========================================================================
async function loadInitialData() {
  try {
    // 0. Load Brand & Outlet from database
    try {
      const brands = await api.getBrands();
      if (brands && brands.length > 0) {
        state.brand = brands[0];
        state.activeBrandId = state.brand.id;
        const outlets = await api.getOutlets(state.brand.id);
        state.outlets = outlets;
        const currentOutlet = outlets.find(o => o.id === state.activeOutletId) || outlets[0];
        state.outlet = currentOutlet;
        if (currentOutlet) state.activeOutletId = currentOutlet.id;

        // Update brand in sidebar
        const brandTitleEl = document.getElementById('brand-header-title');
        const brandSubEl = document.getElementById('brand-badge-text');
        const brandAddressEl = document.getElementById('brand-header-address');
        if (brandTitleEl) brandTitleEl.textContent = state.brand.name;
        if (brandSubEl && currentOutlet) brandSubEl.textContent = currentOutlet.name || 'Outlet';
        if (brandAddressEl && currentOutlet) {
          brandAddressEl.innerText = currentOutlet.address || currentOutlet.name;
        }
        if (state.brand && state.brand.logo) {
          const logoEl = document.querySelector('.sidebar-logo');
          if (logoEl) {
            logoEl.innerHTML = `<img src="${state.brand.logo}" alt="Logo" style="width:100%;height:100%;object-fit:cover;border-radius:var(--radius-md);" onerror="this.innerHTML='☕'">`;
          }
        }
        // Also update login screen brand
        const loginBrandEl = document.getElementById('login-brand-title');
        if (loginBrandEl) loginBrandEl.textContent = state.brand.name;
        document.title = `${state.brand.name}: POS & Management`;
      }
    } catch (e) {
      console.warn('Brand/Outlet info load warning:', e);
    }

    // Load receipt settings
    try {
      state.receiptSettings = await api.getReceiptSettings(state.activeOutletId);
    } catch (e) {
      console.warn('Receipt settings load warning:', e);
    }

    // 1. Shift check
    const shift = await api.getCurrentShift(state.activeOutletId);
    state.currentShift = shift;
    updateShiftUI(shift);

    // 2. Load Tables for selector
    const tables = await api.getTables(state.activeOutletId);
    state.tables = tables;
    populateTableSelector(tables);

    // 3. Load Categories
    const categories = await api.getCategories(state.activeBrandId);
    state.categories = categories;
    renderCategories(categories);

    // 4. Load Items
    const items = await api.getItems(state.activeBrandId);
    state.items = items;
    renderProducts(items);

  } catch (err) {
    console.error('Error loading initial data:', err);
    api.showToast('Gagal memuat data awal server', 'error');
  }
}

function updateShiftUI(shift) {
  const badge = document.getElementById('shift-status-badge');
  if (!badge) return;

  if (shift && shift.status === 'open') {
    badge.innerHTML = `<span class="status-pulse"></span> Shift Aktif: ${shift.employee_name || 'Kasir'}`;
    badge.className = 'status-badge';
    badge.style.color = '';
    badge.style.borderColor = '';
    badge.style.background = '';
  } else {
    badge.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:var(--accent-red);display:inline-block;"></span> Shift Tutup`;
    badge.className = 'status-badge';
    badge.style.color = 'var(--accent-red)';
    badge.style.borderColor = 'var(--accent-red-border)';
    badge.style.background = 'var(--accent-red-bg)';
  }
}

function populateTableSelector(tables) {
  const select = document.getElementById('pos-table-select');
  if (!select) return;
  select.innerHTML = '<option value="">-- Pilih Meja / Pesanan Langsung --</option>';
  tables.forEach(t => {
    const isOccupied = t.status === 'occupied' ? ' 🔴 (Terisi)' : ' 🟢 (Kosong)';
    select.innerHTML += `<option value="${t.id}">${t.table_number}${isOccupied} (${t.capacity} org)</option>`;
  });
}

// ==========================================================================
// Category Pills & Product Filtering
// ==========================================================================
function renderCategories(categories) {
  const container = document.getElementById('pos-category-pills');
  if (!container) return;

  container.innerHTML = `
    <button class="cat-pill active" data-cat="all">Semua Menu</button>
    ${categories.map(c => `<button class="cat-pill" data-cat="${c.id}">${c.name}</button>`).join('')}
  `;

  container.querySelectorAll('.cat-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.selectedCategory = btn.getAttribute('data-cat');
      filterAndRenderProducts();
    });
  });
}

function filterAndRenderProducts() {
  let filtered = state.items.filter(i => i.is_active !== 0 && i.is_active !== false);

  if (state.selectedCategory !== 'all') {
    const catId = parseInt(state.selectedCategory);
    filtered = filtered.filter(i => i.category_id === catId);
  }

  if (state.searchQuery.trim() !== '') {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(i => i.name.toLowerCase().includes(q) || (i.sku && i.sku.toLowerCase().includes(q)));
  }

  renderProducts(filtered);
}

function renderProducts(items) {
  const grid = document.getElementById('pos-products-grid');
  if (!grid) return;

  if (items.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">🔍</div>
        <p style="font-weight:600;font-size:1.05rem;">Tidak ada menu yang sesuai</p>
        <p style="font-size:0.85rem;margin-top:4px;">Coba gunakan kata kunci pencarian atau kategori lain.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = items.map(item => `
    <div class="product-card" onclick="handleItemClick(${item.id})">
      <div class="product-img-wrapper">
        <img src="${item.image_url || '/static/img/coffee.jpg'}" alt="${item.name}" loading="lazy" onerror="this.src='/static/img/coffee.jpg'" />
        <span class="product-badge">${item.category_name || 'Roastery'}</span>
      </div>
      <div class="product-details">
        <div>
          <h4 class="product-title">${item.name}</h4>
          <p class="product-desc">${item.description || 'Racikan istimewa biji kopi pilihan dengan cita rasa khas Aurora.'}</p>
        </div>
        <div class="product-footer">
          <span class="product-price">${api.formatRupiah(item.price)}</span>
          <button class="btn-add-item" onclick="event.stopPropagation(); handleItemClick(${item.id})" title="Pilih ukuran & tambah ke keranjang">+</button>
        </div>
      </div>
    </div>
  `).join('');
}

// ==========================================================================
// Cart & Modifiers Logic (Interactive Size Selection)
// ==========================================================================
function handleItemClick(itemId) {
  const item = state.items.find(i => i.id === itemId);
  if (!item) return;

  if (item.modifiers && item.modifiers.length > 0) {
    openModifierModal(item);
  } else {
    addToCart(item, []);
  }
}

function openModifierModal(item) {
  state.activeItemForModifier = item;
  const modal = document.getElementById('modifier-modal');
  const title = document.getElementById('mod-modal-title');
  const body = document.getElementById('mod-modal-body');

  if (title) title.innerText = `Pilih Ukuran & Varian Menu`;

  const isBeverage = (item.category_name || '').toLowerCase().includes('kopi') || 
                     (item.category_name || '').toLowerCase().includes('tea') || 
                     (item.category_name || '').toLowerCase().includes('minuman') || 
                     item.name.toLowerCase().includes('latte') || 
                     item.name.toLowerCase().includes('espresso') || 
                     item.name.toLowerCase().includes('kopi');

  const defaultIcon = isBeverage ? '🥤' : '🍽️';

  let html = `
    <div class="mod-item-banner">
      <img src="${item.image_url || '/static/img/coffee.jpg'}" alt="${item.name}" class="mod-item-img" onerror="this.src='/static/img/coffee.jpg'" />
      <div class="mod-item-meta">
        <h4>${item.name}</h4>
        <p>${item.category_name || 'Katalog Menu'}</p>
        <div class="mod-item-base-price">Harga Dasar: ${api.formatRupiah(item.price)}</div>
      </div>
    </div>
  `;

  // Sort modifiers to match standard cafe flow: 1) Level Gula, 2) Extra Topping, 3) Pilihan Ukuran
  const sortedModifiers = [...(item.modifiers || [])].sort((a, b) => {
    const getPriority = (mod) => {
      const name = (mod.name || '').toLowerCase();
      if (name.includes('gula') || name.includes('sugar') || name.includes('sweet')) return 1;
      if (name.includes('topping') || name.includes('toping') || name.includes('add-on')) return 2;
      if (name.includes('ukuran') || name.includes('size') || name.includes('porsi')) return 3;
      return 4;
    };
    return getPriority(a) - getPriority(b);
  });

  // Render each modifier group
  html += sortedModifiers.map(mod => {
    const isSizeGroup = mod.name.toLowerCase().includes('ukuran') || mod.name.toLowerCase().includes('size');
    const isSugarGroup = mod.name.toLowerCase().includes('gula') || mod.name.toLowerCase().includes('sugar');
    const isToppingGroup = mod.name.toLowerCase().includes('topping') || mod.name.toLowerCase().includes('toping') || mod.name.toLowerCase().includes('add-on');

    let groupIcon = '✨';
    if (isSizeGroup) groupIcon = '📏';
    else if (isSugarGroup) groupIcon = '🍯';
    else if (isToppingGroup) groupIcon = '🍨';

    if (isSizeGroup) {
      return `
        <div class="modifier-group">
          <div class="modifier-group-title">
            <span>${groupIcon} ${mod.name}</span>
            <span class="modifier-group-badge">Wajib Pilih 1</span>
          </div>
          <div class="size-cards-grid">
            ${mod.options.map((opt, optIdx) => {
              const isLarge = opt.name.toLowerCase().includes('large');
              const isJumbo = opt.name.toLowerCase().includes('jumbo') || opt.name.toLowerCase().includes('extra');

              let desc = 'Porsi Standar';
              if (isLarge) {
                desc = 'Porsi Lebih Puas';
              } else if (isJumbo) {
                desc = 'Porsi Maksimal Extra';
              }

              return `
                <div class="size-card ${optIdx === 0 ? 'selected' : ''}" onclick="selectSizeOptionCard(this, '${opt.id}', 'mod_${mod.id}')">
                  <input type="radio" name="mod_${mod.id}" value="${opt.id}" data-name="${opt.name}" data-price="${opt.additional_price}" data-group="${mod.name}" ${optIdx === 0 ? 'checked' : ''} />
                  <div class="size-card-icon">${defaultIcon}</div>
                  <div class="size-card-name">${opt.name.replace(/\(\+Rp.*?\)/i, '').trim()}</div>
                  <div class="size-card-desc">${desc}</div>
                  <div class="size-card-price">${opt.additional_price > 0 ? `+${api.formatRupiah(opt.additional_price)}` : 'Termasuk'}</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    } else {
      // Non-size modifier (e.g. Sugar, Topping)
      const isSingle = mod.max_selection === 1;
      return `
        <div class="modifier-group">
          <div class="modifier-group-title">
            <span>${groupIcon} ${mod.name}</span>
            <span class="modifier-group-badge">${isSingle ? 'Pilih 1' : 'Bisa Pilih Lebih'}</span>
          </div>
          <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            ${mod.options.map((opt, optIdx) => `
              <label class="mod-option-row ${(isSingle && optIdx === 0) ? 'selected' : ''}" onclick="handleOptionRowClick(this)">
                <div class="mod-option-left">
                  <input type="${isSingle ? 'radio' : 'checkbox'}" name="mod_${mod.id}" value="${opt.id}" data-name="${opt.name}" data-price="${opt.additional_price}" data-group="${mod.name}" class="mod-option-input" ${(isSingle && optIdx === 0) ? 'checked' : ''} onchange="updateModifierModalPrice()" />
                  <span class="mod-option-name">${opt.name}</span>
                </div>
                <span class="mod-option-price">${opt.additional_price > 0 ? `+${api.formatRupiah(opt.additional_price)}` : 'Gratis'}</span>
              </label>
            `).join('')}
          </div>
        </div>
      `;
    }
  }).join('');

  // Live Price Bar
  html += `
    <div class="mod-modal-price-bar">
      <div>
        <div class="mod-live-label">Total Harga Item</div>
        <div class="mod-live-breakdown" id="mod-price-breakdown">Harga Dasar + Pilihan Ukuran</div>
      </div>
      <div class="mod-live-total" id="mod-price-total">${api.formatRupiah(item.price)}</div>
    </div>
  `;

  body.innerHTML = html;
  updateModifierModalPrice();
  modal.classList.add('active');
}

function selectSizeOptionCard(cardEl, optId, groupName) {
  const container = cardEl.closest('.size-cards-grid');
  if (container) {
    container.querySelectorAll('.size-card').forEach(c => c.classList.remove('selected'));
  }
  cardEl.classList.add('selected');
  const radio = cardEl.querySelector('input[type="radio"]');
  if (radio) {
    radio.checked = true;
  }
  updateModifierModalPrice();
}

function handleOptionRowClick(rowEl) {
  setTimeout(() => {
    const input = rowEl.querySelector('input');
    if (!input) return;
    if (input.type === 'radio') {
      const parent = rowEl.closest('.modifier-group');
      if (parent) {
        parent.querySelectorAll('.mod-option-row').forEach(r => r.classList.remove('selected'));
      }
      if (input.checked) rowEl.classList.add('selected');
    } else {
      rowEl.classList.toggle('selected', input.checked);
    }
    updateModifierModalPrice();
  }, 10);
}

function updateModifierModalPrice() {
  if (!state.activeItemForModifier) return;
  const body = document.getElementById('mod-modal-body');
  if (!body) return;

  const basePrice = state.activeItemForModifier.price;
  let addedPrice = 0;

  body.querySelectorAll('input:checked').forEach(input => {
    const p = parseFloat(input.getAttribute('data-price')) || 0;
    addedPrice += p;
  });

  const totalPrice = basePrice + addedPrice;

  const totalEl = document.getElementById('mod-price-total');
  const breakdownEl = document.getElementById('mod-price-breakdown');
  if (totalEl) totalEl.innerText = api.formatRupiah(totalPrice);
  if (breakdownEl) {
    breakdownEl.innerText = `${api.formatRupiah(basePrice)} + Tambahan ${api.formatRupiah(addedPrice)}`;
  }

  const submitBtn = document.getElementById('btn-confirm-modifier');
  if (submitBtn) {
    submitBtn.innerText = `Tambahkan ke Pesanan (${api.formatRupiah(totalPrice)})`;
  }
}

function closeModifierModal() {
  document.getElementById('modifier-modal').classList.remove('active');
  state.activeItemForModifier = null;
}

function confirmModifierAddToCart() {
  if (!state.activeItemForModifier) return;
  const body = document.getElementById('mod-modal-body');
  const selectedOptions = [];

  body.querySelectorAll('input:checked').forEach(input => {
    selectedOptions.push({
      modifier_option_id: parseInt(input.value),
      name: input.getAttribute('data-name'),
      group_name: input.getAttribute('data-group') || '',
      additional_price: parseFloat(input.getAttribute('data-price')) || 0
    });
  });

  addToCart(state.activeItemForModifier, selectedOptions);
  closeModifierModal();
}

function addToCart(item, selectedModifiers) {
  const modTotal = selectedModifiers.reduce((acc, m) => acc + m.additional_price, 0);
  const modKey = selectedModifiers.map(m => m.modifier_option_id).sort().join('-');
  const cartKey = `${item.id}_${modKey}`;

  const existing = state.cart.find(c => c.cartKey === cartKey);
  if (existing) {
    existing.quantity += 1;
  } else {
    state.cart.push({
      cartKey,
      item_id: item.id,
      name: item.name,
      base_price: item.price,
      unit_price: item.price + modTotal,
      quantity: 1,
      modifiers: selectedModifiers,
      notes: ''
    });
  }

  renderCart();
  api.showToast(`Ditambahkan: ${item.name}`);
}

function updateCartQty(cartKey, delta) {
  const idx = state.cart.findIndex(c => c.cartKey === cartKey);
  if (idx === -1) return;

  state.cart[idx].quantity += delta;
  if (state.cart[idx].quantity <= 0) {
    state.cart.splice(idx, 1);
  }

  renderCart();
}

function applyPromoCode() {
  const input = document.getElementById('cart-promo-code');
  if (!input) return;
  const code = input.value.trim().toUpperCase();

  if (!code) {
    api.showToast('Silakan masukkan kode voucher', 'info');
    return;
  }

  if (code === 'AURORAPAS' || code === 'HEMAT10' || code === 'KOPIENAK') {
    state.appliedPromo = { code, discount_amount: 10000 };
    api.showToast(`Voucher ${code} aktif! Diskon Rp 10.000 diterapkan.`, 'success');
  } else if (code === 'AURORA20' || code === 'DISCOUNT20') {
    state.appliedPromo = { code, discount_amount: 20000 };
    api.showToast(`Voucher ${code} aktif! Diskon Rp 20.000 diterapkan.`, 'success');
  } else {
    api.showToast('Kode voucher tidak valid atau sudah kedaluwarsa', 'error');
    state.appliedPromo = null;
  }

  renderCart();
}

function renderCart() {
  const container = document.getElementById('pos-cart-items');
  const checkoutBtn = document.getElementById('btn-pos-checkout');
  const subtotalEl = document.getElementById('cart-subtotal');
  const discountRow = document.getElementById('discount-row');
  const discountEl = document.getElementById('cart-discount');
  const taxEl = document.getElementById('cart-tax');
  const gratuityEl = document.getElementById('cart-gratuity');
  const totalEl = document.getElementById('cart-total');
  const countBadge = document.getElementById('cart-count-badge');

  const totalQty = state.cart.reduce((sum, i) => sum + i.quantity, 0);
  countBadge.innerText = `${totalQty} item`;

  if (state.cart.length === 0) {
    container.innerHTML = `
      <div class="empty-cart-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="9" cy="21" r="1"></circle>
          <circle cx="20" cy="21" r="1"></circle>
          <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
        </svg>
        <p style="font-weight:600;font-size:0.95rem;">Keranjang Masih Kosong</p>
        <p style="font-size:0.8rem;color:var(--text-muted);">Pilih menu dari katalog untuk memulai pesanan kasir.</p>
      </div>
    `;
    subtotalEl.innerText = api.formatRupiah(0);
    if (discountRow) discountRow.style.display = 'none';
    taxEl.innerText = api.formatRupiah(0);
    gratuityEl.innerText = api.formatRupiah(0);
    totalEl.innerText = api.formatRupiah(0);
    checkoutBtn.disabled = true;
    return;
  }

  container.innerHTML = state.cart.map(c => `
    <div class="cart-item">
      <div class="cart-item-top">
        <div style="flex:1;">
          <div class="cart-item-title">${c.name}</div>
          ${c.modifiers && c.modifiers.length > 0 ? `
            <div class="cart-mod-pills">
              ${c.modifiers.map(m => {
                const isSize = m.name.toLowerCase().includes('regular') || m.name.toLowerCase().includes('large') || m.name.toLowerCase().includes('jumbo') || (m.group_name && (m.group_name.toLowerCase().includes('ukuran') || m.group_name.toLowerCase().includes('size')));
                return isSize 
                  ? `<span class="cart-size-badge">🥤 ${m.name.replace(/\(\+Rp.*?\)/i, '').trim()}</span>`
                  : `<span class="cart-mod-badge">✨ ${m.name}</span>`;
              }).join('')}
            </div>
          ` : ''}
        </div>
        <button onclick="updateCartQty('${c.cartKey}', -${c.quantity})" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.2rem;line-height:1;padding:2px 6px;" title="Hapus item">&times;</button>
      </div>
      <div class="cart-item-bottom">
        <div class="qty-control">
          <button class="qty-btn" onclick="updateCartQty('${c.cartKey}', -1)">-</button>
          <span class="qty-num">${c.quantity}</span>
          <button class="qty-btn" onclick="updateCartQty('${c.cartKey}', 1)">+</button>
        </div>
        <div class="cart-item-total">${api.formatRupiah(c.unit_price * c.quantity)}</div>
      </div>
    </div>
  `).join('');

  // Calculations
  const subtotal = state.cart.reduce((sum, i) => sum + (i.unit_price * i.quantity), 0);
  let discount = 0;
  if (state.appliedPromo) {
    discount = Math.min(subtotal, state.appliedPromo.discount_amount || 0);
  }

  const taxableAmount = Math.max(0, subtotal - discount);
  const gratuity = Math.round(taxableAmount * 0.05); // 5% Service
  const taxCfg = getActiveTaxConfig();
  const tax = taxCfg.enabled ? Math.round((taxableAmount + gratuity) * (taxCfg.rate / 100)) : 0;
  const grandTotal = taxableAmount + gratuity + tax;

  subtotalEl.innerText = api.formatRupiah(subtotal);

  if (discountRow && discountEl) {
    if (discount > 0) {
      discountRow.style.display = 'flex';
      discountEl.innerText = `- ${api.formatRupiah(discount)}`;
    } else {
      discountRow.style.display = 'none';
    }
  }

  const cartTaxRow = document.getElementById('cart-tax-row');
  if (cartTaxRow) {
    cartTaxRow.style.display = taxCfg.enabled ? 'flex' : 'none';
  }

  const cartTaxLabel = document.getElementById('cart-tax-label');
  if (cartTaxLabel) {
    cartTaxLabel.innerText = `Pajak (${taxCfg.name} ${taxCfg.rate}%):`;
  }
  taxEl.innerText = api.formatRupiah(tax);
  totalEl.innerText = api.formatRupiah(grandTotal);
  checkoutBtn.disabled = false;
}

function getActiveTaxConfig() {
  const rs = state.receiptSettings || {};
  const enabled = rs.tax_enabled !== false && rs.tax_enabled !== 'false' && rs.tax_enabled !== 0;
  const rate = (typeof rs.tax_rate === 'number') ? rs.tax_rate : parseFloat(rs.tax_rate || '10.0') || 0.0;
  const name = rs.tax_name || 'PB1 / Pajak Restoran';
  const showOnReceipt = rs.show_tax_on_receipt !== false && rs.show_tax_on_receipt !== 'false';
  const paperWidth = rs.paper_width || state.receiptPaperWidth || '58mm';
  return { enabled, rate, name, showOnReceipt, paperWidth };
}

// ==========================================================================
// Payment & Checkout Modal
// ==========================================================================
function openPaymentModal() {
  if (state.cart.length === 0) return;

  const modal = document.getElementById('payment-modal');
  const subtotal = state.cart.reduce((sum, i) => sum + (i.unit_price * i.quantity), 0);
  let discount = 0;
  if (state.appliedPromo) {
    discount = Math.min(subtotal, state.appliedPromo.discount_amount || 0);
  }
  const taxableAmount = Math.max(0, subtotal - discount);
  const gratuity = Math.round(taxableAmount * 0.05);
  const taxCfg = getActiveTaxConfig();
  const tax = taxCfg.enabled ? Math.round((taxableAmount + gratuity) * (taxCfg.rate / 100)) : 0;
  const grandTotal = taxableAmount + gratuity + tax;

  document.getElementById('pay-modal-total').innerText = api.formatRupiah(grandTotal);
  document.getElementById('pay-modal-total').setAttribute('data-amount', grandTotal);

  // Default to cash tab & reset cash input
  setPaymentMethod('Cash');
  document.getElementById('cash-input').value = grandTotal;
  handleCashInputChange();

  modal.classList.add('active');
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.remove('active');
}

function setPaymentMethod(method) {
  state.activePaymentMethod = method;
  document.querySelectorAll('.pay-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-method') === method);
  });

  const cashPanel = document.getElementById('pay-panel-cash');
  const qrisPanel = document.getElementById('pay-panel-qris');
  const bankPanel = document.getElementById('pay-panel-bank');

  cashPanel.style.display = method === 'Cash' ? 'block' : 'none';
  qrisPanel.style.display = method === 'QRIS' ? 'block' : 'none';
  bankPanel.style.display = method === 'Bank Transfer' ? 'block' : 'none';

  if (method === 'QRIS') {
    loadQRISDisplay();
  }
}

function setQuickCash(amount) {
  const input = document.getElementById('cash-input');
  input.value = amount;
  handleCashInputChange();
}

function setExactCash() {
  const total = parseFloat(document.getElementById('pay-modal-total').getAttribute('data-amount'));
  setQuickCash(total);
}

function handleCashInputChange() {
  const input = document.getElementById('cash-input');
  const total = parseFloat(document.getElementById('pay-modal-total').getAttribute('data-amount')) || 0;
  const cash = parseFloat(input.value) || 0;
  state.cashReceived = cash;

  const change = Math.max(0, cash - total);
  document.getElementById('cash-change-display').innerText = api.formatRupiah(change);
}

async function loadQRISDisplay() {
  const total = parseFloat(document.getElementById('pay-modal-total').getAttribute('data-amount'));
  try {
    const qris = await api.generateQRIS({ outlet_id: state.activeOutletId, amount: total });
    document.getElementById('qris-ref-text').innerText = `Ref: ${qris.transaction_reference || 'QRIS-AURORA-2026'}`;
    document.getElementById('qris-payload-preview').innerText = qris.qr_string || '00020101021226590014ID.LINKAJA.WWW01189360091100000000005204581253033605802ID5914AURORA COFFEE6007BANDUNG6304';
  } catch (err) {
    console.error('QRIS error:', err);
  }
}

async function executePayment() {
  const total = parseFloat(document.getElementById('pay-modal-total').getAttribute('data-amount'));
  const tableSelect = document.getElementById('pos-table-select');
  const tableId = tableSelect.value ? parseInt(tableSelect.value) : null;

  if (state.activePaymentMethod === 'Cash' && state.cashReceived < total) {
    api.showToast('Nominal tunai yang diterima masih kurang!', 'error');
    return;
  }

  const payload = {
    outlet_id: state.activeOutletId,
    shift_id: state.currentShift ? state.currentShift.id : 1,
    cashier_id: state.currentUser ? state.currentUser.id : 2,
    customer_id: 1, // Dimas
    table_id: tableId,
    sales_type_id: 1,
    payment_method: state.activePaymentMethod,
    cash_received: state.activePaymentMethod === 'Cash' ? state.cashReceived : total,
    items: state.cart.map(c => ({
      item_id: c.item_id,
      quantity: c.quantity,
      unit_price: c.base_price,
      notes: c.notes,
      modifiers: c.modifiers.map(m => ({ modifier_option_id: m.modifier_option_id, additional_price: m.additional_price }))
    }))
  };

  try {
    const result = await api.checkout(payload);
    closePaymentModal();
    api.showToast('Pembayaran Berhasil! Transaksi selesai.', 'success');

    // Show Digital Receipt
    showReceiptModal(result);

    // Reset Cart & Promo
    state.cart = [];
    state.appliedPromo = null;
    const promoInput = document.getElementById('cart-promo-code');
    if (promoInput) promoInput.value = '';
    renderCart();

    // Reload Table selector & active Shift
    const tables = await api.getTables(state.activeOutletId);
    state.tables = tables;
    populateTableSelector(tables);

  } catch (err) {
    console.error('Checkout error:', err);
    api.showToast(`Gagal menyelesaikan pembayaran: ${err.message}`, 'error');
  }
}

// ==========================================================================
// Digital Receipt Modal
// ==========================================================================
function showReceiptModal(trx) {
  const modal = document.getElementById('receipt-modal');
  const content = document.getElementById('receipt-content');

  const rs = state.receiptSettings || {};
  const brandName = rs.receipt_header || (state.brand && state.brand.name) || 'AURORA CAFE & ROASTERY';
  const outletAddr = (state.outlet && state.outlet.address) ? state.outlet.address : 'Jl. R.E. Martadinata No. 45, Bandung';
  const outletPhone = (state.outlet && state.outlet.phone) ? state.outlet.phone : '022-7201234';
  const taxId = rs.tax_id || '01.892.481.0-421.000';
  const showLogo = rs.show_logo !== false && state.brand && state.brand.logo;
  const showWifi = rs.show_wifi !== false && (rs.wifi_ssid || rs.wifi_password);
  const footerText = rs.receipt_footer || 'Terima kasih atas kunjungan Anda!';
  const igText = rs.instagram || '';

  const isTaxEnabled = rs.tax_enabled !== false && rs.tax_enabled !== 'false' && rs.tax_enabled !== 0;
  const showTaxOnReceipt = rs.show_tax_on_receipt !== false && rs.show_tax_on_receipt !== 'false';

  content.innerHTML = `
    <div class="receipt-header">
      ${showLogo ? `
        <div style="text-align:center;margin-bottom:6px;">
          <img src="${state.brand.logo}" alt="Logo" style="max-height:48px;max-width:120px;object-fit:contain;" onerror="this.style.display='none'" />
        </div>
      ` : ''}
      <h3 style="font-family:var(--font-heading);font-weight:800;font-size:1.25rem;margin-bottom:2px;letter-spacing:0.02em;">${brandName}</h3>
      <p style="font-size:0.75rem;color:#78716c;">${outletAddr}</p>
      <p style="font-size:0.75rem;color:#78716c;">Telp: ${outletPhone} • NPWP: ${taxId}</p>
      <div style="margin-top:0.65rem;font-size:0.8rem;text-align:left;border-top:1px dashed #a8a29e;padding-top:6px;">
        <div style="display:flex;justify-content:space-between;"><span>Nota:</span><strong>${trx.invoice_number || trx.transaction_number}</strong></div>
        <div style="display:flex;justify-content:space-between;"><span>Waktu:</span><span>${new Date(trx.created_at).toLocaleString('id-ID')}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>Kasir:</span><span>${(state.currentUser && state.currentUser.name) ? state.currentUser.name : 'Kasir'}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>Meja:</span><span>${trx.table_number || 'Takeaway'}</span></div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:6px;margin:0.6rem 0;">
      ${trx.items.map(i => `
        <div class="receipt-line" style="font-size:0.84rem;align-items:flex-start;">
          <div>
            <span>${i.quantity}x ${i.name}</span>
            ${i.modifiers && i.modifiers.length > 0 ? `
              <div style="font-size:0.74rem;color:#78716c;margin-top:2px;">
                ${i.modifiers.map(m => m.name.replace(/\(\+Rp.*?\)/i, '').trim()).join(', ')}
              </div>
            ` : ''}
          </div>
          <span style="font-weight:600;">${api.formatRupiah(i.subtotal)}</span>
        </div>
      `).join('')}
    </div>
    <div style="border-top:1px dashed #78716c;padding-top:8px;display:flex;flex-direction:column;gap:4px;font-size:0.82rem;">
      <div class="receipt-line"><span>Subtotal:</span><span>${api.formatRupiah(trx.subtotal)}</span></div>
      ${trx.discount_amount > 0 ? `<div class="receipt-line" style="color:#059669;"><span>Diskon:</span><span>- ${api.formatRupiah(trx.discount_amount)}</span></div>` : ''}
      ${(isTaxEnabled && showTaxOnReceipt && trx.tax_amount > 0) ? `
        <div class="receipt-line">
          <span>${rs.tax_name || 'PB1'} (${rs.tax_rate ?? 10}%):</span>
          <span>${api.formatRupiah(trx.tax_amount)}</span>
        </div>
      ` : ''}
      <div class="receipt-line" style="font-size:1.1rem;font-weight:800;margin-top:4px;border-top:1px solid #1c1917;padding-top:4px;">
        <span>TOTAL:</span><span>${api.formatRupiah(trx.total_amount)}</span>
      </div>
      <div class="receipt-line" style="margin-top:2px;"><span>Metode Bayar:</span><span>${trx.payment_method}</span></div>
      ${trx.payment_method === 'Cash' ? `
        <div class="receipt-line"><span>Tunai Diterima:</span><span>${api.formatRupiah(trx.cash_received)}</span></div>
        <div class="receipt-line" style="font-weight:bold;color:#059669;"><span>Kembalian:</span><span>${api.formatRupiah(trx.change_amount)}</span></div>
      ` : ''}
    </div>
    <div style="text-align:center;font-size:0.75rem;color:#78716c;margin-top:1rem;border-top:1px dashed #78716c;padding-top:0.75rem;">
      ${footerText}<br>
      ${showWifi ? `Wifi: <strong>${rs.wifi_ssid || 'TerasManis_Guest'}</strong> • Password: <strong>${rs.wifi_password || 'kopiterasmanis'}</strong><br>` : ''}
      ${igText ? `Follow Instagram: <strong>${igText}</strong>` : ''}
    </div>
  `;

  modal.classList.add('active');
}

function closeReceiptModal() {
  document.getElementById('receipt-modal').classList.remove('active');
}

// ==========================================================================
// Dashboard Loader
// ==========================================================================
async function loadDashboard() {
  try {
    const data = await api.getDashboard(state.activeOutletId);

    document.getElementById('dash-today-sales').innerText = api.formatRupiah(data.today_sales);
    document.getElementById('dash-today-trx').innerText = data.today_transactions;

    const occupancy = data.tables.total_tables > 0 ? Math.round((data.tables.occupied_tables / data.tables.total_tables) * 100) : 0;
    document.getElementById('dash-table-occupancy').innerText = `${occupancy}%`;
    document.getElementById('dash-active-shift-cash').innerText = data.active_shift ? api.formatRupiah(data.active_shift.expected_cash) : 'Rp 0';

    // Top Selling Items
    const topContainer = document.getElementById('dash-top-items-list');
    if (data.top_selling_items.length === 0) {
      topContainer.innerHTML = '<div style="color:var(--text-muted);font-size:0.88rem;padding:1rem 0;">Belum ada menu yang terjual hari ini.</div>';
    } else {
      topContainer.innerHTML = data.top_selling_items.map((item, idx) => `
        <div class="rank-item">
          <div class="rank-info">
            <div class="rank-num">${idx + 1}</div>
            <div>
              <div style="font-weight:700;font-size:0.92rem;color:var(--text-heading);">${item.name}</div>
              <div style="font-size:0.78rem;color:var(--text-muted);">${item.qty_sold} porsi terjual</div>
            </div>
          </div>
          <div style="font-family:var(--font-heading);font-weight:800;color:var(--primary);font-size:1.05rem;">${api.formatRupiah(item.revenue)}</div>
        </div>
      `).join('');
    }

    // Low stock alerts
    const stockContainer = document.getElementById('dash-low-stock-list');
    if (data.low_stock_alerts.length === 0) {
      stockContainer.innerHTML = '<div style="color:var(--accent-green);font-weight:600;font-size:0.88rem;padding:1rem 0;">✓ Semua persediaan bahan baku pada kondisi aman.</div>';
    } else {
      stockContainer.innerHTML = data.low_stock_alerts.map(item => `
        <div class="stock-alert-box">
          <div>
            <div style="font-weight:700;color:var(--accent-red);font-size:0.92rem;">${item.name}</div>
            <div style="font-size:0.78rem;color:var(--text-muted);">Batas minimum aman: ${item.min_stock_alert} ${item.unit}</div>
          </div>
          <div style="font-weight:800;font-size:1.05rem;color:var(--accent-red);font-family:var(--font-heading);">${item.current_stock} ${item.unit}</div>
        </div>
      `).join('');
    }

  } catch (err) {
    console.error('Dashboard error:', err);
  }
}

// ==========================================================================
// Floor Map Loader & Interactive Controls
// ==========================================================================
async function loadFloorMap() {
  try {
    const tables = await api.getTables(state.activeOutletId);
    state.tables = tables;

    // 1. Calculate & Render KPI Metrics
    const total = tables.length;
    const available = tables.filter(t => t.status === 'available').length;
    const occupied = tables.filter(t => t.status === 'occupied').length;
    const reserved = tables.filter(t => t.status === 'reserved').length;
    const occupancy = total > 0 ? Math.round((occupied / total) * 100) : 0;

    const elTotal = document.getElementById('table-kpi-total');
    const elAvail = document.getElementById('table-kpi-available');
    const elOcc = document.getElementById('table-kpi-occupied');
    const elRes = document.getElementById('table-kpi-reserved');
    const elPct = document.getElementById('table-kpi-occupancy');

    if (elTotal) elTotal.innerText = total;
    if (elAvail) elAvail.innerText = available;
    if (elOcc) elOcc.innerText = occupied;
    if (elRes) elRes.innerText = reserved;
    if (elPct) elPct.innerText = `${occupancy}%`;

    // 2. Zone Filtering
    const activeZone = state.activeFloorZone || 'all';
    const filteredTables = tables.filter(t => {
      if (activeZone === 'all') return true;
      const group = (t.group_name || '').toLowerCase();
      if (activeZone === 'Indoor AC') {
        return group.includes('indoor') || group.includes('ac') || (!group.includes('outdoor') && !group.includes('vip'));
      }
      if (activeZone === 'Outdoor') {
        return group.includes('outdoor') || group.includes('garden') || group.includes('teras');
      }
      if (activeZone === 'VIP') {
        return group.includes('vip') || group.includes('sofa');
      }
      return group.includes(activeZone.toLowerCase());
    });

    // 3. Render Table Nodes Grid
    const grid = document.getElementById('floor-canvas-grid');
    if (!grid) return;

    if (filteredTables.length === 0) {
      grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted);background:var(--bg-surface);border-radius:var(--radius-lg);border:1px dashed var(--border-medium);">
          <div style="font-size:2rem;margin-bottom:0.4rem;">🪑</div>
          <p>Tidak ada meja di area <strong>${activeZone}</strong>.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = filteredTables.map(t => {
      let badgeClass = 'available';
      let badgeLabel = '🟢 Kosong';
      let icon = '🪑';

      if (t.status === 'occupied') {
        badgeClass = 'occupied';
        badgeLabel = '🔴 Terisi';
      } else if (t.status === 'reserved') {
        badgeClass = 'reserved';
        badgeLabel = '🟡 Reservasi';
      }

      if ((t.group_name || '').toLowerCase().includes('vip')) {
        icon = '🛋️';
      }

      return `
        <div class="table-node ${t.status}" onclick="openTableStatusModal(${t.id})" title="Klik untuk ubah status meja atau buka di kasir">
          <span class="table-node-badge ${badgeClass}">${badgeLabel}</span>
          <div class="table-node-icon">${icon}</div>
          <div>
            <div class="table-node-name">Meja ${t.table_number}</div>
            <div class="table-node-area">${t.group_name || 'Indoor AC'}</div>
          </div>
          <div class="table-node-footer">
            <span>👥 ${t.capacity} Kursi</span>
            <span style="color:var(--primary);font-weight:700;">Atur ➔</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Floor map error:', err);
    api.showToast(`Gagal memuat denah meja: ${err.message}`, 'error');
  }
}

function filterFloorZone(zone, btn) {
  state.activeFloorZone = zone;
  document.querySelectorAll('.zone-tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  loadFloorMap();
}

function openTableStatusModal(tableId) {
  const table = (state.tables || []).find(t => t.id === tableId);
  if (!table) return;

  state.activeFloorTable = table;
  const modal = document.getElementById('table-status-modal');
  const modalName = document.getElementById('table-modal-name');
  const modalSubtitle = document.getElementById('table-modal-subtitle');
  const inputId = document.getElementById('table-modal-id');

  if (modalName) modalName.innerText = `Meja ${table.table_number}`;
  if (modalSubtitle) modalSubtitle.innerHTML = `Area: <strong>${table.group_name || 'Indoor AC'}</strong> &bull; Kapasitas: <strong>${table.capacity} Orang</strong>`;
  if (inputId) inputId.value = table.id;

  selectStatusOptionChoice(table.status || 'available');
  if (modal) modal.classList.add('active');
}

function closeTableStatusModal() {
  const modal = document.getElementById('table-status-modal');
  if (modal) modal.classList.remove('active');
}

function selectStatusOptionChoice(status) {
  const inputStatus = document.getElementById('table-modal-selected-status');
  if (inputStatus) inputStatus.value = status;

  document.querySelectorAll('.table-status-option-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  const selectedBtn = document.getElementById(`opt-status-${status}`);
  if (selectedBtn) selectedBtn.classList.add('selected');
}

async function submitTableStatusChange() {
  const tableId = parseInt(document.getElementById('table-modal-id')?.value);
  const newStatus = document.getElementById('table-modal-selected-status')?.value || 'available';
  if (!tableId) return;

  try {
    await api.updateTableStatus(tableId, newStatus);
    api.showToast(`Status Meja berhasil diubah ke ${newStatus.toUpperCase()}`, 'success');
    closeTableStatusModal();
    await loadFloorMap();
  } catch (err) {
    api.showToast(`Gagal mengubah status meja: ${err.message}`, 'error');
  }
}

function navigateToPosWithTable() {
  if (!state.activeFloorTable) return;
  const table = state.activeFloorTable;
  closeTableStatusModal();
  selectTableFromFloor(table.id, table.table_number);
}

function selectTableFromFloor(tableId, tableNum) {
  // Switch to POS tab and select table: supports both old nav-btn and new sidebar-item
  const posBtn = document.querySelector('.sidebar-item[data-target="view-pos"], .nav-btn[data-target="view-pos"]');
  if (posBtn) posBtn.click();
  const select = document.getElementById('pos-table-select');
  if (select) {
    select.value = tableId;
    api.showToast(`Meja ${tableNum} dipilih untuk pesanan kasir`, 'info');
  }
}

// ==========================================================================
// Inventory & Recipes Loader
// ==========================================================================
async function loadInventory() {
  try {
    const ingredients = await api.getIngredients(state.activeOutletId);
    state.ingredients = ingredients;
    const tbody = document.getElementById('inventory-table-body');

    tbody.innerHTML = ingredients.map(ing => {
      const isLow = ing.current_stock <= ing.min_stock_alert;
      return `
        <tr>
          <td style="font-weight:700;color:var(--text-heading);">${ing.name}</td>
          <td style="color:var(--text-muted);">${ing.category_name || '-'}</td>
          <td style="font-weight:800; font-family:var(--font-heading); color: ${isLow ? 'var(--accent-red)' : 'var(--accent-green)'};">
            ${ing.current_stock.toLocaleString()} ${ing.unit}
          </td>
          <td style="color:var(--text-muted);">${ing.min_stock_alert} ${ing.unit}</td>
          <td style="font-weight:600;">${api.formatRupiah(ing.cost_per_unit)} / ${ing.unit}</td>
          <td>
            <span style="display:inline-block;padding:3px 10px;border-radius:var(--radius-full);font-size:0.76rem;font-weight:800;background:${isLow ? 'var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);' : 'var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);'}">
              ${isLow ? '⚠️ Stok Menipis' : '✓ Stok Aman'}
            </span>
          </td>
        </tr>
      `;
    }).join('');

    // Load Items for Recipe Inspector
    const recipeSelect = document.getElementById('recipe-item-select');
    recipeSelect.innerHTML = state.items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
    loadRecipeDetails();

  } catch (err) {
    console.error('Inventory error:', err);
  }
}

async function loadRecipeDetails() {
  const itemId = parseInt(document.getElementById('recipe-item-select').value);
  const container = document.getElementById('recipe-details-container');
  if (!itemId) return;

  try {
    const recipes = await api.getRecipes(itemId);
    if (recipes.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted);font-size:0.88rem;padding:1rem 0;">Resep racikan belum dikonfigurasi untuk menu ini.</div>';
      return;
    }

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:0.65rem;">
        ${recipes.map(r => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:var(--bg-surface);border-radius:var(--radius-sm);border:1px solid var(--border-subtle);">
            <div style="display:flex;align-items:center;gap:0.6rem;">
              <span style="font-size:1.1rem;">🌿</span>
              <span style="font-weight:600;">${r.ingredient_name}</span>
            </div>
            <span style="font-weight:800;color:var(--primary);font-family:var(--font-heading);font-size:0.95rem;">${r.quantity_used} ${r.unit} / porsi</span>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    console.error('Recipe load error:', err);
  }
}

// ==========================================================================
// Shifts & History Loader
// ==========================================================================
async function loadShiftsAndHistory() {
  try {
    const shift = await api.getCurrentShift(state.activeOutletId);
    state.currentShift = shift;
    updateShiftUI(shift);

    const shiftCard = document.getElementById('shift-active-card');
    if (shift && shift.status === 'open') {
      shiftCard.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
          <div>
            <h4 style="color:var(--primary);font-size:1.2rem;font-weight:800;">Shift Aktif: ${shift.employee_name || 'Kasir'}</h4>
            <p style="font-size:0.82rem;color:var(--text-muted);margin-top:2px;">Waktu Buka Shift: ${new Date(shift.start_time).toLocaleString('id-ID')}</p>
          </div>
          <button onclick="openCloseShiftModal()" style="padding:0.65rem 1.35rem;background:var(--accent-red);border:none;border-radius:var(--radius-md);color:#fff;font-weight:800;cursor:pointer;box-shadow:0 3px 12px var(--accent-red-border);">Tutup Shift Kasir</button>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:1rem;margin-top:1.25rem;">
          <div style="background:var(--bg-surface);padding:1rem;border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
            <span style="font-size:0.75rem;color:var(--text-muted);font-weight:700;letter-spacing:0.04em;">MODAL AWAL KAS</span>
            <div style="font-size:1.3rem;font-weight:800;font-family:var(--font-heading);margin-top:2px;">${api.formatRupiah(shift.initial_cash)}</div>
          </div>
          <div style="background:var(--bg-surface);padding:1rem;border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
            <span style="font-size:0.75rem;color:var(--text-muted);font-weight:700;letter-spacing:0.04em;">KAS YANG DIHARAPKAN</span>
            <div style="font-size:1.3rem;font-weight:800;font-family:var(--font-heading);color:var(--accent-green);margin-top:2px;">${api.formatRupiah(shift.expected_cash)}</div>
          </div>
        </div>
      `;
    } else {
      shiftCard.innerHTML = `
        <div style="text-align:center;padding:2rem 1rem;">
          <div style="font-size:2.5rem;margin-bottom:0.5rem;">⏱️</div>
          <p style="color:var(--text-muted);margin-bottom:1.25rem;font-size:0.95rem;">Tidak ada shift kasir yang aktif saat ini.</p>
          <button onclick="openNewShiftModal()" style="padding:0.75rem 1.65rem;background:var(--primary);border:none;border-radius:var(--radius-md);color:#fff;font-weight:800;cursor:pointer;box-shadow:0 4px 15px var(--primary-glow);">Buka Shift Kasir Baru</button>
        </div>
      `;
    }

    // Load past transactions
    const trxs = await api.getTransactions(state.activeOutletId, 15);
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = trxs.map(t => `
      <tr>
        <td style="font-weight:800;font-family:var(--font-heading);color:var(--text-heading);">${t.transaction_number}</td>
        <td style="color:var(--text-muted);">${new Date(t.created_at).toLocaleTimeString('id-ID')}</td>
        <td style="font-weight:600;">${t.table_number || 'Takeaway'}</td>
        <td style="font-weight:800;color:var(--primary);font-family:var(--font-heading);">${api.formatRupiah(t.total_amount)}</td>
        <td><span style="font-weight:600;">${t.payment_method}</span></td>
        <td>
          <span style="display:inline-block;padding:3px 9px;border-radius:var(--radius-full);font-size:0.76rem;font-weight:700;background:${t.payment_status === 'paid' ? 'var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);' : 'var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);'}">
            ${t.payment_status === 'paid' ? 'Lunas (Paid)' : t.payment_status}
          </span>
        </td>
        <td>
          ${t.payment_status === 'paid' ? `
            <button onclick="voidTrx(${t.id})" style="padding:4px 10px;background:var(--accent-red-bg);border:1px solid var(--accent-red-border);border-radius:var(--radius-sm);color:var(--accent-red);font-size:0.78rem;font-weight:700;cursor:pointer;">Void</button>
          ` : '-'}
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Shifts error:', err);
  }
}

async function voidTrx(trxId) {
  if (!confirm(`Batalkan transaksi #${trxId}? Stok bahan baku akan otomatis dikembalikan ke gudang.`)) return;
  try {
    await api.voidTransaction(trxId);
    api.showToast(`Transaksi #${trxId} berhasil dibatalkan & stok dipulihkan!`, 'info');
    loadShiftsAndHistory();
  } catch (err) {
    api.showToast(`Gagal membatalkan transaksi: ${err.message}`, 'error');
  }
}

function openCloseShiftModal() {
  document.getElementById('close-shift-modal').classList.add('active');
}

function closeCloseShiftModal() {
  document.getElementById('close-shift-modal').classList.remove('active');
}

async function submitCloseShift() {
  if (!state.currentShift) return;
  const actualCash = parseFloat(document.getElementById('shift-actual-cash').value) || 0;
  const notes = document.getElementById('shift-close-notes').value;

  try {
    const res = await api.closeShift(state.currentShift.id, { actual_cash: actualCash, notes });
    closeCloseShiftModal();
    api.showToast(`Shift ditutup. Selisih kas: ${api.formatRupiah(res.difference || 0)}`, 'success');
    loadShiftsAndHistory();
  } catch (err) {
    api.showToast(`Gagal menutup shift: ${err.message}`, 'error');
  }
}

// Open Shift Modal handlers
function openNewShiftModal() {
  document.getElementById('open-shift-modal').classList.add('active');
}

function closeOpenShiftModal() {
  document.getElementById('open-shift-modal').classList.remove('active');
}

async function submitOpenShift() {
  const name = document.getElementById('shift-open-name').value.trim() || 'Kasir';
  const initialCash = parseFloat(document.getElementById('shift-open-initial-cash').value) || 0;

  try {
    const shift = await api.openShift({
      outlet_id: state.activeOutletId,
      cashier_id: 2,
      employee_name: name,
      initial_cash: initialCash
    });
    state.currentShift = shift;
    closeOpenShiftModal();
    updateShiftUI(shift);
    api.showToast(`Shift kasir dibuka dengan modal awal ${api.formatRupiah(initialCash)}`, 'success');
    loadShiftsAndHistory();
  } catch (err) {
    api.showToast(`Gagal membuka shift: ${err.message}`, 'error');
  }
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================
function setupEventListeners() {
  const searchInput = document.getElementById('pos-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      filterAndRenderProducts();
    });
  }

  const recipeSelect = document.getElementById('recipe-item-select');
  if (recipeSelect) {
    recipeSelect.addEventListener('change', loadRecipeDetails);
  }

  // Keyboard inputs: Numpad for PIN or Esc for modals
  window.addEventListener('keydown', (e) => {
    const overlay = document.getElementById('login-overlay');
    const isLoginVisible = overlay && !overlay.classList.contains('hidden');

    if (isLoginVisible) {
      if (e.target && e.target.id === 'pin-hidden-input') {
        if (e.key === 'Enter' && state.pinInput.length === 4) {
          submitPinLogin();
        }
        return;
      }

      if (e.key >= '0' && e.key <= '9') {
        handlePinDigit(e.key);
      } else if (e.key === 'Backspace') {
        backspacePin();
      } else if (e.key === 'Escape' || e.key === 'c' || e.key === 'C') {
        clearPin();
      } else if (e.key === 'Enter') {
        if (state.pinInput.length === 4) {
          submitPinLogin();
        }
      }
      return;
    }

    if (e.key === 'Escape') {
      closeModifierModal();
      closePaymentModal();
      closeReceiptModal();
      closeCloseShiftModal();
      closeOpenShiftModal();
      closeMasterCategoryModal();
      closeMasterItemModal();
      closeMasterPriceModal();
    }
  });
}

// ==========================================================================
// MASTER DATA CONTROLLER & VIEWS
// ==========================================================================
function toggleMasterDropdown(e) {
  if (e) e.stopPropagation();
  const menu = document.getElementById('master-dropdown-menu');
  if (menu) menu.classList.toggle('show');
}

function openMasterTab(subTab = 'kategori', updateHash = true) {
  const menu = document.getElementById('master-dropdown-menu');
  if (menu) menu.classList.remove('show');

  // Activate Master section: supports both sidebar-item and old nav-btn
  document.querySelectorAll('.nav-btn, .sidebar-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));

  const masterBtn = document.getElementById('sidebar-master-toggle');
  if (masterBtn) masterBtn.classList.add('active');
  const legacyBtn = document.getElementById('nav-btn-master');
  if (legacyBtn) legacyBtn.classList.add('active');

  const masterSec = document.getElementById('view-master');
  if (masterSec) masterSec.classList.add('active');

  // Ensure sidebar master submenu is open
  const sub = document.getElementById('sidebar-master-sub');
  const chevron = document.getElementById('master-chevron');
  if (sub) sub.classList.add('open');
  if (chevron) chevron.style.transform = 'rotate(180deg)';
  if (masterBtn) masterBtn.classList.add('submenu-open');

  // Update topbar title
  const titleEl = document.getElementById('topbar-page-title');
  if (titleEl) titleEl.textContent = 'Master Data';

  state.activeView = 'view-master';
  state.activeMasterTab = subTab;
  sessionStorage.setItem('aurora_current_view', 'view-master');
  sessionStorage.setItem('aurora_master_subtab', subTab);
  localStorage.setItem('aurora_last_view', 'view-master');
  localStorage.setItem('aurora_master_subtab', subTab);

  if (updateHash) {
    try {
      window.history.replaceState(null, '', `#master/${subTab}`);
    } catch (e) {
      window.location.hash = `#master/${subTab}`;
    }
  }

  // Update sub-tabs UI
  document.querySelectorAll('.master-sub-tab').forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-sub') === subTab);
  });

  // Update Title & Description
  const titles = {
    kategori: { title: '<span>🏷️</span> Master Kategori', desc: 'Kelola dan atur pengelompokan menu restoran' },
    barang: { title: '<span>📦</span> Master Barang / Menu', desc: 'Katalog lengkap daftar menu, SKU, gambar, dan status ketersediaan' },
    harga: { title: '<span>💰</span> Master Harga & HPP', desc: 'Kelola harga jual barang dan monitor persentase margin keuntungan' },
    ukuran: { title: '<span>📏</span> Master Ukuran (Size)', desc: 'Konfigurasi varian porsi (Regular, Large, Jumbo) dan tambahan opsi' },
    gula: { title: '<span>🍯</span> Master Level Gula (Sweetness)', desc: 'Konfigurasi pilihan kadar gula (Normal, Less Sugar, Extra, No Sugar) untuk minuman' },
    toping: { title: '<span>🍨</span> Master Topping & Add-ons', desc: 'Kelola varian extra topping (Boba, Grass Jelly, Cheese Cream, dll) beserta harga tambahannya' },
    jabatan: { title: '<span>🛡️</span> Master Jabatan & Peran', desc: 'Kelola jabatan, hak akses modul, dan peran operasional staf kafe' }
  };

  const info = titles[subTab] || titles.kategori;
  const subTitleEl = document.getElementById('master-active-title');
  const descEl = document.getElementById('master-active-desc');
  if (subTitleEl) subTitleEl.innerHTML = info.title;
  if (descEl) descEl.innerText = info.desc;

  // Render SubTab
  if (subTab === 'kategori') loadMasterCategories();
  else if (subTab === 'barang') loadMasterItems();
  else if (subTab === 'harga') loadMasterPrices();
  else if (subTab === 'ukuran') loadMasterModifiers('ukuran');
  else if (subTab === 'gula') loadMasterModifiers('gula');
  else if (subTab === 'toping') loadMasterModifiers('toping');
  else if (subTab === 'jabatan') loadMasterRoles();
}

// --- 1. Master Kategori ---
async function loadMasterCategories() {
  const container = document.getElementById('master-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat data kategori...</div>';

  try {
    const cats = await api.getCategories(state.activeBrandId);
    state.categories = cats;
    const items = await api.getItems(state.activeBrandId);

    container.innerHTML = `
      <div class="master-toolbar">
        <input type="text" class="master-search-input" id="search-cat-input" placeholder="🔍 Cari nama kategori..." oninput="filterMasterCategories(this.value)" />
        <button class="btn-add-master" onclick="openAddCategoryModal()">
          <span>+</span> Tambah Kategori Baru
        </button>
      </div>

      <div class="master-table-wrapper">
        <table class="master-table">
          <thead>
            <tr>
              <th style="width:60px;">ID</th>
              <th>Nama Kategori</th>
              <th>Deskripsi</th>
              <th style="text-align:center;">Jumlah Menu</th>
              <th style="text-align:center;">Status</th>
              <th style="text-align:right;">Aksi</th>
            </tr>
          </thead>
          <tbody id="master-cat-tbody">
            ${cats.map(c => {
              const count = items.filter(i => i.category_id === c.id).length;
              return `
                <tr id="cat-row-${c.id}">
                  <td style="font-weight:700;color:var(--text-muted);">${c.id}</td>
                  <td style="font-weight:800;color:var(--text-heading);">${c.name}</td>
                  <td style="color:var(--text-muted);font-size:0.84rem;">${c.description || '-'}</td>
                  <td style="text-align:center;"><span style="font-weight:700;padding:2px 8px;background:var(--bg-surface);border-radius:var(--radius-full);border:1px solid var(--border-subtle);">${count} item</span></td>
                  <td style="text-align:center;">
                    <span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);">Aktif</span>
                  </td>
                  <td style="text-align:right;">
                    <button class="btn-table-action" onclick="openEditCategoryModal(${c.id})" title="Edit Kategori">✏️ Edit</button>
                    <button class="btn-table-action danger" onclick="deleteCategoryAction(${c.id}, '${c.name.replace(/'/g, "\\'")}')" style="margin-left:4px;" title="Hapus Kategori">🗑️</button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error loadMasterCategories:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat kategori: ${err.message}</div>`;
  }
}

function filterMasterCategories(q) {
  const query = q.toLowerCase();
  document.querySelectorAll('#master-cat-tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

function openAddCategoryModal() {
  document.getElementById('master-category-modal-title').innerText = 'Tambah Kategori Baru';
  document.getElementById('master-cat-id').value = '';
  document.getElementById('master-cat-name').value = '';
  document.getElementById('master-cat-desc').value = '';
  document.getElementById('master-category-modal').classList.add('active');
}

function openEditCategoryModal(catId) {
  const cat = state.categories.find(c => c.id === catId);
  if (!cat) return;
  document.getElementById('master-category-modal-title').innerText = 'Edit Kategori';
  document.getElementById('master-cat-id').value = cat.id;
  document.getElementById('master-cat-name').value = cat.name;
  document.getElementById('master-cat-desc').value = cat.description || '';
  document.getElementById('master-category-modal').classList.add('active');
}

function closeMasterCategoryModal() {
  const modal = document.getElementById('master-category-modal');
  if (modal) modal.classList.remove('active');
}

async function submitSaveCategory() {
  const catId = document.getElementById('master-cat-id').value;
  const name = document.getElementById('master-cat-name').value.trim();
  const desc = document.getElementById('master-cat-desc').value.trim();

  if (!name) {
    api.showToast('Nama kategori wajib diisi', 'info');
    return;
  }

  try {
    if (catId) {
      await api.updateCategory(parseInt(catId), { name, description: desc });
      api.showToast('Kategori berhasil diperbarui', 'success');
    } else {
      await api.createCategory({ brand_id: state.activeBrandId, name, description: desc });
      api.showToast('Kategori baru berhasil ditambahkan', 'success');
    }
    closeMasterCategoryModal();
    await loadInitialData();
    loadMasterCategories();
  } catch (err) {
    api.showToast(`Gagal menyimpan kategori: ${err.message}`, 'error');
  }
}

async function deleteCategoryAction(catId, catName) {
  if (!confirm(`Hapus kategori "${catName}"?`)) return;
  try {
    await api.deleteCategory(catId);
    api.showToast('Kategori berhasil dihapus', 'info');
    await loadInitialData();
    loadMasterCategories();
  } catch (err) {
    api.showToast(`Gagal menghapus: ${err.message}`, 'error');
  }
}

// --- 2. Master Barang / Menu ---
async function loadMasterItems() {
  const container = document.getElementById('master-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat data menu & barang...</div>';

  try {
    const items = await api.getItems(state.activeBrandId);
    state.items = items;
    const cats = await api.getCategories(state.activeBrandId);
    state.categories = cats;

    container.innerHTML = `
      <div class="master-toolbar">
        <div style="display:flex;gap:0.65rem;flex-wrap:wrap;align-items:center;">
          <input type="text" class="master-search-input" id="search-item-input" placeholder="🔍 Cari nama barang / SKU..." oninput="filterMasterItems()" />
          <select id="filter-item-cat" onchange="filterMasterItems()" style="padding:0.65rem 0.85rem;background:var(--bg-input);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-main);font-size:0.88rem;outline:none;">
            <option value="all">Semua Kategori</option>
            ${cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
          </select>
        </div>
        <button class="btn-add-master" onclick="openAddItemModal()">
          <span>+</span> Tambah Menu / Barang
        </button>
      </div>

      <div class="master-table-wrapper">
        <table class="master-table">
          <thead>
            <tr>
              <th style="width:50px;">Foto</th>
              <th>Nama Barang / Menu</th>
              <th>Kategori</th>
              <th>SKU</th>
              <th style="text-align:right;">Harga Jual</th>
              <th style="text-align:right;">Harga Modal (HPP)</th>
              <th style="text-align:center;">Margin</th>
              <th style="text-align:center;">Status</th>
              <th style="text-align:right;">Aksi</th>
            </tr>
          </thead>
          <tbody id="master-item-tbody">
            ${items.map(i => {
              const margin = i.price > 0 ? (((i.price - (i.cost_price || 0)) / i.price) * 100).toFixed(0) : 0;
              const isActive = i.is_active !== 0 && i.is_active !== false;
              const statusBadge = isActive
                ? `<span style="display:inline-block;padding:2px 7px;border-radius:var(--radius-full);font-size:0.72rem;font-weight:700;background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);">Aktif</span>`
                : `<span style="display:inline-block;padding:2px 7px;border-radius:var(--radius-full);font-size:0.72rem;font-weight:700;background:var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);">Nonaktif</span>`;
              return `
                <tr id="item-row-${i.id}" data-cat="${i.category_id}" style="${isActive ? '' : 'opacity:0.75;'}">
                  <td>
                    <img src="${i.image_url || '/static/img/coffee.jpg'}" alt="${i.name}" style="width:38px;height:38px;border-radius:var(--radius-sm);object-fit:cover;border:1px solid var(--border-medium);" onerror="this.src='/static/img/coffee.jpg'" />
                  </td>
                  <td>
                    <div style="font-weight:800;color:var(--text-heading);">${i.name}</div>
                    <div style="font-size:0.75rem;color:var(--text-muted);">${i.description || '-'}</div>
                  </td>
                  <td><span style="font-size:0.8rem;padding:2px 6px;border-radius:var(--radius-full);background:var(--bg-surface);border:1px solid var(--border-subtle);">${i.category_name || '-'}</span></td>
                  <td style="font-family:monospace;font-size:0.82rem;color:var(--text-muted);">${i.sku || '-'}</td>
                  <td style="text-align:right;font-weight:800;color:var(--primary);font-family:var(--font-heading);">${api.formatRupiah(i.price)}</td>
                  <td style="text-align:right;color:var(--text-muted);font-family:var(--font-heading);">${api.formatRupiah(i.cost_price || 0)}</td>
                  <td style="text-align:center;"><span class="margin-badge">${margin}%</span></td>
                  <td style="text-align:center;">${statusBadge}</td>
                  <td style="text-align:right;white-space:nowrap;">
                    <button class="btn-table-action" onclick="openMasterPriceModal(${i.id})" title="Ubah Harga">💰 Harga</button>
                    <button class="btn-table-action" onclick="openEditItemModal(${i.id})" title="Edit Lengkap">✏️</button>
                    <button class="btn-table-action danger" onclick="deleteItemAction(${i.id}, '${i.name.replace(/'/g, "\\'")}')" title="Hapus Menu">🗑️</button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error loadMasterItems:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat barang: ${err.message}</div>`;
  }
}

function filterMasterItems() {
  const q = (document.getElementById('search-item-input')?.value || '').toLowerCase();
  const cat = document.getElementById('filter-item-cat')?.value || 'all';

  document.querySelectorAll('#master-item-tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    const rowCat = row.getAttribute('data-cat');
    const matchQuery = text.includes(q);
    const matchCat = cat === 'all' || rowCat === cat;
    row.style.display = (matchQuery && matchCat) ? '' : 'none';
  });
}

// --- Helper: Master Item Modifiers & Photos ---
function updateItemImagePreview(url) {
  const preview = document.getElementById('master-item-image-preview');
  const input = document.getElementById('master-item-image');
  const targetUrl = url || input?.value || '/static/img/coffee.jpg';
  if (preview) {
    preview.src = targetUrl;
  }
  if (input && url && input.value !== url) {
    input.value = url;
  }
}

function setPresetItemImage(url) {
  updateItemImagePreview(url);
}

async function handleItemImageUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;

  const spinner = document.getElementById('master-item-upload-spinner');
  if (spinner) spinner.style.display = 'flex';

  try {
    const res = await api.uploadImage(file);
    if (res && res.url) {
      updateItemImagePreview(res.url);
      api.showToast('Foto berhasil diunggah', 'success');
    }
  } catch (err) {
    api.showToast(`Gagal mengunggah foto: ${err.message}`, 'error');
  } finally {
    if (spinner) spinner.style.display = 'none';
    e.target.value = '';
  }
}

function renderMasterItemModifiers(selectedIds = []) {
  const container = document.getElementById('master-item-modifiers-list');
  const countEl = document.getElementById('master-item-mod-count');
  if (!container) return;

  if (!state.modifiers || state.modifiers.length === 0) {
    container.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted);font-style:italic;">Tidak ada varian/modifier terdaftar di sistem.</div>';
    if (countEl) countEl.innerText = '0 Varian';
    return;
  }

  // Sort modifiers by standard hierarchy: Gula -> Topping -> Ukuran
  const sorted = [...state.modifiers].sort((a, b) => {
    const getPri = (m) => {
      const n = (m.name || '').toLowerCase();
      if (n.includes('gula') || n.includes('sugar') || m.id === 1) return 1;
      if (n.includes('topping') || n.includes('toping') || m.id === 2) return 2;
      if (n.includes('ukuran') || n.includes('size') || m.id === 3) return 3;
      return 4;
    };
    return getPri(a) - getPri(b);
  });

  container.innerHTML = sorted.map(mod => {
    const isChecked = selectedIds.includes(mod.id);
    const optionsSummary = (mod.options || []).map(o => o.name).join(', ') || 'Tanpa opsi';
    const nameLower = (mod.name || '').toLowerCase();

    let tagIcon = '✨';
    let typeLabel = 'Varian';
    if (nameLower.includes('gula') || nameLower.includes('sugar') || mod.id === 1) {
      tagIcon = '🍯';
      typeLabel = 'Level Gula';
    } else if (nameLower.includes('topping') || nameLower.includes('toping') || mod.id === 2) {
      tagIcon = '🍨';
      typeLabel = 'Extra Topping';
    } else if (nameLower.includes('ukuran') || nameLower.includes('size') || mod.id === 3) {
      tagIcon = '📏';
      typeLabel = 'Ukuran Porsi';
    }

    return `
      <label class="modifier-checkbox-item ${isChecked ? 'checked' : ''}" id="mod-chip-${mod.id}" style="display:flex;align-items:center;gap:0.75rem;padding:0.75rem 0.9rem;border:1px solid ${isChecked ? 'var(--primary)' : 'var(--border-medium)'};background:${isChecked ? 'rgba(217,119,6,0.06)' : 'var(--bg-surface)'};border-radius:var(--radius-md);cursor:pointer;margin-bottom:0.5rem;transition:var(--transition);">
        <input type="checkbox" value="${mod.id}" ${isChecked ? 'checked' : ''} onchange="toggleModifierItemCheckbox(this, ${mod.id})" style="width:18px;height:18px;accent-color:var(--primary);cursor:pointer;" />
        <div style="flex:1;">
          <div style="font-weight:700;font-size:0.9rem;color:var(--text-heading);display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">
            <span>${tagIcon}</span> <span>${mod.name}</span>
            <span style="font-size:0.7rem;padding:2px 8px;border-radius:10px;background:rgba(217,119,6,0.15);color:var(--primary);font-weight:700;">${typeLabel}</span>
            <span style="font-size:0.72rem;color:var(--text-muted);font-weight:normal;">(${mod.max_selection === 1 ? 'Pilihan Tunggal' : 'Pilihan Banyak'})</span>
          </div>
          <div style="font-size:0.76rem;color:var(--text-muted);margin-top:2px;">Opsi: ${optionsSummary}</div>
        </div>
      </label>
    `;
  }).join('');

  updateMasterItemModCount();
}

function applyModifierPreset(presetType) {
  const checkboxes = document.querySelectorAll('#master-item-modifiers-list input[type="checkbox"]');
  checkboxes.forEach(cb => {
    const modId = parseInt(cb.value);
    const mod = (state.modifiers || []).find(m => m.id === modId);
    if (!mod) return;
    const n = (mod.name || '').toLowerCase();

    if (presetType === 'drink') {
      cb.checked = true; // Minuman: aktifkan semua (Level Gula, Topping, Ukuran)
    } else if (presetType === 'food') {
      const isSugar = n.includes('gula') || n.includes('sugar') || mod.id === 1;
      cb.checked = !isSugar; // Makanan: tanpa opsi gula
    } else if (presetType === 'clear') {
      cb.checked = false;
    }
    toggleModifierItemCheckbox(cb, modId);
  });
  updateMasterItemModCount();
}

function toggleModifierItemCheckbox(cb, modId) {
  const chip = document.getElementById(`mod-chip-${modId}`);
  if (chip) {
    if (cb.checked) {
      chip.classList.add('checked');
      chip.style.borderColor = 'var(--primary)';
      chip.style.background = 'rgba(217,119,6,0.06)';
    } else {
      chip.classList.remove('checked');
      chip.style.borderColor = 'var(--border-medium)';
      chip.style.background = 'var(--bg-surface)';
    }
  }
  updateMasterItemModCount();
}

function updateMasterItemModCount() {
  const countEl = document.getElementById('master-item-mod-count');
  if (!countEl) return;
  const checked = document.querySelectorAll('#master-item-modifiers-list input[type="checkbox"]:checked').length;
  countEl.innerText = `${checked} Varian Dipilih`;
}

async function openAddItemModal() {
  document.getElementById('master-item-modal-title').innerText = 'Tambah Menu / Barang Baru';
  document.getElementById('master-item-id').value = '';
  document.getElementById('master-item-name').value = '';
  document.getElementById('master-item-sku').value = '';
  document.getElementById('master-item-price').value = '';
  document.getElementById('master-item-cost').value = '';
  document.getElementById('master-item-image').value = '/static/img/coffee.jpg';
  document.getElementById('master-item-desc').value = '';

  const statusSelect = document.getElementById('master-item-status');
  if (statusSelect) statusSelect.value = 'true';

  updateItemImagePreview('/static/img/coffee.jpg');

  const catSelect = document.getElementById('master-item-category');
  catSelect.innerHTML = state.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

  if (!state.modifiers || state.modifiers.length === 0) {
    try {
      state.modifiers = await api.getModifiers(state.activeBrandId || 1);
    } catch (err) {
      console.error('Error fetching modifiers:', err);
      state.modifiers = [];
    }
  }

  // Pre-select all available modifiers (Level Gula, Topping, Ukuran) by default for new menu item
  const defaultMods = (state.modifiers || []).map(m => m.id);
  renderMasterItemModifiers(defaultMods);

  document.getElementById('master-item-modal').classList.add('active');
}

async function openEditItemModal(itemId) {
  const item = state.items.find(i => i.id === itemId);
  if (!item) return;

  document.getElementById('master-item-modal-title').innerText = 'Edit Menu / Barang';
  document.getElementById('master-item-id').value = item.id;
  document.getElementById('master-item-name').value = item.name;
  document.getElementById('master-item-sku').value = item.sku || '';
  document.getElementById('master-item-price').value = item.price;
  document.getElementById('master-item-cost').value = item.cost_price || 0;
  
  const imgUrl = item.image_url || '/static/img/coffee.jpg';
  document.getElementById('master-item-image').value = imgUrl;
  updateItemImagePreview(imgUrl);
  document.getElementById('master-item-desc').value = item.description || '';

  const statusSelect = document.getElementById('master-item-status');
  if (statusSelect) {
    statusSelect.value = (item.is_active !== 0 && item.is_active !== false) ? 'true' : 'false';
  }

  const catSelect = document.getElementById('master-item-category');
  catSelect.innerHTML = state.categories.map(c => `<option value="${c.id}" ${c.id === item.category_id ? 'selected' : ''}>${c.name}</option>`).join('');

  if (!state.modifiers || state.modifiers.length === 0) {
    try {
      state.modifiers = await api.getModifiers(state.activeBrandId || 1);
    } catch (err) {
      console.error('Error fetching modifiers:', err);
      state.modifiers = [];
    }
  }

  const attachedIds = (item.modifiers || []).map(m => m.id);
  renderMasterItemModifiers(attachedIds);

  document.getElementById('master-item-modal').classList.add('active');
}

function closeMasterItemModal() {
  const modal = document.getElementById('master-item-modal');
  if (modal) modal.classList.remove('active');
}

async function submitSaveItem() {
  const itemId = document.getElementById('master-item-id').value;
  const name = document.getElementById('master-item-name').value.trim();
  const categoryId = parseInt(document.getElementById('master-item-category').value) || null;
  const sku = document.getElementById('master-item-sku').value.trim();
  const price = parseFloat(document.getElementById('master-item-price').value) || 0;
  const costPrice = parseFloat(document.getElementById('master-item-cost').value) || 0;
  const imageUrl = document.getElementById('master-item-image').value.trim() || '/static/img/coffee.jpg';
  const desc = document.getElementById('master-item-desc').value.trim();
  const isActive = document.getElementById('master-item-status')?.value !== 'false';

  const selectedModIds = Array.from(
    document.querySelectorAll('#master-item-modifiers-list input[type="checkbox"]:checked')
  ).map(cb => parseInt(cb.value));

  if (!name || price <= 0) {
    api.showToast('Nama dan harga jual wajib diisi dengan benar', 'info');
    return;
  }

  try {
    const payload = {
      name,
      category_id: categoryId,
      sku,
      price,
      cost_price: costPrice,
      image_url: imageUrl,
      description: desc,
      is_active: isActive,
      modifier_ids: selectedModIds
    };

    if (itemId) {
      await api.updateItem(parseInt(itemId), payload);
      api.showToast('Menu barang berhasil diperbarui', 'success');
    } else {
      await api.createItem(payload);
      api.showToast('Menu barang baru berhasil ditambahkan', 'success');
    }

    closeMasterItemModal();
    await loadInitialData();
    loadMasterItems();
  } catch (err) {
    api.showToast(`Gagal menyimpan menu: ${err.message}`, 'error');
  }
}

async function deleteItemAction(itemId, itemName) {
  if (!confirm(`Hapus menu "${itemName}" dari katalog?`)) return;
  try {
    await api.deleteItem(itemId);
    api.showToast('Menu berhasil dihapus', 'info');
    await loadInitialData();
    loadMasterItems();
  } catch (err) {
    api.showToast(`Gagal menghapus menu: ${err.message}`, 'error');
  }
}

// --- 3. Master Harga & HPP ---
async function loadMasterPrices() {
  const container = document.getElementById('master-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat daftar harga & margin laba...</div>';

  try {
    const items = await api.getItems(state.activeBrandId);
    state.items = items;

    container.innerHTML = `
      <div class="master-toolbar">
        <input type="text" class="master-search-input" id="search-price-input" placeholder="🔍 Cari menu untuk ubah harga..." oninput="filterMasterPrices(this.value)" />
        <div style="font-size:0.84rem;color:var(--text-muted);">
          💡 <em>Ketik harga jual baru langsung di kolom lalu tekan enter / tombol simpan</em>
        </div>
      </div>

      <div class="master-table-wrapper">
        <table class="master-table">
          <thead>
            <tr>
              <th>Nama Menu / Barang</th>
              <th>Kategori</th>
              <th style="text-align:right;">Harga Modal (HPP)</th>
              <th style="text-align:right;width:150px;">Harga Jual (Rp)</th>
              <th style="text-align:center;">Margin Laba</th>
              <th style="text-align:right;">Aksi</th>
            </tr>
          </thead>
          <tbody id="master-price-tbody">
            ${items.map(i => {
              const margin = i.price > 0 ? (((i.price - (i.cost_price || 0)) / i.price) * 100).toFixed(0) : 0;
              return `
                <tr id="price-row-${i.id}">
                  <td>
                    <div style="font-weight:800;color:var(--text-heading);">${i.name}</div>
                    <div style="font-size:0.75rem;color:var(--text-muted);">${i.sku || 'No SKU'}</div>
                  </td>
                  <td><span style="font-size:0.8rem;padding:2px 6px;border-radius:var(--radius-full);background:var(--bg-surface);border:1px solid var(--border-subtle);">${i.category_name || '-'}</span></td>
                  <td style="text-align:right;font-family:var(--font-heading);color:var(--text-muted);">${api.formatRupiah(i.cost_price || 0)}</td>
                  <td style="text-align:right;">
                    <input type="number" id="inline-price-${i.id}" value="${i.price}" class="quick-price-input" onchange="handleInlinePriceChange(${i.id})" />
                  </td>
                  <td style="text-align:center;" id="margin-val-${i.id}"><span class="margin-badge">${margin}%</span></td>
                  <td style="text-align:right;">
                    <button class="btn-table-action" onclick="saveInlinePrice(${i.id}, ${i.cost_price || 0})">💾 Simpan</button>
                    <button class="btn-table-action" onclick="openMasterPriceModal(${i.id})" style="margin-left:4px;">⚙️ Detail</button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error loadMasterPrices:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat harga: ${err.message}</div>`;
  }
}

function filterMasterPrices(q) {
  const query = q.toLowerCase();
  document.querySelectorAll('#master-price-tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

async function saveInlinePrice(itemId, costPrice) {
  const input = document.getElementById(`inline-price-${itemId}`);
  if (!input) return;
  const newPrice = parseFloat(input.value) || 0;
  if (newPrice <= 0) {
    api.showToast('Harga harus lebih besar dari Rp 0', 'info');
    return;
  }

  try {
    await api.updateItemPrice(itemId, newPrice, costPrice);
    api.showToast(`Harga berhasil diupdate ke ${api.formatRupiah(newPrice)}`, 'success');
    // Update margin badge UI
    const marginEl = document.getElementById(`margin-val-${itemId}`);
    if (marginEl) {
      const margin = newPrice > 0 ? (((newPrice - costPrice) / newPrice) * 100).toFixed(0) : 0;
      marginEl.innerHTML = `<span class="margin-badge">${margin}%</span>`;
    }
    await loadInitialData();
  } catch (err) {
    api.showToast(`Gagal update harga: ${err.message}`, 'error');
  }
}

function handleInlinePriceChange(itemId) {
  const row = document.getElementById(`price-row-${itemId}`);
  if (row) {
    const btn = row.querySelector('.btn-table-action');
    if (btn) {
      btn.style.background = 'var(--primary)';
      btn.style.color = '#fff';
    }
  }
}

function openMasterPriceModal(itemId) {
  const item = state.items.find(i => i.id === itemId);
  if (!item) return;

  document.getElementById('price-edit-item-id').value = item.id;
  document.getElementById('price-edit-item-name').innerText = item.name;
  document.getElementById('price-edit-item-category').innerText = `Kategori: ${item.category_name || '-'} • SKU: ${item.sku || '-'}`;
  document.getElementById('price-edit-selling').value = item.price;
  document.getElementById('price-edit-cost').value = item.cost_price || 0;
  document.getElementById('master-price-modal').classList.add('active');
}

function closeMasterPriceModal() {
  const modal = document.getElementById('master-price-modal');
  if (modal) modal.classList.remove('active');
}

async function submitSaveQuickPrice() {
  const itemId = parseInt(document.getElementById('price-edit-item-id').value);
  const selling = parseFloat(document.getElementById('price-edit-selling').value) || 0;
  const cost = parseFloat(document.getElementById('price-edit-cost').value) || 0;

  if (selling <= 0) {
    api.showToast('Harga jual harus lebih dari Rp 0', 'info');
    return;
  }

  try {
    await api.updateItemPrice(itemId, selling, cost);
    closeMasterPriceModal();
    api.showToast('Harga & HPP berhasil diperbarui', 'success');
    await loadInitialData();
    if (state.activeMasterTab === 'harga') loadMasterPrices();
    else if (state.activeMasterTab === 'barang') loadMasterItems();
  } catch (err) {
    api.showToast(`Gagal update harga: ${err.message}`, 'error');
  }
}

// --- 4. Master Ukuran, Level Gula, Topping & Varian ---
async function loadMasterModifiers(filterType = null) {
  const currentTab = filterType || state.activeMasterTab || 'ukuran';
  const container = document.getElementById('master-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat data master varian...</div>';

  try {
    const modifiers = await api.getModifiers(state.activeBrandId);
    state.modifiers = modifiers;

    // Filter based on active subtab
    const filteredMods = modifiers.filter(mod => {
      const name = (mod.name || '').toLowerCase();
      if (currentTab === 'gula') {
        return name.includes('gula') || name.includes('sugar') || name.includes('manis') || mod.id === 1;
      }
      if (currentTab === 'toping') {
        return name.includes('topping') || name.includes('toping') || name.includes('add-on') || mod.id === 2;
      }
      if (currentTab === 'ukuran') {
        return name.includes('ukuran') || name.includes('size') || name.includes('porsi') || mod.id === 3;
      }
      return true;
    });

    let btnLabel = '+ Tambah Varian Baru';
    let placeholderText = '🔍 Cari nama grup varian / opsi...';
    let emptyHelp = 'Belum ada varian atau modifier terdaftar.';

    if (currentTab === 'gula') {
      btnLabel = '+ Tambah Opsi Level Gula';
      placeholderText = '🔍 Cari level gula (Normal, Less Sugar, dll)...';
      emptyHelp = 'Belum ada pengaturan Level Gula terdaftar.';
    } else if (currentTab === 'toping') {
      btnLabel = '+ Tambah Topping Baru';
      placeholderText = '🔍 Cari extra topping (Boba, Jelly, Foam)...';
      emptyHelp = 'Belum ada Topping & Add-ons terdaftar.';
    } else if (currentTab === 'ukuran') {
      btnLabel = '+ Tambah Ukuran (Size)';
      placeholderText = '🔍 Cari ukuran porsi (Regular, Large)...';
      emptyHelp = 'Belum ada pilihan Ukuran terdaftar.';
    }

    container.innerHTML = `
      <div class="master-toolbar">
        <div style="display:flex;gap:0.65rem;flex-wrap:wrap;align-items:center;">
          <input type="text" class="master-search-input" id="search-mod-input" placeholder="${placeholderText}" oninput="filterMasterModifiers()" />
        </div>
        <button class="btn-add-master" onclick="openAddModifierModal('${currentTab}')">
          <span>+</span> ${btnLabel}
        </button>
      </div>

      <div id="master-modifiers-list" style="display:flex;flex-direction:column;gap:1.25rem;">
        ${filteredMods.length === 0 ? `
          <div style="text-align:center;padding:3rem;color:var(--text-muted);background:var(--bg-surface);border-radius:var(--radius-lg);border:1px dashed var(--border-medium);">
            <div style="font-size:2.2rem;margin-bottom:0.5rem;">${currentTab === 'gula' ? '🍯' : (currentTab === 'toping' ? '🍨' : '📏')}</div>
            <p>${emptyHelp} Klik <strong>${btnLabel}</strong> untuk membuat baru.</p>
          </div>
        ` : filteredMods.map(mod => {
          const isSingle = mod.max_selection === 1;
          const isActive = mod.is_active !== 0 && mod.is_active !== false;
          const statusBadge = isActive
            ? `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);">🟢 Aktif</span>`
            : `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);">🔴 Nonaktif</span>`;
          
          return `
            <div class="master-modifier-card" id="mod-card-${mod.id}" style="background:var(--bg-surface);border:1px solid var(--border-medium);border-radius:var(--radius-lg);padding:1.25rem;${isActive ? '' : 'opacity:0.75;'}">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.6rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.75rem;margin-bottom:1rem;">
                <div>
                  <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
                    <h4 style="font-size:1.1rem;font-weight:800;color:var(--primary);">${mod.name}</h4>
                    <span style="font-size:0.75rem;padding:2px 8px;border-radius:var(--radius-full);background:var(--primary-subtle);color:var(--primary);font-weight:700;border:1px solid var(--border-subtle);">
                      ${isSingle ? '🔘 Wajib Pilih 1 (Radio)' : '☑️ Pilihan Jamak (Checkbox)'}
                    </span>
                    ${statusBadge}
                  </div>
                  <p style="font-size:0.8rem;color:var(--text-muted);margin-top:2px;">
                    ${(mod.options && mod.options.length) || 0} Opsi Pilihan Tersedia
                  </p>
                </div>
                <div style="display:flex;gap:0.4rem;align-items:center;">
                  <button class="btn-table-action" onclick="openEditModifierModal(${mod.id})" title="Edit Grup Varian">✏️ Edit</button>
                  <button class="btn-table-action danger" onclick="deleteModifierAction(${mod.id}, '${mod.name.replace(/'/g, "\\'")}')" title="Hapus Varian">🗑️ Hapus</button>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(200px, 1fr));gap:0.75rem;">
                ${(!mod.options || mod.options.length === 0) ? `
                  <div style="font-size:0.82rem;color:var(--text-muted);font-style:italic;">Belum ada opsi pilihan di grup ini.</div>
                ` : mod.options.map(opt => `
                  <div style="padding:0.75rem 1rem;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-weight:700;font-size:0.88rem;color:var(--text-heading);">${opt.name}</span>
                    <span style="font-weight:800;font-family:var(--font-heading);color:${opt.additional_price > 0 ? 'var(--primary)' : 'var(--text-muted)'};font-size:0.85rem;">
                      ${opt.additional_price > 0 ? `+${api.formatRupiah(opt.additional_price)}` : 'Gratis'}
                    </span>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (err) {
    console.error('Error loadMasterModifiers:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat varian: ${err.message}</div>`;
  }
}

function filterMasterModifiers() {
  const query = (document.getElementById('search-mod-input')?.value || '').toLowerCase().trim();
  document.querySelectorAll('.master-modifier-card').forEach(card => {
    const text = card.innerText.toLowerCase();
    card.style.display = (!query || text.includes(query)) ? '' : 'none';
  });
}

function addModifierOptionRow(name = '', price = 0) {
  const container = document.getElementById('master-mod-options-container');
  if (!container) return;

  const row = document.createElement('div');
  row.className = 'mod-opt-row';
  row.style.cssText = 'display:flex;gap:0.5rem;align-items:center;';
  row.innerHTML = `
    <input type="text" class="mod-opt-name" value="${name}" placeholder="Nama opsi (misal: Large / Boba / Less Sugar)" style="flex:1.4;padding:0.6rem 0.85rem;background:var(--bg-input);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-main);font-size:0.88rem;outline:none;" />
    <div style="display:flex;align-items:center;gap:0.3rem;flex:1;">
      <span style="font-size:0.8rem;color:var(--text-muted);font-weight:700;">+Rp</span>
      <input type="number" class="mod-opt-price" value="${price}" placeholder="0" min="0" step="500" style="width:100%;padding:0.6rem 0.85rem;background:var(--bg-input);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--primary);font-weight:800;font-size:0.95rem;outline:none;" />
    </div>
    <button type="button" onclick="removeModifierOptionRow(this)" style="padding:0.5rem 0.7rem;background:var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);border-radius:var(--radius-sm);cursor:pointer;font-size:0.9rem;" title="Hapus Opsi">🗑️</button>
  `;
  container.appendChild(row);
}

function removeModifierOptionRow(btn) {
  const container = document.getElementById('master-mod-options-container');
  const row = btn.closest('.mod-opt-row');
  if (row) row.remove();

  if (container && container.children.length === 0) {
    addModifierOptionRow();
  }
}

function openAddModifierModal(contextType = null) {
  const currentTab = contextType || state.activeMasterTab || 'ukuran';
  const modal = document.getElementById('master-modifier-modal');
  const titleEl = document.getElementById('master-modifier-modal-title');
  const idInput = document.getElementById('master-mod-id');
  const nameInput = document.getElementById('master-mod-name');
  const typeSelect = document.getElementById('master-mod-type');
  const statusSelect = document.getElementById('master-mod-status');
  const container = document.getElementById('master-mod-options-container');

  idInput.value = '';
  statusSelect.value = 'true';

  if (container) container.innerHTML = '';

  if (currentTab === 'gula') {
    titleEl.innerText = 'Tambah Master Level Gula';
    nameInput.value = 'Level Gula (Sweetness)';
    typeSelect.value = 'single';
    if (container) {
      addModifierOptionRow('Normal Sugar (100%)', 0);
      addModifierOptionRow('Less Sugar (70%)', 0);
      addModifierOptionRow('Half Sugar (50%)', 0);
      addModifierOptionRow('No Sugar (0%)', 0);
    }
  } else if (currentTab === 'toping') {
    titleEl.innerText = 'Tambah Master Extra Topping';
    nameInput.value = 'Extra Topping & Add-ons';
    typeSelect.value = 'multiple';
    if (container) {
      addModifierOptionRow('Boba Brown Sugar', 3000);
      addModifierOptionRow('Coffee Jelly', 3000);
      addModifierOptionRow('Extra Shot Espresso', 5000);
      addModifierOptionRow('Cheese Foam', 4000);
    }
  } else {
    titleEl.innerText = 'Tambah Master Ukuran (Size)';
    nameInput.value = 'Pilihan Ukuran (Size)';
    typeSelect.value = 'single';
    if (container) {
      addModifierOptionRow('Regular (12 oz)', 0);
      addModifierOptionRow('Large (16 oz)', 4000);
      addModifierOptionRow('Jumbo (22 oz)', 7000);
    }
  }

  modal.classList.add('active');
  setTimeout(() => nameInput?.focus(), 150);
}

function openEditModifierModal(modId) {
  const mod = (state.modifiers || []).find(m => m.id === modId);
  if (!mod) return;

  document.getElementById('master-modifier-modal-title').innerText = `Edit Varian: ${mod.name}`;
  document.getElementById('master-mod-id').value = mod.id;
  document.getElementById('master-mod-name').value = mod.name || '';
  document.getElementById('master-mod-type').value = mod.max_selection === 1 ? 'single' : 'multiple';
  document.getElementById('master-mod-status').value = (mod.is_active !== 0 && mod.is_active !== false) ? 'true' : 'false';

  const container = document.getElementById('master-mod-options-container');
  if (container) {
    container.innerHTML = '';
    if (mod.options && mod.options.length > 0) {
      mod.options.forEach(opt => addModifierOptionRow(opt.name, opt.additional_price || 0));
    } else {
      addModifierOptionRow();
    }
  }

  document.getElementById('master-modifier-modal').classList.add('active');
  setTimeout(() => document.getElementById('master-mod-name')?.focus(), 150);
}

function closeMasterModifierModal() {
  const modal = document.getElementById('master-modifier-modal');
  if (modal) modal.classList.remove('active');
}

async function submitSaveModifier() {
  const modId = document.getElementById('master-mod-id').value;
  const name = document.getElementById('master-mod-name').value.trim();
  const type = document.getElementById('master-mod-type').value;
  const status = document.getElementById('master-mod-status').value === 'true';

  if (!name) {
    api.showToast('Nama grup varian wajib diisi', 'info');
    document.getElementById('master-mod-name')?.focus();
    return;
  }

  const optionRows = document.querySelectorAll('.mod-opt-row');
  const options = [];
  optionRows.forEach(row => {
    const optName = (row.querySelector('.mod-opt-name')?.value || '').trim();
    const optPrice = parseFloat(row.querySelector('.mod-opt-price')?.value) || 0;
    if (optName) {
      options.push({ name: optName, additional_price: optPrice });
    }
  });

  if (options.length === 0) {
    api.showToast('Tambahkan minimal 1 opsi pilihan', 'info');
    return;
  }

  const payload = {
    brand_id: state.activeBrandId || 1,
    name,
    min_selection: type === 'single' ? 1 : 0,
    max_selection: type === 'single' ? 1 : 0,
    is_active: status,
    options
  };

  try {
    if (modId) {
      await api.updateModifier(parseInt(modId), payload);
      api.showToast('Varian berhasil diperbarui', 'success');
    } else {
      await api.createModifier(payload);
      api.showToast('Varian baru berhasil ditambahkan', 'success');
    }

    closeMasterModifierModal();
    await loadInitialData();
    await loadMasterModifiers(state.activeMasterTab);
  } catch (err) {
    api.showToast(`Gagal menyimpan varian: ${err.message}`, 'error');
  }
}

async function deleteModifierAction(modId, modName) {
  if (!confirm(`Hapus varian "${modName}"? Opsi di dalamnya akan terhapus.`)) return;

  try {
    await api.deleteModifier(modId);
    api.showToast(`Varian "${modName}" berhasil dihapus`, 'info');
    await loadInitialData();
    await loadMasterModifiers();
  } catch (err) {
    api.showToast(err.message || 'Gagal menghapus varian', 'error');
  }
}

// --- 5. Master Jabatan & Peran (CRUD: Tambah, Edit, Hapus, Filter) ---
const PERMISSION_IDS = ['perm-pos', 'perm-table', 'perm-inventory', 'perm-reports', 'perm-shift', 'perm-shift-open-close', 'perm-settings', 'perm-all'];

function setPermissionsFromArray(permsArray) {
  const hasAll = permsArray.includes('all');
  PERMISSION_IDS.forEach(pid => {
    const el = document.getElementById(pid);
    if (el) el.checked = hasAll || permsArray.includes(el.value);
  });
}

function getPermissionsArray() {
  const allEl = document.getElementById('perm-all');
  if (allEl && allEl.checked) return ['all'];
  const perms = [];
  PERMISSION_IDS.forEach(pid => {
    if (pid === 'perm-all') return;
    const el = document.getElementById(pid);
    if (el && el.checked) perms.push(el.value);
  });
  return perms;
}

function toggleAllPermissions(allCheckbox) {
  const check = allCheckbox.checked;
  PERMISSION_IDS.forEach(pid => {
    if (pid === 'perm-all') return;
    const el = document.getElementById(pid);
    if (el) el.checked = check;
  });
}

async function loadMasterRoles() {
  const container = document.getElementById('master-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat daftar jabatan...</div>';

  try {
    const roles = await api.getRoles();
    state.roles = roles;

    const PERMISSION_LABELS = {
      all: '👑 Akses Penuh', pos: '🛒 POS', table: '🪑 Meja',
      inventory: '📦 Stok', reports: '📊 Laporan', shift: '⏱️ Shift',
      shift_open_close: '🔑 Buka/Tutup', settings: '⚙️ Pengaturan'
    };

    container.innerHTML = `
      <div class="master-toolbar">
        <div style="display:flex;gap:0.65rem;flex-wrap:wrap;align-items:center;">
          <input type="text" class="master-search-input" id="search-role-input" placeholder="🔍 Cari nama jabatan / deskripsi..." oninput="filterMasterRoles()" />
        </div>
        <button class="btn-add-master" onclick="openAddRoleModal()">
          <span>+</span> Tambah Jabatan Baru
        </button>
      </div>

      <div id="master-roles-list" style="display:flex;flex-direction:column;gap:1rem;">
        ${roles.length === 0 ? `
          <div style="text-align:center;padding:3rem;color:var(--text-muted);background:var(--bg-surface);border-radius:var(--radius-lg);border:1px dashed var(--border-medium);">
            Belum ada jabatan terdaftar. Klik <strong>+ Tambah Jabatan Baru</strong>.
          </div>
        ` : roles.map(role => {
          let permsArr = [];
          try { permsArr = JSON.parse(role.permissions || '[]'); } catch(e) {}
          const isOwner = role.id === 1 || (role.name || '').toLowerCase().includes('owner') || (role.name || '').toLowerCase().includes('admin');
          const permBadges = permsArr.includes('all')
            ? `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.72rem;font-weight:700;background:var(--primary-subtle);color:var(--primary);border:1px solid var(--primary-glow);">👑 Akses Penuh</span>`
            : permsArr.map(p => `<span style="display:inline-block;padding:2px 7px;border-radius:var(--radius-full);font-size:0.72rem;font-weight:700;background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border-medium);">${PERMISSION_LABELS[p] || p}</span>`).join('');
          return `
            <div class="master-role-card" id="role-card-${role.id}" data-name="${(role.name||'').toLowerCase()}" data-desc="${(role.description||'').toLowerCase()}"
              style="background:var(--bg-card);border:1px solid ${isOwner ? 'var(--primary-glow)' : 'var(--border-medium)'};border-radius:var(--radius-lg);padding:1.25rem;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.75rem;flex-wrap:wrap;">
                <div style="flex:1;min-width:200px;">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">
                    <h4 style="font-size:1.05rem;font-weight:800;color:${isOwner ? 'var(--primary)' : 'var(--text-heading)'};">🛡️ ${role.name}</h4>
                    ${isOwner ? '<span style="font-size:0.72rem;padding:2px 8px;border-radius:var(--radius-full);background:var(--primary-subtle);color:var(--primary);font-weight:700;border:1px solid var(--primary-glow);">🔒 Dilindungi</span>' : ''}
                    <span style="font-size:0.75rem;padding:2px 8px;border-radius:var(--radius-full);background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border-medium);">👥 ${role.employee_count || 0} staf</span>
                  </div>
                  <p style="font-size:0.83rem;color:var(--text-muted);margin-bottom:0.65rem;">${role.description || '<em>Tidak ada deskripsi</em>'}</p>
                  <div style="display:flex;flex-wrap:wrap;gap:0.35rem;">${permBadges || '<span style="color:var(--text-muted);font-size:0.8rem;">Belum ada hak akses ditentukan</span>'}</div>
                </div>
                <div style="display:flex;gap:0.4rem;align-items:center;flex-shrink:0;">
                  <button class="btn-table-action" onclick="openEditRoleModal(${role.id})" title="Edit Jabatan">✏️ Edit</button>
                  ${isOwner ? '' : `<button class="btn-table-action danger" onclick="deleteRoleAction(${role.id}, '${(role.name||'').replace(/'/g,"\\'")}')" style="margin-left:2px;" title="Hapus Jabatan">🗑️ Hapus</button>`}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (err) {
    console.error('Error loadMasterRoles:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat jabatan: ${err.message}</div>`;
  }
}

function filterMasterRoles() {
  const query = (document.getElementById('search-role-input')?.value || '').toLowerCase().trim();
  document.querySelectorAll('.master-role-card').forEach(card => {
    const name = card.getAttribute('data-name') || '';
    const desc = card.getAttribute('data-desc') || '';
    card.style.display = (!query || name.includes(query) || desc.includes(query)) ? '' : 'none';
  });
}

function openAddRoleModal() {
  document.getElementById('master-role-modal-title').innerText = 'Tambah Jabatan Baru';
  document.getElementById('master-role-id').value = '';
  document.getElementById('master-role-name').value = '';
  document.getElementById('master-role-desc').value = '';
  PERMISSION_IDS.forEach(pid => {
    const el = document.getElementById(pid);
    if (el) el.checked = false;
  });
  // Default: POS + shift_open_close for new roles
  const pos = document.getElementById('perm-pos');
  const shift = document.getElementById('perm-shift-open-close');
  if (pos) pos.checked = true;
  if (shift) shift.checked = true;

  document.getElementById('master-role-modal').classList.add('active');
  setTimeout(() => document.getElementById('master-role-name')?.focus(), 150);
}

function openEditRoleModal(roleId) {
  const role = (state.roles || []).find(r => r.id === roleId);
  if (!role) return;

  document.getElementById('master-role-modal-title').innerText = `Edit Jabatan: ${role.name}`;
  document.getElementById('master-role-id').value = role.id;
  document.getElementById('master-role-name').value = role.name || '';
  document.getElementById('master-role-desc').value = role.description || '';

  let permsArr = [];
  try { permsArr = JSON.parse(role.permissions || '[]'); } catch(e) {}
  setPermissionsFromArray(permsArr);

  document.getElementById('master-role-modal').classList.add('active');
  setTimeout(() => document.getElementById('master-role-name')?.focus(), 150);
}

function closeMasterRoleModal() {
  const modal = document.getElementById('master-role-modal');
  if (modal) modal.classList.remove('active');
}

async function submitSaveRole() {
  const roleId = document.getElementById('master-role-id').value;
  const name = document.getElementById('master-role-name').value.trim();
  const description = document.getElementById('master-role-desc').value.trim();

  if (!name) {
    api.showToast('Nama jabatan wajib diisi', 'info');
    document.getElementById('master-role-name')?.focus();
    return;
  }

  const permsArr = getPermissionsArray();
  const payload = { name, description, permissions: JSON.stringify(permsArr) };

  try {
    if (roleId) {
      await api.updateRole(parseInt(roleId), payload);
      api.showToast(`Jabatan "${name}" berhasil diperbarui`, 'success');
    } else {
      await api.createRole(payload);
      api.showToast(`Jabatan "${name}" berhasil ditambahkan`, 'success');
    }

    closeMasterRoleModal();
    const [updatedRoles] = await Promise.all([api.getRoles().catch(() => [])]);
    state.roles = updatedRoles;
    await loadMasterRoles();
  } catch (err) {
    api.showToast(`Gagal menyimpan jabatan: ${err.message}`, 'error');
  }
}

async function deleteRoleAction(roleId, roleName) {
  if (!confirm(`Apakah Anda yakin ingin menghapus jabatan "${roleName}"?\n\nPastikan tidak ada karyawan yang masih menggunakan jabatan ini.`)) return;

  try {
    await api.deleteRole(roleId);
    api.showToast(`Jabatan "${roleName}" berhasil dihapus`, 'info');
    const [updatedRoles] = await Promise.all([api.getRoles().catch(() => [])]);
    state.roles = updatedRoles;
    await loadMasterRoles();
  } catch (err) {
    api.showToast(err.message || 'Gagal menghapus jabatan', 'error');
  }
}

// --- 6. User / Karyawan: dipindah ke Pengaturan ---
async function loadMasterEmployees() {
  const container = document.getElementById('master-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat daftar akun user & karyawan...</div>';

  try {
    const [emps, roles] = await Promise.all([
      api.getEmployees(state.activeOutletId),
      api.getRoles().catch(() => [])
    ]);

    state.employees = emps;
    state.roles = roles;

    container.innerHTML = `
      <div class="master-toolbar">
        <div style="display:flex;gap:0.65rem;flex-wrap:wrap;align-items:center;">
          <input type="text" class="master-search-input" id="search-emp-input" placeholder="🔍 Cari nama user / no. HP..." oninput="filterMasterEmployees()" />
          <select id="filter-emp-role" onchange="filterMasterEmployees()" style="padding:0.65rem 0.85rem;background:var(--bg-input);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-main);font-size:0.88rem;outline:none;">
            <option value="all">Semua Peran / Jabatan</option>
            ${roles.map(r => `<option value="${r.name}">${r.name}</option>`).join('')}
          </select>
        </div>
        <button class="btn-add-master" onclick="openAddEmployeeModal()">
          <span>+</span> Tambah User Baru
        </button>
      </div>

      <div class="master-table-wrapper">
        <table class="master-table">
          <thead>
            <tr>
              <th style="width:50px;">ID</th>
              <th>Nama User / Karyawan</th>
              <th>Peran / Jabatan</th>
              <th>No. Handphone</th>
              <th style="text-align:center;">PIN Akses</th>
              <th style="text-align:center;">Status</th>
              <th style="text-align:right;width:140px;">Aksi</th>
            </tr>
          </thead>
          <tbody id="master-emp-tbody">
            ${emps.map(e => {
              const isActive = e.is_active !== 0 && e.is_active !== false;
              const roleName = e.role_name || 'Kasir / Barista';
              const statusBadge = isActive
                ? `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);">🟢 Aktif</span>`
                : `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);">🔴 Nonaktif</span>`;
              return `
                <tr id="emp-row-${e.id}" data-role="${roleName}" style="${isActive ? '' : 'opacity:0.75;'}">
                  <td style="font-weight:700;color:var(--text-muted);">${e.id}</td>
                  <td style="font-weight:800;color:var(--text-heading);">
                    <div style="display:flex;align-items:center;gap:0.45rem;">
                      <span style="font-size:1.05rem;">👤</span>
                      <span>${e.name}</span>
                    </div>
                  </td>
                  <td>
                    <span style="padding:3px 10px;border-radius:var(--radius-full);background:var(--primary-subtle);color:var(--primary);font-size:0.78rem;font-weight:700;border:1px solid var(--border-subtle);">
                      ${roleName}
                    </span>
                  </td>
                  <td style="color:var(--text-muted);font-size:0.85rem;">${e.phone || '-'}</td>
                  <td style="text-align:center;">
                    <span class="pin-masked-tag" onclick="toggleShowPin(this, '${e.pin || '••••'}')" title="Klik untuk lihat / sembunyikan PIN" style="font-family:monospace;font-weight:800;letter-spacing:2px;cursor:pointer;padding:3px 8px;border-radius:var(--radius-sm);background:var(--bg-surface);border:1px solid var(--border-medium);user-select:none;">••••</span>
                  </td>
                  <td style="text-align:center;">${statusBadge}</td>
                  <td style="text-align:right;">
                    <button class="btn-table-action" onclick="openEditEmployeeModal(${e.id})" title="Edit Data User">✏️ Edit</button>
                    <button class="btn-table-action danger" onclick="deleteEmployeeAction(${e.id}, '${e.name.replace(/'/g, "\\'")}')" style="margin-left:4px;" title="Hapus User">🗑️</button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error loadMasterEmployees:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat daftar user: ${err.message}</div>`;
  }
}

function filterMasterEmployees() {
  const query = (document.getElementById('search-emp-input')?.value || '').toLowerCase().trim();
  const roleFilter = document.getElementById('filter-emp-role')?.value || 'all';

  document.querySelectorAll('#master-emp-tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    const rowRole = row.getAttribute('data-role') || '';
    const matchQuery = !query || text.includes(query);
    const matchRole = roleFilter === 'all' || rowRole === roleFilter;

    row.style.display = (matchQuery && matchRole) ? '' : 'none';
  });
}

function toggleShowPin(el, pin) {
  if (!pin || pin === '••••') return;
  if (el.innerText === '••••') {
    el.innerText = pin;
    el.style.color = 'var(--primary)';
    el.style.borderColor = 'var(--primary)';
  } else {
    el.innerText = '••••';
    el.style.color = '';
    el.style.borderColor = 'var(--border-medium)';
  }
}

function populateEmployeeRoleSelect(selectedRoleId = null) {
  const select = document.getElementById('master-emp-role');
  if (!select) return;

  const roles = state.roles || [];
  if (roles.length === 0) {
    select.innerHTML = `
      <option value="1">Owner / Admin</option>
      <option value="2">Store Manager</option>
      <option value="3" selected>Cashier / Barista</option>
    `;
    return;
  }

  select.innerHTML = roles.map(r => `
    <option value="${r.id}" ${selectedRoleId === r.id ? 'selected' : ''}>${r.name}</option>
  `).join('');
}

function openAddEmployeeModal() {
  document.getElementById('master-employee-modal-title').innerText = 'Tambah User Baru';
  document.getElementById('master-emp-id').value = '';
  document.getElementById('master-emp-name').value = '';
  document.getElementById('master-emp-pin').value = '';
  document.getElementById('master-emp-phone').value = '';
  document.getElementById('master-emp-status').value = 'true';

  populateEmployeeRoleSelect(3); // Default to Cashier
  document.getElementById('master-employee-modal').classList.add('active');
  setTimeout(() => document.getElementById('master-emp-name')?.focus(), 150);
}

function openEditEmployeeModal(empId) {
  const emp = (state.employees || []).find(e => e.id === empId);
  if (!emp) return;

  document.getElementById('master-employee-modal-title').innerText = `Edit User: ${emp.name}`;
  document.getElementById('master-emp-id').value = emp.id;
  document.getElementById('master-emp-name').value = emp.name || '';
  document.getElementById('master-emp-pin').value = emp.pin || '';
  document.getElementById('master-emp-phone').value = emp.phone || '';
  document.getElementById('master-emp-status').value = (emp.is_active !== 0 && emp.is_active !== false) ? 'true' : 'false';

  populateEmployeeRoleSelect(emp.role_id || 3);
  document.getElementById('master-employee-modal').classList.add('active');
  setTimeout(() => document.getElementById('master-emp-name')?.focus(), 150);
}

function closeMasterEmployeeModal() {
  const modal = document.getElementById('master-employee-modal');
  if (modal) modal.classList.remove('active');
}

async function submitSaveEmployee() {
  const empId = document.getElementById('master-emp-id').value;
  const name = document.getElementById('master-emp-name').value.trim();
  const roleId = parseInt(document.getElementById('master-emp-role').value) || 3;
  const status = document.getElementById('master-emp-status').value === 'true';
  const pin = document.getElementById('master-emp-pin').value.trim();
  const phone = document.getElementById('master-emp-phone').value.trim();

  if (!name) {
    api.showToast('Nama user / karyawan wajib diisi', 'info');
    document.getElementById('master-emp-name')?.focus();
    return;
  }

  if (!pin || pin.length < 4 || !/^\d+$/.test(pin)) {
    api.showToast('PIN login kasir harus berupa 4-6 digit angka', 'info');
    document.getElementById('master-emp-pin')?.focus();
    return;
  }

  try {
    if (empId) {
      await api.updateEmployee(parseInt(empId), { name, role_id: roleId, is_active: status, pin, phone });
      api.showToast(`User "${name}" berhasil diperbarui`, 'success');
    } else {
      await api.createEmployee({ outlet_id: state.activeOutletId || 1, name, role_id: roleId, is_active: status, pin, phone });
      api.showToast(`User "${name}" berhasil ditambahkan`, 'success');
    }

    closeMasterEmployeeModal();
    // Refresh the correct employee list depending on active context
    if (state.activeSettingTab === 'karyawan') {
      await loadSettingsEmployees();
    } else {
      // Fallback for any other context that might call this
    }
    await loadEmployeesForLogin(); // Always refresh POS cashier selector
  } catch (err) {
    api.showToast(`Gagal menyimpan user: ${err.message}`, 'error');
  }
}

async function deleteEmployeeAction(empId, empName) {
  if (!confirm(`Apakah Anda yakin ingin menghapus user "${empName}"?\n\nPerhatian: Jika user memiliki riwayat shift, sistem akan menyarankan untuk menonaktifkan status akun.`)) {
    return;
  }

  try {
    await api.deleteEmployee(empId);
    api.showToast(`User "${empName}" berhasil dihapus`, 'info');
    if (state.activeSettingTab === 'karyawan') {
      await loadSettingsEmployees();
    }
    await loadEmployeesForLogin();
  } catch (err) {
    api.showToast(err.message || 'Gagal menghapus user', 'error');
  }
}

// ==========================================================================
// 7. SETTINGS CONTROLLER (PENGATURAN: TOKO, AKUN, STRUK)
// ==========================================================================

function openSettingsTab(subTab = 'toko', updateHash = true) {
  // Activate Settings section: supports both sidebar-item and old nav-btn
  document.querySelectorAll('.nav-btn, .sidebar-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));

  const settingsBtn = document.querySelector('.sidebar-item[data-target="view-settings"], .nav-btn[data-target="view-settings"]');
  if (settingsBtn) settingsBtn.classList.add('active');

  const settingsSec = document.getElementById('view-settings');
  if (settingsSec) settingsSec.classList.add('active');

  // Update topbar title
  const titleEl = document.getElementById('topbar-page-title');
  if (titleEl) titleEl.textContent = 'Pengaturan';

  state.activeView = 'view-settings';
  state.activeSettingTab = subTab;
  sessionStorage.setItem('aurora_current_view', 'view-settings');
  sessionStorage.setItem('aurora_settings_subtab', subTab);
  localStorage.setItem('aurora_last_view', 'view-settings');
  localStorage.setItem('aurora_settings_subtab', subTab);

  if (updateHash) {
    try {
      window.history.replaceState(null, '', `#settings/${subTab}`);
    } catch (e) {
      window.location.hash = `#settings/${subTab}`;
    }
  }

  // Update tab buttons
  document.querySelectorAll('.settings-sub-tab').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-sub') === subTab);
  });

  const titles = {
    toko: {
      title: '<span>🏪</span> Pengaturan Toko & Outlet',
      desc: 'Kelola profil usaha, logo cafe, nomor kontak, dan alamat operasional'
    },
    akun: {
      title: '<span>👤</span> Pengaturan Akun Kasir',
      desc: 'Profil petugas aktif, informasi hak akses peran, dan pembaruan PIN kasir'
    },
    karyawan: {
      title: '<span>👥</span> Manajemen User & Karyawan',
      desc: 'Kelola akun user staf, peran jabatan operasional, dan PIN login kasir'
    },
    struk: {
      title: '<span>🧾</span> Pengaturan Struk Kasir',
      desc: 'Kustomisasi format cetak struk belanja, header nama toko, wifi, dan live preview'
    }
  };

  const info = titles[subTab] || titles.toko;
  const subTitleEl = document.getElementById('settings-active-title');
  const descEl = document.getElementById('settings-active-desc');
  if (subTitleEl) subTitleEl.innerHTML = info.title;
  if (descEl) descEl.innerText = info.desc;

  if (subTab === 'toko') loadStoreSettings();
  else if (subTab === 'akun') loadAccountSettings();
  else if (subTab === 'karyawan') loadSettingsEmployees();
  else if (subTab === 'struk') loadReceiptSettings();
}

// --------------------------------------------------------------------------
// 7.x SETTINGS: USER & KARYAWAN (dipindah dari Master Data)
// --------------------------------------------------------------------------
async function loadSettingsEmployees() {
  const container = document.getElementById('settings-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat daftar user & karyawan...</div>';

  try {
    const [emps, roles] = await Promise.all([
      api.getEmployees(state.activeOutletId),
      api.getRoles().catch(() => [])
    ]);

    state.employees = emps;
    state.roles = roles;

    container.innerHTML = `
      <div class="master-toolbar">
        <div style="display:flex;gap:0.65rem;flex-wrap:wrap;align-items:center;">
          <input type="text" class="master-search-input" id="search-semp-input" placeholder="🔍 Cari nama user / no. HP..." oninput="filterSettingsEmployees()" />
          <select id="filter-semp-role" onchange="filterSettingsEmployees()" style="padding:0.65rem 0.85rem;background:var(--bg-input);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-main);font-size:0.88rem;outline:none;">
            <option value="all">Semua Peran / Jabatan</option>
            ${roles.map(r => `<option value="${r.name}">${r.name}</option>`).join('')}
          </select>
        </div>
        <button class="btn-add-master" onclick="openAddEmployeeModal()">
          <span>+</span> Tambah User Baru
        </button>
      </div>

      <div class="master-table-wrapper">
        <table class="master-table">
          <thead>
            <tr>
              <th style="width:50px;">ID</th>
              <th>Nama User / Karyawan</th>
              <th>Peran / Jabatan</th>
              <th>No. Handphone</th>
              <th style="text-align:center;">PIN Akses</th>
              <th style="text-align:center;">Status</th>
              <th style="text-align:right;width:140px;">Aksi</th>
            </tr>
          </thead>
          <tbody id="settings-emp-tbody">
            ${emps.map(e => {
              const isActive = e.is_active !== 0 && e.is_active !== false;
              const roleName = e.role_name || 'Kasir / Barista';
              const statusBadge = isActive
                ? `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);">🟢 Aktif</span>`
                : `<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-full);font-size:0.75rem;font-weight:700;background:var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);">🔴 Nonaktif</span>`;
              return `
                <tr id="semp-row-${e.id}" data-role="${roleName}" style="${isActive ? '' : 'opacity:0.75;'}">
                  <td style="font-weight:700;color:var(--text-muted);">${e.id}</td>
                  <td style="font-weight:800;color:var(--text-heading);">
                    <div style="display:flex;align-items:center;gap:0.45rem;">
                      <span style="font-size:1.05rem;">👤</span>
                      <span>${e.name}</span>
                    </div>
                  </td>
                  <td>
                    <span style="padding:3px 10px;border-radius:var(--radius-full);background:var(--primary-subtle);color:var(--primary);font-size:0.78rem;font-weight:700;border:1px solid var(--border-subtle);">
                      ${roleName}
                    </span>
                  </td>
                  <td style="color:var(--text-muted);font-size:0.85rem;">${e.phone || '-'}</td>
                  <td style="text-align:center;">
                    <span class="pin-masked-tag" onclick="toggleShowPin(this, '${e.pin || '••••'}')" title="Klik untuk lihat / sembunyikan PIN" style="font-family:monospace;font-weight:800;letter-spacing:2px;cursor:pointer;padding:3px 8px;border-radius:var(--radius-sm);background:var(--bg-surface);border:1px solid var(--border-medium);user-select:none;">••••</span>
                  </td>
                  <td style="text-align:center;">${statusBadge}</td>
                  <td style="text-align:right;">
                    <button class="btn-table-action" onclick="openEditEmployeeModal(${e.id})" title="Edit Data User">✏️ Edit</button>
                    <button class="btn-table-action danger" onclick="deleteSettingsEmployeeAction(${e.id}, '${e.name.replace(/'/g,"\\'")}') " style="margin-left:4px;" title="Hapus User">🗑️</button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error loadSettingsEmployees:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat daftar user: ${err.message}</div>`;
  }
}

function filterSettingsEmployees() {
  const query = (document.getElementById('search-semp-input')?.value || '').toLowerCase().trim();
  const roleFilter = document.getElementById('filter-semp-role')?.value || 'all';
  document.querySelectorAll('#settings-emp-tbody tr').forEach(row => {
    const text = row.innerText.toLowerCase();
    const rowRole = row.getAttribute('data-role') || '';
    const matchQuery = !query || text.includes(query);
    const matchRole = roleFilter === 'all' || rowRole === roleFilter;
    row.style.display = (matchQuery && matchRole) ? '' : 'none';
  });
}

async function deleteSettingsEmployeeAction(empId, empName) {
  if (!confirm(`Apakah Anda yakin ingin menghapus user "${empName}"?\n\nPerhatian: Jika user memiliki riwayat shift, sistem akan menyarankan untuk menonaktifkan status akun.`)) return;

  try {
    await api.deleteEmployee(empId);
    api.showToast(`User "${empName}" berhasil dihapus`, 'info');
    await loadSettingsEmployees();
    await loadEmployeesForLogin();
  } catch (err) {
    api.showToast(err.message || 'Gagal menghapus user', 'error');
  }
}


// --------------------------------------------------------------------------
// 7.1 SETTING TOKO & UPLOAD LOGO
// --------------------------------------------------------------------------
async function loadStoreSettings() {
  const container = document.getElementById('settings-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat pengaturan toko...</div>';

  try {
    const store = await api.getStoreSettings(state.activeOutletId || 1);
    state.storeSettings = store;

    const currentLogo = store.logo || (state.brand && state.brand.logo) || '/static/img/coffee.jpg';

    container.innerHTML = `
      <div class="settings-section-card">
        <div class="settings-section-header">
          <div class="settings-section-title">
            <span>🖼️</span> Foto & Logo Brand Usaha
          </div>
          <span style="font-size:0.75rem;color:var(--text-muted);font-weight:600;">Format: JPG, PNG, WEBP, SVG (Maks. 5MB)</span>
        </div>

        <div class="logo-upload-container">
          <div class="logo-preview-box">
            <img id="store-logo-preview" src="${currentLogo}" alt="Logo Toko" onerror="this.src='/static/img/coffee.jpg'" />
            <div id="store-logo-spinner" style="display:none;position:absolute;inset:0;background:rgba(0,0,0,0.65);align-items:center;justify-content:center;color:#fff;font-size:0.75rem;font-weight:700;">
              Mengunggah...
            </div>
          </div>

          <div class="logo-upload-actions">
            <div style="display:flex;gap:0.6rem;flex-wrap:wrap;align-items:center;">
              <label class="btn-upload-file" title="Pilih foto/logo dari perangkat">
                <span>📁 Unggah Foto / Logo</span>
                <input type="file" id="store-logo-file-input" accept="image/png, image/jpeg, image/jpg, image/webp, image/svg+xml" style="display:none;" onchange="handleStoreLogoUpload(event)" />
              </label>

              <div style="display:flex;gap:0.35rem;align-items:center;">
                <span style="font-size:0.75rem;color:var(--text-muted);font-weight:700;">Preset:</span>
                <button type="button" class="btn-preset-img" onclick="setPresetStoreLogo('/static/img/coffee.jpg')" title="Preset Coffee">☕ Coffee</button>
                <button type="button" class="btn-preset-img" onclick="setPresetStoreLogo('/static/img/pastry.jpg')" title="Preset Pastry">🥐 Pastry</button>
                <button type="button" class="btn-preset-img" onclick="setPresetStoreLogo('/static/img/roti_thailand.jpg')" title="Preset Cafe">🍞 Cafe</button>
              </div>
            </div>

            <div style="display:flex;flex-direction:column;gap:0.3rem;">
              <label style="font-size:0.76rem;color:var(--text-muted);font-weight:700;">URL / Path File Logo:</label>
              <input type="text" id="store-logo-url" class="settings-field-input" value="${store.logo || ''}" placeholder="/static/img/uploads/... atau URL eksternal" oninput="updateStoreLogoPreview(this.value)" style="font-size:0.84rem;" />
            </div>
          </div>
        </div>
      </div>

      <div class="settings-section-card">
        <div class="settings-section-header">
          <div class="settings-section-title">
            <span>🏢</span> Identitas & Kontak Outlet Cafe
          </div>
          <span style="font-size:0.75rem;padding:3px 8px;border-radius:var(--radius-full);background:var(--primary-subtle);color:var(--primary);font-weight:700;">Outlet #${store.outlet_id}</span>
        </div>

        <div class="settings-form-grid">
          <div class="settings-field-group">
            <label class="settings-field-label">NAMA OUTLET / CABANG:</label>
            <input type="text" id="store-name" class="settings-field-input" value="${store.name || ''}" placeholder="Misal: Teras Manis - Cabang Utama" />
            <span style="font-size:0.72rem;color:var(--text-muted);">Nama cabang spesifik yang tampil pada laporan</span>
          </div>

          <div class="settings-field-group">
            <label class="settings-field-label">NAMA BRAND / USAHA UTAMA:</label>
            <input type="text" id="store-brand-name" class="settings-field-input" value="${store.brand_name || ''}" placeholder="Misal: TERAS MANIS" />
            <span style="font-size:0.72rem;color:var(--text-muted);">Nama brand utama di atas layar & header</span>
          </div>

          <div class="settings-field-group">
            <label class="settings-field-label">NOMOR TELEPON / WHATSAPP:</label>
            <input type="tel" id="store-phone" class="settings-field-input" value="${store.phone || ''}" placeholder="Misal: 0812-3456-7890 / 022-7201234" />
          </div>

          <div class="settings-field-group">
            <label class="settings-field-label">EMAIL OPERASIONAL TOKO:</label>
            <input type="email" id="store-email" class="settings-field-input" value="${store.email || ''}" placeholder="Misal: info@terasmanis.com" />
          </div>
        </div>

        <div class="settings-field-group" style="margin-top:0.35rem;">
          <label class="settings-field-label">ALAMAT LENGKAP OUTLET:</label>
          <textarea id="store-address" rows="2" class="settings-field-textarea" placeholder="Alamat lengkap toko...">${store.address || ''}</textarea>
        </div>

        <div class="settings-field-group">
          <label class="settings-field-label">DESKRIPSI / SLOGAN TOKO:</label>
          <textarea id="store-desc" rows="2" class="settings-field-textarea" placeholder="Keterangan singkat usaha atau tagline...">${store.description || ''}</textarea>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:0.75rem;margin-top:0.75rem;padding-top:1rem;border-top:1px solid var(--border-subtle);">
          <button type="button" onclick="loadStoreSettings()" style="padding:0.75rem 1.4rem;background:var(--bg-main);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-muted);font-weight:700;cursor:pointer;">
            ↺ Reset
          </button>
          <button type="button" onclick="submitSaveStoreSettings()" style="padding:0.75rem 2rem;background:linear-gradient(135deg,var(--primary),var(--primary-dark));border:none;border-radius:var(--radius-md);color:#fff;font-weight:800;cursor:pointer;box-shadow:0 4px 15px var(--primary-glow);display:flex;align-items:center;gap:8px;">
            <span>💾</span> Simpan Pengaturan Toko
          </button>
        </div>
      </div>
    `;
  } catch (err) {
    console.error('Error loadStoreSettings:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat pengaturan toko: ${err.message}</div>`;
  }
}

async function handleStoreLogoUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const spinner = document.getElementById('store-logo-spinner');
  if (spinner) spinner.style.display = 'flex';

  try {
    const res = await api.uploadStoreLogo(file);
    if (res.success && res.image_url) {
      updateStoreLogoPreview(res.image_url);
      const input = document.getElementById('store-logo-url');
      if (input) input.value = res.image_url;
      api.showToast('Foto logo berhasil diunggah! Klik "Simpan Pengaturan Toko" untuk menerapkan.', 'success');
    }
  } catch (err) {
    console.error('Upload logo error:', err);
    api.showToast(`Gagal mengunggah logo: ${err.message}`, 'error');
  } finally {
    if (spinner) spinner.style.display = 'none';
  }
}

function updateStoreLogoPreview(url) {
  const preview = document.getElementById('store-logo-preview');
  if (preview) {
    preview.src = url || '/static/img/coffee.jpg';
  }
}

function setPresetStoreLogo(url) {
  updateStoreLogoPreview(url);
  const input = document.getElementById('store-logo-url');
  if (input) input.value = url;
}

async function submitSaveStoreSettings() {
  const outletId = state.activeOutletId || 1;
  const name = document.getElementById('store-name')?.value.trim();
  const brandName = document.getElementById('store-brand-name')?.value.trim();
  const phone = document.getElementById('store-phone')?.value.trim();
  const email = document.getElementById('store-email')?.value.trim();
  const address = document.getElementById('store-address')?.value.trim();
  const description = document.getElementById('store-desc')?.value.trim();
  const logo = document.getElementById('store-logo-url')?.value.trim();

  if (!name) {
    api.showToast('Nama outlet / toko wajib diisi', 'info');
    document.getElementById('store-name')?.focus();
    return;
  }

  try {
    const payload = {
      outlet_id: outletId,
      name,
      brand_name: brandName || name,
      phone,
      email,
      address,
      description,
      logo: logo || null
    };

    const updated = await api.updateStoreSettings(payload);
    state.storeSettings = updated;

    // Update live state & Navbar Header in real time
    if (state.brand) {
      state.brand.name = updated.brand_name;
      if (updated.logo) state.brand.logo = updated.logo;
    }
    if (state.outlet) {
      state.outlet.name = updated.name;
      state.outlet.address = updated.address;
      state.outlet.phone = updated.phone;
    }

    const brandTitleEl = document.getElementById('brand-header-title');
    const brandAddressEl = document.getElementById('brand-header-address');
    if (brandTitleEl) {
      brandTitleEl.innerHTML = `${updated.brand_name} <span class="brand-badge" id="brand-badge-text">${updated.name}</span>`;
    }
    if (brandAddressEl) {
      brandAddressEl.innerText = updated.address || updated.name;
    }

    if (updated.logo) {
      const logoEl = document.querySelector('.brand-logo');
      if (logoEl) {
        logoEl.innerHTML = `<img src="${updated.logo}" alt="Logo" style="width:100%;height:100%;object-fit:cover;border-radius:var(--radius-md);" onerror="this.outerHTML='☕'">`;
      }
    }

    api.showToast('Pengaturan toko & logo brand berhasil disimpan!', 'success');
  } catch (err) {
    console.error('Error save store settings:', err);
    api.showToast(`Gagal menyimpan toko: ${err.message}`, 'error');
  }
}

// --------------------------------------------------------------------------
// 7.2 SETTING AKUN (USER PROFILE & PIN KASIR)
// --------------------------------------------------------------------------
async function loadAccountSettings() {
  const container = document.getElementById('settings-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat profil akun...</div>';

  try {
    const currentEmpId = state.currentUser ? state.currentUser.id : 1;
    let emp = null;

    try {
      emp = await api.getAccountProfile(currentEmpId);
    } catch (e) {
      // Fallback to state.currentUser or employees list
      emp = state.currentUser || (state.employees && state.employees[0]) || {
        id: 1,
        name: 'Ade Suharmin',
        phone: '081234567890',
        role_name: 'Owner / Admin',
        outlet_name: 'Teras Manis'
      };
    }

    const initials = emp.name ? emp.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'US';

    container.innerHTML = `
      <!-- Account Profile Header Card -->
      <div class="account-profile-header">
        <div class="account-avatar-badge">${initials}</div>
        <div style="flex:1;">
          <h3 style="font-size:1.3rem;font-weight:800;color:var(--text-heading);margin-bottom:2px;">${emp.name}</h3>
          <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
            <span class="account-badge-role">🛡️ ${emp.role_name || 'Kasir / Staf'}</span>
            <span style="font-size:0.8rem;color:var(--text-muted);">📍 ${emp.outlet_name || 'Outlet Utama'}</span>
            <span style="font-size:0.8rem;color:var(--accent-green);font-weight:700;">🟢 Sesi Aktif</span>
          </div>
        </div>
      </div>

      <!-- Account Edit Form Card -->
      <div class="settings-section-card">
        <div class="settings-section-header">
          <div class="settings-section-title">
            <span>👤</span> Informasi Profil Pengguna
          </div>
          <span style="font-size:0.75rem;color:var(--text-muted);font-weight:600;">ID Karyawan #${emp.id}</span>
        </div>

        <input type="hidden" id="account-emp-id" value="${emp.id}" />

        <div class="settings-form-grid">
          <div class="settings-field-group">
            <label class="settings-field-label">NAMA LENGKAP PENGGUNA:</label>
            <input type="text" id="account-name" class="settings-field-input" value="${emp.name || ''}" placeholder="Nama lengkap petugas..." />
          </div>

          <div class="settings-field-group">
            <label class="settings-field-label">NO. HANDPHONE / WHATSAPP:</label>
            <input type="tel" id="account-phone" class="settings-field-input" value="${emp.phone || ''}" placeholder="08xxxxxxxxxx" />
          </div>

          <div class="settings-field-group">
            <label class="settings-field-label">PERAN / HAK AKSES:</label>
            <input type="text" class="settings-field-input" value="${emp.role_name || 'Kasir'}" disabled style="background:var(--bg-main);opacity:0.8;cursor:not-allowed;" />
            <span style="font-size:0.72rem;color:var(--text-muted);">Peran diatur oleh Administrator di Master User</span>
          </div>
        </div>

        <!-- PIN Security Section -->
        <div class="account-pin-security-box">
          <div style="display:flex;align-items:center;gap:8px;font-size:0.92rem;font-weight:800;color:var(--text-heading);">
            <span>🔒</span> Ubah PIN Login Cepat Kasir
          </div>
          <p style="font-size:0.78rem;color:var(--text-muted);line-height:1.4;">
            PIN digunakan untuk membuka layar kasir dan berpindah petugas secara cepat. Biarkan kosong jika tidak ingin mengubah PIN saat ini.
          </p>

          <div class="settings-form-grid" style="margin-top:0.25rem;">
            <div class="settings-field-group">
              <label class="settings-field-label">PIN LAMA (OPSIONAL):</label>
              <input type="password" id="account-current-pin" maxlength="6" inputmode="numeric" class="settings-field-input" placeholder="••••" style="letter-spacing:3px;font-weight:bold;" />
            </div>

            <div class="settings-field-group">
              <label class="settings-field-label">PIN BARU (4-6 ANGKA):</label>
              <input type="password" id="account-new-pin" maxlength="6" inputmode="numeric" class="settings-field-input" placeholder="Misal: 1234" style="letter-spacing:3px;font-weight:bold;color:var(--primary);" />
            </div>

            <div class="settings-field-group">
              <label class="settings-field-label">KONFIRMASI PIN BARU:</label>
              <input type="password" id="account-confirm-pin" maxlength="6" inputmode="numeric" class="settings-field-input" placeholder="Ulangi PIN baru" style="letter-spacing:3px;font-weight:bold;color:var(--primary);" />
            </div>
          </div>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:0.75rem;margin-top:0.75rem;padding-top:1rem;border-top:1px solid var(--border-subtle);">
          <button type="button" onclick="loadAccountSettings()" style="padding:0.75rem 1.4rem;background:var(--bg-main);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-muted);font-weight:700;cursor:pointer;">
            ↺ Batal
          </button>
          <button type="button" onclick="submitSaveAccountSettings()" style="padding:0.75rem 2rem;background:linear-gradient(135deg,var(--primary),var(--primary-dark));border:none;border-radius:var(--radius-md);color:#fff;font-weight:800;cursor:pointer;box-shadow:0 4px 15px var(--primary-glow);display:flex;align-items:center;gap:8px;">
            <span>💾</span> Simpan Perubahan Akun
          </button>
        </div>
      </div>

      <!-- Quick Switch Staff Cards -->
      <div class="settings-section-card">
        <div class="settings-section-header">
          <div class="settings-section-title">
            <span>👥</span> Staf / User Lain di Outlet Ini
          </div>
          <button onclick="openSettingsTab('karyawan')" style="padding:0.35rem 0.8rem;background:var(--primary-subtle);border:1px solid var(--primary-glow);border-radius:var(--radius-sm);color:var(--primary);font-size:0.78rem;font-weight:700;cursor:pointer;">
            + Kelola Semua Staf di Pengaturan
          </button>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:0.85rem;">
          ${(state.employees || []).map(e => `
            <div style="background:var(--bg-card);border:1px solid var(--border-medium);border-radius:var(--radius-md);padding:0.85rem;display:flex;justify-content:space-between;align-items:center;">
              <div>
                <div style="font-weight:800;font-size:0.9rem;color:var(--text-heading);">${e.name}</div>
                <div style="font-size:0.74rem;color:var(--text-muted);">${e.role_name || 'Kasir'}</div>
              </div>
              ${e.id === emp.id ? `
                <span style="font-size:0.72rem;padding:2px 7px;border-radius:var(--radius-full);background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);font-weight:700;">Aktif</span>
              ` : `
                <button type="button" onclick="switchActiveUser(${e.id})" style="padding:0.35rem 0.75rem;background:var(--bg-surface);border:1px solid var(--border-medium);border-radius:var(--radius-sm);color:var(--primary);font-size:0.76rem;font-weight:700;cursor:pointer;">Pilih Sesi</button>
              `}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    console.error('Error loadAccountSettings:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat profil akun: ${err.message}</div>`;
  }
}

function switchActiveUser(empId) {
  const target = (state.employees || []).find(e => e.id === empId);
  if (!target) return;

  state.currentUser = target;
  sessionStorage.setItem('aurora_pos_user', JSON.stringify(target));
  updateCashierBadgeUI(target);
  api.showToast(`Sesi kasir aktif dialihkan ke: ${target.name}`, 'info');
  loadAccountSettings();
}

async function submitSaveAccountSettings() {
  const empId = parseInt(document.getElementById('account-emp-id')?.value) || (state.currentUser ? state.currentUser.id : 1);
  const name = document.getElementById('account-name')?.value.trim();
  const phone = document.getElementById('account-phone')?.value.trim();
  const currentPin = document.getElementById('account-current-pin')?.value.trim();
  const newPin = document.getElementById('account-new-pin')?.value.trim();
  const confirmPin = document.getElementById('account-confirm-pin')?.value.trim();

  if (!name) {
    api.showToast('Nama lengkap pengguna wajib diisi', 'info');
    document.getElementById('account-name')?.focus();
    return;
  }

  if (newPin) {
    if (!/^\d{4,6}$/.test(newPin)) {
      api.showToast('PIN baru harus berupa 4-6 digit angka', 'error');
      document.getElementById('account-new-pin')?.focus();
      return;
    }
    if (newPin !== confirmPin) {
      api.showToast('Konfirmasi PIN baru tidak cocok! Periksa kembali.', 'error');
      document.getElementById('account-confirm-pin')?.focus();
      return;
    }
  }

  try {
    const payload = {
      employee_id: empId,
      name,
      phone,
      current_pin: currentPin || null,
      new_pin: newPin || null
    };

    const res = await api.updateAccountProfile(payload);
    if (res.success && res.employee) {
      state.currentUser = res.employee;
      sessionStorage.setItem('aurora_pos_user', JSON.stringify(res.employee));
      updateCashierBadgeUI(res.employee);

      // Refresh employee list in state
      const empIdx = state.employees.findIndex(e => e.id === empId);
      if (empIdx !== -1) {
        state.employees[empIdx] = { ...state.employees[empIdx], ...res.employee };
      }

      api.showToast('Profil akun dan PIN kasir berhasil diperbarui!', 'success');
      loadAccountSettings();
      await loadEmployeesForLogin();
    }
  } catch (err) {
    console.error('Error save account settings:', err);
    api.showToast(`Gagal menyimpan akun: ${err.message}`, 'error');
  }
}

// --------------------------------------------------------------------------
// 7.3 SETTING STRUK KASIR & PENGATURAN PAJAK DINAMIS (PB1 / PPN)
// --------------------------------------------------------------------------
function setReceiptPaperWidth(width) {
  state.receiptPaperWidth = width;
  const paper = document.getElementById('receipt-live-paper-box');
  const btn58 = document.getElementById('btn-paper-58');
  const btn80 = document.getElementById('btn-paper-80');
  if (paper) {
    paper.classList.toggle('width-80mm', width === '80mm');
  }
  if (btn58 && btn80) {
    btn58.classList.toggle('active', width === '58mm');
    btn80.classList.toggle('active', width === '80mm');
  }
}

function handleTaxToggleChange() {
  const isEnabled = document.getElementById('receipt-tax-enabled')?.checked;
  const fields = document.getElementById('receipt-tax-fields');
  if (fields) {
    fields.style.opacity = isEnabled ? '1' : '0.45';
    fields.style.pointerEvents = isEnabled ? 'auto' : 'none';
  }
  updateLiveReceiptPreview();
}

function setTaxPreset(rate, name = null) {
  const rateInput = document.getElementById('receipt-tax-rate-input');
  const nameInput = document.getElementById('receipt-tax-name-input');
  const enableSwitch = document.getElementById('receipt-tax-enabled');

  if (rateInput) rateInput.value = rate;
  if (name && nameInput) nameInput.value = name;

  if (enableSwitch) {
    enableSwitch.checked = rate > 0;
    handleTaxToggleChange();
  }

  // Update preset button active state
  document.querySelectorAll('.btn-tax-preset[data-rate]').forEach(btn => {
    const btnRate = parseFloat(btn.getAttribute('data-rate'));
    btn.classList.toggle('active', btnRate === rate);
  });

  updateLiveReceiptPreview();
}

async function loadReceiptSettings() {
  const container = document.getElementById('settings-content-area');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);">Memuat pengaturan struk & pajak...</div>';

  try {
    const rs = await api.getReceiptSettings(state.activeOutletId || 1);
    state.receiptSettings = rs;
    state.receiptPaperWidth = rs.paper_width || '58mm';

    const isTaxEnabled = rs.tax_enabled !== false && rs.tax_enabled !== 'false' && rs.tax_enabled !== 0;
    const taxRate = (typeof rs.tax_rate === 'number') ? rs.tax_rate : parseFloat(rs.tax_rate || '10.0') || 0.0;
    const taxName = rs.tax_name || 'PB1 / Pajak Restoran';
    const showTaxOnReceipt = rs.show_tax_on_receipt !== false && rs.show_tax_on_receipt !== 'false';

    container.innerHTML = `
      <div class="receipt-settings-grid">
        <!-- Left: Form Pengaturan Struk & Pajak -->
        <div style="display:flex;flex-direction:column;gap:1.25rem;">
          
          <!-- Card 1: Format & Header Toko -->
          <div class="settings-section-card">
            <div class="settings-section-header">
              <div>
                <div class="settings-section-title">
                  <span>🧾</span> Format &amp; Header Toko
                </div>
                <div class="settings-section-subtitle">Identitas toko yang dicetak paling atas pada setiap lembar struk</div>
              </div>
              <span style="font-size:0.75rem;padding:3px 9px;border-radius:var(--radius-full);background:var(--primary-subtle);color:var(--primary);font-weight:700;">Outlet #${rs.outlet_id}</span>
            </div>

            <div class="settings-field-group">
              <label class="settings-field-label">Header Struk (Nama Usaha):</label>
              <input type="text" id="receipt-header-input" class="settings-field-input" value="${rs.receipt_header || ''}" placeholder="Misal: TERAS MANIS CAFE & RESTO" oninput="updateLiveReceiptPreview()" />
              <span class="settings-hint-text">Nama utama brand yang dicetak tebal di bagian paling atas nota</span>
            </div>

            <div class="settings-field-group">
              <label class="settings-field-label">NPWP / Nomor Pajak Usaha:</label>
              <input type="text" id="receipt-tax-input" class="settings-field-input" value="${rs.tax_id || ''}" placeholder="Misal: 01.892.481.0-421.000" oninput="updateLiveReceiptPreview()" />
              <span class="settings-hint-text">Nomor Pokok Wajib Pajak untuk kepatuhan administrasi fiskal</span>
            </div>

            <div class="toggle-switch-row">
              <div>
                <div style="font-weight:700;font-size:0.88rem;color:var(--text-heading);">Cetak Logo Brand di Struk</div>
                <div style="font-size:0.74rem;color:var(--text-muted);">Mencetak gambar logo cafe di bagian atas struk thermal</div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" id="receipt-show-logo" ${rs.show_logo ? 'checked' : ''} onchange="updateLiveReceiptPreview()" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <!-- Card 2: PENGATURAN PAJAK (PB1 / PPN) [FLEKSIBEL] -->
          <div class="settings-section-card" style="border-left:4px solid var(--primary);">
            <div class="settings-section-header">
              <div>
                <div class="settings-section-title">
                  <span>💰</span> Pengaturan Pajak (PB1 / PPN)
                </div>
                <div class="settings-section-subtitle">Tentukan apakah transaksi membebankan pajak serta tarif persentasenya</div>
              </div>
              <span id="tax-active-status-badge" style="font-size:0.75rem;padding:3px 9px;border-radius:var(--radius-full);font-weight:700;${isTaxEnabled ? 'background:var(--accent-green-bg);color:var(--accent-green);border:1px solid var(--accent-green-border);' : 'background:var(--accent-red-bg);color:var(--accent-red);border:1px solid var(--accent-red-border);'}">
                ${isTaxEnabled ? '🟢 Pajak Aktif' : '⚪ Bebas Pajak'}
              </span>
            </div>

            <!-- Toggle Utama Pajak: Bisa Ditambahkan atau Tidak -->
            <div class="toggle-switch-row" style="background:var(--bg-card);border:1.5px solid ${isTaxEnabled ? 'var(--primary-glow)' : 'var(--border-subtle)'};">
              <div>
                <div style="font-weight:800;font-size:0.92rem;color:var(--text-heading);">Kenakan Pajak pada Transaksi Kasir</div>
                <div style="font-size:0.76rem;color:var(--text-muted);">Jika dinonaktifkan, kasir tidak membebankan pajak pada transaksi (Pajak = Rp 0)</div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" id="receipt-tax-enabled" ${isTaxEnabled ? 'checked' : ''} onchange="handleTaxToggleChange()" />
                <span class="toggle-slider"></span>
              </label>
            </div>

            <!-- Detail Form Pajak (Persentase & Nama) -->
            <div id="receipt-tax-fields" style="display:flex;flex-direction:column;gap:1rem;${isTaxEnabled ? '' : 'opacity:0.45;pointer-events:none;'}">
              
              <div class="settings-field-group">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <label class="settings-field-label">PERSENTASE TARIF PAJAK (%):</label>
                  <span style="font-size:0.75rem;color:var(--primary);font-weight:700;" id="tax-rate-display-badge">Tarif Saat Ini: ${taxRate}%</span>
                </div>
                <div style="position:relative;display:flex;align-items:center;">
                  <input type="number" id="receipt-tax-rate-input" class="settings-field-input" value="${taxRate}" min="0" max="100" step="0.1" placeholder="Misal: 10" oninput="updateLiveReceiptPreview()" style="font-size:1.05rem;font-weight:700;padding-right:3rem;" />
                  <span style="position:absolute;right:14px;font-weight:800;color:var(--text-muted);font-size:1rem;">%</span>
                </div>

                <!-- Tombol Preset Cepat Persentase Pajak -->
                <div class="tax-presets-row">
                  <span style="font-size:0.74rem;color:var(--text-muted);font-weight:700;">Pilihan Cepat:</span>
                  <button type="button" class="btn-tax-preset ${taxRate === 0 ? 'active' : ''}" data-rate="0" onclick="setTaxPreset(0, 'Bebas Pajak')">
                    🚫 0% Bebas Pajak
                  </button>
                  <button type="button" class="btn-tax-preset ${taxRate === 10 ? 'active' : ''}" data-rate="10" onclick="setTaxPreset(10, 'PB1 / Pajak Restoran')">
                    🍽️ 10% (PB1 Resto)
                  </button>
                  <button type="button" class="btn-tax-preset ${taxRate === 11 ? 'active' : ''}" data-rate="11" onclick="setTaxPreset(11, 'PPN 11%')">
                    🏛️ 11% (PPN)
                  </button>
                  <button type="button" class="btn-tax-preset ${taxRate === 12 ? 'active' : ''}" data-rate="12" onclick="setTaxPreset(12, 'PPN 12%')">
                    📈 12% (PPN Baru)
                  </button>
                </div>
              </div>

              <div class="settings-field-group">
                <label class="settings-field-label">Nama / Label Pajak pada Struk:</label>
                <input type="text" id="receipt-tax-name-input" class="settings-field-input" value="${taxName}" placeholder="Misal: PB1 / Pajak Restoran atau PPN" oninput="updateLiveReceiptPreview()" />
                <span class="settings-hint-text">Label nama pajak yang tampil di nota struk dan rincian transaksi belanja</span>
              </div>

              <div class="toggle-switch-row">
                <div>
                  <div style="font-weight:700;font-size:0.88rem;color:var(--text-heading);">Cetak Baris Rincian Pajak di Struk</div>
                  <div style="font-size:0.74rem;color:var(--text-muted);">Menampilkan baris perincian nilai pajak pada struk thermal</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" id="receipt-show-tax-on-receipt" ${showTaxOnReceipt ? 'checked' : ''} onchange="updateLiveReceiptPreview()" />
                  <span class="toggle-slider"></span>
                </label>
              </div>

              <!-- Simulasi Perhitungan Otomatis -->
              <div class="tax-calc-preview-card" id="receipt-tax-calc-card">
                <div>
                  <div style="font-size:0.75rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Simulasi Perhitungan Nota:</div>
                  <div style="font-size:0.86rem;color:var(--text-heading);font-weight:600;margin-top:2px;" id="tax-sim-formula">
                    Pesanan Rp 50.000 &rarr; Pajak: <strong style="color:var(--primary);">Rp 5.000</strong>
                  </div>
                </div>
                <span class="tax-calc-preview-badge" id="tax-sim-total">Total: Rp 55.000</span>
              </div>

            </div>
          </div>

          <!-- Card 3: Wi-Fi, Medsos & Footer -->
          <div class="settings-section-card">
            <div class="settings-section-header">
              <div>
                <div class="settings-section-title">
                  <span>📶</span> Akses Wi-Fi &amp; Footer Struk
                </div>
                <div class="settings-section-subtitle">Informasi fasilitas pelanggan dan pesan penutup struk</div>
              </div>
            </div>

            <div class="toggle-switch-row">
              <div>
                <div style="font-weight:700;font-size:0.88rem;color:var(--text-heading);">Cetak Akses Wi-Fi di Struk</div>
                <div style="font-size:0.74rem;color:var(--text-muted);">Membantu pelanggan langsung terhubung ke Wi-Fi cafe</div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" id="receipt-show-wifi" ${rs.show_wifi ? 'checked' : ''} onchange="updateLiveReceiptPreview()" />
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="settings-form-grid" id="receipt-wifi-fields" style="${rs.show_wifi ? '' : 'opacity:0.45;pointer-events:none;'}">
              <div class="settings-field-group">
                <label class="settings-field-label">Nama Wi-Fi (SSID):</label>
                <input type="text" id="receipt-wifi-ssid" class="settings-field-input" value="${rs.wifi_ssid || ''}" placeholder="TerasManis_Guest" oninput="updateLiveReceiptPreview()" />
              </div>

              <div class="settings-field-group">
                <label class="settings-field-label">Kata Sandi (Password):</label>
                <input type="text" id="receipt-wifi-password" class="settings-field-input" value="${rs.wifi_password || ''}" placeholder="kopiterasmanis" oninput="updateLiveReceiptPreview()" />
              </div>
            </div>

            <div class="settings-field-group">
              <label class="settings-field-label">Akun Instagram / Media Sosial:</label>
              <input type="text" id="receipt-instagram-input" class="settings-field-input" value="${rs.instagram || ''}" placeholder="@terasmanis.cafe" oninput="updateLiveReceiptPreview()" />
            </div>

            <div class="settings-field-group">
              <label class="settings-field-label">Pesan Footer Struk:</label>
              <textarea id="receipt-footer-input" rows="2" class="settings-field-textarea" placeholder="Pesan terima kasih atau pengumuman promo..." oninput="updateLiveReceiptPreview()">${rs.receipt_footer || ''}</textarea>
            </div>

            <div style="display:flex;justify-content:flex-end;gap:0.75rem;margin-top:0.75rem;padding-top:1rem;border-top:1px solid var(--border-subtle);flex-wrap:wrap;">
              <button type="button" onclick="printSampleReceipt()" style="padding:0.75rem 1.35rem;background:var(--bg-main);border:1px solid var(--border-medium);border-radius:var(--radius-md);color:var(--text-main);font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;transition:var(--transition);">
                <span>🖨️</span> Cetak Struk Uji Coba
              </button>
              <button type="button" onclick="submitSaveReceiptSettings()" style="padding:0.75rem 2rem;background:linear-gradient(135deg,var(--primary),var(--primary-dark));border:none;border-radius:var(--radius-md);color:#fff;font-weight:800;cursor:pointer;box-shadow:0 4px 15px var(--primary-glow);display:flex;align-items:center;gap:8px;transition:var(--transition);">
                <span>💾</span> Simpan Pengaturan Struk
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Live Interactive Thermal Receipt Preview -->
        <div class="receipt-preview-wrapper">
          <div class="receipt-preview-header">
            <div>
              <div style="font-size:0.9rem;font-weight:800;color:var(--text-heading);display:flex;align-items:center;gap:6px;">
                <span>📄</span> Pratinjau Struk Kasir
              </div>
              <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;">Kertas Thermal POS Dinamis</div>
            </div>
            <span style="font-size:0.72rem;padding:2px 8px;border-radius:var(--radius-full);background:var(--accent-green-bg);color:var(--accent-green);font-weight:700;border:1px solid var(--accent-green-border);">● Real-Time</span>
          </div>

          <!-- Pilihan Ukuran Kertas Thermal -->
          <div style="display:flex;gap:0.4rem;width:100%;justify-content:center;">
            <button type="button" id="btn-paper-58" class="btn-tax-preset ${(state.receiptPaperWidth !== '80mm') ? 'active' : ''}" onclick="setReceiptPaperWidth('58mm')">
              📏 58mm (Kompak)
            </button>
            <button type="button" id="btn-paper-80" class="btn-tax-preset ${(state.receiptPaperWidth === '80mm') ? 'active' : ''}" onclick="setReceiptPaperWidth('80mm')">
              📐 80mm (Standar Lebar)
            </button>
          </div>

          <!-- Paper Container with Jagged / Serrated Edges -->
          <div class="receipt-paper-container">
            <div style="display:flex;flex-direction:column;align-items:center;width:100%;">
              <div class="receipt-paper-tear-top"></div>
              <div class="receipt-live-paper ${(state.receiptPaperWidth === '80mm') ? 'width-80mm' : ''}" id="receipt-live-paper-box">
                <!-- Dynamically populated by updateLiveReceiptPreview() -->
              </div>
              <div class="receipt-paper-tear-bottom"></div>
            </div>
          </div>

          <div style="font-size:0.74rem;color:var(--text-muted);text-align:center;line-height:1.4;">
            💡 Pratinjau diperbarui otomatis saat teks, toggle switch, atau persentase pajak diubah.
          </div>
        </div>
      </div>
    `;

    updateLiveReceiptPreview();
  } catch (err) {
    console.error('Error loadReceiptSettings:', err);
    container.innerHTML = `<div style="color:var(--accent-red);padding:2rem;">Gagal memuat pengaturan struk: ${err.message}</div>`;
  }
}

function updateLiveReceiptPreview() {
  const paper = document.getElementById('receipt-live-paper-box');
  if (!paper) return;

  const header = document.getElementById('receipt-header-input')?.value.trim() || 'TERAS MANIS CAFE & RESTO';
  const taxId = document.getElementById('receipt-tax-input')?.value.trim() || '01.892.481.0-421.000';
  const showLogo = document.getElementById('receipt-show-logo')?.checked ?? true;
  const showWifi = document.getElementById('receipt-show-wifi')?.checked ?? true;
  const wifiSsid = document.getElementById('receipt-wifi-ssid')?.value.trim() || 'TerasManis_Guest';
  const wifiPassword = document.getElementById('receipt-wifi-password')?.value.trim() || 'kopiterasmanis';
  const instagram = document.getElementById('receipt-instagram-input')?.value.trim() || '@terasmanis.cafe';
  const footer = document.getElementById('receipt-footer-input')?.value.trim() || 'Terima kasih atas kunjungan Anda!';

  // Tax values
  const taxEnabled = document.getElementById('receipt-tax-enabled')?.checked ?? true;
  const rawRate = parseFloat(document.getElementById('receipt-tax-rate-input')?.value);
  const taxRate = isNaN(rawRate) ? 0 : Math.max(0, rawRate);
  const taxName = document.getElementById('receipt-tax-name-input')?.value.trim() || 'PB1';
  const showTaxOnReceipt = document.getElementById('receipt-show-tax-on-receipt')?.checked ?? true;

  // Sync badge status & formula display
  const statusBadge = document.getElementById('tax-active-status-badge');
  if (statusBadge) {
    statusBadge.innerHTML = taxEnabled ? '🟢 Pajak Aktif' : '⚪ Bebas Pajak';
    statusBadge.style.background = taxEnabled ? 'var(--accent-green-bg)' : 'var(--accent-red-bg)';
    statusBadge.style.color = taxEnabled ? 'var(--accent-green)' : 'var(--accent-red)';
    statusBadge.style.border = taxEnabled ? '1px solid var(--accent-green-border)' : '1px solid var(--accent-red-border)';
  }

  const rateBadge = document.getElementById('tax-rate-display-badge');
  if (rateBadge) {
    rateBadge.innerText = `Tarif Saat Ini: ${taxRate}%`;
  }

  // Update Wi-Fi fields disabled state
  const wifiFields = document.getElementById('receipt-wifi-fields');
  if (wifiFields) {
    wifiFields.style.opacity = showWifi ? '1' : '0.45';
    wifiFields.style.pointerEvents = showWifi ? 'auto' : 'none';
  }

  // Sample items calculations
  const sampleSubtotal = 50000;
  const sampleTaxable = sampleSubtotal;
  const sampleTax = taxEnabled ? Math.round(sampleTaxable * (taxRate / 100)) : 0;
  const sampleGrandTotal = sampleTaxable + sampleTax;

  // Update simulation formula card
  const simFormula = document.getElementById('tax-sim-formula');
  const simTotal = document.getElementById('tax-sim-total');
  if (simFormula && simTotal) {
    if (taxEnabled) {
      simFormula.innerHTML = `Pesanan Rp 50.000 &rarr; Pajak (${taxRate}%): <strong style="color:var(--primary);">${api.formatRupiah(sampleTax)}</strong>`;
    } else {
      simFormula.innerHTML = `Pesanan Rp 50.000 &rarr; <span style="color:var(--text-muted);font-weight:700;">Tanpa Beban Pajak (0%)</span>`;
    }
    simTotal.innerText = `Total: ${api.formatRupiah(sampleGrandTotal)}`;
  }

  const logoUrl = (state.brand && state.brand.logo) ? state.brand.logo : '/static/img/coffee.jpg';
  const outletAddr = (state.outlet && state.outlet.address) ? state.outlet.address : 'Jl. Cipasir, Gg. Pancasila, RT.03/RW.09, Bandung';
  const outletPhone = (state.outlet && state.outlet.phone) ? state.outlet.phone : '0812-3456-7890';
  const cashierName = (state.currentUser && state.currentUser.name) ? state.currentUser.name : 'Kasir Utama';

  paper.innerHTML = `
    <div style="text-align:center;border-bottom:1px dashed #78716c;padding-bottom:8px;">
      ${showLogo ? `
        <div style="margin-bottom:6px;">
          <img src="${logoUrl}" alt="Logo" style="max-height:44px;max-width:110px;object-fit:contain;" onerror="this.style.display='none'" />
        </div>
      ` : ''}
      <div style="font-weight:800;font-size:1.05rem;letter-spacing:0.02em;line-height:1.2;">${header}</div>
      <div style="font-size:0.72rem;color:#57534e;margin-top:2px;">${outletAddr}</div>
      <div style="font-size:0.72rem;color:#57534e;">Telp: ${outletPhone} • NPWP: ${taxId}</div>
      <div style="margin-top:8px;font-size:0.74rem;text-align:left;border-top:1px dashed #a8a29e;padding-top:5px;">
        <div style="display:flex;justify-content:space-between;"><span>Nota:</span><strong>INV/2026/09/0088</strong></div>
        <div style="display:flex;justify-content:space-between;"><span>Waktu:</span><span>${new Date().toLocaleString('id-ID', { dateStyle:'short', timeStyle:'short' })}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>Kasir:</span><span>${cashierName}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>Meja:</span><span>Meja 04 (Indoor AC)</span></div>
      </div>
    </div>

    <!-- Sample Items -->
    <div style="display:flex;flex-direction:column;gap:5px;margin:8px 0;font-size:0.78rem;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div style="font-weight:600;">1x Caramel Macchiato</div>
          <div style="font-size:0.68rem;color:#78716c;">Ukuran: Large, Less Sugar</div>
        </div>
        <span style="font-weight:bold;">Rp 28.000</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div style="font-weight:600;">1x Butter Croissant</div>
          <div style="font-size:0.68rem;color:#78716c;">Extra: Warm Butter</div>
        </div>
        <span style="font-weight:bold;">Rp 22.000</span>
      </div>
    </div>

    <!-- Summary -->
    <div style="border-top:1px dashed #78716c;padding-top:6px;display:flex;flex-direction:column;gap:3px;font-size:0.76rem;">
      <div style="display:flex;justify-content:space-between;"><span>Subtotal:</span><span>Rp 50.000</span></div>
      
      ${(taxEnabled && showTaxOnReceipt) ? `
        <div style="display:flex;justify-content:space-between;color:#1e293b;">
          <span>${taxName} (${taxRate}%):</span>
          <span style="font-weight:bold;">${api.formatRupiah(sampleTax)}</span>
        </div>
      ` : ''}

      <div style="display:flex;justify-content:space-between;font-size:0.98rem;font-weight:800;border-top:1px solid #1c1917;padding-top:4px;margin-top:2px;">
        <span>TOTAL:</span><span>${api.formatRupiah(sampleGrandTotal)}</span>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:2px;"><span>Tunai (Cash):</span><span>Rp 100.000</span></div>
      <div style="display:flex;justify-content:space-between;font-weight:bold;color:#059669;"><span>Kembalian:</span><span>${api.formatRupiah(100000 - sampleGrandTotal)}</span></div>
    </div>

    <!-- Footer -->
    <div style="text-align:center;font-size:0.72rem;color:#57534e;margin-top:10px;border-top:1px dashed #78716c;padding-top:8px;line-height:1.4;">
      ${footer}<br>
      ${showWifi ? `Wifi: <strong>${wifiSsid}</strong> • Pass: <strong>${wifiPassword}</strong><br>` : ''}
      ${instagram ? `Instagram: <strong>${instagram}</strong>` : ''}
    </div>
  `;
}

async function submitSaveReceiptSettings() {
  const outletId = state.activeOutletId || 1;
  const header = document.getElementById('receipt-header-input')?.value.trim();
  const taxId = document.getElementById('receipt-tax-input')?.value.trim();
  const showLogo = document.getElementById('receipt-show-logo')?.checked ?? true;
  const showWifi = document.getElementById('receipt-show-wifi')?.checked ?? true;
  const wifiSsid = document.getElementById('receipt-wifi-ssid')?.value.trim();
  const wifiPassword = document.getElementById('receipt-wifi-password')?.value.trim();
  const instagram = document.getElementById('receipt-instagram-input')?.value.trim();
  const footer = document.getElementById('receipt-footer-input')?.value.trim();

  const taxEnabled = document.getElementById('receipt-tax-enabled')?.checked ?? true;
  const rawRate = parseFloat(document.getElementById('receipt-tax-rate-input')?.value);
  const taxRate = isNaN(rawRate) ? 0 : Math.max(0, rawRate);
  const taxName = document.getElementById('receipt-tax-name-input')?.value.trim() || 'PB1 / Pajak Restoran';
  const showTaxOnReceipt = document.getElementById('receipt-show-tax-on-receipt')?.checked ?? true;
  const paperWidth = state.receiptPaperWidth || '58mm';

  try {
    const payload = {
      outlet_id: outletId,
      receipt_header: header,
      tax_id: taxId,
      show_logo: showLogo,
      show_wifi: showWifi,
      wifi_ssid: wifiSsid,
      wifi_password: wifiPassword,
      instagram: instagram,
      receipt_footer: footer,
      tax_enabled: taxEnabled,
      tax_rate: taxRate,
      tax_name: taxName,
      show_tax_on_receipt: showTaxOnReceipt,
      paper_width: paperWidth
    };

    const updated = await api.updateReceiptSettings(payload);
    state.receiptSettings = updated;
    api.showToast('Pengaturan struk & pajak berhasil disimpan!', 'success');
    updateLiveReceiptPreview();
    if (typeof renderCart === 'function') {
      renderCart();
    }
  } catch (err) {
    console.error('Error saving receipt settings:', err);
    api.showToast(`Gagal menyimpan pengaturan struk: ${err.message}`, 'error');
  }
}

function printSampleReceipt() {
  const paper = document.getElementById('receipt-live-paper-box');
  if (!paper) return;

  const printWin = window.open('', '_blank', 'width=380,height=600');
  if (!printWin) {
    window.print();
    return;
  }

  printWin.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Cetak Struk Contoh</title>
      <style>
        body { margin:0; padding:15px; font-family:'Courier New', Courier, monospace; font-size:12px; color:#000; }
        .receipt-live-paper { width:100%; max-width:300px; margin:0 auto; }
      </style>
    </head>
    <body>
      <div class="receipt-live-paper">${paper.innerHTML}</div>
      <script>
        window.onload = function() { window.print(); setTimeout(() => window.close(), 500); };
      <\/script>
    </body>
    </html>
  `);
  printWin.document.close();
}

// ==========================================================================
// EMPLOYEE ATTENDANCE (ABSENSI KARYAWAN) MODULE
// ==========================================================================
state.attendanceData = null;
state.activeAttendanceTab = 'cards';

function switchAttendanceTab(tabName, updateHash = true) {
  state.activeAttendanceTab = tabName;
  sessionStorage.setItem('aurora_current_view', 'view-attendance');
  sessionStorage.setItem('aurora_attendance_subtab', tabName);
  localStorage.setItem('aurora_last_view', 'view-attendance');
  localStorage.setItem('aurora_attendance_subtab', tabName);

  if (updateHash) {
    try {
      window.history.replaceState(null, '', `#attendance/${tabName}`);
    } catch (e) {
      window.location.hash = `#attendance/${tabName}`;
    }
  }

  const btnCards = document.getElementById('att-sub-tab-cards');
  const btnDaily = document.getElementById('att-sub-tab-daily');
  const btnMonthly = document.getElementById('att-sub-tab-monthly');

  const viewCards = document.getElementById('att-view-cards');
  const viewDaily = document.getElementById('att-view-daily');
  const viewMonthly = document.getElementById('att-view-monthly');

  [btnCards, btnDaily, btnMonthly].forEach(b => b && b.classList.remove('active'));
  [viewCards, viewDaily, viewMonthly].forEach(v => v && (v.style.display = 'none'));

  if (tabName === 'cards') {
    if (btnCards) btnCards.classList.add('active');
    if (viewCards) viewCards.style.display = 'block';
  } else if (tabName === 'daily') {
    if (btnDaily) btnDaily.classList.add('active');
    if (viewDaily) viewDaily.style.display = 'block';
    loadDailyAttendanceTable();
  } else if (tabName === 'monthly') {
    if (btnMonthly) btnMonthly.classList.add('active');
    if (viewMonthly) viewMonthly.style.display = 'block';
    loadAttendanceMonthlySummary();
  }
}

function formatTimeOnly(timeStr) {
  if (!timeStr) return '-';
  try {
    const parts = timeStr.trim().split(' ');
    if (parts.length > 1) {
      return parts[1].slice(0, 5);
    }
    return timeStr.slice(11, 16) || timeStr;
  } catch (e) {
    return timeStr;
  }
}

function formatWorkMinutes(minutes) {
  if (minutes === null || minutes === undefined) return '-';
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs > 0) {
    return `${hrs} jam ${mins} mnt`;
  }
  return `${mins} mnt`;
}

function calculateLiveElapsed(clockInStr) {
  if (!clockInStr) return '-';
  try {
    const cin = new Date(clockInStr.replace(' ', 'T'));
    const now = new Date();
    const diffMins = Math.max(1, Math.floor((now - cin) / 60000));
    return formatWorkMinutes(diffMins);
  } catch (e) {
    return '-';
  }
}

async function loadAttendance() {
  const outletId = state.activeOutletId || 1;
  try {
    const data = await api.getAttendance(outletId);
    state.attendanceData = data;

    // 1. Update stats
    const elTotal = document.getElementById('att-stat-total');
    const elPresent = document.getElementById('att-stat-present');
    const elWorking = document.getElementById('att-stat-working');
    const elCompleted = document.getElementById('att-stat-completed');

    if (elTotal) elTotal.innerText = data.total_employees;
    if (elPresent) elPresent.innerText = data.present_count;
    if (elWorking) elWorking.innerText = data.active_working_count;
    if (elCompleted) elCompleted.innerText = data.completed_count;

    // 2. Format current date label
    const dateLabel = document.getElementById('att-current-date-label');
    if (dateLabel) {
      const today = new Date();
      dateLabel.innerText = today.toLocaleDateString('id-ID', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }

    // Set today's date in daily date picker if empty
    const dailyPicker = document.getElementById('att-daily-date-picker');
    if (dailyPicker && !dailyPicker.value) {
      dailyPicker.value = data.date;
    }

    // Set current month in monthly picker if empty
    const monthlyPicker = document.getElementById('att-monthly-month-picker');
    if (monthlyPicker && !monthlyPicker.value) {
      monthlyPicker.value = data.date.slice(0, 7);
    }

    // 3. Populate Quick Select Dropdown
    const quickSelect = document.getElementById('att-quick-emp-select');
    if (quickSelect) {
      quickSelect.innerHTML = '<option value="">Pilih Karyawan...</option>';
      data.employees.forEach(emp => {
        const statusNote = emp.attendance_status === 'working' ? ' (Sedang Bekerja)' : (emp.attendance_status === 'clocked_out' ? ' (Sudah Selesai)' : '');
        quickSelect.innerHTML += `<option value="${emp.employee_id}">${emp.name}${statusNote}</option>`;
      });
    }

    // 4. Render Employee Cards Grid
    const cardsContainer = document.getElementById('att-cards-container');
    if (cardsContainer) {
      if (!data.employees || data.employees.length === 0) {
        cardsContainer.innerHTML = `
          <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted);">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">👥</div>
            <p>Belum ada karyawan aktif di outlet ini.</p>
          </div>
        `;
      } else {
        cardsContainer.innerHTML = data.employees.map(emp => {
          const initial = emp.name.charAt(0).toUpperCase();
          const isWorking = emp.attendance_status === 'working';
          const isClockedOut = emp.attendance_status === 'clocked_out';

          let statusBadgeHtml = '';
          let timesBoxHtml = '';
          let actionBtnHtml = '';
          let cardClass = 'att-card';
          let avatarClass = 'att-card-avatar';

          if (isWorking) {
            cardClass += ' working';
            avatarClass += ' working';
            statusBadgeHtml = `
              <span class="att-status-badge working">
                <span class="att-status-pulse"></span> Sedang Bekerja
              </span>
            `;
            timesBoxHtml = `
              <div class="att-card-times">
                <div class="att-time-row">
                  <span class="label">Jam Masuk:</span>
                  <span class="val" style="color:var(--accent-green);">${formatTimeOnly(emp.clock_in)}</span>
                </div>
                <div class="att-time-row">
                  <span class="label">Durasi Kerja:</span>
                  <span class="val" style="color:var(--accent-amber);">${calculateLiveElapsed(emp.clock_in)}</span>
                </div>
              </div>
            `;
            actionBtnHtml = `
              <button class="att-btn-clockout" onclick="openClockOutModal(${emp.current_attendance_id}, '${emp.name.replace(/'/g, "\\'")}', '${emp.clock_in}')">
                <span>🚪</span> Clock Out (Pulang)
              </button>
            `;
          } else if (isClockedOut) {
            cardClass += ' clocked-out';
            avatarClass += ' clocked-out';
            statusBadgeHtml = `
              <span class="att-status-badge clocked-out">
                <span>✓</span> Selesai Kerja
              </span>
            `;
            timesBoxHtml = `
              <div class="att-card-times">
                <div class="att-time-row">
                  <span class="label">Masuk / Pulang:</span>
                  <span class="val">${formatTimeOnly(emp.clock_in)} - ${formatTimeOnly(emp.clock_out)}</span>
                </div>
                <div class="att-time-row">
                  <span class="label">Total Kerja:</span>
                  <span class="val" style="color:var(--accent-blue);">${formatWorkMinutes(emp.work_minutes)}</span>
                </div>
              </div>
            `;
            actionBtnHtml = `
              <button class="att-btn-clockin" style="background:var(--bg-surface);border:1px solid var(--border-medium);color:var(--text-main);box-shadow:none;" onclick="openClockInModal(${emp.employee_id}, '${emp.name.replace(/'/g, "\\'")}', '${emp.role_name || ''}')">
                <span>⚡</span> Clock In Lagi (Shift 2)
              </button>
            `;
          } else {
            statusBadgeHtml = `
              <span class="att-status-badge not-clocked-in">
                <span>⚪</span> Belum Hadir
              </span>
            `;
            timesBoxHtml = `
              <div class="att-card-times">
                <div class="att-time-row">
                  <span class="label">Jam Masuk:</span>
                  <span class="val">-</span>
                </div>
                <div class="att-time-row">
                  <span class="label">Durasi:</span>
                  <span class="val">-</span>
                </div>
              </div>
            `;
            actionBtnHtml = `
              <button class="att-btn-clockin" onclick="openClockInModal(${emp.employee_id}, '${emp.name.replace(/'/g, "\\'")}', '${emp.role_name || ''}')">
                <span>⚡</span> Clock In (Masuk)
              </button>
            `;
          }

          return `
            <div class="${cardClass}">
              <div class="att-card-header">
                <div class="${avatarClass}">${initial}</div>
                <div class="att-card-info">
                  <div class="att-card-name" title="${emp.name}">${emp.name}</div>
                  <div class="att-card-role">${emp.role_name || 'Karyawan'}</div>
                </div>
                <div>${statusBadgeHtml}</div>
              </div>

              ${timesBoxHtml}
              ${actionBtnHtml}
            </div>
          `;
        }).join('');

        // Apply active search filter if any
        filterAttendanceCards();
      }
    }

    // 5. Render Daily Records Table
    renderDailyAttendanceTable(data.records);

  } catch (err) {
    console.error('Error loading attendance:', err);
    api.showToast(`Gagal memuat absensi: ${err.message}`, 'error');
  }
}

function filterAttendanceCards() {
  const query = (document.getElementById('att-search-input')?.value || '').toLowerCase().trim();
  const cards = document.querySelectorAll('#att-cards-container .att-card');
  let matchCount = 0;

  cards.forEach(card => {
    const name = card.querySelector('.att-card-name')?.innerText.toLowerCase() || '';
    const role = card.querySelector('.att-card-role')?.innerText.toLowerCase() || '';
    if (!query || name.includes(query) || role.includes(query)) {
      card.style.display = '';
      matchCount++;
    } else {
      card.style.display = 'none';
    }
  });

  // If search yields zero results, show helpful empty state
  let noResultEl = document.getElementById('att-cards-no-result');
  if (query && matchCount === 0) {
    if (!noResultEl) {
      noResultEl = document.createElement('div');
      noResultEl.id = 'att-cards-no-result';
      noResultEl.style.cssText = 'grid-column:1/-1;text-align:center;padding:2.5rem;color:var(--text-muted);background:var(--bg-surface);border-radius:var(--radius-lg);border:1px dashed var(--border-medium);';
      document.getElementById('att-cards-container')?.appendChild(noResultEl);
    }
    noResultEl.innerHTML = `<div style="font-size:2rem;margin-bottom:0.4rem;">🔍</div><p>Tidak ditemukan karyawan dengan kata kunci "<strong>${query}</strong>".</p>`;
    noResultEl.style.display = '';
  } else if (noResultEl) {
    noResultEl.style.display = 'none';
  }
}

// Start live timer ticker for active working attendance cards
if (!window._attendanceTickerInterval) {
  window._attendanceTickerInterval = setInterval(() => {
    const activeView = document.getElementById('view-attendance');
    if (!activeView || !activeView.classList.contains('active')) return;
    const workingCards = document.querySelectorAll('#att-cards-container .att-card.working');
    if (workingCards.length === 0) return;

    if (state.attendanceData && state.attendanceData.employees) {
      state.attendanceData.employees.forEach(emp => {
        if (emp.attendance_status === 'working' && emp.clock_in) {
          workingCards.forEach(card => {
            const nameEl = card.querySelector('.att-card-name');
            if (nameEl && nameEl.innerText === emp.name) {
              const valEl = card.querySelector('.att-time-row:nth-child(2) .val');
              if (valEl) valEl.innerText = calculateLiveElapsed(emp.clock_in);
            }
          });
        }
      });
    }
  }, 10000);
}

function renderDailyAttendanceTable(records) {
  const tbody = document.getElementById('att-daily-table-body');
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align:center;padding:2rem;color:var(--text-muted);">
          Belum ada catatan absensi untuk tanggal ini.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = records.map((r, idx) => {
    const isWorking = !r.clock_out;
    const durasi = isWorking ? calculateLiveElapsed(r.clock_in) : formatWorkMinutes(r.work_minutes);

    const statusBadge = isWorking 
      ? '<span class="att-status-badge working"><span class="att-status-pulse"></span> Bekerja</span>'
      : '<span class="att-status-badge clocked-out">Selesai</span>';

    const actionHtml = isWorking 
      ? `<button onclick="openClockOutModal(${r.id}, '${r.employee_name.replace(/'/g, "\\'")}', '${r.clock_in}')" style="padding:0.35rem 0.75rem;background:var(--accent-red);border:none;border-radius:var(--radius-sm);color:#fff;font-size:0.78rem;font-weight:700;cursor:pointer;">Clock Out</button>`
      : `<button onclick="handleDeleteAttendance(${r.id})" style="padding:0.35rem 0.65rem;background:transparent;border:1px solid var(--border-medium);border-radius:var(--radius-sm);color:var(--text-muted);font-size:0.75rem;cursor:pointer;">Hapus</button>`;

    return `
      <tr>
        <td style="text-align:center;font-weight:600;">${idx + 1}</td>
        <td style="font-weight:700;color:var(--text-heading);">${r.employee_name}</td>
        <td><span style="font-size:0.8rem;padding:2px 8px;background:var(--bg-input);border-radius:10px;">${r.role_name || '-'}</span></td>
        <td style="font-family:var(--font-heading);font-weight:700;color:var(--accent-green);">${formatTimeOnly(r.clock_in)}</td>
        <td style="font-family:var(--font-heading);font-weight:700;color:var(--text-muted);">${formatTimeOnly(r.clock_out)}</td>
        <td style="font-weight:700;">${durasi}</td>
        <td>${statusBadge}</td>
        <td style="font-size:0.82rem;color:var(--text-muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;">${r.notes || '-'}</td>
        <td>${actionHtml}</td>
      </tr>
    `;
  }).join('');
}

async function loadDailyAttendanceTable() {
  const outletId = state.activeOutletId || 1;
  const picker = document.getElementById('att-daily-date-picker');
  const date = picker ? picker.value : null;

  try {
    const data = await api.getAttendance(outletId, date);
    renderDailyAttendanceTable(data.records);
  } catch (err) {
    console.error('Error loading daily table:', err);
    api.showToast(`Gagal memuat rekap harian: ${err.message}`, 'error');
  }
}

function resetDailyAttendanceDate() {
  const picker = document.getElementById('att-daily-date-picker');
  if (picker && state.attendanceData) {
    picker.value = state.attendanceData.date;
  }
  loadDailyAttendanceTable();
}

async function loadAttendanceMonthlySummary() {
  const outletId = state.activeOutletId || 1;
  const picker = document.getElementById('att-monthly-month-picker');
  const month = picker ? picker.value : null;

  const tbody = document.getElementById('att-monthly-table-body');
  if (!tbody) return;

  try {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;">Memuat rekap bulanan...</td></tr>`;
    const res = await api.getAttendanceSummary(outletId, month);

    if (!res.items || res.items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center;padding:2rem;color:var(--text-muted);">
            Tidak ada data absensi untuk periode bulan ini.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = res.items.map((it, idx) => {
      const avgHours = it.total_days_present > 0 ? (it.total_work_hours / it.total_days_present).toFixed(1) : 0;
      return `
        <tr>
          <td style="text-align:center;font-weight:600;">${idx + 1}</td>
          <td style="font-weight:700;color:var(--text-heading);">${it.employee_name}</td>
          <td><span style="font-size:0.8rem;padding:2px 8px;background:var(--bg-input);border-radius:10px;">${it.role_name || '-'}</span></td>
          <td style="font-weight:800;font-family:var(--font-heading);color:var(--accent-green);">${it.total_days_present} Hari</td>
          <td style="font-weight:800;font-family:var(--font-heading);">${it.total_work_hours} Jam (${formatWorkMinutes(it.total_work_minutes)})</td>
          <td style="font-weight:700;color:var(--text-muted);">${avgHours} Jam/Hari</td>
          <td><span style="color:${it.late_count > 0 ? 'var(--accent-red)' : 'var(--text-muted)'};font-weight:700;">${it.late_count} Kali</span></td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading monthly summary:', err);
    api.showToast(`Gagal memuat rekap bulanan: ${err.message}`, 'error');
  }
}

// Quick Clock In
async function handleQuickClockIn() {
  const outletId = state.activeOutletId || 1;
  const select = document.getElementById('att-quick-emp-select');
  const pinInput = document.getElementById('att-quick-pin');

  const empId = select ? parseInt(select.value) : null;
  const pin = pinInput ? pinInput.value.trim() : null;

  if (!empId) {
    api.showToast('Pilih karyawan yang akan Clock In terlebih dahulu', 'error');
    return;
  }

  try {
    const payload = {
      outlet_id: outletId,
      employee_id: empId,
      pin: pin || undefined,
      status: 'present'
    };

    const res = await api.clockIn(payload);
    api.showToast(`✓ Clock In Berhasil untuk ${res.employee_name}!`, 'success');

    if (pinInput) pinInput.value = '';
    if (select) select.value = '';

    await loadAttendance();
  } catch (err) {
    api.showToast(`Gagal Clock In: ${err.message}`, 'error');
  }
}

// Modal Clock In
function openClockInModal(empId, empName, roleName) {
  document.getElementById('att-modal-emp-id').value = empId;
  document.getElementById('att-modal-emp-name').innerText = empName;
  document.getElementById('att-modal-emp-role').innerText = roleName || 'Karyawan';
  document.getElementById('att-modal-emp-avatar').innerText = empName.charAt(0).toUpperCase();
  document.getElementById('att-modal-emp-pin').value = '';
  document.getElementById('att-modal-emp-notes').value = '';

  document.getElementById('att-clockin-modal').classList.add('active');
  setTimeout(() => document.getElementById('att-modal-emp-pin').focus(), 100);
}

function closeClockInModal() {
  document.getElementById('att-clockin-modal').classList.remove('active');
}

async function submitModalClockIn() {
  const outletId = state.activeOutletId || 1;
  const empId = parseInt(document.getElementById('att-modal-emp-id').value);
  const pin = document.getElementById('att-modal-emp-pin').value.trim();
  const notes = document.getElementById('att-modal-emp-notes').value.trim();

  if (!empId) return;

  try {
    const payload = {
      outlet_id: outletId,
      employee_id: empId,
      pin: pin || undefined,
      notes: notes || undefined,
      status: 'present'
    };

    const res = await api.clockIn(payload);
    closeClockInModal();
    api.showToast(`✓ Clock In Berhasil untuk ${res.employee_name}!`, 'success');
    await loadAttendance();
  } catch (err) {
    api.showToast(`Gagal Clock In: ${err.message}`, 'error');
  }
}

// Modal Clock Out
function openClockOutModal(attId, empName, clockInStr) {
  document.getElementById('att-modal-out-id').value = attId;
  document.getElementById('att-modal-out-name').innerText = empName;
  document.getElementById('att-modal-out-avatar').innerText = empName.charAt(0).toUpperCase();
  document.getElementById('att-modal-out-info').innerText = `Masuk pukul ${formatTimeOnly(clockInStr)} (${calculateLiveElapsed(clockInStr)})`;
  document.getElementById('att-modal-out-notes').value = '';

  document.getElementById('att-clockout-modal').classList.add('active');
}

function closeClockOutModal() {
  document.getElementById('att-clockout-modal').classList.remove('active');
}

async function submitModalClockOut() {
  const attId = parseInt(document.getElementById('att-modal-out-id').value);
  const notes = document.getElementById('att-modal-out-notes').value.trim();

  if (!attId) return;

  try {
    const res = await api.clockOut(attId, { notes: notes || undefined });
    closeClockOutModal();
    api.showToast(`✓ Clock Out Berhasil untuk ${res.employee_name}! Total kerja: ${formatWorkMinutes(res.work_minutes)}`, 'success');
    await loadAttendance();
  } catch (err) {
    api.showToast(`Gagal Clock Out: ${err.message}`, 'error');
  }
}

async function handleDeleteAttendance(attId) {
  if (!confirm('Apakah Anda yakin ingin menghapus data absensi ini?')) return;

  try {
    await api.deleteAttendance(attId);
    api.showToast('Data absensi berhasil dihapus', 'success');
    await loadAttendance();
  } catch (err) {
    api.showToast(`Gagal menghapus absensi: ${err.message}`, 'error');
  }
}
