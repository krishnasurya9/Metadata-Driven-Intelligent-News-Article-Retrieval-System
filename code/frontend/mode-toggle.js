/**
 * Mode Toggle System
 * Switches the entire UI between:
 *   - IR Mode:     "Metadata-Driven Intelligent News Article Retrieval System"
 *   - Mining Mode: "Automated Data Mining & Pattern Discovery System"
 *
 * BOTH modes use the SAME clean white/monochrome enterprise theme.
 * The only visual differences are the title/branding and which views are shown.
 *
 * This script must load BEFORE app.js and mining-lab.js.
 */

const MODES = {
  ir: {
    key: 'ir',
    title: 'NewsRetrieval',
    titleAccent: 'System',
    pageTitle: 'Metadata-Driven Intelligent News Article Retrieval System',
  },
  mining: {
    key: 'mining',
    title: 'DataMining',
    titleAccent: 'System',
    pageTitle: 'Automated Data Mining and Pattern Discovery System for Unstructured News Corpora',
  }
};

let currentMode = localStorage.getItem('projectMode') || 'ir';

// ── Core: apply a mode ──────────────────────────────────────────────────────
function applyMode(modeKey) {
  const mode = MODES[modeKey];
  currentMode = modeKey;
  localStorage.setItem('projectMode', modeKey);

  // 1. Page title & logo
  document.title = mode.pageTitle;
  const logoText = document.querySelector('.logo-text');
  const logoAccent = document.querySelector('.logo-accent');
  if (logoText) logoText.textContent = mode.title;
  if (logoAccent) logoAccent.textContent = mode.titleAccent;

  // 2. Show / hide the correct project view
  const irViews = ['main-view', 'analytics-view'];
  const miningViews = ['mining-view'];

  if (modeKey === 'ir') {
    // Show IR default (search tab), hide Mining
    irViews.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.remove('hidden');
    });
    miningViews.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add('hidden');
    });

    // Default to search tab inside IR
    const mainView = document.getElementById('main-view');
    const analyticsView = document.getElementById('analytics-view');
    if (mainView) mainView.classList.remove('hidden');
    if (analyticsView) analyticsView.classList.add('hidden');

  } else {
    // Show Mining, hide IR completely
    irViews.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add('hidden');
    });
    miningViews.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.remove('hidden');
    });

    // Auto-load warehouse stats on first switch
    if (window.MiningLab && typeof window.MiningLab.loadWarehouseStats === 'function') {
      setTimeout(() => window.MiningLab.loadWarehouseStats(), 150);
    }
  }

  // 3. Show/hide the right IR nav tabs
  document.querySelectorAll('.nav-btn').forEach(btn => {
    const tabMode = btn.dataset.mode;
    if (modeKey === 'ir') {
      btn.style.display = (tabMode === 'mining') ? 'none' : '';
    } else {
      // Mining mode: hide all IR tabs (sidebar handles navigation)
      btn.style.display = 'none';
    }
  });

  // 4. Update the toggle pill active state
  const irBtn = document.getElementById('toggle-ir-btn');
  const miningBtn = document.getElementById('toggle-mining-btn');
  if (irBtn) irBtn.classList.toggle('toggle-active', modeKey === 'ir');
  if (miningBtn) miningBtn.classList.toggle('toggle-active', modeKey === 'mining');
}

// ── Expose globally so onclick attributes work ──────────────────────────────
window.applyMode = applyMode;

// ── DOM Ready ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // --- Inject the toggle pill into the header ---
  const headerContent = document.querySelector('.header-content');
  if (headerContent) {
    const toggleWrapper = document.createElement('div');
    toggleWrapper.className = 'mode-toggle-wrapper';
    toggleWrapper.innerHTML = `
            <div class="mode-toggle" title="Switch Project">
                <button id="toggle-ir-btn" class="toggle-btn" onclick="applyMode('ir')">
                    🔍 IR System
                </button>
                <button id="toggle-mining-btn" class="toggle-btn" onclick="applyMode('mining')">
                    ⛏️ Mining System
                </button>
            </div>
        `;
    headerContent.appendChild(toggleWrapper);
  }

  // --- Apply the stored / default mode ---
  applyMode(currentMode);

  // --- Override app.js's nav-btn click handlers ---
  setTimeout(() => {
    document.querySelectorAll('.nav-btn').forEach(btn => {
      const clone = btn.cloneNode(true);
      btn.parentNode.replaceChild(clone, btn);

      clone.addEventListener('click', () => {
        const tabMode = clone.dataset.mode;
        const mainView = document.getElementById('main-view');
        const analyticsView = document.getElementById('analytics-view');
        const miningView = document.getElementById('mining-view');

        if (tabMode === 'analytics') {
          if (mainView) mainView.classList.add('hidden');
          if (miningView) miningView.classList.add('hidden');
          if (analyticsView) analyticsView.classList.remove('hidden');
        } else {
          if (analyticsView) analyticsView.classList.add('hidden');
          if (miningView) miningView.classList.add('hidden');
          if (mainView) mainView.classList.remove('hidden');
        }
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        clone.classList.add('active');
      });
    });
  }, 50);
});
