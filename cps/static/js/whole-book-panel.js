/* R214 子项 C：整本任务代价面板（LLD §7）。
 *
 * 零界面文案：所有句式来自 #whole-book-panel 的 data-t-*，本文件只做数字与状态替换。
 * Why：JS 里硬编码中文会绕开 i18n 契约（tests/test_i18n_seed_contract.py 校验 msgid
 * 清单），B 轮的 book-insight.js 同一纪律。
 *
 * 只读边界：本文件只调 /ajax/whole-book-estimate（估算）与既有 start/status 端点；
 * 估算路径绝不建批次——「先看代价再决定」是这块存在的唯一理由。
 */
(function () {
    'use strict';

    // 轮询间隔（LLD §7.4）：翻译 4s / 朗读 5s / 详解 30s。
    // 详解慢是有原因的——它有服务端一次索引级聚合探针，快轮询等于反复扫索引。
    var POLL_INTERVAL = {translate: 4000, tts: 5000, wordDetail: 30000};
    var ACTIVE_STATUSES = ['PENDING', 'RUNNING', 'PARTIAL_FAILED'];
    var STATUS_URL = {translate: 'translateStatus', tts: 'ttsStatus', wordDetail: 'wordDetailProgress'};
    // 一本书上多链路并存时，进度条只跟最先出现的一条（其余算异常，不抢进度条）。
    var KIND_ORDER = ['translate', 'tts', 'wordDetail'];

    function fmtNum(value) {
        if (value === null || value === undefined || value === '') {
            return '0';
        }
        var n = Number(value);
        if (isNaN(n)) {
            return String(value);
        }
        return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    $(function () {
        var $panel = $('#whole-book-panel');
        if (!$panel.length) {
            return;
        }
        var el = $panel[0];

        var texts = {};
        $.each(el.attributes, function (index, attr) {
            if (attr.name.indexOf('data-t-') === 0) {
                texts[attr.name.slice('data-t-'.length)] = attr.value;
            }
        });

        var cfg = {
            bookId: $panel.data('book-id'),
            bookFormat: $panel.data('book-format'),
            csrf: $panel.data('csrf-token'),
            urls: {
                estimate: $panel.data('url-estimate'),
                translateStart: $panel.data('url-translate-start'),
                translateStatus: $panel.data('url-translate-status'),
                ttsStart: $panel.data('url-tts-start'),
                ttsStatus: $panel.data('url-tts-status'),
                wordDetailProgress: $panel.data('url-word-detail-progress'),
                wordDetailPage: $panel.data('url-word-detail-page')
            }
        };

        var state = {
            kind: 'translate',
            estimates: {},
            loading: {},
            job: {},
            timers: {}
        };

        function t(key, vars) {
            var tpl = texts[key];
            if (tpl === undefined) {
                return '';
            }
            // 模板里写的是 \n 字面量（HTML 属性不认转义），这里还原成真换行。
            tpl = tpl.replace(/\\n/g, '\n');
            if (!vars) {
                return tpl;
            }
            return tpl.replace(/\{(\w+)\}/g, function (match, name) {
                return (vars[name] === undefined || vars[name] === null) ? match : String(vars[name]);
            });
        }

        function fmtDuration(seconds) {
            var value = Number(seconds) || 0;
            if (value < 60) {
                return Math.round(value) + ' ' + t('unit-second');
            }
            if (value < 3600) {
                return Math.round(value / 60) + ' ' + t('unit-minute');
            }
            var hours = value / 3600;
            return (hours >= 10 ? Math.round(hours) : Math.round(hours * 10) / 10) + ' ' + t('unit-hour');
        }

        function cardOf(kind) {
            return $('.wb-card[data-kind="' + kind + '"]');
        }

        function setPending(kind) {
            var $card = cardOf(kind);
            $card.find('.wb-units, .wb-coverage, .wb-duration, .wb-credits').text(t('loading'));
            $card.find('.wb-note').removeClass('text-danger').text('');
        }

        function render(kind) {
            var data = state.estimates[kind];
            var $card = cardOf(kind);
            if (!data) {
                return;
            }
            if (data.error) {
                $card.find('.wb-units, .wb-coverage, .wb-duration, .wb-credits').text('—');
                // 失败要看得见：灰色说明句与「暂无数据」长得一样，红字才不会被人当成没数据。
                $card.find('.wb-note').addClass('text-danger').text(data.error);
                updateStart(kind);
                return;
            }

            var units = data.units || {};
            var coverage = data.coverage || {};
            var duration = data.duration || {};
            var credits = data.credits || {};

            $card.find('.wb-units').text(kind === 'wordDetail'
                ? t('units-word', {
                    chapters: fmtNum(units.chapters),
                    billable: fmtNum(units.billable),
                    englishWords: fmtNum(units.englishWords)
                })
                : t('units-text', {
                    chapters: fmtNum(units.chapters),
                    paragraphs: fmtNum(units.paragraphs),
                    chars: fmtNum(units.chars),
                    billable: fmtNum(units.billable)
                }));

            if (kind === 'tts') {
                $card.find('.wb-coverage').text(t('coverage-tts'));
            } else if (coverage.known) {
                var remaining = Math.max(0, (coverage.total || 0) - (coverage.cached || 0));
                $card.find('.wb-coverage').text(kind === 'wordDetail'
                    ? t('coverage-word', {
                        cached: fmtNum(coverage.cached),
                        total: fmtNum(coverage.total),
                        remaining: fmtNum(remaining)
                    })
                    : t('coverage', {
                        cached: fmtNum(coverage.cached),
                        total: fmtNum(coverage.total),
                        remaining: fmtNum(remaining)
                    }));
            } else {
                $card.find('.wb-coverage').text(t('coverage-unavailable'));
            }

            if (duration.known && duration.seconds !== null && duration.seconds !== undefined) {
                $card.find('.wb-duration').text(duration.basis === 'history'
                    ? t('duration-history', {
                        value: fmtDuration(duration.seconds),
                        samples: fmtNum(duration.samples)
                    })
                    : t('duration-constant', {value: fmtDuration(duration.seconds)}));
            } else {
                $card.find('.wb-duration').text(t('duration-unknown'));
            }

            var creditsText;
            if (credits.known) {
                creditsText = t('credits', {value: fmtNum(credits.estimated)});
                if (credits.upperBound && credits.upperBound !== credits.estimated) {
                    creditsText += t('credits-upper', {value: fmtNum(credits.upperBound)});
                }
            } else if (credits.reason === 'tts-not-billed') {
                creditsText = t('credits-tts-off');
            } else {
                creditsText = t('credits-unavailable');
            }
            $card.find('.wb-credits').text(creditsText);

            var active = (data.activeJobs || {})[kind];
            $card.find('.wb-note').removeClass('text-danger').text(active
                ? t('active', {done: fmtNum(active.done), total: fmtNum(active.total)})
                : '');
            updateStart(kind);
        }

        function updateStart(kind) {
            if (kind !== state.kind) {
                return;
            }
            var data = state.estimates[kind] || {};
            var active = (data.activeJobs || {})[kind];
            var $btn = $('#wb-start');
            // Why toLowerCase：HTML 解析器会把属性名统一小写（模板里写 data-t-start-wordDetail，
            // 存下来是 data-t-start-worddetail，texts 的键因此全小写），而 kind 是 camelCase。
            // 不折一下，详解 tab 的按钮文案会是空字符串。
            $btn.text(t('start-' + String(kind).toLowerCase()));
            // 有活跃批次就不给「开始」——再点一次只是幂等复用，不如直接把进度显示出来。
            $btn.prop('disabled', !!data.error || !!active);
        }

        function load(kind, force) {
            if (!force && state.estimates[kind]) {
                render(kind);
                return;
            }
            if (state.loading[kind]) {
                return;
            }
            state.loading[kind] = true;
            setPending(kind);
            $.ajax({
                url: cfg.urls.estimate,
                method: 'POST',
                contentType: 'application/json',
                headers: {'X-CSRFToken': cfg.csrf},
                data: JSON.stringify({
                    book_id: cfg.bookId,
                    book_format: cfg.bookFormat,
                    kind: kind
                })
            }).done(function (response) {
                state.estimates[kind] = (response && response.result) || response || {};
                render(kind);
            }).fail(function (xhr) {
                var message = (xhr.responseJSON && xhr.responseJSON.message) ||
                    (xhr.status + ' ' + (xhr.statusText || ''));
                state.estimates[kind] = {error: t('error', {message: message})};
                render(kind);
            }).always(function () {
                state.loading[kind] = false;
            });
        }

        function renderProgress(kind) {
            var job = state.job[kind];
            if (!job) {
                return;
            }
            var $bar = $('#whole-book-progress');
            $bar.prop('hidden', false);
            var percent = job.total > 0 ? Math.min(100, Math.round(job.done * 100 / job.total)) : 0;
            $bar.find('.progress-bar')
                .css('width', percent + '%')
                .attr('aria-valuenow', percent)
                .text(percent + '%');
            $bar.find('.wb-progress-count').text(fmtNum(job.done) + ' / ' + fmtNum(job.total));

            var label = t('start-' + kind);
            if (job.status === 'COMPLETED') {
                label = t('progress-done');
            } else if (job.status === 'CANCELED' || job.status === 'CANCELLED') {
                label = t('progress-cancelled');
            } else if (job.status === 'PARTIAL_FAILED') {
                label = t('progress-failed');
            }
            $bar.find('.wb-progress-title').text(label);
            $bar.toggleClass('wb-progress-done', job.status === 'COMPLETED');
        }

        function stopPoll(kind) {
            if (state.timers[kind]) {
                window.clearInterval(state.timers[kind]);
                delete state.timers[kind];
            }
        }

        function applyProgress(kind, snapshot) {
            if (!snapshot || snapshot.status === 'NONE') {
                return;
            }
            var total = snapshot.totalCount !== undefined ? snapshot.totalCount
                : (snapshot.targetWords !== undefined ? snapshot.targetWords : snapshot.total);
            var done = snapshot.completedCount !== undefined ? snapshot.completedCount
                : (snapshot.coveredWords !== undefined ? snapshot.coveredWords : snapshot.done);
            var current = state.job[kind] || {};
            state.job[kind] = {
                jobId: snapshot.jobId || current.jobId,
                status: snapshot.status || 'RUNNING',
                total: Number(total) || 0,
                done: Number(done) || 0
            };
            renderProgress(kind);
            if (ACTIVE_STATUSES.indexOf(state.job[kind].status) === -1) {
                stopPoll(kind);
                // 批次结束后缓存率变了，重算一次；失败就保留旧数字（不显示假的新值）。
                load(kind, true);
            }
        }

        function poll(kind) {
            stopPoll(kind);
            var tick = function () {
                var job = state.job[kind];
                if (!job || !job.jobId) {
                    return;
                }
                var payload = kind === 'wordDetail'
                    ? {book_id: cfg.bookId}
                    : {job_id: job.jobId};
                $.ajax({
                    url: cfg.urls[STATUS_URL[kind]],
                    method: 'POST',
                    contentType: 'application/json',
                    headers: {'X-CSRFToken': cfg.csrf},
                    data: JSON.stringify(payload)
                }).done(function (snapshot) {
                    applyProgress(kind, snapshot);
                }).fail(function () {
                    // 单轮轮询失败不打断：下一轮再试，不把临时网络抖动报成失败。
                });
            };
            tick();
            state.timers[kind] = window.setInterval(tick, POLL_INTERVAL[kind] || 5000);
        }

        function startJob(kind) {
            var data = state.estimates[kind] || {};
            var $btn = $('#wb-start');
            var title = t('start-' + kind);
            var durationKnown = data.duration && data.duration.known;
            var creditsKnown = data.credits && data.credits.known;
            var message = (durationKnown && creditsKnown)
                ? t('confirm', {
                    title: title,
                    duration: fmtDuration(data.duration.seconds),
                    credits: fmtNum(data.credits.estimated)
                })
                : t('confirm-unknown', {title: title});
            if (!window.confirm(message)) {
                return;
            }

            var url = kind === 'tts' ? cfg.urls.ttsStart : cfg.urls.translateStart;
            var payload = kind === 'tts'
                ? {book_id: cfg.bookId, book_format: cfg.bookFormat}
                : {book_id: cfg.bookId, book_format: cfg.bookFormat, force: true};

            $btn.prop('disabled', true);
            $.ajax({
                url: url,
                method: 'POST',
                contentType: 'application/json',
                headers: {'X-CSRFToken': cfg.csrf},
                data: JSON.stringify(payload)
            }).done(function (snapshot) {
                $panel.modal('hide');
                var total = snapshot.totalCount !== undefined ? snapshot.totalCount : snapshot.total;
                var done = snapshot.completedCount !== undefined
                    ? snapshot.completedCount
                    : (snapshot.coveredWords !== undefined ? snapshot.coveredWords : snapshot.done);
                state.job[kind] = {
                    jobId: snapshot.jobId,
                    status: snapshot.status || 'RUNNING',
                    total: Number(total) || 0,
                    done: Number(done) || 0
                };
                renderProgress(kind);
                poll(kind);
            }).fail(function (xhr) {
                var message = (xhr.responseJSON && xhr.responseJSON.message) ||
                    (xhr.status + ' ' + (xhr.statusText || ''));
                cardOf(kind).find('.wb-note').text(t('error', {message: message}));
            }).always(function () {
                $btn.prop('disabled', false);
            });
        }

        // ---- 事件接线 ----

        // 入口按钮自己打开面板，不走 Bootstrap 的 data-api。
        // Why：data-api 从 `data-target` 选元素，选不到时静默空转；验收现场出现过
        // 「点整本任务把整页套进另一个弹层」的错乱。显式绑定 + preventDefault 之后，
        // 这个按钮的行为只由这里决定，也不会有祖先链接抢走这次点击。
        $('#whole-book-panel-open').on('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            $panel.modal('show');
        });

        $panel.on('show.bs.modal', function () {
            load(state.kind);
        });

        $panel.find('.wb-tabs a[data-toggle="tab"]').on('shown.bs.tab', function (event) {
            state.kind = $(event.target).data('kind') || 'translate';
            load(state.kind);
            updateStart(state.kind);
        });

        $('#wb-start').on('click', function () {
            if (state.kind === 'wordDetail') {
                // 详解保持两步式页面（R176）：只读预览页有更精确的词数与 notWordLike，
                // 面板这一层只负责把人送到那儿，不替他把单下了。
                window.location.href = cfg.urls.wordDetailPage;
                return;
            }
            startJob(state.kind);
        });

        $('#whole-book-progress .wb-progress-close').on('click', function () {
            $(this).closest('#whole-book-progress').prop('hidden', true);
        });

        // 页面加载时有活跃批次 → 直接进度态（LLD §7.5），不再显示「开始」。
        (function bootstrap() {
            var raw = $('#whole-book-active').text();
            if (!raw) {
                return;
            }
            var active;
            try {
                active = JSON.parse(raw) || {};
            } catch (error) {
                return;
            }
            for (var index = 0; index < KIND_ORDER.length; index += 1) {
                var kind = KIND_ORDER[index];
                var job = active[kind];
                if (!job) {
                    continue;
                }
                state.job[kind] = {
                    jobId: job.jobId,
                    status: job.status || 'RUNNING',
                    total: Number(job.total) || 0,
                    done: Number(job.done) || 0
                };
                renderProgress(kind);
                poll(kind);
                break;
            }
        }());
    });
}());
