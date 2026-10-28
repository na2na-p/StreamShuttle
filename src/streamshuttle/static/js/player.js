// YouTubeプレイリストプレイヤー
// GET /playlist で取得した動画一覧を、GET /playlist/stream で解決した
// ストリームURLを使って順番に再生する。
//
// Androidのブラウザは画面オフ・バックグラウンド時に映像を含む<video>を一時停止するため、
// 「音声のみ」では同じストリームを<audio>で再生し、Media Session APIで
// ロック画面・通知からの操作に対応する。
document.addEventListener('DOMContentLoaded', function() {
  // DOM要素の取得
  const urlInput = document.getElementById('playlist-url-input');
  const loadBtn = document.getElementById('load-playlist-btn');
  const errorMessage = document.getElementById('player-error');
  const noticeMessage = document.getElementById('player-notice');
  const playerContainer = document.getElementById('player-container');
  const playlistTitle = document.getElementById('playlist-title');
  const playlistMeta = document.getElementById('playlist-meta');
  const videoPlayer = document.getElementById('video-player');
  const audioPlayer = document.getElementById('audio-player');
  const nowPlaying = document.getElementById('now-playing');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const shuffleToggle = document.getElementById('shuffle-toggle');
  const repeatMode = document.getElementById('repeat-mode');
  const audioOnlyToggle = document.getElementById('audio-only-toggle');
  const playlistItems = document.getElementById('playlist-items');

  // 状態管理
  let items = [];        // プレイリストの動画一覧
  let playOrder = [];    // 再生順（itemsのインデックスの並び）
  let orderPos = 0;      // playOrder内の現在位置
  let failureCount = 0;  // 連続再生失敗数（全滅時の無限スキップ防止）
  let loadToken = 0;     // 解決結果の到着順による表示ズレを防ぐトークン
  let reportedErrorSrc = null;  // 失敗を通知済みのソース（同一動画の二重スキップ防止）
  let playlistInfo = null;      // 読み込み中のプレイリスト情報（Media Sessionのメタデータ用）
  let media = videoPlayer;      // 再生に使用中のメディア要素（<video>または<audio>）

  loadBtn.addEventListener('click', loadPlaylist);
  prevBtn.addEventListener('click', () => step(-1));
  nextBtn.addEventListener('click', () => step(1));
  shuffleToggle.addEventListener('change', rebuildPlayOrder);
  repeatMode.addEventListener('change', applyRepeatMode);
  audioOnlyToggle.addEventListener('change', applyAudioOnly);
  [videoPlayer, audioPlayer].forEach((element) => {
    // 切り替えで使われなくなった側の要素のイベントは無視する
    element.addEventListener('ended', () => {
      if (element === media) {
        step(1);
      }
    });
    element.addEventListener('error', () => {
      if (element === media) {
        onPlaybackError();
      }
    });
    element.addEventListener('play', () => {
      if (element === media) {
        setPlaybackState('playing');
      }
    });
    element.addEventListener('pause', () => {
      if (element === media) {
        setPlaybackState('paused');
      }
    });
    element.addEventListener('loadedmetadata', () => {
      if (element === media) {
        updatePositionState();
      }
    });
    element.addEventListener('seeked', () => {
      if (element === media) {
        updatePositionState();
      }
    });
  });
  setupMediaSession();
  // リロード時にブラウザが復元したフォーム値も反映する
  applyRepeatMode();
  applyAudioOnly();

  // プレイリストを読み込む
  async function loadPlaylist() {
    const url = urlInput.value.trim();
    if (!url) {
      showError('プレイリストURLを入力してください');
      return;
    }

    hideError();
    hideNotice();
    playerContainer.classList.add('hidden');
    loadBtn.disabled = true;
    loadBtn.textContent = '読み込み中...';

    try {
      const response = await fetch(`/playlist?url=${encodeURIComponent(url)}`);
      const data = await parseResponse(response);

      items = data.items;
      playlistInfo = data.playlist_info;
      playlistTitle.textContent = data.playlist_info.title;
      playlistMeta.textContent = buildMetaText(data.playlist_info);

      renderItems();
      playerContainer.classList.remove('hidden');

      if (data.playlist_info.truncated) {
        showNotice(`動画が多いため、先頭 ${items.length} 件のみ読み込みました`);
      }

      playAt(0);
    } catch (error) {
      showError(`プレイリスト取得エラー: ${error.message}`);
    } finally {
      loadBtn.disabled = false;
      loadBtn.textContent = 'プレイリスト読み込み';
    }
  }

  // レスポンスをJSONとして解釈し、エラー時はサーバーのdetailを例外にする
  async function parseResponse(response) {
    let body = null;
    try {
      body = await response.json();
    } catch (error) {
      body = null;
    }

    if (!response.ok) {
      const detail = body && body.detail ? body.detail : `HTTPエラー: ${response.status}`;
      throw new Error(detail);
    }

    return body;
  }

  // プレイリスト情報の補足テキストを組み立てる
  function buildMetaText(playlistInfo) {
    const parts = [];
    if (playlistInfo.uploader) {
      parts.push(playlistInfo.uploader);
    }
    parts.push(`${playlistInfo.item_count} 件`);
    return parts.join(' / ');
  }

  // 動画一覧を描画する
  function renderItems() {
    playlistItems.innerHTML = '';

    items.forEach((item, index) => {
      const listItem = document.createElement('li');
      listItem.className = 'playlist-item';
      listItem.dataset.index = String(index);

      const thumbnail = document.createElement('img');
      thumbnail.className = 'playlist-item-thumbnail';
      thumbnail.src = item.thumbnail_url;
      thumbnail.alt = '';
      thumbnail.loading = 'lazy';

      const title = document.createElement('span');
      title.className = 'playlist-item-title';
      title.textContent = item.title;

      const duration = document.createElement('span');
      duration.className = 'playlist-item-duration';
      duration.textContent = formatDuration(item.duration_seconds);

      listItem.appendChild(thumbnail);
      listItem.appendChild(title);
      listItem.appendChild(duration);
      listItem.addEventListener('click', () => playAt(index));

      playlistItems.appendChild(listItem);
    });
  }

  // 秒数を mm:ss / h:mm:ss 形式に整形する
  function formatDuration(seconds) {
    if (!seconds) {
      return '--:--';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const padded = (value) => String(value).padStart(2, '0');

    return hours > 0
      ? `${hours}:${padded(minutes)}:${padded(secs)}`
      : `${minutes}:${padded(secs)}`;
  }

  // 指定インデックスの動画を再生する
  async function playAt(index) {
    if (index < 0 || index >= items.length) {
      return;
    }

    buildPlayOrder(index);
    await play(index);
  }

  // 再生順を（シャッフル設定に応じて）組み立て直す
  function buildPlayOrder(currentIndex) {
    const indices = items.map((_, index) => index);

    if (shuffleToggle.checked) {
      const rest = indices.filter((index) => index !== currentIndex);
      shuffle(rest);
      playOrder = [currentIndex, ...rest];
      orderPos = 0;
    } else {
      playOrder = indices;
      orderPos = currentIndex;
    }
  }

  // シャッフル設定の変更時に、再生中の動画を保ったまま再生順を作り直す
  function rebuildPlayOrder() {
    if (items.length === 0) {
      return;
    }
    buildPlayOrder(playOrder[orderPos] ?? 0);
  }

  // 1曲リピート時は<video>のloopで同じ動画を繰り返す（endedが発生しないため次へ進まない）
  // 前へ/次へボタンでの手動移動は従来どおり行える
  function applyRepeatMode() {
    const loop = repeatMode.value === 'one';
    videoPlayer.loop = loop;
    audioPlayer.loop = loop;
  }

  // 「音声のみ」の切り替え。再生中のソース・再生位置・再生状態を引き継いで要素を入れ替える
  function applyAudioOnly() {
    const next = audioOnlyToggle.checked ? audioPlayer : videoPlayer;
    videoPlayer.classList.toggle('hidden', next !== videoPlayer);
    audioPlayer.classList.toggle('hidden', next !== audioPlayer);

    if (next === media) {
      return;
    }

    const previous = media;
    const src = previous.getAttribute('src');
    const currentTime = previous.currentTime;
    const wasPlaying = !previous.paused;

    media = next;
    previous.pause();
    previous.removeAttribute('src');
    previous.load();

    if (!src) {
      return;
    }

    next.addEventListener('loadedmetadata', () => {
      next.currentTime = currentTime;
    }, { once: true });
    next.src = src;
    if (wasPlaying) {
      next.play().catch(() => {});
    }
  }

  // Fisher-Yatesシャッフル
  function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
  }

  // 再生位置を前後に移動する
  function step(delta) {
    if (items.length === 0) {
      return;
    }

    const nextPos = orderPos + delta;

    if (nextPos < 0 || nextPos >= playOrder.length) {
      if (repeatMode.value === 'off') {
        nowPlaying.textContent = '再生を終了しました';
        return;
      }
      orderPos = (nextPos + playOrder.length) % playOrder.length;
    } else {
      orderPos = nextPos;
    }

    play(playOrder[orderPos]);
  }

  // ストリームURLを解決して再生する
  async function play(index) {
    const item = items[index];
    if (!item) {
      return;
    }

    orderPos = Math.max(playOrder.indexOf(index), 0);
    highlightCurrent(index);
    hideError();
    nowPlaying.textContent = `読み込み中: ${item.title}`;

    const token = ++loadToken;

    try {
      const response = await fetch(`/playlist/stream?video_id=${encodeURIComponent(item.video_id)}`);
      const data = await parseResponse(response);

      // 解決中に別の動画へ切り替わっていた場合は、この結果を破棄する
      if (token !== loadToken) {
        return;
      }

      media.src = data.stream_url;
      updateMediaMetadata(item);
      await media.play();

      failureCount = 0;
      nowPlaying.textContent = `再生中: ${item.title}`;
    } catch (error) {
      if (token !== loadToken) {
        return;
      }

      // 自動再生がブラウザにブロックされただけの場合は、失敗として扱わない
      if (error.name === 'NotAllowedError') {
        nowPlaying.textContent = `再生準備完了: ${item.title}（再生ボタンを押してください）`;
        return;
      }

      reportFailure(`再生できませんでした: ${item.title}（${error.message}）`);
    }
  }

  // <video>要素側で発生した再生エラーを処理する
  function onPlaybackError() {
    if (!media.src) {
      return;
    }

    const item = items[playOrder[orderPos]];
    reportFailure(`再生できませんでした: ${item ? item.title : '不明な動画'}`);
  }

  // 再生失敗を通知し、次の動画へスキップする（全動画が失敗した場合は停止）
  //
  // 読み込み失敗時はplay()のPromise棄却と<video>のerrorイベントの両方が発生しうるため、
  // 同一ソースに対する2回目以降の通知は無視して二重スキップを防ぐ。
  function reportFailure(message) {
    if (reportedErrorSrc === media.src) {
      return;
    }
    reportedErrorSrc = media.src;

    showError(message);
    failureCount += 1;

    if (failureCount >= items.length) {
      failureCount = 0;
      nowPlaying.textContent = 'すべての動画を再生できませんでした';
      return;
    }

    step(1);
  }

  // ロック画面・通知の再生操作をプレイヤーに結び付ける
  function setupMediaSession() {
    if (!('mediaSession' in navigator)) {
      return;
    }

    const handlers = {
      play: () => media.play().catch(() => {}),
      pause: () => media.pause(),
      previoustrack: () => step(-1),
      nexttrack: () => step(1),
      seekto: (details) => {
        media.currentTime = details.seekTime;
      },
    };

    Object.entries(handlers).forEach(([action, handler]) => {
      try {
        navigator.mediaSession.setActionHandler(action, handler);
      } catch (error) {
        // 未対応のアクションはブラウザ側で例外になるため無視する
      }
    });
  }

  // ロック画面・通知に表示する曲情報を更新する
  function updateMediaMetadata(item) {
    if (!('mediaSession' in navigator) || typeof MediaMetadata === 'undefined') {
      return;
    }

    navigator.mediaSession.metadata = new MediaMetadata({
      title: item.title,
      artist: playlistInfo && playlistInfo.uploader ? playlistInfo.uploader : '',
      album: playlistInfo ? playlistInfo.title : '',
      artwork: item.thumbnail_url ? [{ src: item.thumbnail_url }] : [],
    });
  }

  function setPlaybackState(state) {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = state;
    }
  }

  // ロック画面のシークバーに再生位置を反映する
  function updatePositionState() {
    if (!('mediaSession' in navigator) || !navigator.mediaSession.setPositionState) {
      return;
    }

    try {
      navigator.mediaSession.setPositionState({
        duration: media.duration,
        playbackRate: media.playbackRate,
        position: media.currentTime,
      });
    } catch (error) {
      // ライブ配信など長さが確定しない場合は位置情報を設定しない
    }
  }

  // 再生中の項目を一覧上で強調する
  function highlightCurrent(index) {
    playlistItems.querySelectorAll('.playlist-item').forEach((element) => {
      element.classList.toggle('playing', Number(element.dataset.index) === index);
    });
  }

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
  }

  function hideError() {
    errorMessage.classList.add('hidden');
  }

  function showNotice(message) {
    noticeMessage.textContent = message;
    noticeMessage.classList.remove('hidden');
  }

  function hideNotice() {
    noticeMessage.classList.add('hidden');
  }
});
