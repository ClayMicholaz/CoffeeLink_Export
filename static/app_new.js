/**
 * CoffeeLink - Shared Application JavaScript
 * Handles sidebar, dropdowns, modals, notifications, and common interactions
 */

(function() {
  'use strict';

  // ============================================
  // Sidebar Management
  // ============================================
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const userMenuTrigger = document.getElementById('userMenuTrigger');
  const userDropdown = document.getElementById('userDropdown');
  const notificationDropdown = document.getElementById('notificationDropdown');
  const topbarUserMenu = document.getElementById('topbarUserMenu');

  // Toggle sidebar on mobile
  if (sidebarToggle && sidebar && sidebarOverlay) {
    sidebarToggle.addEventListener('click', function() {
      const expanded = sidebarToggle.getAttribute('aria-expanded') === 'true';
      sidebarToggle.setAttribute('aria-expanded', !expanded);
      sidebar.classList.toggle('open');
      sidebarOverlay.classList.toggle('open');
      document.body.style.overflow = expanded ? '' : 'hidden';
    });

    sidebarOverlay.addEventListener('click', function() {
      sidebarToggle.setAttribute('aria-expanded', 'false');
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('open');
      document.body.style.overflow = '';
    });
  }

  // ============================================
  // Dropdown Management
  // ============================================
  const dropdowns = document.querySelectorAll('.dropdown');

  function closeAllDropdowns(except = null) {
    dropdowns.forEach(dropdown => {
      if (dropdown !== except) {
        dropdown.classList.remove('open');
        const trigger = dropdown.querySelector('[aria-expanded]');
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  dropdowns.forEach(dropdown => {
    const trigger = dropdown.querySelector('[aria-expanded]');
    const menu = dropdown.querySelector('.dropdown-menu');

    if (trigger && menu) {
      trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        const expanded = trigger.getAttribute('aria-expanded') === 'true';
        closeAllDropdowns(dropdown);
        trigger.setAttribute('aria-expanded', !expanded);
        dropdown.classList.toggle('open');
      });

      // Close on escape key
      dropdown.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          closeAllDropdowns();
          trigger.focus();
        }
      });
    }
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown')) {
      closeAllDropdowns();
    }
  });

  // ============================================
  // Flash Message Auto-dismiss
  // ============================================
  const flashContainer = document.getElementById('flashContainer');
  if (flashContainer) {
    const alerts = flashContainer.querySelectorAll('.alert');
    alerts.forEach(alert => {
      setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 300);
      }, 5000);

      // Manual dismiss
      const closeBtn = alert.querySelector('.alert-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function() {
          alert.style.opacity = '0';
          alert.style.transform = 'translateY(-10px)';
          setTimeout(() => alert.remove(), 300);
        });
      }
    });
  }

  // ============================================
  // Table Interactions
  // ============================================
  // Row click navigation for tables with data-href
  document.querySelectorAll('table tbody tr[data-href]').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function(e) {
      if (!e.target.closest('a, button, .btn, select, input')) {
        window.location.href = this.dataset.href;
      }
    });
  });

  // ============================================
  // Form Enhancements
  // ============================================
  // Character counter for textareas
  document.querySelectorAll('textarea[maxlength]').forEach(textarea => {
    const maxLength = parseInt(textarea.getAttribute('maxlength'), 10);
    const counter = document.createElement('div');
    counter.className = 'char-counter text-xs text-muted text-end mt-1';
    textarea.parentNode.appendChild(counter);

    function updateCounter() {
      const remaining = maxLength - textarea.value.length;
      counter.textContent = `${textarea.value.length} / ${maxLength}`;
      counter.style.color = remaining < 0 ? 'var(--color-error)' : 'var(--color-gray-500)';
    }

    textarea.addEventListener('input', updateCounter);
    updateCounter();
  });

  // ============================================
  // Toast Notifications
  // ============================================
  window.showToast = function(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = `
      <div class="toast-content">
        <svg class="toast-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          ${getToastIcon(type)}
        </svg>
        <span class="toast-message">${message}</span>
      </div>
      <button class="toast-close" aria-label="Dismiss">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Auto dismiss
    const timeout = setTimeout(() => dismissToast(toast), duration);

    // Manual dismiss
    toast.querySelector('.toast-close').addEventListener('click', () => {
      clearTimeout(timeout);
      dismissToast(toast);
    });

    return toast;
  };

  function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
  }

  function dismissToast(toast) {
    toast.classList.remove('show');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }

  function getToastIcon(type) {
    switch (type) {
      case 'success':
        return '<polyline points="20 6 9 17 4 12"/>';
      case 'error':
        return '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>';
      case 'warning':
        return '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>';
      default:
        return '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>';
    }
  }

  // ============================================
  // Confirmation Dialogs
  // ============================================
  window.confirmAction = function(message, onConfirm, onCancel) {
    const modal = document.createElement('div');
    modal.className = 'modal confirm-modal';
    modal.innerHTML = `
      <div class="modal-backdrop"></div>
      <div class="modal-container modal-sm">
        <div class="modal-body text-center p-6">
          <div class="confirm-icon mx-auto mb-4">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <p class="text-secondary mb-6">${message}</p>
          <div class="flex justify-center gap-3">
            <button class="btn btn-secondary confirm-cancel">Cancel</button>
            <button class="btn btn-danger confirm-ok">Confirm</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';

    modal.querySelector('.confirm-ok').addEventListener('click', () => {
      closeModal(modal);
      if (onConfirm) onConfirm();
    });

    modal.querySelector('.confirm-cancel').addEventListener('click', () => {
      closeModal(modal);
      if (onCancel) onCancel();
    });

    modal.querySelector('.modal-backdrop').addEventListener('click', () => {
      closeModal(modal);
      if (onCancel) onCancel();
    });

    function closeModal(m) {
      m.classList.add('closing');
      setTimeout(() => {
        m.remove();
        document.body.style.overflow = '';
      }, 200);
    }
  };

  // ============================================
  // Loading States
  // ============================================
  window.setButtonLoading = function(button, loading) {
    if (loading) {
      button.dataset.originalText = button.innerHTML;
      button.disabled = true;
      button.innerHTML = `
        <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
          <path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1" stroke-linecap="round"/>
        </svg>
        <span>Loading...</span>
      `;
    } else {
      button.disabled = false;
      button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
  };

  // ============================================
  // Number Formatting
  // ============================================
  window.formatNumber = function(num, decimals = 0) {
    return new Intl.NumberFormat('id-ID', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  window.formatCurrency = function(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(amount);
  };

  // ============================================
  // Date Formatting
  // ============================================
  window.formatDate = function(date, options = {}) {
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...options
    };
    return new Date(date).toLocaleDateString('id-ID', defaultOptions);
  };

  window.formatRelativeTime = function(date) {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now - then;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(date);
  };

  // ============================================
  // Initialize on DOM Ready
  // ============================================
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
      });
    }

    // Initialize popovers
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
      document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
        new bootstrap.Popover(el);
      });
    }

    // Update relative time displays
    document.querySelectorAll('[data-relative-time]').forEach(el => {
      el.textContent = formatRelativeTime(el.dataset.relativeTime);
    });

    // Update current year in footer
    const yearEl = document.getElementById('currentYear');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
  });

  // ============================================
  // Export for module systems
  // ============================================
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      showToast,
      confirmAction,
      setButtonLoading,
      formatNumber,
      formatCurrency,
      formatDate,
      formatRelativeTime
    };
  }
})();