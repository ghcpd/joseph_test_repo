const cardsEl = document.getElementById('cards');
const pageInfoEl = document.getElementById('pageInfo');
const pageSizeEl = document.getElementById('pageSize');
const textColorEl = document.getElementById('textColor');
const bgColorEl = document.getElementById('bgColor');

const modal = document.getElementById('modal');
const detailEl = document.getElementById('detail');
const closeModalBtn = document.getElementById('closeModal');

let all = [];
let page = 1;
let pageSize = parseInt(pageSizeEl.value, 10);

async function loadData(){
  const res = await fetch('/static/merged_data.jsonl');
  const text = await res.text();
  all = text.trim().split('\n').map(l=>JSON.parse(l));
  render();
}

function render(){
  const totalPages = Math.max(1, Math.ceil(all.length / pageSize));
  if(page>totalPages) page = totalPages;
  const start = (page-1)*pageSize;
  const slice = all.slice(start, start+pageSize);
  cardsEl.innerHTML = '';
  slice.forEach(rec=>{
    const div = document.createElement('div');
    div.className = 'card';
    div.style.color = textColorEl.value;
    div.style.background = bgColorEl.value;
    div.innerHTML = `<strong>${rec.repo}</strong><br>${rec.issue_title}`;
    div.onclick = ()=>{
      detailEl.textContent = JSON.stringify(rec, null, 2);
      modal.classList.remove('hidden');
    };
    cardsEl.appendChild(div);
  });
  pageInfoEl.textContent = `Page ${page} / ${totalPages}`;
}

document.getElementById('firstBtn').onclick = ()=>{page=1;render();};
document.getElementById('prevBtn').onclick = ()=>{page=Math.max(1,page-1);render();};
document.getElementById('nextBtn').onclick = ()=>{const tp=Math.max(1,Math.ceil(all.length/pageSize));page=Math.min(tp,page+1);render();};
document.getElementById('lastBtn').onclick = ()=>{page=Math.max(1,Math.ceil(all.length/pageSize));render();};
pageSizeEl.onchange = ()=>{pageSize=parseInt(pageSizeEl.value,10);page=1;render();};
textColorEl.oninput = bgColorEl.oninput = ()=>{render();};
closeModalBtn.onclick = ()=>{modal.classList.add('hidden');};

loadData();
