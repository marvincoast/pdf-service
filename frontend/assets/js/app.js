/**
 * PDF AI — Main Application Logic
 * Upload, analysis, HUD rendering, and interactions
 */

// === 3D PARALLAX ===
const mainCard = document.getElementById('mainCard');
if (mainCard) {
  document.addEventListener('mousemove', (e) => {
    const rect = mainCard.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -3;
    const rotateY = ((x - centerX) / centerX) * 3;
    mainCard.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
  });
  document.addEventListener('mouseleave', () => {
    mainCard.style.transform = 'rotateX(0) rotateY(0)';
  });
}

// === PAGE TRANSITIONS ===
document.querySelectorAll('.nav-link[href]').forEach(link => {
  link.addEventListener('click', (e) => {
    const href = link.getAttribute('href');
    if (href && href.endsWith('.html')) {
      e.preventDefault();
      document.body.classList.add('page-exit');
      setTimeout(() => window.location.href = href, 500);
    }
  });
});

if (sessionStorage.getItem('page-transition') === 'enter') {
  document.body.classList.add('page-enter');
  sessionStorage.removeItem('page-transition');
}

// === DRAG & DROP + FORM INIT ===
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('pdfFile');
const fileLabel = document.getElementById('fileLabel');
const pdfForm  = document.getElementById('pdfForm');

// Attach form submit listener (more reliable than inline onsubmit)
if (pdfForm) {
  pdfForm.addEventListener('submit', handleUpload);
  console.log('[PDF AI] Form listener attached ✅');
} else {
  console.error('[PDF AI] #pdfForm not found!');
}

if (dropZone && fileInput) {
  ['dragenter', 'dragover'].forEach(evt =>
    dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('dragover'); })
  );
  ['dragleave', 'drop'].forEach(evt =>
    dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('dragover'); })
  );
  dropZone.addEventListener('drop', e => {
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      updateFileLabel(fileInput.files[0]);
    }
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) updateFileLabel(fileInput.files[0]);
  });
}

function updateFileLabel(file) {
  if (fileLabel) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    fileLabel.innerHTML = `<span class="upload-selected">✅ ${file.name}</span> <span style="color:var(--text-muted)">(${sizeMB} MB)</span>`;
  }
}

// === PROGRESS BAR ===
let progressInterval = null;

function showProgress(step, percent) {
  const container = document.getElementById('progressContainer');
  const fill = document.getElementById('progressFill');
  const label = document.getElementById('progressLabel');
  if (container) container.style.display = 'block';
  if (fill) fill.style.width = percent + '%';
  if (label) label.textContent = step;
}

function startProgressAnimation() {
  const steps = [
    { text: 'Lendo PDF...', pct: 15 },
    { text: 'Extraindo texto...', pct: 30 },
    { text: 'Classificando documento...', pct: 45 },
    { text: 'Analisando com IA...', pct: 60 },
    { text: 'Processando resultado...', pct: 75 },
    { text: 'Finalizando análise...', pct: 90 },
  ];
  let i = 0;
  showProgress(steps[0].text, steps[0].pct);
  progressInterval = setInterval(() => {
    i++;
    if (i < steps.length) {
      showProgress(steps[i].text, steps[i].pct);
    }
  }, 4000);
}

function stopProgress(success) {
  clearInterval(progressInterval);
  showProgress(success ? '✅ Concluído!' : '❌ Falhou', 100);
  setTimeout(() => {
    const container = document.getElementById('progressContainer');
    if (container) container.style.display = 'none';
  }, 1500);
}

// === UPLOAD & ANALYSIS ===
let lastResponse = null;

async function handleUpload(e) {
  e.preventDefault();
  if (!fileInput.files[0]) return;

  const btn = document.getElementById('submitBtn');
  const status = document.getElementById('statusMsg');
  const results = document.getElementById('resultsArea');

  // UI: processing state
  btn.disabled = true;
  btn.textContent = 'Analisando...';
  btn.classList.add('processing');
  status.className = 'status-msg info';
  status.textContent = 'Iniciando pipeline de análise...';
  results.style.display = 'none';

  startProgressAnimation();

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  try {
    const res = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await res.json();

    if (res.ok && data.extracted_data) {
      lastResponse = data;
      status.className = 'status-msg success';
      status.textContent = '✅ Análise concluída com sucesso';
      stopProgress(true);
      renderHUD(data);
      results.style.display = 'flex';
    } else {
      status.className = 'status-msg error';
      status.textContent = `❌ ${data.error || 'Erro desconhecido'}`;
      stopProgress(false);
    }
  } catch (err) {
    console.error('[PDF AI] Erro no upload:', err);
    status.className = 'status-msg error';
    status.textContent = '⚠️ Falha na conexão. Verifique se o backend está rodando.';
    stopProgress(false);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Iniciar Análise';
    btn.classList.remove('processing');
  }
}

// === HUD RENDERING ===
function renderHUD(data) {
  const ext = data.extracted_data || {};

  // Header badges
  document.getElementById('docBadge').textContent = data.document_type_label || 'DOCUMENTO';

  const methodBadge = document.getElementById('methodBadge');
  if (methodBadge) {
    if (data.analysis_method === 'ai') {
      methodBadge.textContent = '🤖 IA';
      methodBadge.className = 'method-badge ai';
    } else {
      methodBadge.textContent = '⚡ Regex';
      methodBadge.className = 'method-badge fallback';
    }
  }

  // Stats
  const statsHtml = `
    <span class="stat">⏱ <span class="stat-value">${data.processing_time_sec}s</span></span>
    <span class="stat">📄 <span class="stat-value">${data.pages} pág</span></span>
    <span class="stat">📝 <span class="stat-value">${(data.text_length / 1000).toFixed(1)}k chars</span></span>
    <span class="stat">🎯 <span class="stat-value">${data.confidence}%</span></span>
  `;
  document.getElementById('hudStats').innerHTML = statsHtml;

  // Summary card
  const summaryEl = document.getElementById('summaryText');
  if (summaryEl) {
    summaryEl.textContent = ext.detailed_summary || ext.summary_preview || 'Resumo não disponível nesta análise.';
  }

  // Build HUD cards
  let html = '';

  // Key Findings
  if (ext.key_findings?.length) {
    html += `<div class="hud-card" style="grid-column: 1 / -1">
      <span class="hud-label">🔍 Achados Principais</span>
      <ul class="findings-list">${ext.key_findings.map(f => `<li>${esc(f)}</li>`).join('')}</ul>
    </div>`;
  }

  // Personal info / identification
  const name = ext.personal_info?.name || ext.student_name || ext.account_holder || ext.patient_name;
  if (name) {
    html += makeCard('👤 Identificação', name);
  }

  // Dynamic fields based on doc type
  if (ext.personal_info?.emails?.length) html += card('📧 Emails', ext.personal_info.emails.join(', '));
  if (ext.personal_info?.phones?.length) html += card('📱 Telefones', ext.personal_info.phones.join(', '));
  if (ext.institution) html += card('🏛 Instituição', ext.institution);
  if (ext.course) html += card('📚 Curso', ext.course);
  if (ext.doctor_info?.name) html += card('👨‍⚕️ Médico', `${ext.doctor_info.name} ${ext.doctor_info?.crm ? '(CRM: ' + ext.doctor_info.crm + ')' : ''}`);
  if (ext.bank_name) html += card('🏦 Banco', ext.bank_name);
  if (ext.invoice_number) html += card('📑 Nota Fiscal', ext.invoice_number);
  if (ext.case_number) html += card('⚖️ Processo', ext.case_number);

  // Skills
  if (ext.skills?.length || ext.skills_found?.length) {
    const skills = ext.skills || ext.skills_found;
    html += `<div class="hud-card">
      <span class="hud-label">💡 Competências</span>
      <div class="entity-tags">${skills.slice(0, 12).map(s => `<span class="entity-tag">${esc(s)}</span>`).join('')}</div>
    </div>`;
  }

  // Experience
  if (ext.experience?.length) {
    html += `<div class="hud-card">
      <span class="hud-label">💼 Experiência</span>
      <ul class="hud-list">${ext.experience.slice(0, 5).map(x =>
        `<li>${esc(x.role || '')} ${x.company ? '@ ' + esc(x.company) : ''} ${x.period ? '(' + esc(x.period) + ')' : ''}</li>`
      ).join('')}</ul>
    </div>`;
  }

  // Education
  if (ext.education?.length) {
    html += `<div class="hud-card">
      <span class="hud-label">🎓 Formação</span>
      <ul class="hud-list">${ext.education.slice(0, 4).map(x =>
        `<li>${esc(x.degree || '')} — ${esc(x.institution || '')} ${x.year ? '(' + esc(x.year) + ')' : ''}</li>`
      ).join('')}</ul>
    </div>`;
  }

  // Medications
  if (ext.medications?.length) {
    html += `<div class="hud-card">
      <span class="hud-label">💊 Medicamentos</span>
      <ul class="hud-list">${ext.medications.slice(0, 8).map(m => {
        if (typeof m === 'object' && m.name) return `<li>${esc(m.name)} ${m.dosage ? '— ' + esc(m.dosage) : ''}</li>`;
        if (Array.isArray(m)) return `<li>${m.map(esc).join(' ')}</li>`;
        return `<li>${esc(String(m))}</li>`;
      }).join('')}</ul>
    </div>`;
  }

  // Items (invoices)
  if (ext.items?.length) {
    html += `<div class="hud-card">
      <span class="hud-label">📦 Itens</span>
      <ul class="hud-list">${ext.items.slice(0, 6).map(i =>
        `<li>${esc(i.description || '')} ${i.total ? '— ' + esc(i.total) : ''}</li>`
      ).join('')}</ul>
    </div>`;
  }

  // Monetary values
  if (ext.values_found?.length || ext.total_value) {
    const vals = ext.values_found || [ext.total_value];
    html += `<div class="hud-card">
      <span class="hud-label">💰 Valores</span>
      <ul class="hud-list">${vals.slice(0, 6).map(v => `<li>${esc(v)}</li>`).join('')}</ul>
    </div>`;
  }

  // Dates
  const dates = ext.dates_found || ext.dates || ext.dates_mentioned;
  if (dates?.length) {
    html += `<div class="hud-card">
      <span class="hud-label">📅 Datas Encontradas</span>
      <div class="entity-tags">${dates.slice(0, 8).map(d => `<span class="entity-tag">${esc(d)}</span>`).join('')}</div>
    </div>`;
  }

  // Recommendations
  if (ext.recommendations?.length) {
    html += `<div class="hud-card" style="grid-column: 1 / -1">
      <span class="hud-label">💡 Recomendações</span>
      <ul class="findings-list">${ext.recommendations.map(r => `<li>${esc(r)}</li>`).join('')}</ul>
    </div>`;
  }

  // Note (analysis method)
  if (ext.note) {
    html += `<div class="hud-card">
      <span class="hud-label">ℹ️ Observação</span>
      <div class="hud-value" style="font-size:0.8rem;opacity:0.7">${esc(ext.note)}</div>
    </div>`;
  }

  document.getElementById('hudGrid').innerHTML = html ||
    '<div class="hud-card"><div class="hud-value">Dados extraídos com sucesso.</div></div>';
}

function makeCard(label, value) {
  return `<div class="hud-card"><span class="hud-label">${label}</span><div class="hud-value">${esc(String(value))}</div></div>`;
}

function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// === ACTION BUTTONS ===
function copyJSON() {
  if (!lastResponse) return;
  navigator.clipboard.writeText(JSON.stringify(lastResponse, null, 2));
  const btn = event.currentTarget;
  const original = btn.textContent;
  btn.textContent = '✅ Copiado!';
  setTimeout(() => btn.textContent = original, 2000);
}

function downloadJSON() {
  if (!lastResponse) return;
  const blob = new Blob([JSON.stringify(lastResponse, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `analise-${lastResponse.filename || 'pdf'}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function newAnalysis() {
  document.getElementById('resultsArea').style.display = 'none';
  document.getElementById('statusMsg').textContent = '';
  document.getElementById('pdfForm').reset();
  if (fileLabel) fileLabel.textContent = 'Suporta: Currículos, Notas Fiscais, Extratos, Certificados, Receitas...';
  lastResponse = null;
}
