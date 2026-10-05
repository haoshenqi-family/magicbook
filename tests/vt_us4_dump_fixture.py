"""视觉夹具生成器（R116/US4 验证资产，不是断言测试）。

文件名不带 test_ 前缀，所以 `pytest tests/` 不会自动收集它（它会往 docs/temp 写文件）；
要重出夹具时显式点名：
    .venv/bin/python -m pytest tests/vt_us4_dump_fixture.py -q -s
再跑 docs/temp/scripts/vt_us4_shots.sh 出图。

用真实模板渲染 /reading/settings，静态资源改写成 /cps/static/... 以便经本机
127.0.0.1:8099 静态服务器（根=仓库根）打开（file:// 下出图后 Chrome 不退出），
并在 vocab-test.js 之前注入 fetch 桩（形状取自 moon-well US3 的 View 定义），
让无头 Chrome 能用 ?state=idle|asking|result|history|error 驱动到指定视图。
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATIC = ROOT / "cps" / "static"
TEMP = ROOT / "docs" / "temp"

SETTINGS = {"hardLevel": 3, "hardLevelName": "CET4", "usingDefault": False,
            "options": [{"code": i, "name": "L%d" % i} for i in range(10)]}

DRIVE = """
<script>
(function () {
  var mode = new URLSearchParams(location.search).get('state') || 'idle';
  var WORDS = [
    ["ubiquitous", "The use of smartphones has become ubiquitous in daily life."],
    ["ephemeral", "Fame on the internet is often ephemeral."],
    ["meticulous", "She kept meticulous notes of every experiment."],
    ["resilience", "The team showed remarkable resilience after the loss."],
    ["ambiguous", "The wording of the contract remained deliberately ambiguous."],
    ["candid", "He gave a candid interview about his early failures."],
    ["frugal", "A frugal lifestyle let her save for a house."],
    ["luminous", "The moon looked luminous above the lake."]
  ];
  var BANDS = [
    {band: 1, questions: 6, known: 6, rate: 1.0, contribution: 1000},
    {band: 2, questions: 6, known: 5, rate: 0.8333, contribution: 850},
    {band: 3, questions: 6, known: 4, rate: 0.6667, contribution: 800},
    {band: 4, questions: 6, known: 3, rate: 0.5, contribution: 900},
    {band: 5, questions: 6, known: 2, rate: 0.3333, contribution: 950},
    {band: 6, questions: 0, known: 0, rate: 0, contribution: 0},
    {band: 7, questions: 0, known: 0, rate: 0, contribution: 0},
    {band: 8, questions: 0, known: 0, rate: 0, contribution: 0}
  ];
  var REPORT = {sessionId: 42, status: 1, startedAt: "2026-10-05 01:10:00",
                finishedAt: "2026-10-05 01:13:40", questionCount: 30, knownCount: 20,
                estimatedSize: 8600, ciLow: 7200, ciHigh: 10000, capped: false,
                finishReason: "CONVERGED", addUnknown: true, bandResults: BANDS,
                addedToNotebook: 4};
  var HISTORY = [REPORT,
    {sessionId: 41, status: 1, startedAt: "2026-09-28 20:02:00",
     finishedAt: "2026-09-28 20:05:12", questionCount: 26, knownCount: 12,
     estimatedSize: 5200, ciLow: 4300, ciHigh: 6100, capped: false,
     finishReason: "CONVERGED", addUnknown: false, bandResults: BANDS,
     addedToNotebook: null}];

  function question(seq) {
    var pair = WORDS[(seq - 1) % WORDS.length];
    return {word: pair[0], sentence: pair[1], seq: seq, band: 3};
  }
  function env(result) {
    return JSON.stringify({success: true, code: 200, message: "", result: result});
  }
  // bootstrap modal 的 .fade 是 CSS 过渡，单帧截图会拍到半透明/位移中态，夹具里去掉
  document.getElementById('vt-overlay').classList.remove('fade');
  // 同理关掉 caliBlur 给 .col-sm-10 的 fadeIn（caliBlur.css:236）：无头 --virtual-time-budget
  // 下动画冻结在半透明，opacity<1 会造出层叠上下文（弹层 z-index 被关在里面、被导航栏盖住），
  // 拍出来的是过渡态而不是用户实际看到的稳态。
  Array.prototype.forEach.call(document.querySelectorAll('.col-sm-10'), function (el) {
    el.style.animation = 'none';
  });
  var nativeFetch = window.fetch;
  var seq = 0;
  function reply(body, status) {
    return Promise.resolve(new Response(body, {
      status: status || 200, headers: {"Content-Type": "application/json"}
    }));
  }
  window.fetch = function (url, opts) {
    var u = String(url);
    if (u.indexOf('/ajax/vocab-test/history') > -1) {
      return reply(env(mode === 'history' ? HISTORY : []));
    }
    if (u.indexOf('/ajax/vocab-test/start') > -1) {
      seq = 1;
      return reply(env({sessionId: 42, question: question(1),
                        progress: {answered: 0, known: 0, band: 3}}));
    }
    if (u.indexOf('/ajax/vocab-test/answer') > -1) {
      var sent = JSON.parse(opts.body);
      seq = sent.seq + 1;
      if (mode === 'error') {
        return reply(JSON.stringify({success: false, code: 500,
                                     message: "vocab test answer service unavailable",
                                     result: null}), 500);
      }
      if (seq > WORDS.length + 1) {
        return reply(env({question: null, finished: true,
                          progress: {answered: WORDS.length, known: WORDS.length, band: 3},
                          estimation: null}));
      }
      return reply(env({question: question(seq), finished: false,
                        progress: {answered: seq - 1, known: seq - 1, band: 3},
                        estimation: null}));
    }
    if (u.indexOf('/ajax/vocab-test/finish') > -1) {
      return reply(env(REPORT));
    }
    return nativeFetch.apply(this, arguments);
  };

  function overlayHidden() {
    var el = document.getElementById('vt-overlay');
    return getComputedStyle(el).display === 'none';
  }
  function askAgain() {
    document.getElementById('vt-known').click();
    setTimeout(tick, 40);
  }
  function tick() {
    if (mode === 'idle') return;
    if (mode === 'error') {
      if (document.getElementById('vt-word').textContent &&
          !document.getElementById('vt-error-line').hidden) return;  // 目标态已到
      if (overlayHidden()) {
        document.getElementById('vt-start').click();
        setTimeout(tick, 40);
        return;
      }
      askAgain();
      return;
    }
    if (mode === 'history') {
      var list = document.getElementById('vt-history-list');
      var toggle = document.getElementById('vt-toggle-history');
      if (!toggle.hidden && list.hidden) toggle.click();
      return;
    }
    if (mode === 'asking') {
      // 停在第二题：答一题后不再点，浮层保持 asking 态
      if (overlayHidden()) {
        document.getElementById('vt-start').click();
        setTimeout(tick, 40);
        return;
      }
      if (!askedOnce) { askedOnce = true; askAgain(); }
      return;
    }
    if (mode === 'result') {
      if (document.getElementById('vt-result').hidden) {
        if (overlayHidden()) {
          document.getElementById('vt-start').click();
        } else {
          askAgain();
        }
        setTimeout(tick, 40);
      }
      return;
    }
  }
  var askedOnce = false;
  window.addEventListener('load', function () { setTimeout(tick, 60); });
})();
</script>
"""


def _envelope(result):
    import json
    return json.dumps({"success": True, "code": 200, "message": "", "result": result}), 200


def _dump(html, name):
    # 静态资源改写成 /cps/static/...：夹具经本机已有的 127.0.0.1:8099 静态服务器（根=仓库根）打开。
    # 不用 file:// —— http 页面里 file:// 子资源会被 Chrome 拦掉，且实测 file:// 下
    # --screenshot 出图后 Chrome 不退出（挂死）。
    html = re.sub(r'(?:href|src)="/static/',
                  lambda m: m.group(0).replace('/static/', '/cps/static/'),
                  html)
    marker = 'js/vocab-test.js'
    idx = html.find(marker)
    assert idx > -1, "vocab-test.js script tag not found in rendered page"
    start = html.rfind('<script', 0, idx)
    html = html[:start] + DRIVE + html[start:]
    path = TEMP / name
    path.write_text(html, encoding="utf-8")
    print("wrote", path, len(html))


def test_dump_vt_fixture(admin_client, monkeypatch):
    import json
    import cps.web as w
    from cps import constants

    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")

    def proxy(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        assert path == "/vocabulary/reading/settings", path
        body, status = _envelope(SETTINGS)
        return body, status, {"Content-Type": "application/json"}

    monkeypatch.setattr(w, "_moonwell_proxy", proxy)
    html = admin_client.get("/reading/settings").get_data(as_text=True)
    assert 'id="vt-root"' in html
    _dump(html, "vt_us4_fixture.html")

    # caliBlur 主题（g.current_theme == 1）变体：config 是 cps/__init__ 里的 _Config 单例，
    # config_theme 是它 __getattr__ 代理到 DB 行的列，直接实例属性覆盖即可生效
    from cps import config as cps_config
    monkeypatch.setattr(cps_config, "config_theme", 1)
    blur_html = admin_client.get("/reading/settings").get_data(as_text=True)
    assert "caliBlur.css" in blur_html, "blur theme not applied"
    _dump(blur_html, "vt_us4_fixture_blur.html")
