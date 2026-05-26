/**
 * charts.js — Chart.js helpers for Academic Intelligence System
 * All chart colours are derived from the CSS design system.
 */

const COLORS = {
  indigo:  '#6366f1',
  indigoLt:'#818cf8',
  success: '#10b981',
  warning: '#f59e0b',
  danger:  '#ef4444',
  info:    '#38bdf8',
  muted:   '#64748b',
  bg:      'rgba(255,255,255,0.04)',
};

// Map a percentage to a colour
function pctColor(pct, threshold = 75) {
  if (pct >= threshold) return COLORS.success;
  if (pct >= threshold * 0.7) return COLORS.warning;
  return COLORS.danger;
}

// Shared default options
const defaultFont = { family: 'Inter, system-ui, sans-serif', size: 12 };

Chart.defaults.font = defaultFont;
Chart.defaults.color = '#94a3b8';

// ── Doughnut / Status Pie ────────────────────────────────────
function buildStatusChart(canvasId, safe, warning, critical) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Safe ✅', 'Warning ⚠️', 'Critical 🔴'],
      datasets: [{
        data: [safe, warning, critical],
        backgroundColor: [
          'rgba(16,185,129,0.85)',
          'rgba(245,158,11,0.85)',
          'rgba(239,68,68,0.85)',
        ],
        borderColor: ['#10b981','#f59e0b','#ef4444'],
        borderWidth: 2,
        hoverOffset: 8,
      }],
    },
    options: {
      cutout: '68%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 20, font: defaultFont } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw} students` } },
      },
      animation: { animateScale: true, duration: 900 },
    },
  });
}

// ── Horizontal Bar (attendance / marks per subject) ──────────
function buildSubjectBar(canvasId, labels, data, label, threshold) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const colors = data.map(v => pctColor(v, threshold));
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: colors.map(c => c + 'cc'),
        borderColor: colors,
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.raw.toFixed(1)}%`,
            afterLabel: ctx => ctx.raw < threshold ? ` ⚠ Below ${threshold}% threshold` : '',
          },
        },
      },
      scales: {
        x: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v + '%' },
        },
        y: {
          grid: { display: false },
        },
      },
      animation: { duration: 800 },
    },
  });
}

// ── Vertical Bar (student comparison) ───────────────────────
function buildStudentBar(canvasId, labels, attendanceData, marksData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Avg Attendance %',
          data: attendanceData,
          backgroundColor: 'rgba(99,102,241,0.7)',
          borderColor: '#6366f1',
          borderWidth: 1.5,
          borderRadius: 6,
        },
        {
          label: 'Avg Marks %',
          data: marksData,
          backgroundColor: 'rgba(16,185,129,0.7)',
          borderColor: '#10b981',
          borderWidth: 1.5,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { padding: 16, font: defaultFont } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}%` } },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v + '%' },
        },
      },
      animation: { duration: 900 },
    },
  });
}

// ── Line chart (marks trend) ─────────────────────────────────
function buildMarksLine(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const palette = [
    COLORS.indigo, COLORS.success, COLORS.warning,
    COLORS.danger, COLORS.info,
  ];
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        borderColor: palette[i % palette.length],
        backgroundColor: palette[i % palette.length] + '22',
        borderWidth: 2.5,
        pointRadius: 4,
        pointHoverRadius: 7,
        tension: 0.4,
        fill: true,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, font: defaultFont } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.raw.toFixed(1)}%` } },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v + '%' },
        },
      },
      animation: { duration: 700 },
    },
  });
}

// ── Radar (attentiveness per subject) ───────────────────────
function buildRadar(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: 'Attentiveness (avg)',
        data,
        borderColor: COLORS.warning,
        backgroundColor: 'rgba(245,158,11,0.15)',
        pointBackgroundColor: COLORS.warning,
        borderWidth: 2,
        pointRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          min: 0, max: 5,
          ticks: { stepSize: 1, backdropColor: 'transparent' },
          grid:  { color: 'rgba(255,255,255,0.08)' },
          angleLines: { color: 'rgba(255,255,255,0.08)' },
          pointLabels: { font: { size: 12 } },
        },
      },
      animation: { duration: 800 },
    },
  });
}

// ── Auto-dismiss flash messages ──────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateX(20px)';
      el.style.transition = 'all 0.4s ease';
      setTimeout(() => el.remove(), 400);
    }, 4500);
  });

  document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const el = btn.closest('.flash');
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 300);
    });
  });

  // Sidebar mobile toggle
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // Modal helpers
  document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.modalOpen;
      document.getElementById(id)?.classList.add('open');
    });
  });
  document.querySelectorAll('[data-modal-close], .modal-overlay').forEach(el => {
    el.addEventListener('click', e => {
      if (e.target === el) {
        el.closest?.('.modal-overlay')?.classList.remove('open');
        document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
      }
    });
  });
  document.querySelectorAll('.modal').forEach(m => {
    m.addEventListener('click', e => e.stopPropagation());
  });

  // Animate progress bars
  document.querySelectorAll('.progress-bar[data-pct]').forEach(bar => {
    const pct = parseFloat(bar.dataset.pct);
    setTimeout(() => { bar.style.width = Math.min(pct, 100) + '%'; }, 200);
  });

  // Animate stat values
  document.querySelectorAll('.stat-value[data-target]').forEach(el => {
    const target = parseFloat(el.dataset.target);
    const isFloat = el.dataset.target.includes('.');
    let current = 0;
    const step = target / 40;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = isFloat ? current.toFixed(1) : Math.round(current);
      if (current >= target) clearInterval(timer);
    }, 20);
  });
});
