(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const dropzone = $("dropzone");
  const fileInput = $("fileInput");
  const uploadPanel = $("uploadPanel");
  const editorPanel = $("editorPanel");
  const pageImage = $("pageImage");
  const pageFrame = $("pageFrame");
  const selBox = $("selBox");
  const applyBtn = $("applyBtn");

  let maxUploadMb = 100;
  let sessionId = null;
  let pages = [];
  let currentPage = 1;
  let drag = null;
  let selection = null;
  let hitBbox = null;

  const savedTheme = localStorage.getItem("docsplit-theme");
  if (savedTheme) document.documentElement.setAttribute("data-theme", savedTheme);

  $("themeBtn").addEventListener("click", () => {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("docsplit-theme", next);
  });

  const API = window.BACKEND_URL || (location.hostname.includes("vercel.app") ? "https://docsplit.fly.dev" : "");
  const api = (path) => (API || "") + path;

  fetch(api("/api/health"))
    .then((r) => {
      if (!r.ok) throw new Error("health " + r.status);
      return r.json();
    })
    .then((info) => {
      maxUploadMb = info.max_upload_mb || 100;
      const envNames = { vercel: "Vercel", railway: "Railway", local: "Local" };
      const env = envNames[info.environment] || info.environment || "Local";
      $("envLabel").textContent = `${env} · editor`;
      $("envBadge").classList.remove("offline");
      $("dzHint").textContent = `Somente .pdf · até ${Math.round(maxUploadMb)} MB`;
      if (info.environment === "vercel") {
        showInfo("Na Vercel a sessão de edição pode expirar entre cliques. Prefira start.bat (local) ou Railway.");
      }
    })
    .catch(() => {
      $("envBadge").classList.add("offline");
      $("envLabel").textContent = "Servidor offline";
      showError("Não foi possível conectar à API. Dê um duplo clique em start.bat.");
    });

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) openFile(fileInput.files[0]);
  });
  ["dragenter", "dragover"].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) openFile(file);
  });

  async function openFile(file) {
    hideAlerts();
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showError("Envie um arquivo PDF.");
      return;
    }
    if (file.size > maxUploadMb * 1024 * 1024) {
      showError(`Arquivo grande demais. Limite: ${Math.round(maxUploadMb)} MB.`);
      return;
    }
    const form = new FormData();
    form.append("file", file);
    try {
      const resp = await fetch(api("/api/edit/session"), { method: "POST", body: form });
      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data || !data.success) {
        throw new Error((data && data.detail) || `Erro ${resp.status}`);
      }
      sessionId = data.session_id;
      pages = data.pages || [];
      currentPage = 1;
      $("editorTitle").textContent = data.filename || "Correção";
      uploadPanel.style.display = "none";
      editorPanel.classList.add("visible");
      clearSelection();
      await loadPage();
    } catch (err) {
      showError(err.message || "Falha ao abrir o PDF.");
    }
  }

  async function loadPage() {
    if (!sessionId) return;
    $("pageLabel").textContent = `Página ${currentPage} / ${pages.length}`;
    $("prevPage").disabled = currentPage <= 1;
    $("nextPage").disabled = currentPage >= pages.length;
    pageImage.src = api(`/api/edit/session/${sessionId}/page/${currentPage}?t=${Date.now()}`);
    clearSelection();
  }

  $("prevPage").addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage -= 1;
      loadPage();
    }
  });
  $("nextPage").addEventListener("click", () => {
    if (currentPage < pages.length) {
      currentPage += 1;
      loadPage();
    }
  });

  pageFrame.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    const pos = localPoint(e);
    drag = { x: pos.x, y: pos.y };
    selection = null;
    selBox.hidden = false;
    placeSel(pos.x, pos.y, pos.x, pos.y);
    e.preventDefault();
  });
  window.addEventListener("mousemove", (e) => {
    if (!drag) return;
    const pos = localPoint(e);
    placeSel(drag.x, drag.y, pos.x, pos.y);
  });
  window.addEventListener("mouseup", async () => {
    if (!drag) return;
    const box = readSel();
    drag = null;
    const geo = pages[currentPage - 1];
    if (!geo) {
      clearSelection();
      return;
    }
    const seed =
      box && (box.w >= 3 || box.h >= 3)
        ? toPdf(box, geo)
        : toPdf({ x: box ? box.x : 0, y: box ? box.y : 0, w: 4, h: 4 }, geo);
    await inspectAndSnap(seed);
  });

  $("fixText").addEventListener("input", () => {
    applyBtn.disabled = !selection || !$("fixText").value.trim();
  });

  $("applyBtn").addEventListener("click", async () => {
    if (!sessionId || !selection) return;
    const text = $("fixText").value.trim();
    if (!text) return;
    const geo = pages[currentPage - 1];
    if (!geo) return;
    const pdfRect = hitBbox || toPdf(selection, geo);
    const fontsize = Number($("fontSize").value) || undefined;
    applyBtn.disabled = true;
    try {
      const resp = await fetch(api(`/api/edit/session/${sessionId}/apply`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corrections: [
            {
              page_number: currentPage,
              ...pdfRect,
              text,
              fontsize,
            },
          ],
        }),
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok) {
        const detail = data && (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail));
        throw new Error(detail || `Erro ${resp.status}`);
      }
      $("fixText").value = "";
      clearSelection();
      await loadPage();
    } catch (err) {
      showError(err.message || "Não foi possível aplicar a correção.");
      applyBtn.disabled = false;
    }
  });

  $("downloadBtn").addEventListener("click", () => {
    if (!sessionId) return;
    window.location.href = api(`/api/edit/session/${sessionId}/download`);
  });

  $("newFileBtn").addEventListener("click", () => {
    sessionId = null;
    pages = [];
    currentPage = 1;
    fileInput.value = "";
    editorPanel.classList.remove("visible");
    uploadPanel.style.display = "";
    hideAlerts();
  });

  function localPoint(e) {
    const r = pageImage.getBoundingClientRect();
    return {
      x: Math.min(Math.max(e.clientX - r.left, 0), r.width),
      y: Math.min(Math.max(e.clientY - r.top, 0), r.height),
    };
  }

  function placeSel(x0, y0, x1, y1) {
    const left = Math.min(x0, x1);
    const top = Math.min(y0, y1);
    selBox.style.left = left + "px";
    selBox.style.top = top + "px";
    selBox.style.width = Math.abs(x1 - x0) + "px";
    selBox.style.height = Math.abs(y1 - y0) + "px";
    selBox.hidden = false;
  }

  function readSel() {
    if (selBox.hidden) return null;
    return {
      x: parseFloat(selBox.style.left) || 0,
      y: parseFloat(selBox.style.top) || 0,
      w: parseFloat(selBox.style.width) || 0,
      h: parseFloat(selBox.style.height) || 0,
    };
  }

  function toPdf(box, geo) {
    const r = pageImage.getBoundingClientRect();
    const sx = geo.width / r.width;
    const sy = geo.height / r.height;
    return {
      x0: box.x * sx,
      y0: box.y * sy,
      x1: (box.x + box.w) * sx,
      y1: (box.y + box.h) * sy,
    };
  }

  function fromPdf(bbox, geo) {
    const r = pageImage.getBoundingClientRect();
    const sx = r.width / geo.width;
    const sy = r.height / geo.height;
    return {
      x: bbox.x0 * sx,
      y: bbox.y0 * sy,
      w: (bbox.x1 - bbox.x0) * sx,
      h: (bbox.y1 - bbox.y0) * sy,
    };
  }

  async function inspectAndSnap(pdfRect) {
    try {
      const resp = await fetch(api(`/api/edit/session/${sessionId}/inspect`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ page_number: currentPage, ...pdfRect }),
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data || !data.success) {
        throw new Error((data && data.detail) || "Nao foi possivel ler o trecho.");
      }
      const geo = pages[currentPage - 1];
      hitBbox = data.bbox;
      const css = fromPdf(data.bbox, geo);
      selection = css;
      placeSel(css.x, css.y, css.x + css.w, css.y + css.h);
      const current = $("currentText");
      if (current) {
        current.textContent =
          data.mode === "text" && data.original
            ? data.original
            : "Sem texto nativo neste ponto (pagina escaneada). Marque so o trecho.";
      }
      if (data.fontsize) $("fontSize").value = String(Math.round(data.fontsize * 10) / 10);
      const fontEl = $("fontName");
      if (fontEl) {
        fontEl.textContent = data.font_label || data.font || "não identificada";
      }
      applyBtn.disabled = !$("fixText").value.trim();
    } catch (err) {
      clearSelection();
      showError(err.message || "Nao foi possivel identificar o texto.");
    }
  }

  function clearSelection() {
    selection = null;
    drag = null;
    hitBbox = null;
    selBox.hidden = true;
    applyBtn.disabled = true;
    const current = $("currentText");
    if (current) current.textContent = "Clique numa linha do PDF.";
    const fontEl = $("fontName");
    if (fontEl) fontEl.textContent = "Clique numa linha para ver a fonte.";
  }

  function showError(msg) {
    $("errorMessage").textContent = msg;
    $("errorAlert").classList.add("visible");
  }
  function showInfo(msg) {
    $("infoMessage").textContent = msg;
    $("infoAlert").classList.add("visible");
  }
  function hideAlerts() {
    $("errorAlert").classList.remove("visible");
    $("infoAlert").classList.remove("visible");
  }
})();
