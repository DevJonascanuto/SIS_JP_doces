/* ═══════════════════════════════════════════════════════════════════════════
   JP DOCES — main.js
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Sidebar toggle (mobile) ───────────────────────────────────────────
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebarOverlay');
  const btnOpen  = document.getElementById('sidebarOpen');
  const btnClose = document.getElementById('sidebarClose');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('active');
    document.body.style.overflow = '';
  }

  btnOpen?.addEventListener('click', openSidebar);
  btnClose?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // ── Topbar date ───────────────────────────────────────────────────────
  const dateEl = document.getElementById('topbarDate');
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('pt-BR', {
      weekday: 'short', day: '2-digit', month: 'short', year: 'numeric',
    });
  }

  // ── Counter animation (dashboard) ────────────────────────────────────
  const counters = document.querySelectorAll('.counter');
  counters.forEach(el => {
    const target = parseInt(el.dataset.target, 10) || 0;
    if (target === 0) { el.textContent = '0'; return; }
    const duration = 900;
    const step     = Math.ceil(target / (duration / 16));
    let current    = 0;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = current.toLocaleString('pt-BR');
    }, 16);
  });

  // ── Auto-dismiss alerts ───────────────────────────────────────────────
  document.querySelectorAll('.alert-float').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert?.close();
    }, 5000);
  });

  // ── Tooltip Bootstrap ─────────────────────────────────────────────────
  const tooltips = document.querySelectorAll('[title]');
  tooltips.forEach(el => {
    new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' });
  });

  // ── Ripple effect nos botões ──────────────────────────────────────────
  document.querySelectorAll('.btn-primary-jp, .btn-outline-jp').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const ripple = document.createElement('span');
      ripple.style.cssText = `
        position:absolute;width:6px;height:6px;border-radius:50%;
        background:rgba(255,255,255,.5);
        left:${x}px;top:${y}px;
        transform:scale(0);
        animation:ripple .5s linear;
        pointer-events:none;
      `;
      btn.style.position = 'relative';
      btn.style.overflow = 'hidden';
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // ── Injetar keyframes de ripple dinamicamente ─────────────────────────
  if (!document.getElementById('rippleStyle')) {
    const style = document.createElement('style');
    style.id = 'rippleStyle';
    style.textContent = `@keyframes ripple{to{transform:scale(40);opacity:0}}`;
    document.head.appendChild(style);
  }

});
