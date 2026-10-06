function formatCurrency(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

function calculateEstimate() {
  const form = document.getElementById('orderForm');
  if (!form) return;

  const copiesInput = form.querySelector('#copies');
  const pageRangeInput = form.querySelector('#pageRange');
  const pageCountInput = form.querySelector('#pageCount');
  const colorMode = form.querySelector('#colorMode');

  const copies = Number(copiesInput?.value || 1);
  const pageCount = Number(pageCountInput?.value || 1);
  const rate = colorMode?.value === 'color' ? 5 : 2;

  let estimatedPages = pageCount;
  if (pageRangeInput && pageRangeInput.value.trim()) {
    const rangeText = pageRangeInput.value.trim();
    const chunks = rangeText.split(',').map((chunk) => chunk.trim()).filter(Boolean);
    estimatedPages = 0;
    chunks.forEach((chunk) => {
      if (chunk.includes('-')) {
        const [start, end] = chunk.split('-').map((item) => Number(item.trim()));
        if (!Number.isNaN(start) && !Number.isNaN(end)) {
          estimatedPages += Math.max(0, Math.abs(end - start) + 1);
        }
      } else {
        const value = Number(chunk);
        if (!Number.isNaN(value) && value > 0) {
          estimatedPages += value;
        }
      }
    });
    if (estimatedPages <= 0) {
      estimatedPages = Number(pageCountInput?.value || 1);
    }
  }

  const total = estimatedPages * copies * rate;
  const pagesEl = document.getElementById('summaryPages');
  const copiesEl = document.getElementById('summaryCopies');
  const typeEl = document.getElementById('summaryType');
  const totalEl = document.getElementById('summaryTotal');

  if (pagesEl) pagesEl.textContent = estimatedPages;
  if (copiesEl) copiesEl.textContent = copies;
  if (typeEl) typeEl.textContent = colorMode?.value === 'color' ? 'Color' : 'Black & White';
  if (totalEl) totalEl.textContent = formatCurrency(total);
}

async function loadSession() {
  try {
    const response = await fetch('/api/session', { credentials: 'same-origin' });
    const data = await response.json();
    return data;
  } catch (error) {
    return { authenticated: false };
  }
}

function renderOrders(orders) {
  const container = document.getElementById('ordersContainer');
  if (!container) return;

  if (!orders || orders.length === 0) {
    container.innerHTML = '<div class="empty-state">No orders yet. Start by creating your first print order.</div>';
    return;
  }

  container.innerHTML = orders.map((order) => {
    const statusClass = (order.order_status || 'Received').toLowerCase().replace(/\s+/g, '-');
    return `
      <article class="order-card">
        <div class="dashboard-header" style="margin-bottom: 18px; align-items:flex-start;">
          <div>
            <strong>${order.order_number}</strong>
            <p class="muted">${order.file_name}</p>
          </div>
          <span class="status-chip ${statusClass}">${order.order_status || 'Received'}</span>
        </div>
        <div class="mini-list">
          <div class="summary-row"><span>Pickup</span><strong>${order.pickup_date} ${order.pickup_time}</strong></div>
          <div class="summary-row"><span>Amount</span><strong>${formatCurrency(order.total_amount)}</strong></div>
          <div class="summary-row"><span>Payment</span><strong>${order.payment_status || 'Pending'}</strong></div>
        </div>
        <div class="page-toggle" style="margin-top:18px;">
          <a href="/api/orders/${order.id}/qr" target="_blank" class="secondary-btn" style="text-decoration:none;">View QR</a>
        </div>
      </article>
    `;
  }).join('');
}

async function loadStudentDashboard() {
  const session = await loadSession();
  if (!session.authenticated) {
    window.location.href = 'login.html';
    return;
  }

  const nameEl = document.getElementById('studentName');
  if (nameEl) nameEl.textContent = session.user.name;

  const response = await fetch(`/api/orders/user/${session.user.id}`, { credentials: 'same-origin' });
  const data = await response.json();
  const orders = data.orders || [];

  const orderCountEl = document.getElementById('orderCount');
  const pendingCountEl = document.getElementById('pendingCount');
  const paidCountEl = document.getElementById('paidCount');
  const readyCountEl = document.getElementById('readyCount');

  if (orderCountEl) orderCountEl.textContent = String(orders.length);
  if (pendingCountEl) pendingCountEl.textContent = String(orders.filter((order) => order.payment_status === 'Pending').length);
  if (paidCountEl) paidCountEl.textContent = String(orders.filter((order) => order.payment_status === 'Paid').length);
  if (readyCountEl) readyCountEl.textContent = String(orders.filter((order) => order.order_status === 'Ready for Pickup').length);

  renderOrders(orders);
}

async function loadAdminDashboard() {
  const session = await loadSession();
  if (!session.authenticated || session.user.role !== 'admin') {
    const loginCard = document.getElementById('adminLoginCard');
    const dashboard = document.getElementById('adminDashboard');
    if (loginCard) loginCard.style.display = 'block';
    if (dashboard) dashboard.style.display = 'none';
    return;
  }

  const dashboard = document.getElementById('adminDashboard');
  const loginCard = document.getElementById('adminLoginCard');
  if (dashboard) dashboard.style.display = 'block';
  if (loginCard) loginCard.style.display = 'none';

  const response = await fetch('/api/admin/orders', { credentials: 'same-origin' });
  const data = await response.json();
  const orders = data.orders || [];

  const totalOrders = document.getElementById('totalOrders');
  const pendingOrders = document.getElementById('pendingOrders');
  const paidOrders = document.getElementById('paidOrders');
  const readyOrders = document.getElementById('readyOrders');

  if (totalOrders) totalOrders.textContent = String(orders.length);
  if (pendingOrders) pendingOrders.textContent = String(orders.filter((order) => order.payment_status === 'Pending').length);
  if (paidOrders) paidOrders.textContent = String(orders.filter((order) => order.payment_status === 'Paid').length);
  if (readyOrders) readyOrders.textContent = String(orders.filter((order) => order.order_status === 'Ready for Pickup').length);

  const tbody = document.getElementById('adminOrdersBody');
  if (!tbody) return;

  tbody.innerHTML = orders.map((order) => {
    const statusClass = (order.order_status || 'Received').toLowerCase().replace(/\s+/g, '-');
    return `
      <tr>
        <td>${order.order_number}</td>
        <td>${order.student_name || 'Student'}</td>
        <td>${order.file_name}</td>
        <td>${order.paper_size}</td>
        <td>${order.pickup_date} ${order.pickup_time}</td>
        <td>${order.payment_status}</td>
        <td>
          <span class="status-chip ${statusClass}">${order.order_status || 'Received'}</span>
        </td>
        <td>
          <select class="status-select" data-order-id="${order.id}">
            <option value="Received" ${order.order_status === 'Received' ? 'selected' : ''}>Received</option>
            <option value="Payment Confirmed" ${order.order_status === 'Payment Confirmed' ? 'selected' : ''}>Payment Confirmed</option>
            <option value="Printing" ${order.order_status === 'Printing' ? 'selected' : ''}>Printing</option>
            <option value="Ready for Pickup" ${order.order_status === 'Ready for Pickup' ? 'selected' : ''}>Ready for Pickup</option>
            <option value="Collected" ${order.order_status === 'Collected' ? 'selected' : ''}>Collected</option>
            <option value="Cancelled" ${order.order_status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
          </select>
        </td>
        <td>
          <a href="/api/orders/${order.id}/qr" target="_blank" class="secondary-btn" style="padding:10px 12px; text-decoration:none;">QR</a>
        </td>
      </tr>
    `;
  }).join('');

  document.querySelectorAll('.status-select').forEach((select) => {
    select.addEventListener('change', async (event) => {
      const orderId = event.target.dataset.orderId;
      const nextStatus = event.target.value;
      const payload = { order_status: nextStatus };
      if (nextStatus === 'Ready for Pickup') {
        payload.payment_status = 'Paid';
      }
      try {
        const response = await fetch(`/api/orders/${orderId}/status`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          throw new Error('Unable to update order status.');
        }
        await loadAdminDashboard();
      } catch (error) {
        alert(error.message);
      }
    });
  });

  const searchInput = document.getElementById('adminSearch');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const query = searchInput.value.toLowerCase();
      const rows = [...document.querySelectorAll('#adminOrdersBody tr')];
      rows.forEach((row) => {
        const rowText = row.textContent.toLowerCase();
        row.style.display = rowText.includes(query) ? '' : 'none';
      });
    });
  }
}

async function setupOrderPage() {
  const session = await loadSession();
  if (!session.authenticated) {
    window.location.href = 'login.html';
    return;
  }

  const form = document.getElementById('orderForm');
  if (!form) return;

  form.querySelectorAll('input, select').forEach((field) => {
    field.addEventListener('input', calculateEstimate);
    field.addEventListener('change', calculateEstimate);
  });

  calculateEstimate();

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const messageBox = document.getElementById('orderMessage');
    try {
      const formData = new FormData(form);
      const response = await fetch('/api/orders', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || 'Unable to create your order. Please try again.');
      }

      const order = data.order;
      const paymentSection = document.getElementById('paymentSection');
      const confirmation = document.getElementById('confirmationBlock');
      paymentSection.classList.add('visible');
      document.getElementById('paymentOrderId').value = order.id;
      document.getElementById('paymentOrderNumber').textContent = order.order_number;
      document.getElementById('paymentTotal').textContent = formatCurrency(order.total_amount);
      document.getElementById('paymentPickup').textContent = order.pickup_time;
      confirmation.innerHTML = '<div class="empty-state">Ready for demo payment.</div>';
      setMessage(messageBox, data.message || 'Order created.', 'success');
    } catch (error) {
      setMessage(messageBox, error.message, 'error');
    }
  });

  const payButton = document.getElementById('payNowBtn');
  if (payButton) {
    payButton.addEventListener('click', async () => {
      const orderId = document.getElementById('paymentOrderId').value;
      const confirmation = document.getElementById('confirmationBlock');
      try {
        const response = await fetch(`/api/orders/${orderId}/pay`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.error || 'Unable to complete the demo payment.');
        }

        const qrResponse = await fetch(`/api/orders/${orderId}/qr`, { credentials: 'same-origin' });
        if (!qrResponse.ok) {
          throw new Error('Payment succeeded, but the pickup QR code could not be loaded.');
        }
        const qrBlob = await qrResponse.blob();
        const qrUrl = URL.createObjectURL(qrBlob);

        confirmation.innerHTML = `
          <div class="summary-row"><span>Payment</span><strong>Paid</strong></div>
          <div class="summary-row"><span>Transaction</span><strong>QPPAY-${String(orderId).padStart(6, '0')}</strong></div>
          <div class="summary-row"><span>Status</span><strong>Payment Confirmed</strong></div>
          <img class="qr-image" src="${qrUrl}" alt="Order QR code" />
          <p class="muted" style="text-align:center;">Show this QR code when collecting your prints.</p>
        `;
      } catch (error) {
        setMessage(document.getElementById('orderMessage'), error.message, 'error');
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.body.dataset.page === 'student-dashboard') {
    loadStudentDashboard();
  }

  if (document.body.dataset.page === 'admin-dashboard') {
    loadAdminDashboard();
  }

  if (document.body.dataset.page === 'order-page') {
    setupOrderPage();
  }

  if (document.body.dataset.page === 'student-login') {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.dataset.redirectTo = 'student-dashboard.html';
    }
  }

  if (document.body.dataset.page === 'admin-login') {
    const adminForm = document.getElementById('adminLoginForm');
    if (adminForm) {
      adminForm.dataset.redirectTo = 'admin-dashboard.html';
    }
  }
});
