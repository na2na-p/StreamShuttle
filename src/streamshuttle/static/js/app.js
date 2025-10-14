// DOMContentLoadedイベントで初期化
document.addEventListener('DOMContentLoaded', function() {
  // DOM要素の取得
  const form = document.getElementById('download-form');
  const urlInput = document.getElementById('url-input');
  const fetchFormatsBtn = document.getElementById('fetch-formats-btn');
  const formatsContainer = document.getElementById('formats-container');
  const formatsList = document.getElementById('formats-list');
  const downloadContainer = document.getElementById('download-container');
  const downloadBtn = document.getElementById('download-btn');
  const errorMessage = document.getElementById('error-message');

  // 状態管理
  let selectedFormat = null;
  let currentUrl = '';
  let csrfToken = '';

  // フォーマット取得ボタンのクリックイベント
  fetchFormatsBtn.addEventListener('click', async function() {
    const url = urlInput.value.trim();
    if (!url) {
      showError('YouTube URLを入力してください');
      return;
    }

    currentUrl = url;
    hideError();
    formatsContainer.classList.add('hidden');
    downloadContainer.classList.add('hidden');
    fetchFormatsBtn.disabled = true;
    fetchFormatsBtn.textContent = '取得中...';

    try {
      const response = await fetch(`/formats?url=${encodeURIComponent(url)}`);
      if (!response.ok) {
        throw new Error(`HTTPエラー: ${response.status}`);
      }

      const data = await response.json();
      csrfToken = data.csrf_token;
      displayFormats(data.formats);
    } catch (error) {
      showError(`フォーマット取得エラー: ${error.message}`);
    } finally {
      fetchFormatsBtn.disabled = false;
      fetchFormatsBtn.textContent = 'フォーマット取得';
    }
  });

  // フォーマット一覧を表示
  function displayFormats(formats) {
    formatsList.innerHTML = '';
    selectedFormat = null;

    formats.forEach(format => {
      const option = document.createElement('div');
      option.className = 'format-option';
      option.textContent = `${format.quality} - ${format.codec} (${format.format_id})`;
      option.dataset.formatId = format.format_id;

      option.addEventListener('click', function() {
        // 全ての選択を解除
        document.querySelectorAll('.format-option').forEach(el => {
          el.classList.remove('selected');
        });
        // 選択したフォーマットをハイライト
        option.classList.add('selected');
        selectedFormat = format.format_id;
        downloadContainer.classList.remove('hidden');
      });

      formatsList.appendChild(option);
    });

    formatsContainer.classList.remove('hidden');
  }

  // ダウンロードボタンのクリックイベント
  downloadBtn.addEventListener('click', function() {
    if (!selectedFormat || !currentUrl || !csrfToken) {
      showError('フォーマットを選択してください');
      return;
    }

    const downloadUrl = `/download?url=${encodeURIComponent(currentUrl)}&format_id=${encodeURIComponent(selectedFormat)}&csrf_token=${encodeURIComponent(csrfToken)}`;
    window.open(downloadUrl, '_blank');
  });

  // エラーメッセージを表示
  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
  }

  // エラーメッセージを非表示
  function hideError() {
    errorMessage.classList.add('hidden');
  }
});
