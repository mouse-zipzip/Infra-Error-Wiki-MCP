const state = {
  pages: [],
  selectedSlug: "",
  selectedContent: "",
  conversation: [],
};

const nodes = {
  workspace: document.querySelector("#workspace"),
  status: document.querySelector("#viewerStatus"),
  search: document.querySelector("#search"),
  resetSearch: document.querySelector("#resetSearch"),
  toggleLeft: document.querySelector("#toggleLeft"),
  toggleRight: document.querySelector("#toggleRight"),
  pageList: document.querySelector("#pageList"),
  article: document.querySelector("#article"),
  pagePath: document.querySelector("#pagePath"),
  errorInput: document.querySelector("#errorInput"),
  runAgent: document.querySelector("#runAgent"),
  agentResult: document.querySelector("#agentResult"),
  conversationLog: document.querySelector("#conversationLog"),
};

const icons = {
  incidents: "I",
};

async function loadViewer() {
  try {
    const pages = await fetchWikiIndex();
    state.pages = pages.map(normalizePage);
    state.selectedSlug = "";
    nodes.status.textContent = `문제 유형 ${state.pages.length}개 불러옴`;
    renderList();
  } catch (error) {
    nodes.status.textContent = "wiki/index.json을 불러오지 못했습니다";
    nodes.article.innerHTML = `
      <p class="error">${escapeHtml(koreanFetchError(error))}</p>
      <p class="empty">프로젝트 루트에서 <code>python tools/viewer_server.py</code>를 실행한 뒤 <code>http://127.0.0.1:8000/</code>로 접속하세요.</p>
    `;
    nodes.agentResult.textContent = "프로젝트 루트에서 정적 서버를 실행해야 문제 유형 wiki를 읽을 수 있습니다.";
    state.conversation = [
      {
        role: "시스템",
        text: "위키 파일을 읽으려면 프로젝트 루트에서 정적 서버를 실행해야 합니다.",
      },
    ];
    renderConversation();
  }
}

async function fetchWikiIndex() {
  try {
    return await fetchJson("../wiki/index.json");
  } catch (error) {
    if (String(error.message).includes("(404)")) {
      return fetchJson("../wiki/index.example.json");
    }
    throw error;
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not read ${url} (${response.status})`);
  }
  return response.json();
}

async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not read ${url} (${response.status})`);
  }
  return response.text();
}

function normalizePage(page) {
  return {
    slug: String(page.slug || ""),
    title: String(page.title || page.slug || "제목 없음"),
    category: String(page.category || "incidents"),
    path: String(page.path || ""),
    tags: Array.isArray(page.tags) ? page.tags.map(String) : [],
    symptoms: Array.isArray(page.symptoms) ? page.symptoms.map(String) : [],
    case_count: Number(page.case_count || 0),
    source_paths: Array.isArray(page.source_paths) ? page.source_paths.map(String) : [],
    status: String(page.status || "draft"),
    updated_at: String(page.updated_at || ""),
  };
}

async function selectPage(slug) {
  const page = state.pages.find(item => item.slug === slug);
  if (!page) {
    nodes.article.innerHTML = '<p class="empty">아직 정리된 문제 유형이 없습니다. raw 오류 기록이 추가되면 이곳에 위키가 표시됩니다.</p>';
    nodes.pagePath.textContent = "선택한 문제 유형 없음";
    return;
  }

  state.selectedSlug = slug;
  renderList();
  nodes.pagePath.textContent = page.path;
  nodes.article.innerHTML = '<p class="empty">문제 유형 문서를 불러오는 중입니다.</p>';

  try {
    const markdown = await fetchText(`../${page.path}`);
    state.selectedContent = markdown;
    renderArticle(page, markdown);
    renderAgentTrace(page, "page-selected");
  } catch (error) {
    nodes.article.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

function renderList() {
  const query = nodes.search.value.trim().toLowerCase();
  const filtered = state.pages.filter(page => {
    const haystack = [
      page.title,
      page.category,
      page.status,
      page.updated_at,
      page.tags.join(" "),
      page.symptoms.join(" "),
      page.source_paths.join(" "),
      page.path,
    ].join(" ").toLowerCase();
    return !query || haystack.includes(query);
  });

  if (!filtered.length) {
    nodes.pageList.innerHTML = state.pages.length
      ? '<p class="empty">검색 결과가 없습니다. 다른 오류 메시지, 증상, 태그로 검색해 보세요.</p>'
      : '<p class="empty">아직 등록된 문제 유형이 없습니다.</p>';
    return;
  }

  nodes.pageList.innerHTML = filtered.map(page => `
    <button class="page-button ${page.slug === state.selectedSlug ? "active" : ""}" data-slug="${escapeHtml(page.slug)}">
      <span class="type-icon">${icons[page.category] || "?"}</span>
      <span>
        <span class="page-title">${escapeHtml(page.title)}</span>
        <span class="page-meta">${escapeHtml(categoryLabel(page.category))} | 사례 ${page.case_count}개 | 증상 ${page.symptoms.length}개</span>
      </span>
    </button>
  `).join("");

  nodes.pageList.querySelectorAll(".page-button").forEach(button => {
    button.addEventListener("click", () => selectPage(button.dataset.slug));
  });
}

function renderArticle(page, markdown) {
  const body = markdown.replace(/^# .+(\r?\n)+/, "");
  nodes.article.innerHTML = `
    <h1 class="reader-title">${escapeHtml(page.title)}</h1>
    <div class="tag-row">
      ${page.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}
    </div>
    ${renderMarkdown(body)}
  `;
}

function renderMarkdown(markdown) {
  const lines = markdown.split(/\r?\n/);
  let html = "";
  let listType = "";
  let inCode = false;
  let codeBuffer = [];
  let tableBuffer = [];

  const closeList = () => {
    if (listType) { html += `</${listType}>`; listType = ""; }
  };
  const closeCode = () => {
    if (inCode) {
      html += `<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`;
      codeBuffer = []; inCode = false;
    }
  };
  const flushTable = () => {
    if (!tableBuffer.length) return;
    const rows = tableBuffer.map(row =>
      row.split("|").map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1)
    );
    const headers = rows[0] || [];
    const dataRows = rows.slice(1);
    html += '<ul class="table-as-list">';
    dataRows.forEach(row => {
      const label = row[0] || "";
      const details = row.slice(1).map((cell, index) => {
        const header = headers[index + 1] ? `${headers[index + 1]}: ` : "";
        return `${header}${cell}`;
      }).filter(Boolean).join(" / ");
      html += `<li>${inlineMarkdown(escapeHtml(label ? `${label}: ${details}` : details))}</li>`;
    });
    html += "</ul>";
    tableBuffer = [];
  };

  lines.forEach(line => {
    if (line.startsWith("```")) {
      if (inCode) { closeCode(); } else { closeList(); flushTable(); inCode = true; }
      return;
    }
    if (inCode) { codeBuffer.push(line); return; }

    // 테이블 구분선 (|---|---| 형태) 스킵
    if (/^\|[\s\-|:]+\|$/.test(line.trim())) return;

    // 테이블 행
    if (/^\|.+\|$/.test(line.trim())) {
      closeList();
      tableBuffer.push(line.trim());
      return;
    }
    flushTable();

    if (/^-{3,}$/.test(line.trim())) {
      closeList();
      html += '<hr class="section-divider">';
    } else if (line.startsWith("### ")) {
      closeList();
      html += `<h3>${inlineMarkdown(escapeHtml(line.slice(4)))}</h3>`;
    } else if (line.startsWith("## ")) {
      closeList();
      html += `<h2>${inlineMarkdown(escapeHtml(line.slice(3)))}</h2>`;
    } else if (/^[-*] \[[ xX]\] /.test(line)) {
      if (listType !== "ul") { closeList(); html += "<ul>"; listType = "ul"; }
      const checked = /\[[xX]\]/.test(line) ? "checked" : "";
      html += `<li><input type="checkbox" disabled ${checked}> ${inlineMarkdown(escapeHtml(line.replace(/^[-*] \[[ xX]\] /, "")))}</li>`;
    } else if (/^(\s*)[-*] /.test(line)) {
      if (listType !== "ul") { closeList(); html += "<ul>"; listType = "ul"; }
      html += `<li>${inlineMarkdown(escapeHtml(line.replace(/^\s*[-*] /, "")))}</li>`;
    } else if (/^\d+\. /.test(line)) {
      if (listType !== "ol") { closeList(); html += "<ol>"; listType = "ol"; }
      html += `<li>${inlineMarkdown(escapeHtml(line.replace(/^\d+\. /, "")))}</li>`;
    } else if (/^(증상|원인|확인|해결|사례|요약):$/.test(line.trim())) {
      closeList();
      html += `<p class="cause-label">${escapeHtml(line.trim())}</p>`;
    } else if (line.trim()) {
      closeList();
      html += `<p>${inlineMarkdown(escapeHtml(line))}</p>`;
    } else {
      closeList();
    }
  });

  closeCode(); flushTable(); closeList();
  return html || '<p class="empty">문서 내용이 비어 있습니다.</p>';
}

function inlineMarkdown(value) {
  return value
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function inlineCode(value) {
  return inlineMarkdown(value);
}

async function runAgent() {
  const message = nodes.errorInput.value.trim();
  if (!message) {
    nodes.agentResult.textContent = "분석할 에러 메시지를 입력하세요.";
    return;
  }

  appendConversation("사용자", message, "user");
  nodes.agentResult.innerHTML = "오류 메시지를 분석하는 중입니다.";

  try {
    const result = await requestSuggestFix(message);
    await renderSuggestFixResult(result);
  } catch (error) {
    nodes.agentResult.innerHTML = `<strong>분석 실패:</strong> ${escapeHtml(koreanApiError(error))}`;
    appendConversation("분석 결과", koreanApiError(error), "agent-reply");
  }
}

async function requestSuggestFix(message) {
  const response = await fetch("../api/suggest-fix", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "분석 요청에 실패했습니다.");
  }
  return data;
}

async function renderSuggestFixResult(result) {
  const message = String(result.message || "");
  const matchedType = result.matched_problem_type;
  const relatedPages = Array.isArray(result.related_pages) ? result.related_pages : [];
  const checks = Array.isArray(result.recommended_checks) ? result.recommended_checks : [];
  const strategies = Array.isArray(result.resolution_strategy) ? result.resolution_strategy : [];
  const cases = Array.isArray(result.related_cases) ? result.related_cases : [];

  if (matchedType && relatedPages[0]?.slug) {
    await selectPage(relatedPages[0].slug);
    const checksHtml = checks.length
      ? `<ol class="result-checklist">${checks.map(c => `<li>${escapeHtml(c)}</li>`).join("")}</ol>`
      : `<p class="result-value">위키 문서를 확인하세요.</p>`;
    nodes.agentResult.innerHTML = `
      <div class="result-section">
        <div class="result-label">관련 문제 유형</div>
        <div class="result-value-strong">${escapeHtml(matchedType)}</div>
      </div>
      <div class="result-section">
        <div class="result-label">추천 확인 순서</div>
        ${checksHtml}
      </div>
      <div class="result-section">
        <div class="result-label">과거 발생 사례</div>
        <div class="result-badge">${cases.length}개</div>
      </div>
    `;
    appendConversation("분석 결과", `${matchedType} 문제 유형과 연결했습니다.`, "agent-reply");
  } else if (!state.pages.length) {
    nodes.agentResult.innerHTML = "<strong>분석 불가:</strong> 아직 참고할 위키가 없습니다.";
    appendConversation(
      "분석 결과",
      "아직 참고할 위키가 없어 이 질문을 분석할 수 없습니다. 오류 기록이 추가되면 관련 문제 유형과 확인 순서를 보여줄 수 있습니다.",
      "agent-reply"
    );
    return;
  } else {
    renderNoMatchState(message);
    appendConversation(
      "분석 결과",
      "현재 위키에서 이 오류와 연결되는 문제 유형을 찾지 못했습니다. 새 오류 기록으로 남기면 이후 비슷한 문제가 들어왔을 때 연결할 수 있습니다.",
      "agent-reply"
    );
    return;
  }

}

function renderAgentTrace(page, mode) {
  if (mode !== "triage") return;
  const checks = recommendedChecks(page);
  nodes.agentResult.innerHTML = `
    <div class="result-section">
      <div class="result-label">관련 문제 유형</div>
      <div class="result-value-strong">${escapeHtml(page.title)}</div>
    </div>
    <div class="result-section">
      <div class="result-label">추천 확인 순서</div>
      <ol class="result-checklist">${checks.map(c => `<li>${escapeHtml(c)}</li>`).join("")}</ol>
    </div>
    <div class="result-section">
      <div class="result-label">과거 발생 사례</div>
      <div class="result-badge">${page.case_count}개</div>
    </div>
  `;
}

function renderNoMatchState(message) {
  nodes.agentResult.innerHTML = "<strong>관련 지식 없음:</strong> 현재 위키에서 가까운 문제 유형을 찾지 못했습니다.";
}

function recommendedChecks(page) {
  if (page.slug.includes("nginx")) {
    return ["업스트림 프로세스 확인", "proxy_pass 포트 확인", "Nginx 에러 로그 확인"];
  }
  if (page.slug.includes("docker") || page.tags.includes("port")) {
    return ["포트 점유 프로세스 확인", "컨테이너 포트 매핑 확인", "필요하면 호스트 포트 변경"];
  }
  return ["관련 문제 유형 확인", "대표 증상 비교", "해결 후 raw 사건 기록 보강"];
}

function appendConversation(role, text, type = "") {
  state.conversation.push({ role, text, type });
  renderConversation();
}

function renderConversation() {
  if (!state.conversation.length) {
    nodes.conversationLog.innerHTML = "";
    return;
  }

  nodes.conversationLog.innerHTML = [...state.conversation].reverse().map((item, reversedIndex) => {
    const originalIndex = state.conversation.length - 1 - reversedIndex;
    return `
      <div class="chat-message ${escapeHtml(item.type || "")}" data-index="${originalIndex}" title="클릭하면 삭제">
        <div class="chat-role">${escapeHtml(item.role)}</div>
        <div class="chat-text">${escapeHtml(item.text)}</div>
      </div>
    `;
  }).join("");

  nodes.conversationLog.querySelectorAll(".chat-message").forEach(el => {
    el.addEventListener("click", () => {
      const idx = parseInt(el.dataset.index, 10);
      state.conversation.splice(idx, 1);
      renderConversation();
    });
  });
}

function resetConversation() {
  state.conversation = [];
  nodes.agentResult.innerHTML = "";
  renderConversation();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;",
  }[char]));
}

function setPanelCollapsed(side, collapsed) {
  const isLeft = side === "left";
  const className = isLeft ? "left-collapsed" : "right-collapsed";
  const button = isLeft ? nodes.toggleLeft : nodes.toggleRight;
  const label = isLeft ? "왼쪽 패널" : "오른쪽 패널";

  nodes.workspace.classList.toggle(className, collapsed);
  button.textContent = isLeft
    ? (collapsed ? "›" : "‹")
    : (collapsed ? "‹" : "›");
  button.setAttribute("aria-expanded", String(!collapsed));
  button.setAttribute("aria-label", `${label} ${collapsed ? "펼치기" : "접기"}`);
}

function togglePanel(side) {
  const className = side === "left" ? "left-collapsed" : "right-collapsed";
  setPanelCollapsed(side, !nodes.workspace.classList.contains(className));
}

function categoryLabel(category) {
  return { incidents: "Incident" }[category] || category;
}

function koreanFetchError(error) {
  if (String(error.message).includes("Failed to fetch")) {
    return "위키 파일을 불러오지 못했습니다. HTML 파일을 직접 열면 브라우저 보안 정책 때문에 fetch가 막힐 수 있습니다.";
  }
  return error.message
    .replace("Could not read", "파일을 읽을 수 없습니다:")
    .replace("Failed to fetch", "파일 요청 실패");
}

function koreanApiError(error) {
  if (String(error.message).includes("Failed to fetch")) {
    return "로컬 API 서버에 연결할 수 없습니다. python tools/viewer_server.py로 실행했는지 확인하세요.";
  }
  return error.message;
}

nodes.search.addEventListener("input", renderList);
nodes.resetSearch.addEventListener("click", () => {
  nodes.search.value = "";
  state.selectedSlug = "";
  nodes.pagePath.textContent = "선택한 문제 유형 없음";
  nodes.article.innerHTML = '<p class="empty">문제 유형을 선택하세요.</p>';
  renderList();
});
nodes.runAgent.addEventListener("click", runAgent);
nodes.toggleLeft.addEventListener("click", () => togglePanel("left"));
nodes.toggleRight.addEventListener("click", () => togglePanel("right"));

loadViewer();
