// State Management
const state = {
  currentView: 'landing',
  currentUser: {
    id: 'usr_aarav',
    name: 'Aarav Sharma (Y22 CSE)'
  },
  reports: [],
  myReports: [],
  matches: [],
  stats: null,
  aiStatus: null,
  filters: {
    type: 'all',
    category: 'all',
    location: 'all',
    search: '',
    sort: 'newest'
  },
  activeModalReport: null,
  activeMatchRecord: null,
  // Voice Recording state
  mediaRecorder: null,
  audioChunks: [],
  recordingInterval: null,
  recordingSeconds: 0,
  recordedBlob: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupEventListeners();
  await loadAIStatus();
  await loadStats();
  await loadReports();
  lucide.createIcons();
});

// Navigation Handling
function setupNavigation() {
  document.querySelectorAll('[data-nav]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = btn.getAttribute('data-nav');
      switchView(targetView);
    });
  });
}

function switchView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.add('hidden');
  });

  const activeSection = document.getElementById(`view-${viewName}`);
  if (activeSection) {
    activeSection.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Highlight active nav item
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-nav') === viewName) {
      link.classList.add('text-orange-600', 'font-semibold');
      link.classList.remove('text-slate-600');
    } else {
      link.classList.remove('text-orange-600', 'font-semibold');
      link.classList.add('text-slate-600');
    }
  });

  // Trigger view specific loads
  if (viewName === 'browse') {
    loadReports();
  } else if (viewName === 'my-reports') {
    loadMyReports();
  } else if (viewName === 'matches') {
    loadMatches();
  } else if (viewName === 'landing') {
    loadStats();
    loadRecentLandingReports();
  }

  lucide.createIcons();
}

// Event Listeners Setup
function setupEventListeners() {
  // User switcher
  const userSelect = document.getElementById('user-selector');
  if (userSelect) {
    userSelect.addEventListener('change', (e) => {
      state.currentUser.id = e.target.value;
      state.currentUser.name = e.target.options[e.target.selectedIndex].text;
      showToast(`Switched active profile to ${state.currentUser.name}`, 'info');
      if (state.currentView === 'my-reports') {
        loadMyReports();
      }
    });
  }

  // Search input debounced
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let timeout;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        state.filters.search = e.target.value;
        loadReports();
      }, 300);
    });
  }

  // Filter dropdowns
  const typeFilter = document.getElementById('filter-type');
  if (typeFilter) {
    typeFilter.addEventListener('change', (e) => {
      state.filters.type = e.target.value;
      loadReports();
    });
  }

  const catFilter = document.getElementById('filter-category');
  if (catFilter) {
    catFilter.addEventListener('change', (e) => {
      state.filters.category = e.target.value;
      loadReports();
    });
  }

  const locFilter = document.getElementById('filter-location');
  if (locFilter) {
    locFilter.addEventListener('change', (e) => {
      state.filters.location = e.target.value;
      loadReports();
    });
  }

  // Report Form submission
  const reportForm = document.getElementById('report-form');
  if (reportForm) {
    reportForm.addEventListener('submit', handleReportSubmit);
  }

  // AI Extract button
  const aiExtractBtn = document.getElementById('btn-ai-extract');
  if (aiExtractBtn) {
    aiExtractBtn.addEventListener('click', handleAIExtract);
  }

  // Voice recording buttons
  const startRecBtn = document.getElementById('btn-start-record');
  if (startRecBtn) {
    startRecBtn.addEventListener('click', startVoiceRecording);
  }

  const stopRecBtn = document.getElementById('btn-stop-record');
  if (stopRecBtn) {
    stopRecBtn.addEventListener('click', stopVoiceRecording);
  }

  const resetRecBtn = document.getElementById('btn-reset-record');
  if (resetRecBtn) {
    resetRecBtn.addEventListener('click', resetVoiceRecording);
  }

  // Photo upload input preview
  const photoInput = document.getElementById('item-photo-input');
  if (photoInput) {
    photoInput.addEventListener('change', handlePhotoSelected);
  }

  // Hero Quick Search
  const heroSearchInput = document.getElementById('hero-search-input');
  const heroSearchBtn = document.getElementById('hero-search-btn');
  if (heroSearchBtn && heroSearchInput) {
    heroSearchBtn.addEventListener('click', () => {
      const q = heroSearchInput.value.trim();
      state.filters.search = q;
      if (document.getElementById('search-input')) {
        document.getElementById('search-input').value = q;
      }
      switchView('browse');
    });
  }
}

// API Calls: Load AI Status
async function loadAIStatus() {
  try {
    const res = await fetch('/api/ai/status');
    const data = await res.json();
    state.aiStatus = data;
    renderAIBadge(data);
  } catch (err) {
    console.error('Failed to load AI status', err);
  }
}

function renderAIBadge(status) {
  const badgeContainer = document.getElementById('ai-status-badge');
  if (!badgeContainer) return;

  if (status.sarvam_api_key_configured) {
    badgeContainer.innerHTML = `
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        Sarvam 105B Live
      </span>
    `;
  } else {
    badgeContainer.innerHTML = `
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200" title="Add SARVAM_API_KEY to .env for cloud AI">
        <span class="w-2 h-2 rounded-full bg-amber-500"></span>
        Offline Heuristic Mode (Ready for API Key)
      </span>
    `;
  }
}

// API Calls: Load Stats
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    state.stats = data;

    const elTotal = document.getElementById('stat-total');
    const elLost = document.getElementById('stat-lost');
    const elFound = document.getElementById('stat-found');
    const elMatches = document.getElementById('stat-matches');
    const elReturned = document.getElementById('stat-returned');

    if (elTotal) elTotal.innerText = data.total_reports;
    if (elLost) elLost.innerText = data.lost_count;
    if (elFound) elFound.innerText = data.found_count;
    if (elMatches) elMatches.innerText = data.matched_count;
    if (elReturned) elReturned.innerText = data.returned_count;
  } catch (err) {
    console.error('Failed to load stats', err);
  }
}

// API Calls: Load Reports
async function loadReports() {
  const listEl = document.getElementById('reports-grid');
  const emptyEl = document.getElementById('reports-empty');
  if (!listEl) return;

  listEl.innerHTML = `<div class="col-span-full py-16 text-center text-slate-500 flex flex-col items-center">
    <i data-lucide="loader-2" class="w-8 h-8 animate-spin text-orange-600 mb-2"></i>
    <p>Searching campus reports...</p>
  </div>`;
  lucide.createIcons();

  try {
    const params = new URLSearchParams();
    if (state.filters.type !== 'all') params.append('report_type', state.filters.type);
    if (state.filters.category !== 'all') params.append('category', state.filters.category);
    if (state.filters.location !== 'all') params.append('location', state.filters.location);
    if (state.filters.search) params.append('search', state.filters.search);
    params.append('sort', state.filters.sort);

    const res = await fetch(`/api/reports?${params.toString()}`);
    const reports = await res.json();
    state.reports = reports;

    if (reports.length === 0) {
      listEl.innerHTML = '';
      if (emptyEl) emptyEl.classList.remove('hidden');
    } else {
      if (emptyEl) emptyEl.classList.add('hidden');
      listEl.innerHTML = reports.map(r => createReportCardHTML(r)).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load reports', err);
    listEl.innerHTML = `<div class="col-span-full py-8 text-center text-red-500">Failed to load reports. Please retry.</div>`;
  }
}

// Load Recent Reports for Landing Page
async function loadRecentLandingReports() {
  const container = document.getElementById('landing-recent-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/reports?sort=newest');
    const reports = await res.json();
    const recent = reports.slice(0, 4);

    if (recent.length === 0) {
      container.innerHTML = `<div class="col-span-full text-center py-8 text-slate-400">No reports submitted yet.</div>`;
    } else {
      container.innerHTML = recent.map(r => createReportCardHTML(r)).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load recent reports', err);
  }
}

// Load My Reports
async function loadMyReports() {
  const listEl = document.getElementById('my-reports-list');
  const emptyEl = document.getElementById('my-reports-empty');
  if (!listEl) return;

  listEl.innerHTML = `<div class="py-12 text-center text-slate-500"><i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-orange-600 mb-2"></i>Loading your reports...</div>`;
  lucide.createIcons();

  try {
    const res = await fetch(`/api/reports/my-reports?user_id=${state.currentUser.id}`);
    const reports = await res.json();
    state.myReports = reports;

    if (reports.length === 0) {
      listEl.innerHTML = '';
      if (emptyEl) emptyEl.classList.remove('hidden');
    } else {
      if (emptyEl) emptyEl.classList.add('hidden');
      listEl.innerHTML = reports.map(r => createMyReportRowHTML(r)).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load user reports', err);
  }
}

// Load Matches
async function loadMatches() {
  const listEl = document.getElementById('matches-grid');
  const emptyEl = document.getElementById('matches-empty');
  if (!listEl) return;

  listEl.innerHTML = `<div class="col-span-full py-16 text-center text-slate-500"><i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-orange-600 mb-2"></i>Analyzing item matches...</div>`;
  lucide.createIcons();

  try {
    const res = await fetch('/api/matches');
    const matches = await res.json();
    state.matches = matches;

    if (matches.length === 0) {
      listEl.innerHTML = '';
      if (emptyEl) emptyEl.classList.remove('hidden');
    } else {
      if (emptyEl) emptyEl.classList.add('hidden');
      listEl.innerHTML = matches.map(m => createMatchCardHTML(m)).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load matches', err);
  }
}

// Card HTML Generators
function createReportCardHTML(report) {
  const isLost = report.report_type === 'lost';
  const typeBadge = isLost
    ? `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200"><i data-lucide="help-circle" class="w-3 h-3"></i> LOST</span>`
    : `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"><i data-lucide="check-circle-2" class="w-3 h-3"></i> FOUND</span>`;

  let statusBadge = '';
  if (report.status === 'returned') {
    statusBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">RETURNED</span>`;
  } else if (report.status === 'matched') {
    statusBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">MATCH CANDIDATE</span>`;
  }

  const demoBadge = report.is_demo
    ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-100 text-amber-800" title="Sample demonstration data">DEMO ITEM</span>`
    : '';

  const photoThumb = report.photo_url
    ? `<div class="w-full h-40 bg-slate-100 rounded-xl overflow-hidden mb-3"><img src="${report.photo_url}" class="w-full h-full object-cover" alt="Item photo"></div>`
    : '';

  const matchPill = report.potential_matches_count > 0
    ? `<span class="inline-flex items-center gap-1 text-xs font-semibold text-orange-600 bg-orange-50 px-2 py-1 rounded-lg border border-orange-200 cursor-pointer hover:bg-orange-100 transition" onclick="openMatchesForReport('${report.id}')">
        <i data-lucide="sparkles" class="w-3 h-3"></i> ${report.potential_matches_count} ${report.potential_matches_count === 1 ? 'Match' : 'Matches'}
      </span>`
    : '';

  return `
    <div class="bg-white rounded-2xl p-5 border border-slate-200/80 card-shadow card-hover transition duration-200 flex flex-col justify-between">
      <div>
        ${photoThumb}
        <div class="flex items-center justify-between gap-2 mb-2.5">
          <div class="flex items-center gap-1.5 flex-wrap">
            ${typeBadge}
            ${statusBadge}
            ${demoBadge}
          </div>
          <span class="text-xs text-slate-400 capitalize">${report.category.replace('_', ' ')}</span>
        </div>

        <h3 class="text-base font-bold text-slate-900 mb-1.5 hover:text-orange-600 transition cursor-pointer line-clamp-1" onclick="openReportDetailModal('${report.id}')">
          ${escapeHtml(report.item_name)}
        </h3>

        <p class="text-xs text-slate-600 line-clamp-2 mb-3 leading-relaxed">
          ${escapeHtml(report.original_description)}
        </p>

        <div class="space-y-1.5 text-xs text-slate-500 mb-4 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          <div class="flex items-center gap-1.5">
            <i data-lucide="map-pin" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
            <span class="truncate font-medium text-slate-700">${escapeHtml(report.location)}</span>
          </div>
          ${report.occurrence_time ? `
          <div class="flex items-center gap-1.5">
            <i data-lucide="clock" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
            <span class="truncate">${escapeHtml(report.occurrence_time)}</span>
          </div>` : ''}
          ${report.color ? `
          <div class="flex items-center gap-1.5">
            <i data-lucide="palette" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
            <span>Color: <strong>${escapeHtml(report.color)}</strong></span>
          </div>` : ''}
        </div>
      </div>

      <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
        ${matchPill || `<span class="text-[11px] text-slate-400">${formatDate(report.created_at)}</span>`}
        <button onclick="openReportDetailModal('${report.id}')" class="text-xs font-semibold text-orange-600 hover:text-orange-700 flex items-center gap-1 ml-auto">
          View Details <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    </div>
  `;
}

function createMyReportRowHTML(report) {
  const isLost = report.report_type === 'lost';
  const typeBadge = isLost
    ? `<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">LOST</span>`
    : `<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">FOUND</span>`;

  return `
    <div class="bg-white rounded-2xl p-5 border border-slate-200/80 card-shadow flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="space-y-1.5 max-w-xl">
        <div class="flex items-center gap-2 flex-wrap">
          ${typeBadge}
          <span class="text-xs font-medium px-2 py-0.5 rounded-full ${report.status === 'returned' ? 'bg-slate-100 text-slate-600' : 'bg-blue-50 text-blue-700'}">
            Status: ${report.status.toUpperCase()}
          </span>
          <span class="text-xs text-slate-400">${formatDate(report.created_at)}</span>
        </div>
        <h4 class="text-base font-bold text-slate-900">${escapeHtml(report.item_name)}</h4>
        <p class="text-xs text-slate-600 line-clamp-2">${escapeHtml(report.original_description)}</p>
        <div class="text-xs text-slate-500 flex items-center gap-3">
          <span><i data-lucide="map-pin" class="w-3 h-3 inline mr-1 text-slate-400"></i>${escapeHtml(report.location)}</span>
          <span><i data-lucide="tag" class="w-3 h-3 inline mr-1 text-slate-400"></i>${report.category}</span>
        </div>
      </div>

      <div class="flex items-center gap-2 flex-wrap shrink-0">
        ${report.potential_matches_count > 0 ? `
          <button onclick="openMatchesForReport('${report.id}')" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition flex items-center gap-1.5">
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i> ${report.potential_matches_count} Matches
          </button>
        ` : ''}

        ${report.status !== 'returned' ? `
          <button onclick="markReportReturned('${report.id}')" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition flex items-center gap-1.5">
            <i data-lucide="check" class="w-3.5 h-3.5"></i> Mark Returned
          </button>
        ` : `
          <button onclick="reopenReport('${report.id}')" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">
            Reopen
          </button>
        `}

        <button onclick="deleteReport('${report.id}')" class="p-2 rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 transition" title="Delete report">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
        </button>
      </div>
    </div>
  `;
}

function createMatchCardHTML(m) {
  const score = Math.round(m.match_score);
  let scoreColor = 'bg-amber-500';
  let badgeColor = 'text-amber-700 bg-amber-50 border-amber-200';
  if (score >= 80) {
    scoreColor = 'bg-emerald-500';
    badgeColor = 'text-emerald-700 bg-emerald-50 border-emerald-200';
  } else if (score < 50) {
    scoreColor = 'bg-slate-400';
    badgeColor = 'text-slate-700 bg-slate-50 border-slate-200';
  }

  const reasonsList = m.matching_reasons.slice(0, 3).map(r => `
    <li class="flex items-start gap-1.5 text-xs text-slate-600">
      <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5"></i>
      <span>${escapeHtml(r)}</span>
    </li>
  `).join('');

  return `
    <div class="bg-white rounded-2xl p-5 border border-slate-200/80 card-shadow card-hover transition duration-200 flex flex-col justify-between">
      <div>
        <!-- Match Score Bar -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-1 rounded-full text-xs font-bold border ${badgeColor}">
              ${score}% Match
            </span>
            <span class="text-[11px] text-slate-400 font-medium">${m.review_status.toUpperCase()}</span>
          </div>
          <div class="w-24 bg-slate-100 h-2 rounded-full overflow-hidden">
            <div class="${scoreColor} h-full rounded-full" style="width: ${score}%"></div>
          </div>
        </div>

        <!-- Side-by-side snippet -->
        <div class="grid grid-cols-2 gap-3 mb-4 bg-slate-50 p-3 rounded-xl border border-slate-100">
          <div>
            <span class="text-[10px] font-bold uppercase tracking-wider text-rose-600">Lost Item</span>
            <h4 class="text-xs font-bold text-slate-800 line-clamp-1">${escapeHtml(m.lost_item_name)}</h4>
            <p class="text-[11px] text-slate-500 mt-0.5 truncate"><i data-lucide="map-pin" class="w-3 h-3 inline mr-0.5"></i>${escapeHtml(m.lost_location)}</p>
          </div>
          <div class="border-l border-slate-200 pl-3">
            <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-600">Found Item</span>
            <h4 class="text-xs font-bold text-slate-800 line-clamp-1">${escapeHtml(m.found_item_name)}</h4>
            <p class="text-[11px] text-slate-500 mt-0.5 truncate"><i data-lucide="map-pin" class="w-3 h-3 inline mr-0.5"></i>${escapeHtml(m.found_location)}</p>
          </div>
        </div>

        <!-- Matching Reasons -->
        <div class="mb-4">
          <span class="text-[11px] font-semibold text-slate-700 block mb-1.5">Why these match:</span>
          <ul class="space-y-1">
            ${reasonsList}
          </ul>
        </div>
      </div>

      <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
        <button onclick="openMatchDetailModal('${m.id}')" class="w-full py-2 px-3 rounded-xl text-xs font-semibold bg-orange-600 text-white hover:bg-orange-700 transition flex items-center justify-center gap-1.5 shadow-sm">
          Compare & Verify Details <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    </div>
  `;
}

// Modal: Report Detail View
async function openReportDetailModal(reportId) {
  const modal = document.getElementById('report-detail-modal');
  const content = document.getElementById('report-detail-content');
  if (!modal || !content) return;

  content.innerHTML = `<div class="p-8 text-center text-slate-500"><i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-orange-600 mb-2"></i>Loading details...</div>`;
  modal.classList.remove('hidden');
  lucide.createIcons();

  try {
    const res = await fetch(`/api/reports/${reportId}`);
    const r = await res.json();
    state.activeModalReport = r;

    const isLost = r.report_type === 'lost';
    const typeBadge = isLost
      ? `<span class="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">LOST ITEM</span>`
      : `<span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">FOUND ITEM</span>`;

    const candidateMatches = r.candidate_matches || [];
    const matchesSection = candidateMatches.length > 0 ? `
      <div class="mt-6 pt-6 border-t border-slate-200">
        <h4 class="text-sm font-bold text-slate-900 mb-3 flex items-center gap-1.5">
          <i data-lucide="sparkles" class="w-4 h-4 text-orange-600"></i>
          Potential Matches Found (${candidateMatches.length})
        </h4>
        <div class="space-y-2">
          ${candidateMatches.map(c => `
            <div class="bg-amber-50/50 p-3 rounded-xl border border-amber-200/60 flex items-center justify-between">
              <div>
                <span class="text-xs font-bold text-slate-800">${escapeHtml(c.matched_report.item_name)}</span>
                <p class="text-[11px] text-slate-600 mt-0.5">${escapeHtml(c.matching_reasons[0] || 'Similar category and location')}</p>
              </div>
              <div class="text-right">
                <span class="text-xs font-extrabold text-orange-600">${Math.round(c.match_score)}% match</span>
                <button onclick="openCandidateMatchModal('${c.lost_report_id}', '${c.found_report_id}')" class="block text-[11px] font-semibold text-slate-700 underline mt-0.5">
                  Compare
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    ` : '';

    content.innerHTML = `
      <div class="p-6">
        <div class="flex items-center justify-between gap-2 mb-4">
          <div class="flex items-center gap-2">
            ${typeBadge}
            <span class="text-xs text-slate-400 capitalize bg-slate-100 px-2 py-1 rounded-md">${r.category.replace('_', ' ')}</span>
            ${r.is_demo ? `<span class="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">DEMO REPORT</span>` : ''}
          </div>
          <button onclick="closeReportDetailModal()" class="text-slate-400 hover:text-slate-600 p-1">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>

        <h3 class="text-xl font-extrabold text-slate-900 mb-2">${escapeHtml(r.item_name)}</h3>
        <p class="text-xs text-slate-400 mb-4">Reported by ${escapeHtml(r.user_name || 'Student')} on ${formatDate(r.created_at)}</p>

        ${r.photo_url ? `
          <div class="w-full h-56 bg-slate-100 rounded-2xl overflow-hidden mb-4">
            <img src="${r.photo_url}" class="w-full h-full object-cover" alt="Item photo">
          </div>
        ` : ''}

        <!-- Description Box -->
        <div class="bg-amber-50/30 p-4 rounded-xl border border-amber-100 mb-4">
          <span class="text-[11px] font-bold text-amber-900 uppercase tracking-wider block mb-1">Original Description (${r.preferred_language})</span>
          <p class="text-sm text-slate-700 leading-relaxed">${escapeHtml(r.original_description)}</p>
        </div>

        ${r.normalized_description ? `
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 mb-4">
          <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider block mb-1">AI Normalized Description</span>
          <p class="text-xs text-slate-600">${escapeHtml(r.normalized_description)}</p>
        </div>` : ''}

        <!-- Details Grid -->
        <div class="grid grid-cols-2 gap-3 text-xs">
          <div class="bg-slate-50 p-3 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Location</span>
            <span class="font-bold text-slate-800">${escapeHtml(r.location)}</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Occurrence Time</span>
            <span class="font-bold text-slate-800">${escapeHtml(r.occurrence_time || 'Not specified')}</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Color</span>
            <span class="font-bold text-slate-800">${escapeHtml(r.color || 'Not specified')}</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Brand / Model</span>
            <span class="font-bold text-slate-800">${escapeHtml(r.brand || 'Not specified')}</span>
          </div>
        </div>

        ${r.distinguishing_features ? `
        <div class="mt-3 bg-slate-50 p-3 rounded-xl text-xs">
          <span class="text-slate-400 block mb-0.5">Distinguishing Features</span>
          <span class="font-medium text-slate-800">${escapeHtml(r.distinguishing_features)}</span>
        </div>` : ''}

        ${matchesSection}

        <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
          <span class="text-[11px] text-slate-400">Campus: IIT Kanpur</span>
          <button onclick="closeReportDetailModal()" class="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200">
            Close
          </button>
        </div>
      </div>
    `;
    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load report detail', err);
    content.innerHTML = `<div class="p-6 text-center text-red-500">Failed to load report.</div>`;
  }
}

function closeReportDetailModal() {
  const modal = document.getElementById('report-detail-modal');
  if (modal) modal.classList.add('hidden');
}

// Modal: Match Comparison & Verification Details
async function openMatchDetailModal(matchId) {
  const modal = document.getElementById('match-detail-modal');
  const content = document.getElementById('match-detail-content');
  if (!modal || !content) return;

  content.innerHTML = `<div class="p-8 text-center text-slate-500"><i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-orange-600 mb-2"></i>Comparing item attributes...</div>`;
  modal.classList.remove('hidden');
  lucide.createIcons();

  try {
    const res = await fetch(`/api/matches/${matchId}`);
    const m = await res.json();
    state.activeMatchRecord = m;

    const lost = m.lost_report;
    const found = m.found_report;
    const score = Math.round(m.match_score);

    content.innerHTML = `
      <div class="p-6">
        <div class="flex items-center justify-between gap-2 mb-4">
          <div class="flex items-center gap-2">
            <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-orange-100 text-orange-800 border border-orange-200">
              ${score}% Match Confidence
            </span>
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Status: ${m.review_status}
            </span>
          </div>
          <button onclick="closeMatchDetailModal()" class="text-slate-400 hover:text-slate-600 p-1">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>

        <h3 class="text-lg font-bold text-slate-900 mb-1">Item Comparison & Matching Analysis</h3>
        <p class="text-xs text-slate-500 mb-5">Calculated by KHOJ Explainable Matching Algorithm (Category 30%, Features 25%, Color/Brand 15%, Location 15%, Time 15%)</p>

        <!-- Side-by-side comparison -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <!-- Lost item column -->
          <div class="bg-rose-50/40 p-4 rounded-2xl border border-rose-100">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">LOST ITEM</span>
              <span class="text-xs text-slate-400">${lost.category}</span>
            </div>
            <h4 class="text-base font-bold text-slate-900 mb-1">${escapeHtml(lost.item_name)}</h4>
            <p class="text-xs text-slate-600 mb-3 bg-white/80 p-2.5 rounded-xl border border-rose-50">
              "${escapeHtml(lost.original_description)}"
            </p>
            <div class="space-y-1.5 text-xs">
              <div class="flex justify-between py-1 border-b border-rose-100/60"><span class="text-slate-400">Location:</span> <span class="font-semibold text-slate-800">${escapeHtml(lost.location)}</span></div>
              <div class="flex justify-between py-1 border-b border-rose-100/60"><span class="text-slate-400">Colour:</span> <span class="font-semibold text-slate-800">${escapeHtml(lost.color || 'Unspecified')}</span></div>
              <div class="flex justify-between py-1 border-b border-rose-100/60"><span class="text-slate-400">Brand:</span> <span class="font-semibold text-slate-800">${escapeHtml(lost.brand || 'Unspecified')}</span></div>
              <div class="flex justify-between py-1"><span class="text-slate-400">Features:</span> <span class="font-semibold text-slate-800">${escapeHtml(lost.distinguishing_features || 'Unspecified')}</span></div>
            </div>
          </div>

          <!-- Found item column -->
          <div class="bg-emerald-50/40 p-4 rounded-2xl border border-emerald-100">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">FOUND ITEM</span>
              <span class="text-xs text-slate-400">${found.category}</span>
            </div>
            <h4 class="text-base font-bold text-slate-900 mb-1">${escapeHtml(found.item_name)}</h4>
            <p class="text-xs text-slate-600 mb-3 bg-white/80 p-2.5 rounded-xl border border-emerald-50">
              "${escapeHtml(found.original_description)}"
            </p>
            <div class="space-y-1.5 text-xs">
              <div class="flex justify-between py-1 border-b border-emerald-100/60"><span class="text-slate-400">Location:</span> <span class="font-semibold text-slate-800">${escapeHtml(found.location)}</span></div>
              <div class="flex justify-between py-1 border-b border-emerald-100/60"><span class="text-slate-400">Colour:</span> <span class="font-semibold text-slate-800">${escapeHtml(found.color || 'Unspecified')}</span></div>
              <div class="flex justify-between py-1 border-b border-emerald-100/60"><span class="text-slate-400">Brand:</span> <span class="font-semibold text-slate-800">${escapeHtml(found.brand || 'Unspecified')}</span></div>
              <div class="flex justify-between py-1"><span class="text-slate-400">Features:</span> <span class="font-semibold text-slate-800">${escapeHtml(found.distinguishing_features || 'Unspecified')}</span></div>
            </div>
          </div>
        </div>

        <!-- Explainable reasons breakdown -->
        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 mb-6">
          <h4 class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <i data-lucide="check-check" class="w-4 h-4 text-emerald-600"></i>
            Matching Breakdown Reasons
          </h4>
          <ul class="space-y-1.5">
            ${m.matching_reasons.map(r => `
              <li class="flex items-center gap-2 text-xs text-slate-700">
                <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600 shrink-0"></i>
                <span>${escapeHtml(r)}</span>
              </li>
            `).join('')}
          </ul>
        </div>

        <!-- Verification Claim Workflow -->
        <div class="bg-amber-50/40 p-4 rounded-2xl border border-amber-200">
          <h4 class="text-xs font-bold text-amber-900 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <i data-lucide="shield-check" class="w-4 h-4 text-orange-600"></i>
            Safe Verification Claim Workflow
          </h4>
          <p class="text-xs text-slate-600 mb-3">
            To prevent false claims and protect privacy, please provide a specific verification detail (such as a sticker description, internal pocket content, or lock screen wallpaper) that only the genuine owner knows.
          </p>

          <textarea id="claim-verification-notes" rows="2" placeholder="e.g. My bottle has a small scratch under the cap and my room number written in black marker..." class="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500 mb-3"></textarea>

          <button onclick="submitMatchInterest('${m.id}')" class="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-orange-600 text-white hover:bg-orange-700 transition flex items-center justify-center gap-2 shadow-sm">
            <i data-lucide="send" class="w-3.5 h-3.5"></i>
            Express Interest & Request Verification
          </button>
        </div>
      </div>
    `;
    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load match detail', err);
    content.innerHTML = `<div class="p-6 text-center text-red-500">Failed to load match comparison.</div>`;
  }
}

function closeMatchDetailModal() {
  const modal = document.getElementById('match-detail-modal');
  if (modal) modal.classList.add('hidden');
}

async function openCandidateMatchModal(lostId, foundId) {
  closeReportDetailModal();
  // Find match record
  const matchId = `match_${lostId}_${foundId}`;
  await openMatchDetailModal(matchId);
}

function openMatchesForReport(reportId) {
  switchView('matches');
}

// Action: Submit Match Interest
async function submitMatchInterest(matchId) {
  const notesEl = document.getElementById('claim-verification-notes');
  const notes = notesEl ? notesEl.value.trim() : '';

  if (!notes || notes.length < 5) {
    showToast('Please provide a specific detail to verify ownership.', 'warning');
    return;
  }

  try {
    const res = await fetch(`/api/matches/${matchId}/interest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ claimant_notes: notes })
    });
    const data = await res.json();
    if (res.ok) {
      showToast('Interest recorded! The finder has been notified.', 'success');
      closeMatchDetailModal();
      loadMatches();
      loadReports();
    } else {
      showToast(data.detail || 'Could not record interest', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Failed to record interest', 'error');
  }
}

// Action: Mark Report Returned
async function markReportReturned(reportId) {
  try {
    const res = await fetch(`/api/reports/${reportId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'returned' })
    });
    if (res.ok) {
      showToast('Item marked as safely returned!', 'success');
      loadMyReports();
      loadStats();
    }
  } catch (err) {
    showToast('Failed to update status', 'error');
  }
}

async function reopenReport(reportId) {
  try {
    const res = await fetch(`/api/reports/${reportId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'open' })
    });
    if (res.ok) {
      showToast('Report reopened.', 'info');
      loadMyReports();
      loadStats();
    }
  } catch (err) {
    showToast('Failed to reopen report', 'error');
  }
}

async function deleteReport(reportId) {
  if (!confirm('Are you sure you want to delete this report?')) return;
  try {
    const res = await fetch(`/api/reports/${reportId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Report deleted.', 'info');
      loadMyReports();
      loadReports();
      loadStats();
    }
  } catch (err) {
    showToast('Failed to delete report', 'error');
  }
}

// Action: Sarvam AI Auto-Extract from Description
async function handleAIExtract() {
  const descEl = document.getElementById('report-desc');
  const langEl = document.getElementById('report-lang');
  const text = descEl ? descEl.value.trim() : '';
  const lang = langEl ? langEl.value : 'unknown';

  if (!text || text.length < 5) {
    showToast('Please enter a description first before extracting.', 'warning');
    return;
  }

  const btn = document.getElementById('btn-ai-extract');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin mr-1"></i> Extracting...`;
  lucide.createIcons();

  try {
    const res = await fetch('/api/ai/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, preferred_language: lang })
    });
    const data = await res.json();

    // Auto populate form fields if returned
    if (data.item_type && document.getElementById('report-name')) {
      document.getElementById('report-name').value = data.item_type;
    }
    if (data.category && document.getElementById('report-category')) {
      document.getElementById('report-category').value = data.category;
    }
    if (data.color && document.getElementById('report-color')) {
      document.getElementById('report-color').value = data.color;
    }
    if (data.brand && document.getElementById('report-brand')) {
      document.getElementById('report-brand').value = data.brand;
    }
    if (data.distinguishing_features && document.getElementById('report-features')) {
      document.getElementById('report-features').value = data.distinguishing_features;
    }
    if (data.location && document.getElementById('report-location')) {
      document.getElementById('report-location').value = data.location;
    }
    if (data.approximate_time && document.getElementById('report-time')) {
      document.getElementById('report-time').value = data.approximate_time;
    }

    const aiFeedbackEl = document.getElementById('ai-extraction-feedback');
    if (aiFeedbackEl) {
      aiFeedbackEl.classList.remove('hidden');
      aiFeedbackEl.innerHTML = `
        <div class="p-3 bg-orange-50 border border-orange-200 rounded-xl text-xs text-orange-950 flex items-start gap-2">
          <i data-lucide="sparkles" class="w-4 h-4 text-orange-600 shrink-0 mt-0.5"></i>
          <div>
            <span class="font-bold block">${data.is_ai_powered ? 'Extracted by Sarvam 105B AI' : 'Extracted by Rule-based Parser'}</span>
            <span class="text-slate-600">${data.normalized_description || 'Fields auto-filled from your description. Review and adjust if needed.'}</span>
          </div>
        </div>
      `;
      lucide.createIcons();
    }

    showToast('Attributes extracted and fields populated!', 'success');
  } catch (err) {
    console.error(err);
    showToast('Failed to analyze description', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
    lucide.createIcons();
  }
}

// Voice Recording Handling (Sarvam STT)
async function startVoiceRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast('Audio recording is not supported in this browser.', 'error');
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.mediaRecorder = new MediaRecorder(stream);
    state.audioChunks = [];

    state.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) state.audioChunks.push(e.data);
    };

    state.mediaRecorder.onstop = async () => {
      state.recordedBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
      const audioUrl = URL.createObjectURL(state.recordedBlob);
      const audioPreview = document.getElementById('voice-preview-player');
      if (audioPreview) {
        audioPreview.src = audioUrl;
        audioPreview.classList.remove('hidden');
      }
      // Send to Sarvam STT API
      await transcribeRecordedAudio(state.recordedBlob);
    };

    state.mediaRecorder.start();

    // Toggle UI buttons
    document.getElementById('btn-start-record').classList.add('hidden');
    document.getElementById('btn-stop-record').classList.remove('hidden');
    document.getElementById('recording-indicator').classList.remove('hidden');

    state.recordingSeconds = 0;
    state.recordingInterval = setInterval(() => {
      state.recordingSeconds++;
      const mins = String(Math.floor(state.recordingSeconds / 60)).padStart(2, '0');
      const secs = String(state.recordingSeconds % 60).padStart(2, '0');
      const timerEl = document.getElementById('recording-timer');
      if (timerEl) timerEl.innerText = `${mins}:${secs}`;
    }, 1000);

    showToast('Recording voice note... Describe your item in Hindi, English, or Hinglish', 'info');
  } catch (err) {
    console.error('Microphone error', err);
    showToast('Microphone access denied or unavailable. You can type your description below.', 'warning');
  }
}

function stopVoiceRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
    state.mediaRecorder.stop();
    state.mediaRecorder.stream.getTracks().forEach(track => track.stop());
  }
  clearInterval(state.recordingInterval);

  document.getElementById('btn-stop-record').classList.add('hidden');
  document.getElementById('btn-reset-record').classList.remove('hidden');
  document.getElementById('recording-indicator').classList.add('hidden');
}

function resetVoiceRecording() {
  state.recordedBlob = null;
  state.audioChunks = [];
  const audioPreview = document.getElementById('voice-preview-player');
  if (audioPreview) {
    audioPreview.src = '';
    audioPreview.classList.add('hidden');
  }
  document.getElementById('btn-reset-record').classList.add('hidden');
  document.getElementById('btn-start-record').classList.remove('hidden');
  document.getElementById('recording-timer').innerText = '00:00';
}

async function transcribeRecordedAudio(audioBlob) {
  const descEl = document.getElementById('report-desc');
  const transcribeStatus = document.getElementById('transcription-status');
  if (transcribeStatus) {
    transcribeStatus.classList.remove('hidden');
    transcribeStatus.innerHTML = `<span class="text-xs text-orange-600 flex items-center gap-1.5"><i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> Transcribing voice note via Sarvam Speech-to-Text...</span>`;
    lucide.createIcons();
  }

  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');

  try {
    const res = await fetch('/api/voice/transcribe', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (res.ok) {
      if (descEl) {
        descEl.value = data.transcript;
        showToast('Voice transcribed successfully! Click AI Extract to auto-fill fields.', 'success');
      }
      if (transcribeStatus) {
        transcribeStatus.innerHTML = `<span class="text-xs text-emerald-700 font-medium">✓ Transcribed (${data.detected_language})</span>`;
      }
      // Trigger AI extraction automatically on transcript
      handleAIExtract();
    } else {
      if (transcribeStatus) {
        transcribeStatus.innerHTML = `<span class="text-xs text-amber-700 font-medium">${data.detail}</span>`;
      }
      showToast(data.detail, 'warning');
    }
  } catch (err) {
    console.error('Transcription error', err);
    if (transcribeStatus) {
      transcribeStatus.innerHTML = `<span class="text-xs text-red-500">Speech-to-text service error. Please type description manually.</span>`;
    }
  }
}

// Action: Handle Photo Upload
async function handlePhotoSelected(e) {
  const file = e.target.files[0];
  if (!file) return;

  const preview = document.getElementById('photo-preview');
  const previewImg = document.getElementById('photo-preview-img');
  const uploadStatus = document.getElementById('photo-upload-status');

  if (uploadStatus) uploadStatus.innerText = 'Uploading photo...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (res.ok) {
      document.getElementById('report-photo-url').value = data.photo_url;
      if (preview && previewImg) {
        previewImg.src = data.photo_url;
        preview.classList.remove('hidden');
      }
      if (uploadStatus) uploadStatus.innerText = 'Photo uploaded safely';
      showToast('Photo uploaded successfully', 'success');
    } else {
      showToast(data.detail || 'Photo upload failed', 'error');
      if (uploadStatus) uploadStatus.innerText = '';
    }
  } catch (err) {
    showToast('Failed to upload photo', 'error');
    if (uploadStatus) uploadStatus.innerText = '';
  }
}

// Form Submission: Create Report
async function handleReportSubmit(e) {
  e.preventDefault();

  const type = document.querySelector('input[name="report_type"]:checked').value;
  const name = document.getElementById('report-name').value.trim();
  const desc = document.getElementById('report-desc').value.trim();
  const cat = document.getElementById('report-category').value;
  const loc = document.getElementById('report-location').value.trim();
  const color = document.getElementById('report-color').value.trim();
  const brand = document.getElementById('report-brand').value.trim();
  const features = document.getElementById('report-features').value.trim();
  const time = document.getElementById('report-time').value.trim();
  const lang = document.getElementById('report-lang').value;
  const photoUrl = document.getElementById('report-photo-url').value.trim();

  if (!name || !desc || !loc) {
    showToast('Please fill out the item name, description, and location.', 'warning');
    return;
  }

  const payload = {
    report_type: type,
    item_name: name,
    original_description: desc,
    category: cat,
    location: loc,
    color: color || null,
    brand: brand || null,
    distinguishing_features: features || null,
    occurrence_time: time || null,
    preferred_language: lang,
    photo_url: photoUrl || null,
    user_id: state.currentUser.id,
    is_demo: false
  };

  const submitBtn = document.getElementById('btn-submit-report');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin mr-1.5"></i> Publishing Report...`;

  try {
    const res = await fetch('/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const created = await res.json();

    if (res.ok) {
      showToast('Report published! Khoj matching engine is scanning for matches.', 'success');
      document.getElementById('report-form').reset();
      resetVoiceRecording();
      document.getElementById('photo-preview').classList.add('hidden');
      document.getElementById('ai-extraction-feedback').classList.add('hidden');
      await loadStats();
      switchView('browse');
    } else {
      showToast(created.detail || 'Failed to submit report', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Failed to create report', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `Submit Report`;
    lucide.createIcons();
  }
}

// Demo Data Control Actions
async function handleSeedDemoData() {
  try {
    const res = await fetch('/api/demo/seed', { method: 'POST' });
    if (res.ok) {
      showToast('Sample IIT Kanpur demo reports loaded!', 'success');
      await loadStats();
      await loadReports();
    }
  } catch (err) {
    showToast('Failed to load demo data', 'error');
  }
}

async function handleResetDemoData() {
  try {
    const res = await fetch('/api/demo/reset', { method: 'POST' });
    if (res.ok) {
      showToast('Demo data reset to clean state.', 'info');
      await loadStats();
      await loadReports();
    }
  } catch (err) {
    showToast('Failed to reset demo data', 'error');
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const bgColors = {
    info: 'bg-slate-900 text-white',
    success: 'bg-emerald-600 text-white',
    warning: 'bg-amber-600 text-white',
    error: 'bg-rose-600 text-white'
  };

  toast.className = `${bgColors[type] || bgColors.info} px-4 py-3 rounded-2xl shadow-xl text-xs font-semibold flex items-center gap-2 transform transition-all duration-300 translate-y-4 opacity-0 z-50 pointer-events-auto`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  });

  // Remove after 3.5s
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Utility Helpers
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return isoStr;
  }
}
