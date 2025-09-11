function byId(id){ return document.getElementById(id); }

function parseRepo(url){
  const m = url.trim().match(/^https:\/\/github.com\/([^\/]+)\/([^\/]+)$/);
  if(!m) return null;
  return `${m[1]}/${m[2]}`;
}

async function fetchJSON(url){
  const res = await fetch(url);
  if(!res.ok){
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}

const listCache = new Map();

async function loadList(){
  const repoUrl = byId('repoUrl').value;
  const repo = parseRepo(repoUrl);
  if(!repo){
    alert('Invalid URL. Expected format: https://github.com/owner/repo');
    return;
  }
  const type = byId('type').value;
  const key = `${repo}-${type}`;
  const listEl = byId('list');
  listEl.innerHTML='';

  let items;
  if(listCache.has(key)){
    items = listCache.get(key);
  } else {
    const endpoint = type === 'Issues' ? `/api/issues?repo=${encodeURIComponent(repo)}` : `/api/prs?repo=${encodeURIComponent(repo)}`;
    const data = await fetchJSON(endpoint);
    items = data.map(i => ({
      number: i.number,
      title: i.title,
      user: i.user?.login,
      state: i.state,
      labels: i.labels || []
    }));
    listCache.set(key, items);
  }

  for(const it of items){
    const opt = document.createElement('option');
    opt.value = String(it.number);
    const isBug = (it.labels||[]).some(l => (l.name||'').toLowerCase()==='bug');
    opt.textContent = `#${it.number} ${it.title}` + (isBug ? ' [bug]' : '');
    if(isBug) opt.className = 'bug';
    listEl.appendChild(opt);
  }
}

async function showDetails(){
  const selections = Array.from(byId('list').selectedOptions).map(o => Number(o.value));
  const repo = parseRepo(byId('repoUrl').value);
  if(!repo || selections.length === 0) return;
  const type = byId('type').value;

  if(selections.length > 1){
    byId('d-title').textContent = `Selected ${selections.length} items`;
    byId('d-meta').textContent = 'Multiple selection summary';
    byId('d-body').textContent = selections.map(n => `#${n}`).join('\n');
    return;
  }

  const number = selections[0];
  const endpoint = type === 'Issues' ? `/api/issues/${number}?repo=${encodeURIComponent(repo)}` : `/api/prs/${number}?repo=${encodeURIComponent(repo)}`;
  try{
    const d = await fetchJSON(endpoint);
    const status = d.merged ? 'merged' : d.state;
    byId('d-title').textContent = d.title || '';
    byId('d-meta').textContent = `#${d.number} by ${d.user?.login} – ${status} – created ${d.created_at} – updated ${d.updated_at}`;
    byId('d-body').textContent = d.body || '';
  }catch(e){
    alert(`Error: ${e.message}`);
  }
}

byId('fetchBtn').addEventListener('click', loadList);
byId('list').addEventListener('change', showDetails);
