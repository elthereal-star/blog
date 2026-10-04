/* ============================================================
   「墨序」改良版同步 —— 全局交互脚本
   纯原生 JS，零依赖；所有动效尊重 prefers-reduced-motion。

   模块：
     1. 全局 Toast 反馈
     2. 禅意伴读白噪音（Web Audio 实时合成，无外部音频文件）
     3. 桌面环境光标（mix-blend-difference 柔光点）
     4. 文章卡片光标聚光
     5. 点赞（卡片 / 文章 / 碎碎念通用，localStorage 持久化）
     6. 选中文案浮动工具栏（引用金句 / 复制）
     7. 图片灯箱
     8. 专栏页标签过滤
     9. 关于页热力图悬停读数
    10. 碎碎念：发表框 + 本地发表 + 点赞

   与 custom.js 的关系：音效统一走 window.mzSfx（custom.js 暴露），
   这里不再单独 new AudioContext，避免「音效开关」失效。
   ============================================================ */

(function () {
    "use strict";

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function $(sel, root) {
        return (root || document).querySelector(sel);
    }

    function $$(sel, root) {
        return Array.prototype.slice.call((root || document).querySelectorAll(sel));
    }

    function store(key, value) {
        try {
            if (value === undefined) return window.localStorage.getItem(key);
            if (value === null) window.localStorage.removeItem(key);
            else window.localStorage.setItem(key, value);
        } catch (e) {
            /* 隐私模式下降级 */
        }
        return null;
    }

    function readJSON(key, fallback) {
        try {
            var raw = window.localStorage.getItem(key);
            return raw ? JSON.parse(raw) : fallback;
        } catch (e) {
            return fallback;
        }
    }

    function writeJSON(key, value) {
        try {
            window.localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            /* 忽略 */
        }
    }

    function sfx(kind, pitch) {
        if (!window.mzSfx) return;
        if (kind === "pop") window.mzSfx.pop();
        else if (kind === "chime") window.mzSfx.chime(pitch || 1);
        else window.mzSfx.click();
    }

    /* =========================================================
       1. 全局 Toast
       ========================================================= */
    var toastTimer = null;

    function toast(msg) {
        var el = document.getElementById("mzToast");
        var txt = document.getElementById("mzToastText");
        if (!el || !txt) return;
        txt.textContent = msg;
        el.hidden = false;
        // 先脱离 hidden 再上 transition，否则不会播放动画
        void el.offsetWidth;
        el.classList.add("is-on");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            el.classList.remove("is-on");
            toastTimer = setTimeout(function () {
                el.hidden = true;
            }, 240);
        }, 2400);
    }

    // 暴露给 mz-reading.js
    window.mzToast = toast;

    /* =========================================================
       2. 禅意伴读白噪音
       纯 Web Audio 合成：粉噪声 buffer + 滤波 + 随机「事件音」
       （雨滴 / 木柴爆裂 / 微风起伏），零外部音频文件。
       ========================================================= */
    var ambient = (function () {
        var ctx = null;
        var master = null;
        var noiseNode = null;
        var eventTimer = null;
        var current = "none";
        var volume = 0.35;
        var volumeKey = "mz-ambient-volume";

        var savedVol = parseFloat(store(volumeKey));
        if (!isNaN(savedVol) && savedVol >= 0 && savedVol <= 1) volume = savedVol;

        function init() {
            if (!ctx) {
                var Ctx = window.AudioContext || window.webkitAudioContext;
                if (!Ctx) return false;
                ctx = new Ctx();
                master = ctx.createGain();
                master.gain.setValueAtTime(volume, ctx.currentTime);
                master.connect(ctx.destination);
            }
            if (ctx.state === "suspended") ctx.resume();
            return true;
        }

        function pinkNoise() {
            var size = ctx.sampleRate * 2;
            var buffer = ctx.createBuffer(1, size, ctx.sampleRate);
            var data = buffer.getChannelData(0);
            var b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
            for (var i = 0; i < size; i++) {
                var white = Math.random() * 2 - 1;
                b0 = 0.99886 * b0 + white * 0.0555179;
                b1 = 0.99332 * b1 + white * 0.0750759;
                b2 = 0.969 * b2 + white * 0.153852;
                b3 = 0.8665 * b3 + white * 0.3104856;
                b4 = 0.55 * b4 + white * 0.5329522;
                b5 = -0.7616 * b5 - white * 0.016898;
                data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.05;
                b6 = white * 0.115926;
            }
            return buffer;
        }

        function loopNoise(filterType, freq, q) {
            var src = ctx.createBufferSource();
            src.buffer = pinkNoise();
            src.loop = true;
            var filter = ctx.createBiquadFilter();
            filter.type = filterType;
            filter.frequency.setValueAtTime(freq, ctx.currentTime);
            if (q) filter.Q.setValueAtTime(q, ctx.currentTime);
            src.connect(filter);
            filter.connect(master);
            src.start();
            noiseNode = src;
            return filter;
        }

        function startRain() {
            var lp = ctx.createBiquadFilter();
            lp.type = "lowpass";
            lp.frequency.setValueAtTime(800, ctx.currentTime);
            var hp = ctx.createBiquadFilter();
            hp.type = "highpass";
            hp.frequency.setValueAtTime(120, ctx.currentTime);

            var src = ctx.createBufferSource();
            src.buffer = pinkNoise();
            src.loop = true;
            src.connect(lp);
            lp.connect(hp);
            hp.connect(master);
            src.start();
            noiseNode = src;

            eventTimer = window.setInterval(function () {
                if (!ctx || current !== "rain") return;
                if (Math.random() > 0.4) return;
                var osc = ctx.createOscillator();
                var g = ctx.createGain();
                osc.type = "sine";
                var f = 1200 + Math.random() * 800;
                osc.frequency.setValueAtTime(f, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(f * 0.6, ctx.currentTime + 0.06);
                g.gain.setValueAtTime(0.012, ctx.currentTime);
                g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.06);
                osc.connect(g);
                g.connect(master);
                osc.start();
                osc.stop(ctx.currentTime + 0.06);
            }, 400);
        }

        function startFireplace() {
            loopNoise("lowpass", 350);
            eventTimer = window.setInterval(function () {
                if (!ctx || current !== "fireplace") return;
                if (Math.random() > 0.35) return;
                var osc = ctx.createOscillator();
                var g = ctx.createGain();
                osc.type = "triangle";
                osc.frequency.setValueAtTime(200 + Math.random() * 600, ctx.currentTime);
                g.gain.setValueAtTime(0.02 + Math.random() * 0.03, ctx.currentTime);
                g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.03);
                osc.connect(g);
                g.connect(master);
                osc.start();
                osc.stop(ctx.currentTime + 0.03);
            }, 300);
        }

        function startBreeze() {
            var filter = loopNoise("bandpass", 450, 0.8);
            var phase = 0;
            eventTimer = window.setInterval(function () {
                if (!ctx || current !== "breeze") return;
                phase += 0.15;
                filter.frequency.setTargetAtTime(450 + Math.sin(phase) * 150, ctx.currentTime, 0.4);
            }, 400);
        }

        function play(type) {
            if (!init()) return;
            if (current === type || type === "none") {
                stop();
                return;
            }
            stop();
            current = type;
            if (type === "rain") startRain();
            else if (type === "fireplace") startFireplace();
            else if (type === "breeze") startBreeze();
        }

        function stop() {
            if (eventTimer) {
                window.clearInterval(eventTimer);
                eventTimer = null;
            }
            if (noiseNode) {
                try {
                    if (noiseNode.stop) noiseNode.stop();
                    noiseNode.disconnect();
                } catch (e) {
                    /* 忽略 */
                }
                noiseNode = null;
            }
            current = "none";
        }

        function setVolume(v) {
            volume = Math.max(0, Math.min(1, v));
            store(volumeKey, String(volume));
            if (master && ctx) master.gain.setTargetAtTime(volume, ctx.currentTime, 0.05);
        }

        return {
            play: play,
            stop: stop,
            setVolume: setVolume,
            volume: function () {
                return volume;
            },
            current: function () {
                return current;
            }
        };
    })();

    function initAmbient() {
        var modal = $("#mzAmbientModal");
        if (!modal) return;

        var dot = $("#mzAmbientDot");
        var stopBtn = $("#mzAmbStop");
        var range = $("#mzAmbVolume");
        var volLabel = $("#mzAmbVolumeLabel");
        var items = $$("[data-mz-amb]", modal);

        function render() {
            var cur = ambient.current();
            items.forEach(function (btn) {
                var on = btn.getAttribute("data-mz-amb") === cur;
                btn.classList.toggle("is-on", on);
                btn.setAttribute("aria-pressed", on ? "true" : "false");
                var state = $(".mz-amb-state", btn);
                if (state) state.textContent = on ? "播放中" : "点击开启";
                var ping = $(".mz-amb-ping", btn);
                if (ping) ping.hidden = !on;
            });
            if (stopBtn) stopBtn.hidden = cur === "none";
            if (dot) dot.hidden = cur === "none";
        }

        items.forEach(function (btn) {
            btn.addEventListener("click", function () {
                var type = btn.getAttribute("data-mz-amb");
                ambient.play(type);
                render();
                if (ambient.current() !== "none") {
                    var label = $(".mz-amb-label span", btn);
                    toast("已开启伴读背景音：" + (label ? label.textContent : type));
                }
            });
        });

        if (stopBtn) {
            stopBtn.addEventListener("click", function () {
                ambient.stop();
                render();
                sfx("click");
                toast("已停止伴读音");
            });
        }

        if (range) {
            range.value = String(ambient.volume());
            if (volLabel) volLabel.textContent = Math.round(ambient.volume() * 100) + "%";
            range.addEventListener("input", function () {
                ambient.setVolume(parseFloat(range.value));
                if (volLabel) volLabel.textContent = Math.round(ambient.volume() * 100) + "%";
            });
        }

        // 打开弹窗的入口：导航栏耳机图标 + 文章页阅读栏
        ["mzAmbientBtn", "mzAmbientOpen"].forEach(function (id) {
            var openBtn = document.getElementById(id);
            if (!openBtn) return;
            openBtn.addEventListener("click", function () {
                sfx("pop");
                if (window.mzOpenModal) window.mzOpenModal(modal);
                else modal.hidden = false;
                render();
            });
        });

        render();
    }

    /* =========================================================
       3. 桌面环境光标
       ========================================================= */
    function initCursor() {
        if (reduceMotion) return;
        if (!window.matchMedia("(pointer: fine)").matches) return;

        var dot = document.createElement("div");
        dot.className = "mz-cursor";
        dot.setAttribute("aria-hidden", "true");
        document.body.appendChild(dot);

        var tx = -100, ty = -100, cx = -100, cy = -100;
        var raf = null;

        function loop() {
            // 简单阻尼跟随，比 transition 更顺滑
            cx += (tx - cx) * 0.2;
            cy += (ty - cy) * 0.2;
            dot.style.transform = "translate(" + cx + "px," + cy + "px) translate(-50%,-50%)";
            if (Math.abs(tx - cx) > 0.4 || Math.abs(ty - cy) > 0.4) {
                raf = requestAnimationFrame(loop);
            } else {
                raf = null;
            }
        }

        window.addEventListener(
            "mousemove",
            function (e) {
                tx = e.clientX;
                ty = e.clientY;
                dot.style.opacity = "";
                if (!raf) raf = requestAnimationFrame(loop);

                var t = e.target;
                var clickable =
                    t && t.closest
                        ? t.closest("a, button, input, textarea, select, [role='button'], .mz-interactive")
                        : null;
                dot.classList.toggle("is-on-link", Boolean(clickable));
            },
            { passive: true }
        );

        document.addEventListener("mouseleave", function () {
            dot.style.opacity = "0";
        });
    }

    /* =========================================================
       4. 文章卡片光标聚光
       ========================================================= */
    function initCardSpotlight() {
        if (reduceMotion) return;
        if (!window.matchMedia("(pointer: fine)").matches) return;

        $$(".post-entry").forEach(function (card) {
            var ticking = false;
            var lastX = 0, lastY = 0;

            card.addEventListener(
                "mousemove",
                function (e) {
                    var rect = card.getBoundingClientRect();
                    lastX = e.clientX - rect.left;
                    lastY = e.clientY - rect.top;
                    if (ticking) return;
                    ticking = true;
                    requestAnimationFrame(function () {
                        card.style.setProperty("--mz-mx", lastX + "px");
                        card.style.setProperty("--mz-my", lastY + "px");
                        ticking = false;
                    });
                },
                { passive: true }
            );
        });
    }

    /* =========================================================
       5. 点赞（通用）
       存储：mz-likes = { [key]: 本机累加的点赞数 }
       展示：base（front matter 里的 likes）+ 本机累加
       ========================================================= */
    var likes = readJSON("mz-likes", {});

    function likeTotal(key, base) {
        return (base || 0) + (likes[key] || 0);
    }

    function renderLike(el) {
        var key = el.getAttribute("data-like-key");
        var base = parseInt(el.getAttribute("data-like-base") || "0", 10) || 0;
        var total = likeTotal(key, base);
        var count = $(".mz-card-like-count", el) || $(".mz-clap-count", el) || $(".mz-moment-like-count", el);
        if (count) count.textContent = String(total);
        el.classList.toggle("is-on", total > 0);
        el.setAttribute("aria-pressed", total > 0 ? "true" : "false");
        if (el.classList.contains("mz-card-like")) {
            el.setAttribute("data-zero", total === 0 ? "1" : "0");
        }
    }

    function initLikes() {
        var els = $$("[data-mz-like]");
        els.forEach(renderLike);

        // 委托：碎碎念本地新卡片是动态插入的
        document.addEventListener("click", function (e) {
            var t = e.target;
            if (!t || !t.closest) return;
            var el = t.closest("[data-mz-like]");
            if (!el) return;
            e.preventDefault();
            e.stopPropagation();

            var key = el.getAttribute("data-like-key") || "anon";
            likes[key] = (likes[key] || 0) + 1;
            writeJSON("mz-likes", likes);
            renderLike(el);

            // 交给 mz-reading.js 做连击 / 粒子
            el.dispatchEvent(
                new CustomEvent("mz:like", { bubbles: true, detail: { key: key } })
            );
        });
    }

    /* =========================================================
       6. 选中文案浮动工具栏
       ========================================================= */
    function initSelectionToolbar() {
        var bar = $("#mzSelBar");
        var article = $(".mz-article");
        if (!bar || !article) return;

        var body = $("#mzArticleBody");
        var title = article.getAttribute("data-mz-title") || document.title;
        var currentText = "";

        function hide() {
            bar.hidden = true;
            currentText = "";
        }

        function place() {
            var sel = window.getSelection();
            if (!sel || sel.isCollapsed || sel.rangeCount === 0) return hide();

            var text = sel.toString().trim();
            if (text.length < 2) return hide();

            var range = sel.getRangeAt(0);
            // 只在正文里生效
            if (!body || !body.contains(range.commonAncestorContainer)) return hide();

            var rect = range.getBoundingClientRect();
            if (!rect.width || !rect.height) return hide();

            currentText = text;
            bar.hidden = false;
            bar.style.left = rect.left + rect.width / 2 + "px";
            bar.style.top = rect.top - 10 + "px";
        }

        document.addEventListener("mouseup", function () {
            window.setTimeout(place, 0);
        });

        document.addEventListener("selectionchange", function () {
            var sel = window.getSelection();
            if (!sel || sel.isCollapsed) hide();
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") hide();
        });

        bar.addEventListener("click", function (e) {
            var btn = e.target.closest("[data-mz-sel]");
            if (!btn) return;
            var kind = btn.getAttribute("data-mz-sel");
            var payload = kind === "quote" ? "“" + currentText + "”\n——《" + title + "》" : currentText;

            function done() {
                sfx(kind === "quote" ? "pop" : "click");
                toast(kind === "quote" ? "已复制金句与文章出处" : "已复制所选纯文本");
                try {
                    var sel = window.getSelection();
                    if (sel) sel.removeAllRanges();
                } catch (err) {
                    /* 忽略 */
                }
                hide();
            }

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(payload).then(done, done);
            } else {
                var ta = document.createElement("textarea");
                ta.value = payload;
                document.body.appendChild(ta);
                ta.select();
                try {
                    document.execCommand("copy");
                } catch (err) {
                    /* 忽略 */
                }
                document.body.removeChild(ta);
                done();
            }
        });
    }

    /* =========================================================
       7. 图片灯箱
       ========================================================= */
    function initLightbox() {
        var box = $("#mzLightbox");
        var img = $("#mzLightboxImg");
        var body = $("#mzArticleBody");
        if (!box || !img || !body) return;

        function close() {
            box.hidden = true;
            img.setAttribute("src", "");
        }

        body.addEventListener("click", function (e) {
            var target = e.target;
            if (!target || target.tagName !== "IMG") return;
            // 封面 / 示意图都可以点开
            e.preventDefault();
            img.setAttribute("src", target.getAttribute("src"));
            img.setAttribute("alt", target.getAttribute("alt") || "");
            box.hidden = false;
            sfx("pop");
        });

        box.addEventListener("click", function (e) {
            // 点图片本身不关闭，点背景或按钮才关
            if (e.target === img) return;
            close();
        });

        var closeBtn = $("#mzLightboxClose");
        if (closeBtn) closeBtn.addEventListener("click", close);

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !box.hidden) close();
        });
    }

    /* =========================================================
       8. 专栏页标签过滤
       ========================================================= */
    function initTagFilter() {
        var cloud = $("#mzTagCloud");
        var groups = $("#mzCatGroups");
        if (!cloud || !groups) return;

        var chips = $$("[data-mz-tag]", cloud);
        var clearBtn = $("#mzTagClear");
        var status = $("#mzTagStatus");
        var emptyMsg = $("#mzTagEmpty");
        var selected = [];

        function apply() {
            var rows = $$("[data-mz-tags]", groups);
            var shown = 0;

            rows.forEach(function (row) {
                var tags = (row.getAttribute("data-mz-tags") || "").split("|");
                var ok = selected.every(function (t) {
                    return tags.indexOf(t) !== -1;
                });
                row.hidden = !ok;
                if (ok) shown++;
            });

            // 整组都没命中时把分组头也藏起来
            $$(".mz-catgroup", groups).forEach(function (g) {
                var any = $$("[data-mz-tags]", g).some(function (r) {
                    return !r.hidden;
                });
                g.hidden = !any;
            });

            chips.forEach(function (chip) {
                var on = selected.indexOf(chip.getAttribute("data-mz-tag")) !== -1;
                chip.classList.toggle("is-active", on);
                chip.setAttribute("aria-pressed", on ? "true" : "false");
            });

            if (clearBtn) clearBtn.hidden = selected.length === 0;

            if (status) {
                if (selected.length === 0) {
                    status.hidden = true;
                } else {
                    status.hidden = false;
                    status.innerHTML =
                        "正在筛选同时带有 " +
                        selected
                            .map(function (t) {
                                return "<strong>#" + t + "</strong>";
                            })
                            .join(" + ") +
                        " 的文章，共 <strong>" + shown + "</strong> 篇";
                }
            }

            if (emptyMsg) emptyMsg.hidden = shown !== 0;
        }

        chips.forEach(function (chip) {
            chip.addEventListener("click", function () {
                var tag = chip.getAttribute("data-mz-tag");
                var i = selected.indexOf(tag);
                if (i === -1) selected.push(tag);
                else selected.splice(i, 1);
                sfx("click");
                apply();
            });
        });

        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                selected = [];
                sfx("click");
                apply();
            });
        }

        apply();
    }

    /* =========================================================
       9. 关于页热力图悬停读数
       ========================================================= */
    function initHeatmap() {
        var heat = $("#mzHeat");
        if (!heat) return;
        var label = $("#mzHeatLabel");
        if (!label) return;
        var initial = label.textContent;

        $$(".mz-heat-cell", heat).forEach(function (cell) {
            cell.addEventListener("mouseenter", function () {
                var date = cell.getAttribute("data-date");
                var count = cell.getAttribute("data-count");
                if (cell.classList.contains("is-future")) {
                    label.textContent = date + " · 还没到";
                } else if (count === "0") {
                    label.textContent = date + " · 无记录";
                } else {
                    label.textContent = date + " · " + count + " 篇";
                }
                cell.classList.add("is-active");
            });
            cell.addEventListener("mouseleave", function () {
                cell.classList.remove("is-active");
                label.textContent = initial;
            });
        });
    }

    /* =========================================================
       10. 碎碎念：发表 + 本地存储
       ========================================================= */
    function initMoments() {
        var page = $("#mzMomentsPage");
        if (!page) return;

        var composer = $("#mzMomentComposer");
        var openBtn = $("#mzMomentCompose");
        var cancelBtn = $("#mzMomentCancel");
        var input = $("#mzMomentInput");
        var submit = $("#mzMomentSubmit");
        var chips = $$(".mz-mood-chip", page);
        var list = $("#mzMomentList");
        var countEl = $("#mzMomentCount");
        if (!composer || !list) return;

        var moods = [];
        try {
            moods = JSON.parse(composer.getAttribute("data-moods") || "[]");
        } catch (e) {
            moods = [];
        }
        var mood = moods[0] || "💭 闪念记录";
        var location = composer.getAttribute("data-placeholder") || "生活手记";
        var key = "mz-moments";
        var local = readJSON(key, []);

        function escapeHTML(s) {
            return String(s)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;");
        }

        function today() {
            var d = new Date();
            function p(n) {
                return String(n).padStart(2, "0");
            }
            return {
                date: d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()),
                time: p(d.getHours()) + ":" + p(d.getMinutes()),
            };
        }

        function build(lite) {
            var article = document.createElement("article");
            article.className = "mz-moment is-local";
            article.setAttribute("data-mz-moment", "");
            article.innerHTML =
                '<div class="mz-moment-meta">' +
                '<span class="mz-moment-time"><span>' + lite.date + '</span><span>' + lite.time + "</span></span>" +
                '<span aria-hidden="true">·</span>' +
                '<span class="mz-moment-mood">' + escapeHTML(lite.mood) + "</span>" +
                '<span aria-hidden="true">·</span>' +
                '<span class="mz-moment-loc"><span>' + escapeHTML(lite.location) + "</span></span>" +
                "</div>" +
                '<p class="mz-moment-text">' + escapeHTML(lite.content) + "</p>" +
                '<div class="mz-moment-foot">' +
                '<span class="mz-moment-hash">#即时闪念 · 仅本机可见</span>' +
                '<button class="mz-moment-like" type="button" data-mz-like data-like-key="' +
                escapeHTML(lite.id) + '" data-like-base="1" aria-pressed="false">' +
                '<span class="mz-moment-like-count">1</span>' +
                "</button>" +
                "</div>";
            return article;
        }

        function refreshCount() {
            if (!countEl) return;
            countEl.textContent = String($$("[data-mz-moment]", list).length);
        }

        // 渲染上一次在本机发表的
        local
            .slice()
            .reverse()
            .forEach(function (m) {
                list.insertBefore(build(m), list.firstChild);
            });
        refreshCount();

        function setOpen(on) {
            composer.hidden = !on;
            if (on && input) {
                window.setTimeout(function () {
                    input.focus();
                }, 60);
            }
        }

        if (openBtn) {
            openBtn.addEventListener("click", function () {
                sfx("click");
                setOpen(composer.hidden);
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener("click", function () {
                setOpen(false);
            });
        }

        chips.forEach(function (chip) {
            chip.addEventListener("click", function () {
                chips.forEach(function (c) {
                    c.classList.remove("is-active");
                });
                chip.classList.add("is-active");
                mood = chip.getAttribute("data-mz-mood") || mood;
                sfx("click");
            });
        });

        if (input && submit) {
            input.addEventListener("input", function () {
                submit.disabled = !input.value.trim();
            });
        }

        composer.addEventListener("submit", function (e) {
            e.preventDefault();
            if (!input || !input.value.trim()) return;
            var t = today();
            var lite = {
                id: "local-" + Date.now(),
                content: input.value.trim(),
                date: t.date,
                time: t.time,
                mood: mood,
                location: location,
            };
            local.push(lite);
            writeJSON(key, local);

            list.insertBefore(build(lite), list.firstChild);
            if (page.querySelector(".mz-empty")) {
                var empty = page.querySelector(".mz-empty");
                if (empty && empty.parentNode === list) empty.remove();
            }
            input.value = "";
            submit.disabled = true;
            setOpen(false);
            refreshCount();
            toast("碎碎念已发表（只存在本机浏览器）");
            sfx("pop");
        });
    }

    /* =========================================================
       启动
       ========================================================= */
    function boot() {
        initAmbient();
        initCursor();
        initCardSpotlight();
        initLikes();
        initSelectionToolbar();
        initLightbox();
        initTagFilter();
        initHeatmap();
        initMoments();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
