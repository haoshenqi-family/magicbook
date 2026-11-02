// AI 口语陪练（R166 自 speaking_writing.js 迁出；R221 改为语音优先）。
//
// 交互契约：
// - 教练消息始终先显示语音条，点击“转文字”才展开原文；
// - 用户必须先录一段真实语音，ASR 只负责把转写填进可编辑预览；
// - 只有点发送才上传录音 + 调 LLM；预览阶段不产生消息与积分。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, li = MB.li,
      esc = MB.esc, busy = MB.busy, getJson = MB.getJson, postJson = MB.postJson,
      resultOf = MB.resultOf;
  var urls = window.learningUrls || {};
  // 与 moon-well LearningSpeakingService.MAX_SPOKEN_CHARS 对齐：合成与回读必须用同一前缀。
  var MAX_VOICE_CHARS = 1800;

  var els = {};
  ['sw-s-scenario', 'sw-s-style', 'sw-s-book', 'sw-s-start', 'sw-s-setup',
   'sw-s-chat-panel', 'sw-s-chat', 'sw-s-input', 'sw-s-send', 'sw-s-report',
   'sw-s-report-panel', 'sw-s-summary', 'sw-s-progress-line',
   'sw-s-vocab', 'sw-s-corrections', 'sw-s-history-panel', 'sw-s-history',
   'sw-s-mic', 'sw-s-audio-status', 'sw-s-mic-device', 'sw-s-voice-preview',
   'sw-s-rerecord', 'sw-s-text-toggle',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-s-start']) return;

  var speaking = {
    sessionId: null,
    pending: null,       // { wav, text, durationMs, audioObject }，仅在“已转写、未发送”时存在
    typing: false,
    audio: null,
    autoplay: false,
  };

  function scrollChat() {
    els['sw-s-chat'].scrollTop = els['sw-s-chat'].scrollHeight;
  }

  function durationLabel(ms) {
    var seconds = Math.max(1, Math.round((ms || 0) / 1000));
    return Math.floor(seconds / 60) + ':' + ('0' + (seconds % 60)).slice(-2);
  }

  /**
   * 一条语音消息 = 可点击语音条 + 默认折叠的转写。
   * 原文只走 textContent，点击“转文字”展开；不把消息内容拼进 HTML。
   */
  function voiceMessage(role, text, options) {
    options = options || {};
    var wrap = document.createElement('div');
    wrap.className = 'sw-msg ' + (role === 'coach' ? 'sw-msg-coach' : 'sw-msg-user');

    var who = document.createElement('div');
    who.className = 'sw-msg-who';
    who.textContent = role === 'coach' ? mbT('Coach') : mbT('You');
    wrap.appendChild(who);

    var line = document.createElement('div');
    line.className = 'sw-voice-line';
    var bubble = document.createElement('button');
    bubble.type = 'button';
    bubble.className = 'sw-voice-bubble';
    bubble.setAttribute('aria-label', mbT('Play voice message'));
    var icon = document.createElement('span');
    icon.className = 'glyphicon glyphicon-play';
    var duration = document.createElement('span');
    duration.textContent = durationLabel(options.durationMs || Math.max(1200, String(text).length * 65));
    bubble.appendChild(icon);
    bubble.appendChild(duration);
    line.appendChild(bubble);

    var transcriptBtn = document.createElement('button');
    transcriptBtn.type = 'button';
    transcriptBtn.className = 'btn btn-link btn-xs';
    transcriptBtn.textContent = mbT('Show text');
    line.appendChild(transcriptBtn);
    wrap.appendChild(line);

    var transcript = document.createElement('div');
    transcript.className = 'sw-msg-transcript';
    transcript.hidden = true;
    esc(transcript, text);
    wrap.appendChild(transcript);

    transcriptBtn.addEventListener('click', function () {
      transcript.hidden = !transcript.hidden;
      transcriptBtn.textContent = transcript.hidden ? mbT('Show text') : mbT('Hide text');
    });

    bubble.addEventListener('click', function () {
      playVoice(role, text, options, bubble, icon);
    });
    return wrap;
  }

  /** 音频优先读缓存；教练缓存 miss 时显式合成一次，用户录音直接读鉴权端点。 */
  function playVoice(role, text, options, bubble, icon) {
    if (!text) return;
    options = options || {};
    try { if (speaking.audio) speaking.audio.pause(); } catch (e) { /* 已释放 */ }
    if (!bubble || !icon) {
      bubble = document.createElement('span');
      icon = document.createElement('span');
    }
    bubble.classList.add('sw-playing');
    icon.className = 'glyphicon glyphicon-volume-up';

    function done() {
      bubble.classList.remove('sw-playing');
      icon.className = 'glyphicon glyphicon-play';
    }

    function playBlob(blob) {
      var audio = new Audio(URL.createObjectURL(blob));
      speaking.audio = audio;
      audio.addEventListener('ended', done);
      audio.addEventListener('error', done);
      return audio.play().catch(function () {
        done();
        throw new Error(mbT('Voice playback failed'));
      });
    }

    var hasPreparedAudio = role === 'coach' && !!options.audioUrl;
    var request;
    if (role === 'user') {
      if (!options.audioObject) {
        window.alert(mbT('Voice playback failed'));
        done();
        return;
      }
      request = postAudio(urls.speakingRecordingAudio, {
        sessionId: speaking.sessionId,
        audioObject: options.audioObject,
      });
    } else {
      request = postAudio(urls.readingTtsCached, {
        text: String(text).slice(0, MAX_VOICE_CHARS),
      });
    }

    var load = request.then(function (response) {
      if (!response.ok) throw new Error('audio ' + response.status);
      return response.blob();
    }).catch(function () {
      // 正常轮次由后端同步合成并返回 cached URL；只有缓存确实未命中时才允许
      // 调用 /tts/speak 补合成（该端点按「听=消费」扣 1 积分）。
      if (role !== 'coach' || hasPreparedAudio) {
        throw new Error(mbT('Voice playback failed'));
      }
      return postAudio(urls.readingTts, { text: String(text).slice(0, MAX_VOICE_CHARS) })
        .then(function (response) {
          if (!response.ok) throw new Error('tts ' + response.status);
          return response.blob();
        });
    });

    // 自动播放只在有用户手势链（首次开聊/发送后的 Promise 链）时触发；历史回放
    // 不传 autoplay，避免浏览器拦截后弹「播放失败」。
    load.then(playBlob).catch(function () {
      done();
      if (!options.autoplay) window.alert(mbT('Voice playback failed'));
    });
  }

  function postAudio(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': MB.csrfToken() },
      body: JSON.stringify(body),
    });
  }

  function feedbackBlock(feedback) {
    var box = document.createElement('div');
    box.className = 'sw-feedback';
    if (feedback.encourage) {
      var line = document.createElement('div');
      esc(line, feedback.encourage);
      box.appendChild(line);
    }
    (feedback.errors || []).forEach(function (item) {
      var fix = document.createElement('div');
      fix.className = 'sw-correction';
      fix.textContent = '✎ ' + (item.original || '') + ' → ' + (item.corrected || '') +
        (item.note ? '（' + item.note + '）' : '');
      box.appendChild(fix);
    });
    if (feedback.better) {
      var better = document.createElement('div');
      better.className = 'sw-correction';
      better.textContent = '✦ ' + mbT('Better phrasing') + '：' + feedback.better;
      box.appendChild(better);
    }
    return box;
  }

  // ---------- 历史与回放 ----------

  function loadSpeakingHistory() {
    getJson(urls.speakingHistory).then(function (response) {
      var items = resultOf(response) || [];
      var panel = els['sw-s-history-panel'];
      if (!items.length) { show(panel, false); return; }
      var list = els['sw-s-history'];
      clear(list);
      items.forEach(function (session) {
        var line = li((session.scenarioLabel || session.scenario || '') +
          ' · ' + (session.roundCount || 0) + ' ' + mbT('rounds') + ' · ' +
          (session.createdAt || ''));
        line.style.cursor = 'pointer';
        line.addEventListener('click', function () { replaySession(session.sessionId); });
        list.appendChild(line);
      });
      show(panel, true);
    }).catch(function () { show(els['sw-s-history-panel'], false); });
  }

  function renderMessage(chat, message) {
    if (message.role !== 'coach' && !message.voice) {
      // 兼容 R212 前的纯文字历史；语音消息才使用录音回放地址。
      var text = document.createElement('div');
      text.className = 'sw-msg sw-msg-user';
      var who = document.createElement('div');
      who.className = 'sw-msg-who';
      who.textContent = mbT('You');
      text.appendChild(who);
      var body = document.createElement('div');
      esc(body, message.content);
      text.appendChild(body);
      chat.appendChild(text);
      return;
    }
    chat.appendChild(voiceMessage(message.role === 'coach' ? 'coach' : 'user',
      message.content, {
        durationMs: message.durationMs,
        audioObject: message.audioObject,
      }));
    if (message.role === 'coach' && message.feedback) {
      chat.appendChild(feedbackBlock(message.feedback));
    }
  }

  function replaySession(sessionId) {
    postJson(urls.speakingMessages, { sessionId: sessionId }).then(function (response) {
      var messages = resultOf(response) || [];
      openSession(sessionId);
      var chat = els['sw-s-chat'];
      clear(chat);
      messages.forEach(function (message) { renderMessage(chat, message); });
      scrollChat();
    }).catch(function (err) { window.alert(err.message); });
  }

  // ---------- 会话 ----------

  function statusLine(message, isError) {
    var node = els['sw-s-audio-status'];
    if (!node) return;
    node.textContent = message || '';
    node.classList.toggle('sw-status-error', !!isError);
  }

  function openSession(sessionId) {
    speaking.sessionId = sessionId;
    show(els['sw-s-setup'], false);
    show(els['sw-s-chat-panel'], true);
    show(els['sw-s-report-panel'], false);
    resetCompose();
  }

  els['sw-s-start'].addEventListener('click', function () {
    busy(els['sw-s-start'], true, mbT('Loading'));
    postJson(urls.speakingSession, {
      scenario: els['sw-s-scenario'].value,
      coachStyle: els['sw-s-style'].value,
      bookTitle: els['sw-s-book'].value || null,
    }).then(function (response) {
      var start = resultOf(response);
      openSession(start.sessionId);
      var chat = els['sw-s-chat'];
      clear(chat);
      chat.appendChild(voiceMessage('coach', start.greeting, {
        audioUrl: start.greetingAudioUrl,
      }));
      scrollChat();
      playVoice('coach', start.greeting, {
        audioUrl: start.greetingAudioUrl,
        autoplay: true,
      });
    }).catch(function (err) { window.alert(err.message); })
      .finally(function () { busy(els['sw-s-start'], false); });
  });

  function resetCompose() {
    speaking.pending = null;
    speaking.typing = false;
    statusLine('', false);
    els['sw-s-input'].value = '';
    els['sw-s-input'].readOnly = true;
    els['sw-s-input'].placeholder = mbT('Your words will appear here after recording');
    els['sw-s-send'].disabled = true;
    els['sw-s-rerecord'].hidden = true;
    els['sw-s-voice-preview'].hidden = true;
    els['sw-s-text-toggle'].textContent = mbT('Type instead');
  }

  function setPreview(recording) {
    speaking.pending = recording;
    speaking.typing = false;
    els['sw-s-input'].readOnly = false;
    els['sw-s-input'].value = recording.text;
    els['sw-s-send'].disabled = false;
    els['sw-s-rerecord'].hidden = false;
    els['sw-s-voice-preview'].hidden = false;
    els['sw-s-voice-preview'].querySelector('.sw-voice-preview-label').textContent =
      mbT('Review your transcript before sending') + ' · ' + durationLabel(recording.durationMs);
    els['sw-s-input'].focus();
  }

  function sendCurrent() {
    var text = els['sw-s-input'].value.trim();
    if (!text || !speaking.sessionId) return;
    var voice = !!speaking.pending;
    var durationMs = voice ? speaking.pending.durationMs : null;
    var audioObject = voice ? speaking.pending.audioObject : null;
    var succeeded = false;
    statusLine('', false);
    busy(els['sw-s-send'], true, mbT('Thinking…'));

    var upload = voice
      ? (speaking.pending.audioObject
        ? Promise.resolve(speaking.pending.audioObject)
        : uploadRecording(speaking.pending.wav).then(function (audioObject) {
          speaking.pending.audioObject = audioObject;
          return audioObject;
        }))
      : Promise.resolve(null);

    upload.then(function (audioObject) {
      return postJson(urls.speakingMessage, {
        sessionId: speaking.sessionId,
        text: text,
        voice: voice,
        audioObject: audioObject,
        durationMs: durationMs,
      });
    }).then(function (response) {
      var turn = resultOf(response);
      var chat = els['sw-s-chat'];
      chat.appendChild(voiceMessage('user', text, {
        durationMs: durationMs,
        audioObject: voice ? (speaking.pending || {}).audioObject || audioObject : null,
      }));
      chat.appendChild(voiceMessage('coach', turn.reply, {
        audioUrl: turn.replyAudioUrl,
      }));
      if (turn.feedback) chat.appendChild(feedbackBlock(turn.feedback));
      scrollChat();
      succeeded = true;
      resetCompose();
      playVoice('coach', turn.reply, {
        audioUrl: turn.replyAudioUrl,
        autoplay: true,
      });
    }).catch(function (err) {
      // 失败时保留 pending 与可编辑转写，用户可直接重试，不用重新录音。
      statusLine(err.message || mbT('Something went wrong'), true);
    }).finally(function () {
      busy(els['sw-s-send'], false);
      if (succeeded) {
        els['sw-s-send'].disabled = true;
      } else {
        els['sw-s-send'].disabled = !els['sw-s-input'].value.trim();
      }
    });
  }

  function uploadRecording(wav) {
    var form = new FormData();
    form.append('sessionId', speaking.sessionId);
    form.append('file', wav, 'recording.wav');
    return fetch(urls.speakingRecordingUpload, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': MB.csrfToken() },
      body: form,
    }).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok || !data || data.success !== true) {
          throw new Error((data && data.message) || mbT('Something went wrong'));
        }
        return String(data.result || '');
      });
    });
  }

  els['sw-s-send'].addEventListener('click', sendCurrent);
  els['sw-s-rerecord'].addEventListener('click', function () {
    resetCompose();
    els['sw-s-mic'].click();
  });
  els['sw-s-text-toggle'].addEventListener('click', function () {
    speaking.typing = !speaking.typing;
    if (speaking.typing) {
      speaking.pending = null;
      els['sw-s-input'].readOnly = false;
      els['sw-s-input'].placeholder = mbT('Type what you would say, in English');
      els['sw-s-send'].disabled = false;
      els['sw-s-rerecord'].hidden = true;
      els['sw-s-voice-preview'].hidden = true;
      els['sw-s-text-toggle'].textContent = mbT('Use voice instead');
      els['sw-s-input'].focus();
    } else {
      resetCompose();
    }
  });

  els['sw-s-report'].addEventListener('click', function () {
    if (!speaking.sessionId) return;
    busy(els['sw-s-report'], true, mbT('Reviewing…'));
    postJson(urls.speakingReport, { sessionId: speaking.sessionId })
      .then(function (response) {
        var report = resultOf(response);
        esc(els['sw-s-summary'], report.summary);
        esc(els['sw-s-progress-line'], report.progress);
        clear(els['sw-s-vocab']);
        (report.activeVocab || []).forEach(function (word) {
          els['sw-s-vocab'].appendChild(li(word));
        });
        clear(els['sw-s-corrections']);
        (report.corrections || []).forEach(function (item) {
          els['sw-s-corrections'].appendChild(li(
            (item.original || '') + ' → ' + (item.corrected || '') +
            (item.note ? '（' + item.note + '）' : '')));
        });
        show(els['sw-s-report-panel'], true);
        speaking.sessionId = null;
        show(els['sw-s-setup'], true);
        loadSpeakingHistory();
      })
      .catch(function (err) { window.alert(err.message); })
      .finally(function () { busy(els['sw-s-report'], false); });
  });

  window.MBLearningVoice.attach({
    micBtn: els['sw-s-mic'],
    statusEl: els['sw-s-audio-status'],
    deviceSelect: els['sw-s-mic-device'],
    onRecording: setPreview,
  });

  loadSpeakingHistory();
})();
