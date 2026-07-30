/* ═══════════════════════════════════════════════════════════════
   VinAI Knowledge Assistant — App Logic v3 (Discord clone)
   ═══════════════════════════════════════════════════════════════ */

const API_BASE   = 'http://localhost:8000';
const SESSION_ID = 'sess_' + Math.random().toString(36).slice(2, 9);

let isLoading    = false;
let kbDocuments  = [];
let messageCount = 0;

// ── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  loadKnowledgeBase();
  setupSynthTextarea();
  focusInput();
});

function focusInput() {
  const i = document.getElementById('chatInput');
  if (i) i.focus();
}

// ═══ HEALTH ════════════════════════════════════════════════════
async function checkApiHealth() {
  const dot  = document.querySelector('.status-dot');
  const text = document.querySelector('.status-text');
  try {
    const res  = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    if (data.status === 'ok') {
      dot.classList.add('online');
      text.textContent = data.gemini_configured
        ? `Gemini ✓ · ${data.kb_docs || 0} docs`
        : 'Online · Chưa có API Key';
      if (!data.gemini_configured) {
        showToast('⚠️ Chưa có GEMINI_API_KEY trong .env', 'error');
      } else {
        showToast(`✅ Connected · ${data.kb_docs} tài liệu trong KB`, 'success');
      }
      // Update stats
      const sd = document.getElementById('statDocs');
      if (sd) sd.textContent = data.kb_docs || '—';
    }
  } catch {
    dot.classList.add('error');
    text.textContent = 'Backend offline';
    showToast('❌ Backend chưa chạy! Xem HUONG_DAN_CHAY.md để khởi động.', 'error');
  }
}

// ═══ VIEW SWITCHING ════════════════════════════════════════════
function switchChannel(ch) {
  // Update active channel item
  document.querySelectorAll('.channel-item').forEach(el => el.classList.remove('active'));
  const chEl = document.getElementById(`ch-${ch}`);
  if (chEl) chEl.classList.add('active');

  // Show correct view
  document.getElementById('view-chat').style.display      = ch === 'chat'      ? 'flex' : 'none';
  document.getElementById('view-documents').style.display = ch === 'documents'  ? 'flex' : 'none';
  document.getElementById('view-synthesize').style.display= ch === 'synthesize' ? 'flex' : 'none';

  if (ch === 'documents') renderDocsGrid();
  if (ch === 'chat') focusInput();
}

function switchView(v) { switchChannel(v); }

// ═══ KNOWLEDGE BASE ═══════════════════════════════════════════
async function loadKnowledgeBase() {
  try {
    const res  = await fetch(`${API_BASE}/api/knowledge-base`);
    const data = await res.json();
    kbDocuments = data.documents || [];
    renderKbRightSidebar();
    document.getElementById('kbCount').textContent  = kbDocuments.length;
    const sd = document.getElementById('statDocs');
    if (sd) sd.textContent = kbDocuments.length;
  } catch {
    document.getElementById('kbList').innerHTML =
      '<div style="font-size:12px;color:#6d6f78;padding:8px;">KB offline</div>';
  }
}

function renderKbRightSidebar() {
  const list = document.getElementById('kbList');
  if (!kbDocuments.length) { list.innerHTML = ''; return; }
  list.innerHTML = kbDocuments.map(doc => `
    <div class="kb-channel-item" onclick="askAboutDoc('${escHtml(doc.title)}')">
      <span class="kb-item-type">${docIcon(doc.type)}</span>
      <div class="kb-item-text">
        <div class="kb-item-name">${escHtml(doc.id)} ${escHtml(doc.title).slice(0, 24)}${doc.title.length > 24 ? '…' : ''}</div>
        <div class="kb-item-meta">${doc.level || ''}</div>
      </div>
      <span class="kb-day-badge ${doc.module === 'Day 1' ? 'day1' : 'day2'}">${(doc.module||'').replace('Day ','D')}</span>
    </div>
  `).join('');
}

function renderDocsGrid() {
  const grid = document.getElementById('docsGrid');
  const stats = document.getElementById('docsStats');

  if (!kbDocuments.length) {
    grid.innerHTML = '<div class="loading-state"><div class="spinner"></div></div>';
    return;
  }

  if (stats) {
    stats.innerHTML = `
      <span>📄 ${kbDocuments.length} tài liệu</span>
      <span>📝 ${kbDocuments.filter(d=>d.type==='transcript').length} transcripts</span>
      <span>📊 ${kbDocuments.filter(d=>d.type==='slide').length} slides</span>
    `;
  }

  grid.innerHTML = kbDocuments.map(doc => {
    const colors = ['tag-purple','tag-blue','tag-green','tag-amber'];
    const concepts = (doc.key_concepts||[]).slice(0,4).map((c,i)=>
      `<span class="embed-tag ${colors[i%4]}">${escHtml(c)}</span>`
    ).join('');
    return `
    <div class="doc-card" onclick="showDocModal('${escHtml(doc.id)}')">
      <div class="doc-card-header">
        <span class="doc-card-icon">${docIcon(doc.type)}</span>
        <div class="doc-card-badges">
          <span class="embed-tag ${doc.module==='Day 1'?'tag-purple':'tag-green'}">${escHtml(doc.module||'')}</span>
          <span class="embed-tag tag-blue">${escHtml(doc.level||'')}</span>
        </div>
      </div>
      <div class="doc-card-title">${escHtml(doc.title)}</div>
      <div class="doc-card-summary">${escHtml(doc.summary||'')}</div>
      <div class="doc-tags">${concepts}</div>
      <div class="doc-card-footer">
        <span>${doc.reliability ? '🟢 ' + doc.reliability : ''}</span>
        <span>${doc.id}</span>
      </div>
    </div>`;
  }).join('');
}

function askAboutDoc(title) {
  switchChannel('chat');
  const input = document.getElementById('chatInput');
  input.value = `Cho mình biết về: "${title}"`;
  input.focus();
}

// ═══ CHAT ══════════════════════════════════════════════════════
function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const input   = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message || isLoading) return;

  input.value = '';
  appendUserMessage(message);
  showTypingIndicator();
  setLoading(true);

  try {
    const res  = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: SESSION_ID }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Lỗi server');
    removeTypingIndicator();
    appendBotMessage(data, message);
  } catch (err) {
    removeTypingIndicator();
    appendErrorMessage(err.message);
  } finally {
    setLoading(false);
    focusInput();
  }
}

// ─── Append messages ──────────────────────────────────────────
function appendUserMessage(text) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'user-msg-wrap';
  div.innerHTML = `<div class="user-bubble">${escHtml(text)}</div>`;
  container.appendChild(div);
  scrollChat();
}

function appendBotMessage(data, query = '') {
  const container = document.getElementById('chatMessages');
  const msgId = `msg-${++messageCount}`;
  const group = document.createElement('div');
  group.className = 'msg-group';
  group.id = msgId;

  // Route badge
  let routeTag = '';
  let bodyHtml = '';

  if (data.is_out_of_scope) {
    routeTag = '<span class="route-tag route-blocked">⛔ Ngoài phạm vi</span>';
    bodyHtml = `<div class="scope-warning">${markdownToHtml(data.response)}</div>`;
  } else if (!data.found_in_kb) {
    routeTag = '<span class="route-tag route-ambiguous">💭 Hỏi lại</span>';
    bodyHtml = `<div class="kb-not-found">${markdownToHtml(data.response)}</div>`;
  } else {
    routeTag = '<span class="route-tag route-rag">📚 KB</span>';
    bodyHtml = `<div class="msg-content">${markdownToHtml(data.response)}</div>`;
  }

  // Citations
  if (data.citations && data.citations.length) {
    const chips = data.citations.map(c =>
      `<span class="citation-chip" title="Từ tài liệu khoá học — mở KB để xem chi tiết">${escHtml(c)}</span>`
    ).join('');
    bodyHtml += `<div class="citations-row" style="margin-top:8px;">
      <span class="citation-label">📎</span>${chips}
    </div>`;
  }

  // Suggested docs
  if (data.suggested_docs && data.suggested_docs.filter(Boolean).length) {
    const sugg = data.suggested_docs.filter(Boolean).map(d =>
      `<span class="embed-tag tag-purple" style="cursor:pointer;" onclick="askAboutDoc('${escHtml(d)}')">${escHtml(d)}</span>`
    ).join(' ');
    bodyHtml += `<div style="margin-top:8px;font-size:12px;color:#6d6f78;">Xem thêm: ${sugg}</div>`;
  }

  // Disclaimer
  if (data.found_in_kb) {
    bodyHtml += `<div class="auto-disclaimer">🤖 Tóm tắt tự động — xem nguyên văn để xác nhận</div>`;
  }

  // Feedback
  bodyHtml += `
    <div class="feedback-row" id="fb-${msgId}">
      <span class="feedback-label">Hữu ích?</span>
      <button class="feedback-btn" onclick="sendFeedback('${msgId}','up')" title="Đúng rồi">👍</button>
      <button class="feedback-btn" onclick="sendFeedback('${msgId}','down')" title="Chưa đúng">👎</button>
    </div>`;

  group.innerHTML = `
    <div class="msg-avatar">⚡</div>
    <div class="msg-body">
      <div class="msg-header">
        <span class="msg-author">VinAI Assistant</span>
        <span class="msg-badge">BOT</span>
        ${routeTag}
        <span class="msg-time">${currentTime()}</span>
      </div>
      ${bodyHtml}
    </div>`;

  container.appendChild(group);
  scrollChat();
}

function appendErrorMessage(msg) {
  const container = document.getElementById('chatMessages');
  const group = document.createElement('div');
  group.className = 'msg-group';
  group.innerHTML = `
    <div class="msg-avatar">⚡</div>
    <div class="msg-body">
      <div class="msg-header">
        <span class="msg-author">VinAI Assistant</span>
        <span class="msg-badge">BOT</span>
        <span class="msg-time">${currentTime()}</span>
      </div>
      <div class="scope-warning">❌ ${escHtml(msg)}</div>
    </div>`;
  container.appendChild(group);
  scrollChat();
}

// ─── Typing indicator ─────────────────────────────────────────
function showTypingIndicator() {
  const c = document.getElementById('chatMessages');
  const el = document.createElement('div');
  el.id = 'typing';
  el.className = 'msg-group';
  el.innerHTML = `
    <div class="msg-avatar" style="font-size:14px;">⚡</div>
    <div class="msg-body">
      <div class="typing-indicator">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        <span>VinAI Assistant đang phân tích...</span>
      </div>
    </div>`;
  c.appendChild(el);
  scrollChat();
}
function removeTypingIndicator() {
  const el = document.getElementById('typing');
  if (el) el.remove();
}
function scrollChat() {
  const c = document.getElementById('chatMessages');
  if (c) c.scrollTop = c.scrollHeight;
}

// ═══ FILE UPLOAD ═══════════════════════════════════════════════
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) uploadFile(file);
  e.target.value = '';
}

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Chỉ hỗ trợ file PDF', 'error');
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    showToast('File quá lớn (tối đa 20MB)', 'error');
    return;
  }

  switchChannel('chat');
  appendUserMessage(`📎 Upload: ${file.name} (${(file.size/1024).toFixed(0)} KB)`);
  showTypingIndicator();
  setLoading(true);

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res  = await fetch(`${API_BASE}/api/summarize`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload thất bại');
    removeTypingIndicator();
    appendSummaryEmbed(data, file.name);
    showToast(`✅ Đã phân tích: ${file.name}`, 'success');
  } catch (err) {
    removeTypingIndicator();
    appendErrorMessage(err.message);
    showToast(`❌ ${err.message}`, 'error');
  } finally {
    setLoading(false);
    focusInput();
  }
}

function appendSummaryEmbed(data, filename) {
  const s = data.summary || {};
  const container = document.getElementById('chatMessages');
  const group = document.createElement('div');
  group.className = 'msg-group';

  const colors = ['tag-purple','tag-blue','tag-green','tag-amber'];
  const conceptTags = (s.key_concepts||[]).slice(0,5).map((c,i)=>
    `<span class="embed-tag ${colors[i%4]}">${escHtml(c)}</span>`
  ).join('');

  const takeaways = (s.key_takeaways||[]).map(t=>
    `<li style="margin:4px 0;">${markdownToHtml(t)}</li>`
  ).join('');

  const citations = (s.citations||[]).map(c=>
    `<span class="citation-chip" title="Trích từ tài liệu gốc">${escHtml(c)}</span>`
  ).join('');

  const conf = s.reliability_score || 88;
  const mod  = s.module || 'Không xác định';
  const modClass = mod.includes('1') ? 'tag-purple' : mod.includes('2') ? 'tag-green' : 'tag-amber';

  group.innerHTML = `
    <div class="msg-avatar">⚡</div>
    <div class="msg-body">
      <div class="msg-header">
        <span class="msg-author">VinAI Assistant</span>
        <span class="msg-badge">BOT</span>
        <span class="route-tag route-pdf">📄 PDF Summary</span>
        <span class="msg-time">${currentTime()}</span>
      </div>
      <div class="msg-content" style="margin-bottom:6px;">✅ Đã phân tích <strong>${escHtml(filename)}</strong> (${data.page_count||'?'} trang)</div>
      <div class="embed-card">
        <div class="embed-title">${escHtml(s.title || filename)}</div>
        <div class="embed-meta">
          <span class="embed-tag ${modClass}">${escHtml(mod)}</span>
          <span class="embed-tag tag-blue" style="margin-left:4px;">${escHtml(s.level||'Foundation')}</span>
          ${mod.includes('Không') ? '<span class="embed-tag tag-amber" style="margin-left:4px;">⚠️ Auto-classified</span>' : ''}
        </div>
        <div class="embed-body" style="font-size:13px;color:#b5bac1;">
          ${escHtml(s.subject||'')}
        </div>
        <div class="embed-field">
          <div class="embed-field-name">Khái niệm chính</div>
          <div class="embed-tags">${conceptTags}</div>
        </div>
        <div class="embed-field">
          <div class="embed-field-name">Key Takeaways</div>
          <ul class="embed-field-value" style="margin-left:16px;">${takeaways}</ul>
        </div>
        <div class="embed-footer">
          <span>Độ tin cậy</span>
          <div class="confidence-bar"><div class="confidence-fill" style="width:${conf}%"></div></div>
          <span>${conf}%</span>
          <span style="margin-left:8px;">${citations}</span>
        </div>
      </div>
      <div class="auto-disclaimer">🤖 Tóm tắt tự động — xem nguyên văn để xác nhận · ${escHtml(s.note||'')}</div>
    </div>`;

  container.appendChild(group);
  scrollChat();
}

// ═══ FEEDBACK ══════════════════════════════════════════════════
async function sendFeedback(msgId, rating) {
  const row = document.getElementById(`fb-${msgId}`);
  if (row) row.innerHTML = rating === 'up'
    ? '<span style="font-size:12px;color:#23a55a;">✅ Cảm ơn!</span>'
    : '<span style="font-size:12px;color:#fbbf24;">📝 Cảm ơn, mình sẽ cải thiện.</span>';

  try {
    await fetch(`${API_BASE}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message_id: msgId, rating, session_id: SESSION_ID }),
    });
  } catch { /* silent */ }
}

// ═══ SYNTHESIZE ════════════════════════════════════════════════
function setupSynthTextarea() {
  const ta = document.getElementById('synthInput');
  if (!ta) return;
  ta.addEventListener('input', () => {
    document.getElementById('charCount').textContent = `${ta.value.length} ký tự`;
  });
}

async function synthesizeChat() {
  const text = document.getElementById('synthInput').value.trim();
  if (!text) { showToast('Paste đoạn chat vào trước', 'error'); return; }
  if (text.length < 50) { showToast('Cần ít nhất 50 ký tự', 'error'); return; }

  const result = document.getElementById('synthResult');
  result.innerHTML = '<div class="loading-state"><div class="spinner"></div><span>Đang tổng hợp...</span></div>';

  try {
    const res  = await fetch(`${API_BASE}/api/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_text: text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    renderSynthResult(data, result);
  } catch (err) {
    result.innerHTML = `<div class="scope-warning">❌ ${escHtml(err.message)}</div>`;
  }
}

function renderSynthResult(data, container) {
  if (data.error) {
    container.innerHTML = `<div class="scope-warning">${escHtml(data.error)}</div>`;
    return;
  }
  const max = Math.max(...(data.main_topics||[]).map(t=>t.count), 1);
  const topics = (data.main_topics||[]).map(t=>`
    <div class="synth-topic-row">
      <div class="synth-topic-name">${escHtml(t.topic)}</div>
      <div class="synth-bar-track"><div class="synth-bar-fill" style="width:${Math.round(t.count/max*100)}%"></div></div>
      <div class="synth-count">${t.count}</div>
    </div>`).join('');
  const qas = (data.popular_questions||[]).map(q=>`
    <div class="synth-qa-card">
      <div class="synth-question">❓ ${escHtml(q.question)}</div>
      <div class="synth-answer">${escHtml(q.brief_answer)}</div>
      <div class="synth-asked">Hỏi bởi ${q.asked_by} người</div>
    </div>`).join('');
  const stuck = (data.stuck_points||[]).map(p=>`<span class="stuck-chip">⚠️ ${escHtml(p)}</span>`).join('');
  const res2  = (data.suggested_resources||[]).map(r=>
    `<span class="embed-tag tag-blue" style="cursor:pointer;margin:2px;" onclick="askAboutDoc('${escHtml(r)}')">${escHtml(r)}</span>`
  ).join('');

  container.innerHTML = `<div class="synth-result">
    ${data.summary ? `<div class="synth-section"><div class="synth-section-title">📋 Tổng kết</div><div style="font-size:14px;color:#dbdee1;">${markdownToHtml(data.summary)}</div></div>` : ''}
    ${topics ? `<div class="synth-section"><div class="synth-section-title">📊 Chủ đề nổi bật</div>${topics}</div>` : ''}
    ${qas    ? `<div class="synth-section"><div class="synth-section-title">💬 Câu hỏi phổ biến</div>${qas}</div>` : ''}
    ${stuck  ? `<div class="synth-section"><div class="synth-section-title">🚧 Điểm đang stuck</div><div>${stuck}</div></div>` : ''}
    ${res2   ? `<div class="synth-section"><div class="synth-section-title">📚 Tài liệu gợi ý</div><div style="display:flex;flex-wrap:wrap;gap:4px;">${res2}</div></div>` : ''}
  </div>`;
}

// ═══ MODAL ═════════════════════════════════════════════════════
function showDocModal(id) {
  const doc = kbDocuments.find(d => d.id === id);
  if (!doc) return;

  const colors = ['tag-purple','tag-blue','tag-green','tag-amber'];
  const concepts = (doc.key_concepts||[]).map((c,i)=>
    `<span class="embed-tag ${colors[i%4]}">${escHtml(c)}</span>`
  ).join('');
  const takeaways = (doc.key_takeaways||[]).map(t=>
    `<li style="margin:5px 0;font-size:13px;color:#b5bac1;">${markdownToHtml(t)}</li>`
  ).join('');
  const citations = (doc.citations||[]).map(c=>
    `<span class="citation-chip">${escHtml(c)}</span>`
  ).join('');

  document.getElementById('modalContent').innerHTML = `
    <div class="modal-body">
      <div class="modal-title">${docIcon(doc.type)} ${escHtml(doc.title)}</div>
      <div class="modal-meta">${escHtml(doc.module||'')} · ${escHtml(doc.level||'')} · ${escHtml(doc.id)}</div>
      <div class="modal-field">
        <div class="modal-field-name">Tóm Tắt</div>
        <div style="font-size:13px;color:#b5bac1;line-height:1.6;">${escHtml(doc.summary||'')}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-name">Khái Niệm Chính</div>
        <div class="embed-tags">${concepts}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-name">Key Takeaways (có citation)</div>
        <ul style="margin-left:16px;">${takeaways}</ul>
      </div>
      <div class="modal-field">
        <div class="modal-field-name">Citations</div>
        <div class="citations-row">${citations}</div>
      </div>
      <div style="margin-top:4px;font-size:11px;color:#6d6f78;">
        🤖 Source: ${escHtml(doc.source_file||'—')} · Độ tin cậy: ${escHtml(doc.reliability||'—')}
      </div>
      <button style="margin-top:16px;width:100%;background:#5865f2;border:none;color:#fff;font-size:14px;font-weight:600;padding:10px;border-radius:4px;cursor:pointer;"
        onclick="closeModal(); askAboutDoc('${escHtml(doc.title)}')">
        💬 Hỏi về tài liệu này
      </button>
    </div>`;

  document.getElementById('modalOverlay').classList.add('show');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('show');
}

// ═══ TOAST ═════════════════════════════════════════════════════
function showToast(message, type = 'info') {
  const wrap = document.getElementById('toastWrap');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  t.innerHTML = `<span>${icons[type]||'ℹ️'}</span> ${escHtml(message)}`;
  wrap.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateX(20px)';
    t.style.transition = '300ms';
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

// ═══ UTILS ═════════════════════════════════════════════════════
function setLoading(state) {
  isLoading = state;
  const btn = document.getElementById('sendBtn');
  if (btn) btn.disabled = state;
}

function escHtml(str) {
  if (typeof str !== 'string') return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function markdownToHtml(text) {
  if (!text) return '';
  return escHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\[([T][0-9]{2,3}-[0-9]{3,4})\]/g, '<span class="citation-inline" title="Mã citation — verify với tài liệu gốc">[$1]</span>')
    .replace(/^[-•] (.*)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');
}

function docIcon(type) {
  return { transcript:'📝', slide:'📊', paper:'📄', code:'💻' }[type] || '📄';
}

function currentTime() {
  return new Date().toLocaleTimeString('vi-VN', { hour:'2-digit', minute:'2-digit' });
}
