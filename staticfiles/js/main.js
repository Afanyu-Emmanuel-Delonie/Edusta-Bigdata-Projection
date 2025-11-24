// Toggle mobile menu
const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileMenu = document.getElementById("mobile-menu");

if (mobileMenuButton && mobileMenu) {
  mobileMenuButton.addEventListener("click", () => {
    mobileMenu.classList.toggle("hidden");
  });

  // Close menu when clicking outside
  document.addEventListener("click", (event) => {
    const isClickInside =
      mobileMenuButton.contains(event.target) ||
      mobileMenu.contains(event.target);

    if (!isClickInside && !mobileMenu.classList.contains("hidden")) {
      mobileMenu.classList.add("hidden");
    }
  });

  // Close menu when resizing to desktop
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 1024) {
      mobileMenu.classList.add("hidden");
    }
  });
}

// Mobile dropdown toggles
const mobileDropdownToggles = document.querySelectorAll('.mobile-dropdown-toggle');

mobileDropdownToggles.forEach(toggle => {
  toggle.addEventListener('click', () => {
    const content = toggle.nextElementSibling;
    const arrow = toggle.querySelector('svg');

    content.classList.toggle('hidden');
    arrow.classList.toggle('rotate-180');
  });
});


/// hero page content slider

// Dynamic dashboard updater: polls KPI and chart endpoints and updates DOM
document.addEventListener('DOMContentLoaded', () => {
  // Only run on pages with the dashboard KPI element
  const totalStudentsEl = document.getElementById('kpi-total-students');
  if (!totalStudentsEl) return;

  const endpoints = {
    kpis: '/performance/api/kpis/',
    charts: {
      distribution: '/performance/api/chart/distribution/',
      status_pie: '/performance/api/chart/status_pie/',
      course_comparison: '/performance/api/chart/course_comparison/',
      grade_distribution: '/performance/api/chart/grade_distribution/',
      top_bottom: '/performance/api/chart/top_bottom/',
    }
  };

  async function fetchKpis() {
    try {
      const res = await fetch(endpoints.kpis, { credentials: 'same-origin' });
      if (!res.ok) return;
      const kpis = await res.json();

      // Update KPI elements if present
      const sets = [
        ['kpi-total-students', kpis.total_students],
        ['kpi-average-score', kpis.average_score ? `${kpis.average_score}%` : kpis.average_score],
        ['kpi-pass-rate', kpis.pass_rate ? `${kpis.pass_rate}%` : kpis.pass_rate],
        ['kpi-excellent', kpis.excellent_count],
        ['kpi-excellent-2', kpis.excellent_count],
        ['kpi-good', kpis.good_count],
        ['kpi-average', kpis.average_count],
        ['kpi-poor', kpis.poor_count],
      ];

      sets.forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el && typeof value !== 'undefined') el.textContent = value;
      });
    } catch (err) {
      console.error('Error fetching KPIs', err);
    }
  }

  async function fetchAndSetChart(id, url) {
    try {
      const res = await fetch(url, { credentials: 'same-origin' });
      if (!res.ok) return;
      const data = await res.json();
      if (data.chart) {
        const img = document.getElementById(id);
        if (img) img.src = data.chart;
      }
    } catch (err) {
      console.error('Error fetching chart', id, err);
    }
  }

  async function refreshAll() {
    await fetchKpis();

    // Update charts
    await Promise.all(Object.entries(endpoints.charts).map(([name, url]) => {
      const id = `chart-${name.replace('_', '-')}`;
      return fetchAndSetChart(id, url);
    }));
  }

  // Initial load
  refreshAll();

  // Poll every 30 seconds
  setInterval(refreshAll, 30000);
  // Expose to other handlers
  window.Dashboard = {
    endpoints,
    refreshAll,
    fetchKpis,
    fetchAndSetChart
  };
});

// Helper: get CSRF token from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

// Wire filter form to update dashboard dynamically
document.addEventListener('DOMContentLoaded', () => {
  const filterForm = document.getElementById('dashboard-filter-form');
  if (!filterForm) return;

  const updateEndpointsWithQuery = () => {
    const qs = new URLSearchParams(new FormData(filterForm)).toString();
    // Update endpoints used by refreshAll
    const endpoints = window.Dashboard && window.Dashboard.endpoints;
    if (!endpoints) return;
    endpoints.kpis = `/performance/api/kpis/?${qs}`;
    Object.keys(endpoints.charts).forEach(name => {
      endpoints.charts[name] = `/performance/api/chart/${name}/?${qs}`;
    });
  };

  // intercept submit
  filterForm.addEventListener('submit', (e) => {
    e.preventDefault();
    updateEndpointsWithQuery();
    if (window.Dashboard && window.Dashboard.refreshAll) window.Dashboard.refreshAll();
  });

  // auto-submit on change for selects/inputs
  Array.from(filterForm.elements).forEach(el => {
    el.addEventListener('change', () => {
      updateEndpointsWithQuery();
      if (window.Dashboard && window.Dashboard.refreshAll) window.Dashboard.refreshAll();
    });
  });
});

// AJAX CSV upload handling (if present)
document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('csv-upload-form');
  if (!uploadForm) return;

  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(uploadForm);
    const action = uploadForm.getAttribute('action') || window.location.href;

    try {
      const res = await fetch(action, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCookie('csrftoken') || ''
        }
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ errors: ['Upload failed'] }));
        alert('Upload failed: ' + (err.errors ? err.errors.join('\n') : 'Unknown'));
        return;
      }

      const data = await res.json();
      if (data.success) {
        alert(`Upload succeeded: ${data.success_count} records imported.`);
        // refresh dashboard immediately
        if (window.Dashboard && window.Dashboard.refreshAll) window.Dashboard.refreshAll();
      } else {
        alert('Upload completed with errors: ' + (data.errors || []).join('\n'));
      }
    } catch (error) {
      console.error('Upload error', error);
      alert('Upload error: ' + error.message);
    }
  });
});

