let currentProfile = null;
async function fetchProfile(){
  const res = await fetch('/api/profiles');
  if(!res.ok){ console.error('failed to fetch profile'); return; }
  const p = await res.json();
  currentProfile = p;
  document.getElementById('profile-img').src = p.image;   // was p.pic
  document.getElementById('profile-name').innerText = p.name; // remove age since not provided
  document.getElementById('profile-bio').innerText = p.bio + (p.personality ? ' · ' + p.personality : '');
}

document.getElementById('left-btn').addEventListener('click', ()=>{
  // skip -> just fetch next profile
  fetchProfile();
});

document.getElementById('right-btn').addEventListener('click', async ()=>{
  if(!currentProfile) return;
  const res = await fetch('/api/swipe', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({direction:'right', profile: currentProfile})
  });
  const j = await res.json();
  if(j.match){
    openChat();
  } else {
    fetchProfile();
  }
});

document.getElementById('back-btn').addEventListener('click', ()=>{
  document.getElementById('chat-screen').classList.add('hidden');
  document.getElementById('swipe-area').classList.remove('hidden');
  // clear session match on client; backend keeps history for demo
  currentProfile = null;
  fetchProfile();
});

async function openChat(){
  document.getElementById('chat-with').innerText = currentProfile.name + ' (AI-generated)';
  document.getElementById('swipe-area').classList.add('hidden');
  document.getElementById('chat-screen').classList.remove('hidden');
  await loadHistory();
}

async function loadHistory(){
  const res = await fetch('/api/history');
  const msgs = await res.json();
  const box = document.getElementById('messages');
  box.innerHTML = '';
  for(const m of msgs){
    const d = document.createElement('div');
    d.className = 'm ' + (m.from === 'user' ? 'user' : 'ai');
    d.innerText = m.text;
    box.appendChild(d);
  }
  box.scrollTop = box.scrollHeight;
}

document.getElementById('send-btn').addEventListener('click', async ()=>{
  const input = document.getElementById('msg-input');
  const text = input.value.trim();
  if(!text) return;
  input.value = '';
  // optimistic append
  const box = document.getElementById('messages');
  const u = document.createElement('div'); u.className='m user'; u.innerText=text; box.appendChild(u);
  box.scrollTop = box.scrollHeight;

  const res = await fetch('/api/send_message', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message:text, profile: currentProfile})
  });
  const j = await res.json();
  if(j.ok){
    const a = document.createElement('div'); a.className='m ai'; a.innerText = j.reply; box.appendChild(a);
    box.scrollTop = box.scrollHeight;
  } else {
    const a = document.createElement('div'); a.className='m ai'; a.innerText = 'Error: ' + (j.error || 'unknown'); box.appendChild(a);
  }
});

// init
fetchProfile();
