const repoInput = document.getElementById('repoUrl');
const loadBtn = document.getElementById('loadBtn');
const typeSelect = document.getElementById('typeSelect');
const listSelect = document.getElementById('listSelect');
const details = document.getElementById('details');

const cache = new Map();

function parseRepoUrl(url){
  const m = url.match(/^https?:\/\/github.com\/([^\/]+)\/([^\/]+)\/?$/);
  if(!m) return null;
  return { owner: m[1], repo: m[2] };
}

async function fetchItems(owner, repo, type){
  const key = `${owner}/${repo}/${type}`;
  if(cache.has(key)) return cache.get(key);
  const endpoint = type === 'Pull Requests'
    ? `https://api.github.com/repos/${owner}/${repo}/pulls?per_page=50&state=all`
    : `https://api.github.com/repos/${owner}/${repo}/issues?per_page=50&state=all`;
  const res = await fetch(endpoint, { headers: { 'Accept': 'application/vnd.github+json' }});
  if(!res.ok) throw new Error(`GitHub API error ${res.status}`);
  const data = await res.json();
  cache.set(key, data);
  return data;
}

function formatItem(item){
  const num = item.number ? `#${item.number} ` : '';
  return `${num}${item.title || item.name}`;
}

function showError(msg){
  alert(msg);
}

function renderList(items){
  listSelect.innerHTML = '';
  items.forEach(i => {
    const opt = document.createElement('option');
    opt.value = i.number || i.id;
    opt.textContent = formatItem(i);
    if((i.labels||[]).some(l => l.name === 'bug')) opt.classList.add('highlight');
    listSelect.appendChild(opt);
  });
}

function renderDetails(items){
  if(!items.length){ details.innerHTML = ''; return; }
  const blocks = items.map(i => `
    <div class="card ${ (i.labels||[]).some(l=>l.name==='bug') ? 'highlight' : ''}">
      <h3>${formatItem(i)}</h3>
      <div>Author: ${i.user?.login || 'unknown'}</div>
      <div>Status: ${i.state}${i.merged_at ? '/merged' : ''}</div>
      <div>Created: ${new Date(i.created_at).toLocaleString()}</div>
      <div>Updated: ${new Date(i.updated_at).toLocaleString()}</div>
      <pre>${(i.body || '').slice(0, 1000)}</pre>
    </div>`);
  details.innerHTML = blocks.join('\n');
}

async function handleLoad(){
  const parsed = parseRepoUrl(repoInput.value.trim());
  if(!parsed){ showError('Invalid GitHub URL. Expected format: https://github.com/owner/repo'); return; }
  try{
    const items = await fetchItems(parsed.owner, parsed.repo, typeSelect.value);
    renderList(items);
  }catch(e){ showError(e.message); }
}

listSelect.addEventListener('change', () => {
  const selectedNumbers = Array.from(listSelect.selectedOptions).map(o => Number(o.value));
  const parsed = parseRepoUrl(repoInput.value.trim());
  if(!parsed) return;
  const all = cache.get(`${parsed.owner}/${parsed.repo}/${typeSelect.value}`) || [];
  const chosen = all.filter(i => selectedNumbers.includes(i.number || i.id));
  renderDetails(chosen);
});

loadBtn.addEventListener('click', handleLoad);

typeSelect.addEventListener('change', () => {
  if(repoInput.value.trim()) handleLoad();
});
