// API Client for Aurora Cafe POS
const API_BASE = '/api';

const api = {
  // Convert any value to safe finite number (default 0)
  toSafeNumber(val, fallback = 0) {
    if (val === null || val === undefined || val === '' || val === 'undefined' || val === 'NaN') {
      return fallback;
    }
    const num = Number(val);
    return (!isFinite(num) || isNaN(num)) ? fallback : num;
  },

  // Convert empty/undefined/nan to safe string (default '0')
  toSafeString(val, fallback = '0') {
    if (val === null || val === undefined || val === '' || val === 'undefined' || val === 'NaN') {
      return fallback;
    }
    return String(val);
  },

  // Format currency helper (IDR)
  formatRupiah(number) {
    if (number === null || number === undefined || number === '' || number === 'undefined' || number === 'NaN') {
      return 'Rp 0';
    }
    const val = Number(number);
    const safeNumber = (!isFinite(val) || isNaN(val)) ? 0 : val;
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(safeNumber);
  },

  // Toast notification helper
  showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '✓';
    if (type === 'error') icon = '✕';
    if (type === 'info') icon = 'ℹ';

    toast.innerHTML = `<span style="font-weight:bold;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(50px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  // Request wrapper
  async request(endpoint, options = {}) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || 'Terjadi kesalahan sistem');
      }

      return await res.json();
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Endpoints
  loginAccount(username, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  },

  getCurrentUser(token) {
    return this.request('/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  },

  logoutAccount() {
    return this.request('/auth/logout', {
      method: 'POST'
    });
  },

  getBrands() {
    return this.request('/auth/brands');
  },

  getRoles() {
    return this.request('/auth/roles');
  },

  createRole(payload) {
    return this.request('/auth/roles', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateRole(roleId, payload) {
    return this.request(`/auth/roles/${roleId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  deleteRole(roleId) {
    return this.request(`/auth/roles/${roleId}`, {
      method: 'DELETE'
    });
  },

  getOutlets(brandId = 1) {
    return this.request(`/auth/outlets?brand_id=${brandId}`);
  },

  getEmployees(outletId = 1) {
    return this.request(`/auth/employees?outlet_id=${outletId}`);
  },

  createEmployee(payload) {
    return this.request('/auth/employees', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateEmployee(empId, payload) {
    return this.request(`/auth/employees/${empId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  deleteEmployee(empId) {
    return this.request(`/auth/employees/${empId}`, {
      method: 'DELETE'
    });
  },

  verifyPin(outletId, pin, employeeId = null) {
    const payload = {
      outlet_id: parseInt(outletId) || 1,
      pin: String(pin).trim()
    };
    if (employeeId) {
      payload.employee_id = parseInt(employeeId);
    }
    return this.request('/auth/employees/verify-pin', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  getItems(brandId = 1) {
    return this.request(`/catalog/items?brand_id=${brandId}`);
  },

  getCategories(brandId = 1) {
    return this.request(`/catalog/categories?brand_id=${brandId}`);
  },

  async getTables(outletId = 1) {
    try {
      const data = await this.request(`/tables?outlet_id=${outletId}`);
      if (Array.isArray(data) && data.length > 0) return data;
      if (data && Array.isArray(data.tables)) return data.tables;
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.warn('API getTables fallback triggered:', err);
      if (typeof state !== 'undefined' && Array.isArray(state.tables) && state.tables.length > 0) {
        return state.tables;
      }
      return [
        { id: 1, table_number: '01', table_no: '01', capacity: 2, status: 'available', group_name: 'Indoor AC', outlet_id: outletId },
        { id: 2, table_number: '02', table_no: '02', capacity: 4, status: 'occupied', group_name: 'Indoor AC', outlet_id: outletId },
        { id: 3, table_number: '03', table_no: '03', capacity: 4, status: 'available', group_name: 'Indoor AC', outlet_id: outletId },
        { id: 4, table_number: '04', table_no: '04', capacity: 6, status: 'available', group_name: 'VIP', outlet_id: outletId },
        { id: 5, table_number: '05', table_no: '05', capacity: 4, status: 'available', group_name: 'Outdoor', outlet_id: outletId },
        { id: 6, table_number: '06', table_no: '06', capacity: 4, status: 'available', group_name: 'Outdoor', outlet_id: outletId }
      ];
    }
  },

  getIngredients(outletId = 1) {
    return this.request(`/inventory/ingredients?outlet_id=${outletId}`);
  },

  getRecipes(itemId) {
    return this.request(`/inventory/recipes/${itemId}`);
  },

  getCurrentShift(outletId = 1) {
    return this.request(`/shifts/current?outlet_id=${outletId}`);
  },

  openShift(payload) {
    return this.request('/shifts/open', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  closeShift(shiftId, payload) {
    return this.request(`/shifts/${shiftId}/close`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  getDashboard(outletId = 1, period = 'today', startDate = null, endDate = null) {
    let url = `/reports/dashboard?outlet_id=${outletId}&period=${encodeURIComponent(period)}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return this.request(url);
  },

  getSalesReport(outletId = 1) {
    return this.request(`/reports/sales?outlet_id=${outletId}`);
  },

  getTableReport(outletId = 1) {
    return this.request(`/reports/tables?outlet_id=${outletId}`);
  },

  getDailyReport(outletId = 1, date = null) {
    let url = `/reports/daily?outlet_id=${outletId}`;
    if (date) url += `&date=${encodeURIComponent(date)}`;
    return this.request(url);
  },

  getMonthlyReport(outletId = 1, year = null, month = null) {
    let url = `/reports/monthly?outlet_id=${outletId}`;
    if (year)  url += `&year=${year}`;
    if (month) url += `&month=${month}`;
    return this.request(url);
  },

  getCustomReport(outletId = 1, startDate, endDate) {
    return this.request(`/reports/custom?outlet_id=${outletId}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`);
  },

  getProfitReport(outletId = 1, period = 'this_month', startDate = null, endDate = null) {
    let url = `/reports/profit?outlet_id=${outletId}&period=${encodeURIComponent(period)}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return this.request(url);
  },

  getStockValueReport(outletId = 1) {
    return this.request(`/reports/stock-value?outlet_id=${outletId}`);
  },

  getTransactions(outletId = 1, limit = 20) {
    return this.request(`/pos/transactions?outlet_id=${outletId}&limit=${limit}`);
  },

  checkout(payload) {
    return this.request('/pos/checkout', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  voidTransaction(trxId) {
    return this.request(`/pos/transactions/${trxId}/void`, {
      method: 'POST'
    });
  },

  generateQRIS(payload) {
    return this.request('/finance/qris/generate', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  getBankAccounts(outletId = 1) {
    return this.request(`/finance/bank-accounts?outlet_id=${outletId}`);
  },

  getSyncStatus(outletId = 1) {
    return this.request(`/sync/status?outlet_id=${outletId}`);
  },

  // Master Data APIs
  createCategory(payload) {
    return this.request('/catalog/categories', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateCategory(catId, payload) {
    return this.request(`/catalog/categories/${catId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  deleteCategory(catId) {
    return this.request(`/catalog/categories/${catId}`, {
      method: 'DELETE'
    });
  },

  createItem(payload) {
    return this.request('/catalog/items', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateItem(itemId, payload) {
    return this.request(`/catalog/items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  updateItemPrice(itemId, price, costPrice = 0) {
    return this.request(`/catalog/items/${itemId}/price`, {
      method: 'PATCH',
      body: JSON.stringify({ price, cost_price: costPrice })
    });
  },

  deleteItem(itemId) {
    return this.request(`/catalog/items/${itemId}`, {
      method: 'DELETE'
    });
  },

  getModifiers(brandId = 1) {
    return this.request(`/catalog/modifiers?brand_id=${brandId}`);
  },

  createModifier(payload) {
    return this.request('/catalog/modifiers', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateModifier(modId, payload) {
    return this.request(`/catalog/modifiers/${modId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  deleteModifier(modId) {
    return this.request(`/catalog/modifiers/${modId}`, {
      method: 'DELETE'
    });
  },

  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/catalog/upload-image`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorData.detail || 'Gagal mengunggah gambar');
    }

    return await res.json();
  },

  // Settings APIs (Toko, Struk, Akun, Upload Logo)
  getStoreSettings(outletId = 1) {
    return this.request(`/settings/store?outlet_id=${outletId}`);
  },

  updateStoreSettings(payload) {
    return this.request('/settings/store', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  getReceiptSettings(outletId = 1) {
    return this.request(`/settings/receipt?outlet_id=${outletId}`);
  },

  updateReceiptSettings(payload) {
    return this.request('/settings/receipt', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  getAccountProfile(employeeId) {
    return this.request(`/settings/account?employee_id=${employeeId}`);
  },

  updateAccountProfile(payload) {
    return this.request('/settings/account', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  async uploadStoreLogo(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/settings/upload-logo`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorData.detail || 'Gagal mengunggah logo toko');
    }

    return await res.json();
  },

  // Attendance APIs (Clock In, Clock Out, Rekap & Riwayat)
  getAttendance(outletId = 1, date = null) {
    let url = `/attendance?outlet_id=${outletId}`;
    if (date) url += `&date=${encodeURIComponent(date)}`;
    return this.request(url);
  },

  clockIn(payload) {
    return this.request('/attendance/clock-in', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  clockOut(attendanceId, payload = {}) {
    return this.request(`/attendance/${attendanceId}/clock-out`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  clockOutByEmployee(employeeId, outletId = 1, notes = '') {
    return this.request(`/attendance/clock-out-by-employee?employee_id=${employeeId}&outlet_id=${outletId}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`, {
      method: 'POST'
    });
  },

  getAttendanceSummary(outletId = 1, month = null) {
    let url = `/attendance/summary?outlet_id=${outletId}`;
    if (month) url += `&month=${encodeURIComponent(month)}`;
    return this.request(url);
  },

  getAttendanceHistory(outletId = 1, employeeId = null, startDate = null, endDate = null) {
    let url = `/attendance/history?outlet_id=${outletId}`;
    if (employeeId) url += `&employee_id=${employeeId}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return this.request(url);
  },

  deleteAttendance(attendanceId) {
    return this.request(`/attendance/${attendanceId}`, {
      method: 'DELETE'
    });
  },

  // Table Management APIs
  getTableGroups(outletId = 1) {
    return this.request(`/tables/groups?outlet_id=${outletId}`);
  },

  updateTableStatus(tableId, status, currentTransactionId = null) {
    return this.request(`/tables/${tableId}/status`, {
      method: 'PUT',
      body: JSON.stringify({
        status,
        current_transaction_id: currentTransactionId
      })
    });
  },

  createTable(payload) {
    return this.request('/tables', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateTableLayout(tableId, posX, posY) {
    return this.request(`/tables/${tableId}/layout`, {
      method: 'PUT',
      body: JSON.stringify({ pos_x: posX, pos_y: posY })
    });
  },

  // Menu Permissions & Visibility
  getMenuPermissions(outletId = 1) {
    return this.request(`/settings/menu-permissions?outlet_id=${outletId}`);
  },

  saveMenuPermissions(menus, outletId = 1) {
    return this.request(`/settings/menu-permissions?outlet_id=${outletId}`, {
      method: 'PUT',
      body: JSON.stringify({ menus })
    });
  }
};

