(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const dropzone = $("dropzone");
  const fileInput = $("fileInput");
  const fileChip = $("fileChip");
  const processBtn = $("processBtn");
  const uploadPanel = $("uploadPanel");
  const processingPanel = $("processingPanel");
  const resultsPanel = $("resultsPanel");

  let selectedFile = null;
  let zipBlob = null;
  let zipFilename = "documentos_separados.zip";
  let zipArchive = null;
  let documents = [];
  let stepTimer = null;
  let maxUploadMb = 100;

  const savedTheme = localStorage.getItem("docsplit-theme");
  if (savedTheme) document.documentElement.setAttribute("data-theme", savedTheme);

  $("themeBtn").addEventListener("click", () => {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("docsplit-theme", next);
  });

  fetch("/api/health")
    .then((r) => {
      if (!r.ok) throw new Error("health " + r.status);
      return r.json();
    })
    .then((info) => {
      maxUploadMb = info.max_upload_mb || 100;
      const envNames = { vercel: "Vercel", railway: "Railway", local: "Local" };
      const env = envNames[info.environment] || info.environment || "Local";
      const ocr = info.ocr_available ? "OCR" : "sem OCR";
      const llm = info.llm_available ? "IA" : "sem IA";
      $("envLabel").textContent = `${env} · ${ocr} · ${llm}`;
      $("envBadge").classList.remove("offline");
      $("dzHint").textContent = `Somente .pdf · até ${Math.round(maxUploadMb)} MB · máx. ${info.max_pages || "—"} páginas`;
      if (!info.ocr_available) {
        showInfo(
          "OCR indisponível neste ambiente. PDFs com texto selecionável são classificados; páginas só-imagem vão para revisão manual."
        );
      }
      if (info.environment === "vercel") {
        showInfo(
          "Na Vercel o limite é ~4 MB e 20 páginas. Para OCR e lotes maiores use start.bat (local) ou o deploy no Railway."
        );
      }
    })
    .catch(() => {
      $("envBadge").classList.add("offline");
      $("envLabel").textContent = "Servidor offline";
      const onVercel = /vercel\.app$/i.test(location.hostname);
      showError(
        onVercel
          ? "A API na nuvem não respondeu. Recarregue em alguns segundos (novo deploy) ou use o modo local."
          : "Não foi possível conectar à API. Dê um duplo clique em start.bat."
      );
    });

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) setFile(fileInput.files[0]);
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
    if (file) setFile(file);
  });

  $("fcRemove").addEventListener("click", clearFile);

  function setFile(file) {
    hideAlerts();
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showError("Envie um arquivo PDF.");
      return;
    }
    if (file.size > maxUploadMb * 1024 * 1024) {
      showError(`Arquivo grande demais (${formatSize(file.size)}). Limite: ${Math.round(maxUploadMb)} MB.`);
      return;
    }
    selectedFile = file;
    $("fcName").textContent = file.name;
    $("fcSize").textContent = formatSize(file.size);
    fileChip.classList.add("visible");
    processBtn.disabled = false;
  }

  function clearFile() {
    selectedFile = null;
    fileInput.value = "";
    fileChip.classList.remove("visible");
    processBtn.disabled = true;
  }

  function formatSize(bytes) {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  }

  processBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    hideAlerts();
    uploadPanel.style.display = "none";
    resultsPanel.classList.remove("visible");
    processingPanel.classList.add("visible");
    animateSteps();

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const resp = await fetch("/api/process", { method: "POST", body: formData });
      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data || !data.success) {
        const detail =
          (data && (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))) ||
          `Erro ${resp.status} ao processar o arquivo.`;
        throw new Error(detail);
      }
      finishSteps();
      setTimeout(() => renderResults(data), 350);
    } catch (err) {
      stopSteps();
      processingPanel.classList.remove("visible");
      uploadPanel.style.display = "";
      showError(err.message || "Falha inesperada durante o processamento.");
    }
  });

  function animateSteps() {
    const steps = document.querySelectorAll(".step");
    steps.forEach((s) => {
      s.classList.remove("active", "done");
      s.querySelector(".n").textContent = Number(s.dataset.step) + 1;
    });
    let current = 0;
    const activate = (i) => {
      steps[i].classList.add("active");
      steps[i].querySelector(".n").innerHTML = '<div class="spinner"></div>';
    };
    const complete = (i) => {
      steps[i].classList.remove("active");
      steps[i].classList.add("done");
      steps[i].querySelector(".n").textContent = "✓";
    };
    activate(current);
    stepTimer = setInterval(() => {
      if (current < steps.length - 1) {
        complete(current);
        current += 1;
        activate(current);
      }
    }, 2000);
  }

  function finishSteps() {
    stopSteps();
    document.querySelectorAll(".step").forEach((s) => {
      s.classList.remove("active");
      s.classList.add("done");
      s.querySelector(".n").textContent = "✓";
    });
  }

  function stopSteps() {
    if (stepTimer) {
      clearInterval(stepTimer);
      stepTimer = null;
    }
  }

  async function renderResults(data) {
    processingPanel.classList.remove("visible");
    const bytes = Uint8Array.from(atob(data.zip_base64), (c) => c.charCodeAt(0));
    zipBlob = new Blob([bytes], { type: "application/zip" });
    zipFilename = data.zip_filename || "documentos_separados.zip";
    documents = data.documents || [];
    zipArchive = window.JSZip ? await JSZip.loadAsync(zipBlob) : null;

    $("statDocs").textContent = data.stats.total_documents;
    $("statPages").textContent = data.stats.total_pages;
    $("statReview").textContent = data.stats.needs_review;
    $("filterInput").value = "";
    paintTable(documents);
    resultsPanel.classList.add("visible");
    resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function paintTable(rows) {
    const tbody = $("resultsBody");
    tbody.innerHTML = "";
    rows.forEach((doc, i) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="mono">${String(i + 1).padStart(2, "0")}</td>
        <td class="mono">${escapeHtml(doc.filename)}</td>
        <td><span class="badge type">${escapeHtml(doc.doc_type_label)}</span></td>
        <td>${escapeHtml(doc.supplier || "—")}</td>
        <td class="mono">${escapeHtml(doc.pages)}</td>
        <td>${doc.needs_review ? '<span class="badge review">Revisar</span>' : '<span class="badge ok">OK</span>'}</td>
        <td><button class="linkish" data-file="${escapeHtml(doc.filename)}" type="button">Baixar</button></td>`;
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll("button[data-file]").forEach((btn) => {
      btn.addEventListener("click", () => downloadOne(btn.dataset.file));
    });
  }

  $("filterInput").addEventListener("input", () => {
    const q = $("filterInput").value.toLowerCase().trim();
    const rows = !q
      ? documents
      : documents.filter((d) =>
          [d.filename, d.doc_type_label, d.supplier || ""].join(" ").toLowerCase().includes(q)
        );
    paintTable(rows);
  });

  async function downloadOne(filename) {
    if (!zipArchive) {
      $("downloadBtn").click();
      return;
    }
    const entry = zipArchive.file(filename);
    if (!entry) return;
    const blob = await entry.async("blob");
    triggerDownload(blob, filename);
  }

  $("downloadBtn").addEventListener("click", () => {
    if (!zipBlob) return;
    triggerDownload(zipBlob, zipFilename);
  });

  $("resetBtn").addEventListener("click", () => {
    clearFile();
    zipBlob = null;
    zipArchive = null;
    documents = [];
    resultsPanel.classList.remove("visible");
    uploadPanel.style.display = "";
    hideAlerts();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  function triggerDownload(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
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
  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])
    );
  }
})();
