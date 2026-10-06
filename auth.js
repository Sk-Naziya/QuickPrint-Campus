async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Something went wrong. Please try again.');
  }
  return data;
}

function setMessage(element, message, type) {
  if (!element) return;
  element.textContent = message || '';
  element.className = 'message-box ' + (type || '');
}

async function handleAuthForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const action = form.dataset.action;
  const endpoint = action === 'register' ? '/api/register' : '/api/login';
  const messageBox = form.querySelector('.message-box');

  try {
    setMessage(messageBox, 'Submitting…', '');
    const data = await apiFetch(endpoint, {
      method: 'POST',
      body: formData,
    });

    setMessage(messageBox, data.message || 'Success', 'success');
    const redirectTarget = form.dataset.redirectTo || 'student-dashboard.html';
    setTimeout(() => {
      window.location.href = redirectTarget;
    }, 500);
  } catch (error) {
    setMessage(messageBox, error.message, 'error');
  }
}

async function handleInterestForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const messageBox = form.querySelector('.message-box');
  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    setMessage(messageBox, 'Submitting your details…', '');
    const data = await apiFetch('/api/interest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    setMessage(messageBox, data.message || 'Success', 'success');
    setTimeout(() => {
      window.location.href = 'success.html';
    }, 500);
  } catch (error) {
    setMessage(messageBox, error.message, 'error');
  }
}

async function handleLogout() {
  try {
    await apiFetch('/api/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    window.location.href = 'login.html';
  } catch (error) {
    console.error(error);
    window.location.href = 'login.html';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const authForms = document.querySelectorAll('form[data-action]');
  const interestForm = document.getElementById('interestForm');
  const logoutButtons = document.querySelectorAll('[data-logout]');

  authForms.forEach((form) => {
    form.addEventListener('submit', handleAuthForm);
  });

  if (interestForm) {
    interestForm.addEventListener('submit', handleInterestForm);
  }

  logoutButtons.forEach((button) => {
    button.addEventListener('click', handleLogout);
  });
});
