const API_ENDPOINT = "/api/v1/formula/recognize";

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const dropText = document.getElementById("dropText");
const previewImage = document.getElementById("previewImage");
const backendSelect = document.getElementById("backendSelect");
const recognizeBtn = document.getElementById("recognizeBtn");
const statusText = document.getElementById("statusText");
const latexOutput = document.getElementById("latexOutput");
const copyBtn = document.getElementById("copyBtn");
const engineMeta = document.getElementById("engineMeta");

let currentFile = null;
let previewUrl = null;

function setStatus(text, type = "info") {
  statusText.textContent = text;
  statusText.dataset.type = type;
}

function releasePreviewUrl() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }
}

function setCurrentFile(file) {
  currentFile = file;
  dropText.textContent = `已选择：${file.name}`;

  releasePreviewUrl();
  previewUrl = URL.createObjectURL(file);
  previewImage.src = previewUrl;
  previewImage.hidden = false;
}

function onFileSelected(file) {
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    setStatus("请选择图片文件。", "error");
    return;
  }
  setCurrentFile(file);
  setStatus("图片已就绪，点击“识别”开始。", "success");
}

fileInput.addEventListener("change", (event) => {
  const file = event.target.files && event.target.files[0];
  onFileSelected(file);
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("is-dragover");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragover");
  const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
  onFileSelected(file);
});

recognizeBtn.addEventListener("click", async () => {
  if (!currentFile) {
    setStatus("请先上传图片。", "error");
    return;
  }

  recognizeBtn.disabled = true;
  setStatus("识别中，请稍候...", "info");
  engineMeta.textContent = "";

  const formData = new FormData();
  formData.append("file", currentFile);

  const backend = backendSelect.value || "auto";
  const url = `${API_ENDPOINT}?backend=${encodeURIComponent(backend)}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      headers: { Accept: "application/json" }
    });
    const data = await response.json();

    if (!response.ok) {
      const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
      throw new Error(String(detail));
    }

    latexOutput.value = data.latex || "";
    engineMeta.textContent = `engine=${data.engine_name}, ready=${data.engine_ready}`;

    if (data.engine_ready) {
      setStatus("识别完成。", "success");
    } else {
      setStatus(`识别返回，但引擎未就绪：${data.engine_message}`, "warn");
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setStatus(`识别失败：${message}`, "error");
  } finally {
    recognizeBtn.disabled = false;
  }
});

copyBtn.addEventListener("click", async () => {
  const text = latexOutput.value.trim();
  if (!text) {
    setStatus("当前没有可复制的 LaTeX。", "warn");
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus("LaTeX 已复制到剪贴板。", "success");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setStatus(`复制失败：${message}`, "error");
  }
});
