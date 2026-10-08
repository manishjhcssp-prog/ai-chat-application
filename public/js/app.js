/**
 * NEXUS AI CHAT STUDIO - CLIENT APPLICATION CONTROLLER
 * Module 3: LLM APIs & Application Development
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Cost Tracker
  const costTracker = new ClientCostTracker(0.50);

  // State Management
  let sessions = [];
  let currentSessionId = null;
  let isGenerating = false;
  let customApiKey = localStorage.getItem('nexus_user_api_key') || '';

  // DOM Elements
  const messagesContainer = document.getElementById('messagesContainer');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const sessionsList = document.getElementById('sessionsList');
  const btnNewChat = document.getElementById('btnNewChat');
  const modelSelect = document.getElementById('modelSelect');
  const personaSelect = document.getElementById('personaSelect');
  const tempSlider = document.getElementById('tempSlider');
  const tempValue = document.getElementById('tempValue');
  const tokensSlider = document.getElementById('tokensSlider');
  const tokensValue = document.getElementById('tokensValue');
  const structuredModeToggle = document.getElementById('structuredModeToggle');
  const activePersonaTag = document.getElementById('activePersonaTag');
  const contextTokensDisplay = document.getElementById('contextTokensDisplay');
  const totalCostDisplay = document.getElementById('totalCostDisplay');
  const hudPill = document.getElementById('hudPill');
  const budgetFill = document.getElementById('budgetFill');
  const budgetText = document.getElementById('budgetText');

  // Modals
  const settingsBtn = document.getElementById('settingsBtn');
  const settingsModal = document.getElementById('settingsModal');
  const closeSettingsBtn = document.getElementById('closeSettingsBtn');
  const saveSettingsBtn = document.getElementById('saveSettingsBtn');
  const apiKeyInput = document.getElementById('apiKeyInput');

  const costModal = document.getElementById('costModal');
  const closeCostBtn = document.getElementById('closeCostBtn');
  const costTableBody = document.getElementById('costTableBody');
  const resetLedgerBtn = document.getElementById('resetLedgerBtn');

  // --- Session Management ---
  function loadSessions() {
    const raw = localStorage.getItem('nexus_chat_sessions');
    if (raw) {
      try {
        sessions = JSON.parse(raw);
      } catch (e) {
        sessions = [];
      }
    }
    if (!sessions || sessions.length === 0) {
      createNewSession('Default Workspace');
    } else {
      currentSessionId = sessions[0].id;
      renderSessionsList();
      renderCurrentMessages();
    }
  }

  function saveSessions() {
    localStorage.setItem('nexus_chat_sessions', JSON.stringify(sessions));
  }

  function createNewSession(title = 'New Conversation') {
    const newSession = {
      id: 'session_' + Date.now(),
      title: title,
      createdAt: Date.now(),
      messages: [],
      systemInstruction: getSelectedPersonaInstruction(),
      temperature: parseFloat(tempSlider.value),
      maxTokens: parseInt(tokensSlider.value, 10),
      model: modelSelect.value,
    };
    sessions.unshift(newSession);
    currentSessionId = newSession.id;
    saveSessions();
    renderSessionsList();
    renderCurrentMessages();
    chatInput.focus();
  }

  function getCurrentSession() {
    return sessions.find(s => s.id === currentSessionId) || sessions[0];
  }

  function renderSessionsList() {
    sessionsList.innerHTML = '';
    sessions.forEach(sess => {
      const item = document.createElement('div');
      item.className = `session-item ${sess.id === currentSessionId ? 'active' : ''}`;
      item.innerHTML = `
        <span class="session-title">${escapeHtml(sess.title)}</span>
        <button class="session-del-btn" title="Delete conversation">&times;</button>
      `;

      item.querySelector('.session-title').addEventListener('click', () => {
        currentSessionId = sess.id;
        renderSessionsList();
        renderCurrentMessages();
      });

      item.querySelector('.session-del-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('Delete this conversation?')) {
          sessions = sessions.filter(s => s.id !== sess.id);
          if (sessions.length === 0) {
            createNewSession('New Conversation');
          } else {
            currentSessionId = sessions[0].id;
            saveSessions();
            renderSessionsList();
            renderCurrentMessages();
          }
        }
      });

      sessionsList.appendChild(item);
    });
  }

  // --- Persona & Parameter Handling ---
  function getSelectedPersonaInstruction() {
    const personaKey = personaSelect.value;
    const preset = window.PERSONA_PRESETS[personaKey];
    return preset ? preset.instruction : 'You are a helpful AI assistant.';
  }

  function updatePersonaDisplay() {
    const personaKey = personaSelect.value;
    const preset = window.PERSONA_PRESETS[personaKey];
    if (preset) {
      activePersonaTag.innerHTML = `<span>${preset.icon}</span> <span>${preset.name}</span>`;
      const cur = getCurrentSession();
      if (cur) {
        cur.systemInstruction = preset.instruction;
        saveSessions();
      }
    }
  }

  personaSelect.addEventListener('change', updatePersonaDisplay);

  tempSlider.addEventListener('input', () => {
    tempValue.textContent = tempSlider.value;
    const cur = getCurrentSession();
    if (cur) cur.temperature = parseFloat(tempSlider.value);
  });

  tokensSlider.addEventListener('input', () => {
    tokensValue.textContent = tokensSlider.value;
    const cur = getCurrentSession();
    if (cur) cur.maxTokens = parseInt(tokensSlider.value, 10);
  });

  // --- Markdown & Rendering Helpers ---
  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function renderMarkdown(raw) {
    if (!raw) return '';
    let parsed = escapeHtml(raw);

    // Code blocks with syntax formatting and copy button
    parsed = parsed.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const codeId = 'code_' + Math.random().toString(36).substring(2, 9);
      return `
        <div style="position: relative; margin: 10px 0;">
          <div style="display: flex; justify-content: space-between; background: #162032; padding: 4px 10px; border-radius: 6px 6px 0 0; font-size: 0.72rem; color: #94a3b8; font-family: var(--font-mono);">
            <span>${lang || 'code'}</span>
            <button onclick="navigator.clipboard.writeText(document.getElementById('${codeId}').innerText); alert('Code copied to clipboard!');" style="background: none; border: none; color: #38bdf8; cursor: pointer; font-size: 0.72rem;">Copy</button>
          </div>
          <pre style="margin: 0; border-radius: 0 0 6px 6px;"><code id="${codeId}">${code}</code></pre>
        </div>
      `;
    });

    // Inline code
    parsed = parsed.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold & Italics
    parsed = parsed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Headings
    parsed = parsed.replace(/^### (.*$)/gim, '<h3 style="font-size: 1.05rem; margin: 12px 0 6px; color: #f8fafc;">$1</h3>');
    parsed = parsed.replace(/^## (.*$)/gim, '<h2 style="font-size: 1.2rem; margin: 14px 0 8px; color: #f8fafc;">$1</h2>');
    parsed = parsed.replace(/^# (.*$)/gim, '<h1 style="font-size: 1.35rem; margin: 16px 0 10px; color: #f8fafc;">$1</h1>');

    // Bullet points
    parsed = parsed.replace(/^\s*[-*]\s+(.*$)/gim, '<li style="margin-left: 20px;">$1</li>');

    // Line breaks to paragraphs
    const paragraphs = parsed.split(/\n{2,}/).map(p => {
      if (p.startsWith('<h') || p.startsWith('<div') || p.startsWith('<li')) return p;
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    });

    return paragraphs.join('');
  }

  // --- Messages Viewport Rendering ---
  function renderCurrentMessages() {
    const session = getCurrentSession();
    messagesContainer.innerHTML = '';

    if (!session || session.messages.length === 0) {
      renderWelcomeState();
      updateMetricsHUD();
      return;
    }

    session.messages.forEach(msg => {
      appendMessageDOM(msg);
    });

    scrollToBottom();
    updateMetricsHUD();
  }

  function renderWelcomeState() {
    const div = document.createElement('div');
    div.className = 'welcome-state';
    div.innerHTML = `
      <div class="welcome-icon-ring">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2">
          <path d="M12 2a10 10 0 0 1 10 10v4a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3v-4a10 10 0 0 1 10-10z"></path>
          <path d="M8 12h.01M16 12h.01M12 16a4 4 0 0 1-4-3"></path>
        </svg>
      </div>
      <h2 class="welcome-title">Welcome to Nexus AI Studio</h2>
      <p class="welcome-subtitle">
        A production-grade LLM conversational application demonstrating multi-turn history,
        sliding context windows, structured JSON outputs, and real-time cost economics.
      </p>
      <div class="starter-chips-grid">
        <div class="starter-chip" data-prompt="Explain how sliding context windows prevent token overflow in multi-turn LLM chat.">
          <div class="starter-chip-title">Context Window Architecture</div>
          <div class="starter-chip-desc">How sliding buffers optimize memory & prevent 400 errors.</div>
        </div>
        <div class="starter-chip" data-prompt="Provide a step-by-step cost management strategy for scaling LLM applications under budget constraints.">
          <div class="starter-chip-title">API Cost Optimization</div>
          <div class="starter-chip-desc">Model tiering, prompt compression, and token economics.</div>
        </div>
        <div class="starter-chip" data-prompt="Perform a code review on a Python exponential backoff retry decorator with structured JSON analysis.">
          <div class="starter-chip-title">Structured Code Review</div>
          <div class="starter-chip-desc">Automated code audits with strict schema validation.</div>
        </div>
        <div class="starter-chip" data-prompt="Design an end-to-end multi-agent orchestration architecture for automated customer support.">
          <div class="starter-chip-title">System Architecture Design</div>
          <div class="starter-chip-desc">Explore state machines, fallback routing, and tools.</div>
        </div>
      </div>
    `;

    div.querySelectorAll('.starter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        chatInput.value = chip.getAttribute('data-prompt');
        handleSendMessage();
      });
    });

    messagesContainer.appendChild(div);
  }

  function appendMessageDOM(msg) {
    const isUser = msg.role === 'user';
    const row = document.createElement('div');
    row.className = `message-row ${isUser ? 'user-row' : 'assistant-row'}`;

    const avatar = isUser
      ? `<div class="avatar-badge user-avatar">👤</div>`
      : `<div class="avatar-badge ai-avatar">✨</div>`;

    const statsInfo = isUser
      ? `<span class="stat-tag">Tokens: ~${msg.estimatedTokens || costTracker.estimateTokens(msg.content)}</span>`
      : `<div class="meta-stats">
           <span class="stat-tag">${msg.model || 'gpt-4o-mini'}</span>
           <span class="stat-tag">${msg.totalTokens ? msg.totalTokens + ' tok' : '~' + costTracker.estimateTokens(msg.content) + ' tok'}</span>
           <span class="stat-tag" style="color: var(--accent-emerald);">$${msg.costUsd !== undefined ? msg.costUsd.toFixed(6) : '0.000000'}</span>
           ${msg.latencyMs ? `<span class="stat-tag">${msg.latencyMs}ms</span>` : ''}
         </div>
         <button class="btn-msg-action" onclick="navigator.clipboard.writeText(decodeURIComponent('${encodeURIComponent(msg.content)}')); alert('Message copied!');" title="Copy Message">📋</button>`;

    row.innerHTML = `
      ${!isUser ? avatar : ''}
      <div class="message-card">
        <div class="message-content">${isUser ? escapeHtml(msg.content).replace(/\n/g, '<br>') : renderMarkdown(msg.content)}</div>
        <div class="message-footer">
          ${statsInfo}
        </div>
      </div>
      ${isUser ? avatar : ''}
    `;

    messagesContainer.appendChild(row);
  }

  function appendLoadingIndicator() {
    const row = document.createElement('div');
    row.id = 'loadingRow';
    row.className = 'message-row assistant-row';
    row.innerHTML = `
      <div class="avatar-badge ai-avatar">✨</div>
      <div class="message-card" style="padding: 10px 14px;">
        <div class="typing-indicator">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
    scrollToBottom();
  }

  function removeLoadingIndicator() {
    const row = document.getElementById('loadingRow');
    if (row) row.remove();
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function updateMetricsHUD() {
    const session = getCurrentSession();
    let currentTokens = 0;
    if (session) {
      currentTokens = costTracker.estimateTokens(session.systemInstruction || '');
      session.messages.forEach(m => {
        currentTokens += m.estimatedTokens || costTracker.estimateTokens(m.content);
      });
    }

    contextTokensDisplay.textContent = currentTokens;
    totalCostDisplay.textContent = `$${costTracker.getTotalCost().toFixed(5)}`;
    hudPill.querySelector('.stat-highlight').textContent = `$${costTracker.getTotalCost().toFixed(5)}`;

    const usedPct = costTracker.getBudgetUtilizationPercent();
    budgetFill.style.width = `${usedPct}%`;
    budgetText.textContent = `$${costTracker.getTotalCost().toFixed(4)} / $${costTracker.budgetUsd.toFixed(2)} (${usedPct}%)`;

    if (usedPct >= 90) {
      budgetFill.style.background = 'var(--accent-rose)';
    } else if (usedPct >= 70) {
      budgetFill.style.background = 'var(--accent-amber)';
    } else {
      budgetFill.style.background = 'var(--gradient-brand)';
    }
  }

  // --- Send Message & API Call ---
  async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text || isGenerating) return;

    const session = getCurrentSession();
    if (!session) return;

    // Check budget cap
    if (costTracker.isBudgetExceeded()) {
      alert(`Session budget of $${costTracker.budgetUsd.toFixed(2)} has been reached! You can reset the cost ledger in the Cost HUD.`);
      return;
    }

    // Append User Message
    const userEstimatedTokens = costTracker.estimateTokens(text);
    const userMsg = {
      role: 'user',
      content: text,
      timestamp: Date.now(),
      estimatedTokens: userEstimatedTokens,
    };
    session.messages.push(userMsg);

    // Auto update session title if first turn
    if (session.messages.length === 1) {
      session.title = text.slice(0, 30) + (text.length > 30 ? '...' : '');
      renderSessionsList();
    }

    saveSessions();
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Clear welcome state if present
    const welcome = messagesContainer.querySelector('.welcome-state');
    if (welcome) welcome.remove();

    appendMessageDOM(userMsg);
    appendLoadingIndicator();
    scrollToBottom();

    isGenerating = true;
    sendBtn.disabled = true;

    // Context Window Sliding: keep system instruction + last 10 messages for API payload
    const historyPayload = session.messages.slice(-10).map(m => ({
      role: m.role,
      content: m.content,
    }));

    const requestBody = {
      messages: historyPayload,
      model: modelSelect.value,
      system_instruction: structuredModeToggle.checked
        ? window.PERSONA_PRESETS.json_analyst.instruction
        : session.systemInstruction || getSelectedPersonaInstruction(),
      temperature: parseFloat(tempSlider.value),
      max_tokens: parseInt(tokensSlider.value, 10),
      api_key: customApiKey || undefined,
    };

    try {
      // Primary: Post to /api/chat
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`API returned HTTP ${response.status}`);
      }

      const data = await response.json();
      removeLoadingIndicator();

      const asstMsg = {
        role: 'assistant',
        content: data.content,
        timestamp: Date.now(),
        model: data.model || modelSelect.value,
        promptTokens: data.prompt_tokens || userEstimatedTokens,
        completionTokens: data.completion_tokens || costTracker.estimateTokens(data.content),
        totalTokens: data.total_tokens || (userEstimatedTokens + costTracker.estimateTokens(data.content)),
        costUsd: data.cost_usd !== undefined ? data.cost_usd : costTracker.calculateTurnCost(modelSelect.value, userEstimatedTokens, costTracker.estimateTokens(data.content)),
        latencyMs: data.latency_ms || 120,
      };

      session.messages.push(asstMsg);
      saveSessions();
      appendMessageDOM(asstMsg);

      // Record Turn in Cost Tracker
      costTracker.recordTurn(
        asstMsg.model,
        asstMsg.promptTokens,
        asstMsg.completionTokens,
        asstMsg.latencyMs
      );

      updateMetricsHUD();
    } catch (err) {
      console.warn('Backend API connection issue, running client-side simulation:', err);
      // Fallback: Client-side intelligent simulation
      setTimeout(() => {
        removeLoadingIndicator();
        const fallbackText = generateClientFallback(text, session.systemInstruction);
        const pTok = userEstimatedTokens;
        const cTok = costTracker.estimateTokens(fallbackText);
        const cost = costTracker.calculateTurnCost(modelSelect.value, pTok, cTok);

        const asstMsg = {
          role: 'assistant',
          content: fallbackText,
          timestamp: Date.now(),
          model: modelSelect.value + ' (Simulated)',
          promptTokens: pTok,
          completionTokens: cTok,
          totalTokens: pTok + cTok,
          costUsd: cost,
          latencyMs: 90,
        };

        session.messages.push(asstMsg);
        saveSessions();
        appendMessageDOM(asstMsg);

        costTracker.recordTurn(asstMsg.model, pTok, cTok, 90);
        updateMetricsHUD();
      }, 500);
    } finally {
      isGenerating = false;
      sendBtn.disabled = false;
      scrollToBottom();
      chatInput.focus();
    }
  }

  function generateClientFallback(userInput, systemPrompt) {
    const lower = userInput.toLowerCase();
    if (lower.includes('sliding') || lower.includes('window') || lower.includes('context')) {
      return `**Context Window Management Architecture:**

1. **The Problem:** LLMs have finite context limits (e.g. 8k, 32k, 128k tokens). Sending unbounded history causes exponential token costs and eventually HTTP 400 ContextLengthExceeded errors.
2. **The Sliding Window Solution:**
   - Always retain the **System Prompt** at index 0 (anchoring the persona).
   - Maintain a sliding window of the most recent $N$ dialog pairs.
   - When token budget approaches the ceiling, prune oldest user/assistant turns.
3. **Summarization Compression:** In advanced setups, older turns are summarized into a concise state paragraph before ejection.`;
    }
    return `I received your inquiry regarding **"${userInput.slice(0, 50)}..."**.

- **Active Model:** \`${modelSelect.value}\`
- **Temperature:** \`${tempSlider.value}\` | **Max Output:** \`${tokensSlider.value}\` tokens
- **Context Preservation:** Dialogue turns are persisted locally in your browser session.

Feel free to test additional custom instructions or switch personas using the sidebar!`;
  }

  // --- Event Listeners ---
  sendBtn.addEventListener('click', handleSendMessage);

  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
  });

  btnNewChat.addEventListener('click', () => createNewSession());

  document.getElementById('btnClearChat').addEventListener('click', () => {
    const cur = getCurrentSession();
    if (cur && confirm('Clear messages in this conversation?')) {
      cur.messages = [];
      saveSessions();
      renderCurrentMessages();
    }
  });

  // Settings Modal Handlers
  settingsBtn.addEventListener('click', () => {
    apiKeyInput.value = customApiKey;
    settingsModal.classList.add('open');
  });

  closeSettingsBtn.addEventListener('click', () => {
    settingsModal.classList.remove('open');
  });

  saveSettingsBtn.addEventListener('click', () => {
    customApiKey = apiKeyInput.value.trim();
    if (customApiKey) {
      localStorage.setItem('nexus_user_api_key', customApiKey);
      alert('API key stored securely in your browser localStorage!');
    } else {
      localStorage.removeItem('nexus_user_api_key');
      alert('Custom API key removed. Using simulation/server mode.');
    }
    settingsModal.classList.remove('open');
  });

  // Cost HUD Modal Handlers
  hudPill.addEventListener('click', () => {
    renderCostTable();
    costModal.classList.add('open');
  });

  closeCostBtn.addEventListener('click', () => {
    costModal.classList.remove('open');
  });

  resetLedgerBtn.addEventListener('click', () => {
    if (confirm('Reset cost and token ledger?')) {
      costTracker.resetLedger();
      renderCostTable();
      updateMetricsHUD();
    }
  });

  function renderCostTable() {
    costTableBody.innerHTML = '';
    if (costTracker.records.length === 0) {
      costTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No API turns recorded yet.</td></tr>';
      return;
    }

    costTracker.records.slice(-20).reverse().forEach(r => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>#${r.id}</td>
        <td>${r.model}</td>
        <td>${r.promptTokens}</td>
        <td>${r.completionTokens}</td>
        <td style="color: var(--accent-emerald); font-weight: 600;">$${r.costUsd.toFixed(6)}</td>
        <td>${r.latencyMs}ms</td>
      `;
      costTableBody.appendChild(row);
    });
  }

  // Close modals on outside click
  [settingsModal, costModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('open');
    });
  });

  // Initial Load
  loadSessions();
  updatePersonaDisplay();
  updateMetricsHUD();
});
