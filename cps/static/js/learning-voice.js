// 语音输入（R166 自 speaking_writing.js 迁出；采集/转写链路属 R155/R158/R159/R160）。
//
// Why 单独一个文件：只有口语陪练与复述训练两页要麦克风，中枢与其余四页
// 不必载这 200 行 WebAudio。
//
// Why 不用 MediaRecorder：其产物 webm/opus 在 SiliconFlow 转写端兼容性存疑，
// 且浏览器间编码不可控；WebAudio 拿原始 PCM 后在采集端编码 16k 单声道 wav
//（≈32KB/s，3 分钟 <6MB），上游转写链路只见标准音频。ScriptProcessor 虽已
// 被标记过时，但兼容性最稳，个人工具量级足够。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, esc = MB.esc;
  var urls = window.learningUrls || {};

  var DEVICE_KEY = 'sw-mic-device';   // 沿用 R160 的键，站内已存的设备选择继续生效

  function readDevice() {
    try { return window.localStorage.getItem(DEVICE_KEY); } catch (e) { /* 隐私模式降级默认 */ }
    return null;
  }

  function writeDevice(value) {
    try {
      if (value) window.localStorage.setItem(DEVICE_KEY, value);
      else window.localStorage.removeItem(DEVICE_KEY);
    } catch (e) { /* 隐私模式忽略 */ }
  }

  function encodeWav(chunks, inputRate) {
    var targetRate = 16000;
    var count = 0;
    chunks.forEach(function (chunk) { count += chunk.length; });
    // 先合并成单条 PCM（逐块索引在 3 分钟音频上会是百万次链表遍历）
    var merged = new Float32Array(count);
    var offset = 0;
    chunks.forEach(function (chunk) {
      merged.set(chunk, offset);
      offset += chunk.length;
    });
    var outLength = Math.max(1, Math.floor(count * targetRate / inputRate));
    var samples = new Int16Array(outLength);
    for (var i = 0; i < outLength; i++) {
      var pos = i * inputRate / targetRate;
      var index = Math.floor(pos);
      var frac = pos - index;
      var a = merged[Math.min(index, count - 1)];
      var b = merged[Math.min(index + 1, count - 1)];
      var sample = a + (b - a) * frac;
      samples[i] = Math.max(-32768, Math.min(32767, Math.round(sample * 32767)));
    }
    var buffer = new ArrayBuffer(44 + samples.length * 2);
    var view = new DataView(buffer);
    function str(off, value) {
      for (var i = 0; i < value.length; i++) view.setUint8(off + i, value.charCodeAt(i));
    }
    str(0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true); str(8, 'WAVE');
    str(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, targetRate, true);
    view.setUint32(28, targetRate * 2, true); view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    str(36, 'data'); view.setUint32(40, samples.length * 2, true);
    new Int16Array(buffer, 44).set(samples);
    return new Blob([buffer], { type: 'audio/wav' });
  }

  var recorder = { ctx: null, stream: null, source: null, processor: null,
                   chunks: [], startedAt: 0, timerId: null };

  function recorderStart(onTick) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return Promise.reject(new Error(mbT('Microphone unavailable')));
    }
    // R160：浏览器 per-site 会记住旧设备、系统默认切换不影响已钉住的站内选择，
    // 这里显式按用户选择取流
    var saved = readDevice();
    var constraints = { audio: { channelCount: 1 } };
    if (saved) constraints.audio.deviceId = { exact: saved };
    return navigator.mediaDevices.getUserMedia(constraints)
      .then(function (stream) {
        var AudioCtx = window.AudioContext || window.webkitAudioContext;
        recorder.ctx = new AudioCtx();
        recorder.stream = stream;
        recorder.source = recorder.ctx.createMediaStreamSource(stream);
        recorder.processor = recorder.ctx.createScriptProcessor(4096, 1, 1);
        recorder.chunks = [];
        recorder.startedAt = Date.now();
        recorder.processor.onaudioprocess = function (event) {
          recorder.chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
        };
        if (recorder.ctx.state === 'suspended') recorder.ctx.resume();
        recorder.source.connect(recorder.processor);
        recorder.processor.connect(recorder.ctx.destination);
        recorder.timerId = setInterval(function () {
          var seconds = Math.round((Date.now() - recorder.startedAt) / 1000);
          onTick(mbT('Recording {{t}}').replace('{{t}}',
            Math.floor(seconds / 60) + ':' + ('0' + (seconds % 60)).slice(-2)));
        }, 500);
      });
  }

  function recorderStop() {
    if (recorder.timerId) { clearInterval(recorder.timerId); recorder.timerId = null; }
    try {
      if (recorder.processor) recorder.processor.onaudioprocess = null;
      if (recorder.processor) recorder.processor.disconnect();
      if (recorder.source) recorder.source.disconnect();
      if (recorder.stream) recorder.stream.getTracks().forEach(function (t) { t.stop(); });
    } catch (e) { /* 已停止时忽略 */ }
    var rate = recorder.ctx ? recorder.ctx.sampleRate : 48000;
    var chunks = recorder.chunks.slice();
    if (recorder.ctx && recorder.ctx.close) recorder.ctx.close();
    recorder.ctx = null; recorder.processor = null; recorder.source = null;
    recorder.stream = null;
    if (!chunks.length) return Promise.reject(new Error(mbT('Recording too short')));
    var maxAmp = 0;
    chunks.forEach(function (chunk) {
      for (var i = 0; i < chunk.length; i++) {
        var abs = Math.abs(chunk[i]);
        if (abs > maxAmp) maxAmp = abs;
      }
    });
    // R159：实测用户链路曾把全静音录音送进引擎（200+空文本→50517 不可读）。
    // 阈值 -46dB（0.005）：低于它几乎必然是设备静音/选错输入源，直接给可操作提示
    console.info('[voice] recording peak amplitude:', maxAmp.toFixed(4));
    if (maxAmp < 0.005) {
      return Promise.reject(new Error(mbT('Microphone captured no sound — check the system input device or mute switch')));
    }
    return Promise.resolve(encodeWav(chunks, rate));
  }

  function transcribeRecording() {
    var seconds = Math.round((Date.now() - recorder.startedAt) / 1000);
    if (seconds < 1) return Promise.reject(new Error(mbT('Recording too short')));
    return recorderStop().then(function (blob) {
      var form = new FormData();
      form.append('file', blob, 'recording.wav');
      return fetch(urls.asrTranscribe, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': MB.csrfToken() },
        body: form,
      }).then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok || !data || data.success !== true) {
            throw new Error((data && data.message) || mbT('Something went wrong'));
          }
          var text = String(data.result && data.result.text || '').trim();
          if (!text) throw new Error(mbT('No speech detected'));
          return text;
        });
      });
    });
  }

  function micLabel(btn, text) {
    var label = btn.querySelector('.sw-mic-label');
    if (label) label.textContent = text;
  }

  function refreshDeviceSelect(select) {
    if (!select || !navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
    navigator.mediaDevices.enumerateDevices().then(function (devices) {
      var mics = devices.filter(function (d) { return d.kind === 'audioinput'; });
      var saved = readDevice();
      MB.clear(select);
      var def = document.createElement('option');
      def.value = '';
      def.textContent = mbT('Default (follow system)');
      select.appendChild(def);
      mics.forEach(function (d, index) {
        var opt = document.createElement('option');
        opt.value = d.deviceId;
        // 权限未授予时 label 为空——占位编号，授予后 devicechange/再次刷新会带出真名
        opt.textContent = d.label || mbT('Microphone {{n}}').replace('{{n}}', index + 1);
        select.appendChild(opt);
      });
      select.value = saved && mics.some(function (d) { return d.deviceId === saved; })
        ? saved : '';
    }).catch(function () { /* 枚举失败保持默认 */ });
  }

  /**
   * 挂一个麦克风按钮。状态全在按钮上自更新：语音输入 → 录音中 mm:ss（红底，
   * 再点停止）→ 转写中…；图标字体缺失时按钮仍有文字，不再是「空白按钮」（R156）。
   *
   * idleLabel 取按钮当前文案而非写死英文：R166 前复位用的是硬编码 'Voice input'，
   * 中文用户录完一次后标签会跳回英文。
   */
  function attach(options) {
    var btn = options.micBtn;
    var statusNode = options.statusEl;
    if (!btn) return;
    var idle = (btn.querySelector('.sw-mic-label') || {}).textContent || '';
    function reset() {
      micLabel(btn, idle);
      btn.disabled = false;
    }
    if (options.deviceSelect) {
      options.deviceSelect.addEventListener('focus', function () {
        refreshDeviceSelect(options.deviceSelect);
      });
      options.deviceSelect.addEventListener('change', function () {
        writeDevice(options.deviceSelect.value);
      });
      if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
        navigator.mediaDevices.addEventListener('devicechange', function () {
          refreshDeviceSelect(options.deviceSelect);
        });
      }
      refreshDeviceSelect(options.deviceSelect);
    }
    btn.addEventListener('click', function () {
      if (!btn.classList.contains('sw-rec')) {
        btn.classList.add('sw-rec');
        micLabel(btn, mbT('Recording {{t}}').replace('{{t}}', '0:00')
          + ' · ' + mbT('click to stop'));
        recorderStart(function (label) {
          if (statusNode) esc(statusNode, label);
          micLabel(btn, label + ' · ' + mbT('click to stop'));
        }).catch(function (err) {
          btn.classList.remove('sw-rec');
          if (statusNode) esc(statusNode, '');
          reset();
          window.alert(err.message);
        });
        return;
      }
      btn.classList.remove('sw-rec');
      btn.disabled = true;
      micLabel(btn, mbT('Transcribing…'));
      if (statusNode) esc(statusNode, '');
      // R158：同步段抛错也必须复原按钮——此前 statusNode 未注册时同步 TypeError
      // 让按钮永远停在「转写中…」且无任何提示
      try {
        transcribeRecording().then(function (text) {
          reset();
          options.onText(text);
        }).catch(function (err) {
          reset();
          window.alert(err.message);
        });
      } catch (err) {
        reset();
        window.alert(err.message);
      }
    });
  }

  window.MBLearningVoice = { attach: attach };
})();
