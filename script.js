(function () {
  const state = {
    records: [],
    page: 1,
    pageSize: 20,
    colors: {
      text: '#1a1a1a',
      bg: '#ffffff'
    }
  };

  const els = {
    sidebar: document.getElementById('sidebar'),
    toggleSidebar: document.getElementById('toggleSidebar'),
    cards: document.getElementById('cards'),
    pageSize: document.getElementById('pageSize'),
    firstPage: document.getElementById('firstPage'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),
    lastPage: document.getElementById('lastPage'),
    pageInfo: document.getElementById('pageInfo'),
    textColor: document.getElementById('textColor'),
    bgColor: document.getElementById('bgColor'),
    modal: document.getElementById('modal'),
    closeModal: document.getElementById('closeModal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalBody'),
  };

  function applyCardStyles() {
    const cards = els.cards.querySelectorAll('.card');
    cards.forEach(card => {
      card.style.color = state.colors.text;
      card.style.backgroundColor = state.colors.bg;
    });
  }

  function render() {
    const totalPages = Math.max(1, Math.ceil(state.records.length / state.pageSize));
    if (state.page > totalPages) state.page = totalPages;

    const start = (state.page - 1) * state.pageSize;
    const end = start + state.pageSize;
    const pageRecords = state.records.slice(start, end);

    els.cards.innerHTML = pageRecords.map((rec, idx) => {
      const safeTitle = escapeHTML(rec.issue_title || '');
      const safeRepo = escapeHTML(rec.repo || '');
      return `<article class="card" data-index="${start + idx}">
        <div class="repo">${safeRepo}</div>
        <div class="title">${safeTitle}</div>
      </article>`;
    }).join('');

    els.pageInfo.textContent = `Page ${state.page} of ${totalPages}`;

    applyCardStyles();
  }

  function escapeHTML(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function parseJSONL(text) {
    const lines = text.split(/\r?\n/).filter(Boolean);
    const out = [];
    for (const line of lines) {
      try {
        out.push(JSON.parse(line));
      } catch (e) {
        // skip malformed lines
      }
    }
    return out;
  }

  async function loadData() {
    const res = await fetch('./data/merged_data.jsonl');
    const text = await res.text();
    state.records = parseJSONL(text);
    render();
  }

  function openModal(record) {
    els.modalTitle.textContent = record.issue_title || 'Details';
    els.modalBody.textContent = JSON.stringify(record, null, 2);
    els.modal.classList.add('show');
    els.modal.setAttribute('aria-hidden', 'false');
  }

  function closeModal() {
    els.modal.classList.remove('show');
    els.modal.setAttribute('aria-hidden', 'true');
  }

  // Event listeners
  els.toggleSidebar.addEventListener('click', () => {
    els.sidebar.classList.toggle('collapsed');
  });

  els.pageSize.addEventListener('change', (e) => {
    state.pageSize = parseInt(e.target.value, 10) || 20;
    state.page = 1;
    render();
  });

  els.firstPage.addEventListener('click', () => {
    state.page = 1;
    render();
  });

  els.prevPage.addEventListener('click', () => {
    state.page = Math.max(1, state.page - 1);
    render();
  });

  els.nextPage.addEventListener('click', () => {
    const totalPages = Math.max(1, Math.ceil(state.records.length / state.pageSize));
    state.page = Math.min(totalPages, state.page + 1);
    render();
  });

  els.lastPage.addEventListener('click', () => {
    state.page = Math.max(1, Math.ceil(state.records.length / state.pageSize));
    render();
  });

  els.textColor.addEventListener('input', (e) => {
    state.colors.text = e.target.value;
    applyCardStyles();
  });

  els.bgColor.addEventListener('input', (e) => {
    state.colors.bg = e.target.value;
    applyCardStyles();
  });

  els.cards.addEventListener('click', (e) => {
    const card = e.target.closest('.card');
    if (!card) return;
    const idx = parseInt(card.getAttribute('data-index'), 10);
    const record = state.records[idx];
    if (record) openModal(record);
  });

  els.closeModal.addEventListener('click', closeModal);
  els.modal.addEventListener('click', (e) => {
    if (e.target === els.modal) closeModal();
  });

  // Init
  loadData();
})();
