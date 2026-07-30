/* ═══════════════════════════════════════════════════════════════
   VinAI Knowledge Assistant — App Logic
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:8000';

// ── State ────────────────────────────────────────────────────────
let isLoading = false;
let kbDocuments = [];

// ── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  loadKnowledgeBase();
  setupSynthTextarea();
});

// ═══ API HEALTH CHECK ════════════════════════════════════════════
async function checkApiHealth() {
  const dot  = document.querySelector('.status-dot');
  const text = document.querySelector('.status-text');
  try {
    const res  = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    if (data.status === 'ok') {
      dot.classList.add('online');
      text.textContent = data.gemini_configured ? 'Gemini ✓' : 'API OK · No Key';
      if (!data.gemini_configured) {
        showToast('⚠️ Chưa có GEMINI_API_KEY — set trong file .env', 'info');
      }
    }
  } catch {
    dot.classList.add('error');
    text.textContent = 'Backend offline';
    showToast('❌ Backend chưa chạy. Chạy: python main.py', 'error');
  }
}

// ═══ TAB SWITCHING ═══════════════════════════════════════════════
function switchTab(tabName) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  document.getElementById(`tab-${tabName}`).classList.add('active');

  if (tabName === 'documents') renderDocsTab();
}

// ═══ KNOWLEDGE BASE ═══════════════════════════════════════════════
async function loadKnowledgeBase() {
  try {
    const res  = await fetch(`${API_BASE}/api/knowledge-base`);
    const data = await res.json();
    kbDocuments = data.documents || [];
    renderKbSidebar();
    document.getElementById('statDocs').textContent = kbDocuments.length;
    document.getElementById('kbCount').textContent  = kbDocuments.length;
  } catch {
    document.getElementById('kbList').innerHTML =
      '<div class="kb-loading">Không thể tải KB — backend offline</div>';
  }
}

function renderKbSidebar() {
  const list = document.getElementById('kbList');
  if (!kbDocuments.length) {
    list.innerHTML = '<div class="kb-loading">Chưa có tài liệu</div>';
    return;
  }
  list.innerHTML = kbDocuments.map(doc => `
    <div class="kb-item" onclick="askAboutDoc('${escHtml(doc.title)}')">
      <span class="kb-item-icon">${docIcon(doc.type)}</span>
      <div class="kb-item-info">
        <div class="kb-item-title">${escHtml(doc.title)}</div>
        <div class="kb-item-meta">${doc.level} · ${doc.segments || '—'} đoạn</div>
      </div>
      <span class="kb-badge ${doc.module === 'Day 1' ? 'kb-badge-day1' : 'kb-badge-day2'}">
        ${escHtml(doc.module)}
      </span>
    </div>
  `).join('');
}

function renderDocsTab() {
  const grid = document.getElementById('docsGrid');
  if (!kbDocuments.length) {
    grid.innerHTML = '<div class="loading-state"><div class="spinner"></div><br>Đang tải...</div>';
    loadKnowledgeBase().then(renderDocsTab);
    return;
  }
  grid.innerHTML = kbDocuments.map(doc => {
    const tagColors = ['tag-purple', 'tag-blue', 'tag-green', 'tag-amber'];
    const concepts  = (doc.key_concepts || []).slice(0, 4).map((c, i) =>
      `<span class="tag ${tagColors[i % 4]}">${escHtml(c)}</span>`
    ).join('');

    return `
    <div class="doc-card" onclick="showDocModal(${doc.id ? `'${doc.id}'` : `null`}, '${escHtml(doc.title)}')">
      <div class="doc-card-header">
        <span class="doc-card-icon">${docIcon(doc.type)}</span>
        <div class="doc-card-badges">
          <span class="tag ${doc.module === 'Day 1' ? 'tag-purple' : 'tag-blue'}">${escHtml(doc.module)}</span>
          <span class="tag tag-green">${escHtml(doc.level)}</span>
        </div>
      </div>
      <div class="doc-card-title">${escHtml(doc.title)}</div>
      <div class="doc-card-summary">${escHtml(doc.summary || '')}</div>
      <div class="doc-card-concepts">${concepts}</div>
      <div class="doc-card-footer">
        <span>${doc.reliability ? `🟢 Độ tin cậy: ${doc.reliability}` : ''}</span>
        <span>${doc.type}</span>
      </div>
    </div>`;
  }).join('');
}

function askAboutDoc(title) {
  switchTab('chat');
  const input = document.getElementById('chatInput');
  input.value = `Cho mình biết về tài liệu "${title}"`;
  input.focus();
}

// ═══ CHAT ════════════════════════════════════════════════════════
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
      body: JSON.stringify({ message }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Lỗi không xác định');
    appendBotResponse(data);
  } catch (err) {
    appendBotError(err.message);
  } finally {
    removeTypingIndicator();
    setLoading(false);
  }
}

function appendUserMessage(text) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'user-bubble';
  div.innerHTML = `<div class="user-bubble-inner">${escHtml(text)}</div>`;
  container.appendChild(div);
  scrollChat();
}

function appendBotResponse(data) {
  const container = document.getElementById('chatMessages');
  const group = document.createElement('div');
  group.className = 'message-group';

  let bodyHtml = '';

  if (data.is_out_of_scope) {
    bodyHtml = `<div class="scope-warning">${markdownToHtml(data.response)}</div>`;
  } else if (!data.found_in_kb && !data.is_out_of_scope) {
    bodyHtml = `<div class="kb-not-found">${markdownToHtml(data.response)}</div>`;
  } else {
    bodyHtml = `<div class="message-text">${markdownToHtml(data.response)}</div>`;
  }

  // Citations
  if (data.citations && data.citations.length) {
    const chips = data.citations.map(c =>
      `<span class="citation-chip">${escHtml(c)}</span>`
    ).join('');
    bodyHtml += `<div class="citations-row" style="margin-top:8px;">${chips}</div>`;
  }

  // Suggested docs
  if (data.suggested_docs && data.suggested_docs.length) {
    const sugg = data.suggested_docs.map(d =>
      `<span class="tag tag-purple" style="cursor:pointer;" onclick="askAboutDoc('${escHtml(d)}')">${escHtml(d)}</span>`
    ).join(' ');
    bodyHtml += `<div style="margin-top:8px;"><span style="font-size:11px;color:var(--text-muted);">Xem thêm: </span>${sugg}</div>`;
  }

  group.innerHTML = `
    <div class="bot-avatar-wrap"><div class="bot-avatar">⚡</div></div>
    <div class="message-content">
      <div class="message-author">
        VinAI Assistant <span class="bot-badge">BOT</span>
        <span class="message-time">${currentTime()}</span>
      </div>
      ${bodyHtml}
    </div>`;

  container.appendChild(group);
  scrollChat();
}

function appendBotError(msg) {
  const container = document.getElementById('chatMessages');
  const group = document.createElement('div');
  group.className = 'message-group';
  group.innerHTML = `
    <div class="bot-avatar-wrap"><div class="bot-avatar">⚡</div></div>
    <div class="message-content">
      <div class="message-author">VinAI Assistant <span class="bot-badge">BOT</span></div>
      <div class="scope-warning">❌ ${escHtml(msg)}</div>
    </div>`;
  container.appendChild(group);
  scrollChat();
}

function showTypingIndicator() {
  const container = document.getElementById('chatMessages');
  const el = document.createElement('div');
  el.id = 'typingIndicator';
  el.className = 'message-group';
  el.innerHTML = `
    <div class="bot-avatar-wrap"><div class="bot-avatar">⚡</div></div>
    <div class="message-content">
      <div class="typing-indicator">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        <span>Đang phân tích...</span>
      </div>
    </div>`;
  container.appendChild(el);
  scrollChat();
}

function removeTypingIndicator() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

function scrollChat() {
  const c = document.getElementById('chatMessages');
  c.scrollTop = c.scrollHeight;
}

// ═══ FILE UPLOAD ══════════════════════════════════════════════════
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.add('dragover');
}
function handleDragLeave() {
  document.getElementById('dropzone').classList.remove('dragover');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
}
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

  // Show processing in chat
  appendUserMessage(`📎 Upload tài liệu: ${file.name}`);
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

    appendAnalysisCard(data);
    showToast(`✅ Đã phân tích: ${file.name}`, 'success');
  } catch (err) {
    appendBotError(err.message);
    showToast(`❌ ${err.message}`, 'error');
  } finally {
    removeTypingIndicator();
    setLoading(false);
  }
}

function appendAnalysisCard(data) {
  const s = data.summary || {};
  const container = document.getElementById('chatMessages');
  const group = document.createElement('div');
  group.className = 'message-group';

  const tagColors = ['tag-purple', 'tag-blue', 'tag-green', 'tag-amber'];
  const concepts = (s.key_concepts || []).slice(0, 5).map((c, i) =>
    `<span class="tag ${tagColors[i % 4]}">${escHtml(c)}</span>`
  ).join('');

  const takeaways = (s.key_takeaways || []).map(t =>
    `<li>${escHtml(t)}</li>`
  ).join('');

  const citations = (s.citations || []).map(c =>
    `<span class="citation-chip">${escHtml(c)}</span>`
  ).join('');

  const confidence = s.reliability_score || 88;
  const levelBadge = s.level || 'Foundation';
  const moduleBadge = s.module || 'Day 1';

  group.innerHTML = `
    <div class="bot-avatar-wrap"><div class="bot-avatar">⚡</div></div>
    <div class="message-content">
      <div class="message-author">
        VinAI Assistant <span class="bot-badge">BOT</span>
        <span class="message-time">${currentTime()}</span>
      </div>
      <div class="message-text" style="margin-bottom:8px;">
        ✅ Đã phân tích tài liệu thành công! Đây là kết quả:
      </div>
      <div class="analysis-card">
        <div class="analysis-card-header">
          <div class="analysis-card-title">
            📄 ${escHtml(s.title || data.filename)}
          </div>
          <div class="analysis-card-meta">${data.page_count || '?'} trang · ${moduleBadge}</div>
        </div>
        <div class="analysis-card-body">
          <div class="analysis-section">
            <div class="analysis-section-title">Khái niệm chính</div>
            <div class="tags-row">${concepts}</div>
          </div>
          <div class="analysis-section">
            <div class="analysis-section-title">Cấp độ & Module</div>
            <div class="tags-row">
              <span class="tag tag-green">${escHtml(levelBadge)}</span>
              <span class="tag tag-blue">${escHtml(moduleBadge)}</span>
            </div>
            ${s.prerequisites && s.prerequisites.length ?
              `<div style="margin-top:6px;font-size:11px;color:var(--text-muted);">
                Prerequisites: ${s.prerequisites.join(', ')}
              </div>` : ''}
          </div>
          <div class="analysis-section" style="grid-column:1/-1;">
            <div class="analysis-section-title">Key Takeaways</div>
            <ul class="takeaway-list">${takeaways}</ul>
          </div>
        </div>
        <div class="analysis-card-footer">
          <div class="confidence-bar-wrap">
            <span>Độ tin cậy</span>
            <div class="confidence-bar-track">
              <div class="confidence-bar-fill" style="width:${confidence}%"></div>
            </div>
            <span class="confidence-value">${confidence}%</span>
          </div>
          <div class="citations-row">${citations}</div>
        </div>
      </div>
      ${s.note ? `<div class="kb-not-found" style="margin-top:8px;font-size:12px;">ℹ️ ${escHtml(s.note)}</div>` : ''}
    </div>`;

  container.appendChild(group);
  scrollChat();
}

// ═══ SYNTHESIZE ═══════════════════════════════════════════════════
function setupSynthTextarea() {
  const ta = document.getElementById('synthInput');
  ta.addEventListener('input', () => {
    document.getElementById('charCount').textContent = `${ta.value.length} ký tự`;
  });
}

async function synthesizeChat() {
  const text = document.getElementById('synthInput').value.trim();
  if (!text) { showToast('Vui lòng paste đoạn chat trước', 'error'); return; }
  if (text.length < 50) { showToast('Cần ít nhất 50 ký tự', 'error'); return; }

  const resultArea = document.getElementById('synthResult');
  resultArea.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div><br>
      Đang tổng hợp... (~5-10 giây)
    </div>`;

  try {
    const res  = await fetch(`${API_BASE}/api/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_text: text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    renderSynthResult(data, resultArea);
  } catch (err) {
    resultArea.innerHTML = `<div class="scope-warning">❌ ${escHtml(err.message)}</div>`;
  }
}

function renderSynthResult(data, container) {
  if (data.error) {
    container.innerHTML = `<div class="scope-warning">${escHtml(data.error)}</div>`;
    return;
  }

  // Topic bars
  const maxCount = Math.max(...(data.main_topics || []).map(t => t.count), 1);
  const topicsHtml = (data.main_topics || []).map(t => `
    <div class="synth-topic-row">
      <div class="synth-topic-name">${escHtml(t.topic)}</div>
      <div class="synth-bar-track">
        <div class="synth-bar-fill" style="width:${Math.round(t.count / maxCount * 100)}%"></div>
      </div>
      <div class="synth-count">${t.count}</div>
    </div>
  `).join('');

  // Q&A cards
  const qaHtml = (data.popular_questions || []).map(q => `
    <div class="synth-qa-card">
      <div class="synth-question">❓ ${escHtml(q.question)}</div>
      <div class="synth-answer">${escHtml(q.brief_answer)}</div>
      <div class="synth-asked">Được hỏi bởi ${q.asked_by} học viên</div>
    </div>
  `).join('');

  // Stuck points
  const stuckHtml = (data.stuck_points || []).map(p =>
    `<span class="stuck-chip">⚠️ ${escHtml(p)}</span>`
  ).join('');

  // Summary
  const summaryHtml = data.summary ? `
    <div class="synth-section">
      <div class="synth-section-title">📋 Tổng kết</div>
      <div class="message-text">${escHtml(data.summary)}</div>
    </div>` : '';

  container.innerHTML = `
    <div class="synth-result">
      ${summaryHtml}
      ${topicsHtml ? `
        <div class="synth-section">
          <div class="synth-section-title">📊 Chủ đề nổi bật</div>
          ${topicsHtml}
        </div>` : ''}
      ${qaHtml ? `
        <div class="synth-section">
          <div class="synth-section-title">💬 Câu hỏi phổ biến</div>
          ${qaHtml}
        </div>` : ''}
      ${stuckHtml ? `
        <div class="synth-section">
          <div class="synth-section-title">🚧 Điểm học viên đang stuck</div>
          <div>${stuckHtml}</div>
        </div>` : ''}
    </div>`;
}

// ═══ MODAL ════════════════════════════════════════════════════════
function showDocModal(id, title) {
  const doc = kbDocuments.find(d => d.id === id || d.title === title);
  if (!doc) return;

  const tagColors = ['tag-purple', 'tag-blue', 'tag-green', 'tag-amber'];
  const concepts  = (doc.key_concepts || []).map((c, i) =>
    `<span class="tag ${tagColors[i % 4]}">${escHtml(c)}</span>`
  ).join('');
  const takeaways = (doc.key_takeaways || []).map(t =>
    `<li>${escHtml(t)}</li>`
  ).join('');
  const citations = (doc.citations || []).map(c =>
    `<span class="citation-chip">${escHtml(c)}</span>`
  ).join('');

  document.getElementById('modalContent').innerHTML = `
    <div class="analysis-card" style="margin:0;">
      <div class="analysis-card-header">
        <div class="analysis-card-title">
          ${docIcon(doc.type)} ${escHtml(doc.title)}
        </div>
        <div class="analysis-card-meta">${escHtml(doc.module)} · ${escHtml(doc.level)}</div>
      </div>
      <div style="padding:16px;">
        <div style="margin-bottom:14px;">
          <div class="analysis-section-title">Tóm tắt</div>
          <div class="message-text">${escHtml(doc.summary || '')}</div>
        </div>
        <div style="margin-bottom:14px;">
          <div class="analysis-section-title">Khái niệm chính</div>
          <div class="tags-row">${concepts}</div>
        </div>
        <div style="margin-bottom:14px;">
          <div class="analysis-section-title">Key Takeaways</div>
          <ul class="takeaway-list">${takeaways}</ul>
        </div>
        ${doc.reliability ? `
          <div style="margin-bottom:14px;">
            <div class="analysis-section-title">Độ tin cậy</div>
            <span class="tag tag-green">🟢 ${escHtml(doc.reliability)}</span>
          </div>` : ''}
      </div>
      <div class="analysis-card-footer">
        <div class="citations-row">${citations}</div>
        <button class="btn-primary" onclick="closeModal(); askAboutDoc('${escHtml(doc.title)}')">
          💬 Hỏi về tài liệu này
        </button>
      </div>
    </div>`;

  document.getElementById('modalOverlay').classList.add('show');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('show');
}

// ═══ TOAST ════════════════════════════════════════════════════════
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type]}</span> ${escHtml(message)}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = '300ms ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ═══ UTILS ════════════════════════════════════════════════════════
function setLoading(state) {
  isLoading = state;
  const btn = document.getElementById('sendBtn');
  if (btn) btn.disabled = state;
}

function escHtml(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function markdownToHtml(text) {
  if (!text) return '';
  return escHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(124,58,237,0.12);padding:1px 5px;border-radius:4px;font-size:12px;">$1</code>')
    .replace(/^• (.*)/gm, '<li>$1</li>')
    .replace(/^- (.*)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');
}

function docIcon(type) {
  const icons = { transcript: '📝', slide: '📊', paper: '📄', code: '💻', blog: '📰' };
  return icons[type] || '📄';
}

function currentTime() {
  return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}
