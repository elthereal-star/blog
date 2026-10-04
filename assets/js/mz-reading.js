/* ============================================================
   「墨序」改良版同步 —— 文章页阅读增强脚本
   只在含 .mz-article 的页面起作用（模板：layouts/single.html）。

   模块：
     1. 阅读偏好（衬线/黑体 · 字号三档 · 正文宽度三档）→ localStorage
     2. 专注模式（隐藏干扰，ESC 退出）
     3. 阅读进度条
     4. 「预计 HH:MM 读完」
     5. Claps 连击点赞（xN 徽章 + emoji 粒子 + 音高递增）
     6. 免登录评论（localStorage，按文章隔离）
     7. 分享书签卡片弹窗（米白 / 羊皮纸 / 墨夜）

   点赞的计数与持久化在 mz-base.js 里统一处理，这里只订阅 mz:like 事件
   做「连击 / 粒子 / 音效」的附加表现。
   ============================================================ */

(function () {
    "use strict";

    var article = document.querySelector(".mz-article");
    if (!article) return;

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var root = document.documentElement;

    function $(sel, ctx) {
        return (ctx || document).querySelector(sel);
    }

    function $$(sel, ctx) {
        return Array.prototype.slice.call((ctx || document).querySelectorAll(sel));
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

    function readStr(key, fallback) {
        try {
            return window.localStorage.getItem(key) || fallback;
        } catch (e) {
            return fallback;
        }
    }

    function writeStr(key, value) {
        try {
            window.localStorage.setItem(key, value);
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

    function toast(msg) {
        if (window.mzToast) window.mzToast(msg);
    }

    /* =========================================================
       1. 阅读偏好
       ========================================================= */
    var SIZES = ["sm", "base", "lg"];
    var WIDTHS = ["compact", "normal", "wide"];

    function initPrefs() {
        var wrap = $("#mzReadWrap");
        if (!wrap) return;

        var prefs = readJSON("mz-read-prefs", { font: "serif", size: "base", width: "normal" });
        if (SIZES.indexOf(prefs.size) === -1) prefs.size = "base";
        if (WIDTHS.indexOf(prefs.width) === -1) prefs.width = "normal";
        if (prefs.font !== "sans") prefs.font = "serif";

        var fontBtn = $("#mzFontBtn");
        var fontLabel = $("#mzFontLabel");
        var widthBtn = $("#mzWidthBtn");
        var widthLabel = $("#mzWidthLabel");
        var sizeBtns = $$("[data-mz-size]", wrap.parentNode);

        function render() {
            wrap.setAttribute("data-mz-font", prefs.font);
            wrap.setAttribute("data-mz-size", prefs.size);
            wrap.setAttribute("data-mz-width", prefs.width);
            // 宽度同时写到 :root，好让 .main 的宽度限制跟着变
            root.setAttribute("data-mz-width", prefs.width);

            if (fontLabel) fontLabel.textContent = prefs.font === "serif" ? "Serif" : "Sans";
            if (widthLabel) widthLabel.textContent = prefs.width;

            sizeBtns.forEach(function (btn) {
                var dir = btn.getAttribute("data-mz-size");
                btn.disabled = (dir === "-" && prefs.size === "sm") || (dir === "+" && prefs.size === "lg");
            });

            writeJSON("mz-read-prefs", prefs);
        }

        if (fontBtn) {
            fontBtn.addEventListener("click", function () {
                prefs.font = prefs.font === "serif" ? "sans" : "serif";
                render();
                sfx("click");
                toast(prefs.font === "serif" ? "正文已切换为衬线体" : "正文已切换为无衬线体");
            });
        }

        if (widthBtn) {
            widthBtn.addEventListener("click", function () {
                var i = WIDTHS.indexOf(prefs.width);
                prefs.width = WIDTHS[(i + 1) % WIDTHS.length];
                render();
                sfx("click");
            });
        }

        sizeBtns.forEach(function (btn) {
            btn.addEventListener("click", function () {
                var dir = btn.getAttribute("data-mz-size");
                var i = SIZES.indexOf(prefs.size);
                i = dir === "-" ? Math.max(0, i - 1) : Math.min(SIZES.length - 1, i + 1);
                prefs.size = SIZES[i];
                render();
                sfx("click");
            });
        });

        render();
    }

    /* =========================================================
       2. 专注模式
       ========================================================= */
    function initFocusMode() {
        var btn = $("#mzFocusBtn");
        var bar = $("#mzFocusBar");
        var exit = $("#mzFocusExit");
        if (!btn || !bar) return;

        function set(on) {
            root.classList.toggle("mz-focus", on);
            bar.hidden = !on;
            if (on) {
                sfx("pop");
                toast("已进入纯粹专注模式");
            } else {
                sfx("pop");
            }
        }

        btn.addEventListener("click", function () {
            set(true);
        });

        if (exit) {
            exit.addEventListener("click", function () {
                set(false);
            });
        }

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && root.classList.contains("mz-focus")) {
                set(false);
            }
        });
    }

    /* =========================================================
       3. 阅读进度条
       ========================================================= */
    function initProgress() {
        var fill = $("#mzReadBarFill");
        if (!fill) return;
        var ticking = false;

        function update() {
            var total = document.documentElement.scrollHeight - window.innerHeight;
            var pct = total > 0 ? (window.scrollY / total) * 100 : 0;
            fill.style.width = Math.max(0, Math.min(100, pct)) + "%";
            ticking = false;
        }

        window.addEventListener(
            "scroll",
            function () {
                if (!ticking) {
                    ticking = true;
                    requestAnimationFrame(update);
                }
            },
            { passive: true }
        );
        update();
    }

    /* =========================================================
       4. 预计读完时间
       ========================================================= */
    function initFinishTime() {
        var el = $("#mzFinishTime");
        if (!el) return;
        var minutes = parseInt(article.getAttribute("data-mz-readtime") || "5", 10) || 5;
        var d = new Date(Date.now() + minutes * 60000);
        function p(n) {
            return String(n).padStart(2, "0");
        }
        el.textContent = p(d.getHours()) + ":" + p(d.getMinutes());
    }

    /* =========================================================
       5. Claps 连击
       ========================================================= */
    function initClaps() {
        var btn = $("#mzClapBtn");
        var comboEl = $("#mzClapCombo");
        var particleBox = $("#mzClapParticles");
        if (!btn) return;

        var combo = 0;
        var timer = null;
        var EMOJI = ["💖", "✨", "👏", "💡", "🎉", "🌟"];

        function burst() {
            if (reduceMotion || !particleBox) return;
            var count = Math.min(3 + Math.floor(combo / 3), 7);
            for (var i = 0; i < count; i++) {
                var span = document.createElement("span");
                span.textContent = EMOJI[Math.floor(Math.random() * EMOJI.length)];
                span.style.setProperty("--dx", (Math.random() - 0.5) * 90 + "px");
                span.style.setProperty("--dy", -(34 + Math.random() * 56) + "px");
                span.style.setProperty("--dr", (Math.random() - 0.5) * 70 + "deg");
                particleBox.appendChild(span);
                (function (node) {
                    window.setTimeout(function () {
                        if (node.parentNode) node.parentNode.removeChild(node);
                    }, 900);
                })(span);
            }
        }

        btn.addEventListener("mz:like", function () {
            combo += 1;
            if (comboEl) {
                if (combo > 1) {
                    comboEl.hidden = false;
                    comboEl.textContent = "x" + combo + " Combo!";
                }
            }
            // 连击越高音越亮
            sfx("chime", 1 + Math.min(combo * 0.08, 0.8));
            burst();

            if (timer) window.clearTimeout(timer);
            timer = window.setTimeout(function () {
                combo = 0;
                if (comboEl) comboEl.hidden = true;
            }, 1500);
        });
    }

    /* =========================================================
       6. 免登录评论
       ========================================================= */
    function initComments() {
        var section = $("#mzComments");
        var list = $("#mzCommentList");
        var form = $("#mzCommentForm");
        var nameInput = $("#mzCommentName");
        var textInput = $("#mzCommentText");
        var submit = $("#mzCommentSubmit");
        var countEl = $("#mzCommentCount");
        if (!section || !list || !form) return;

        var key = "mz-comments:" + (section.getAttribute("data-mz-comment-key") || location.pathname);
        var items = readJSON(key, []);

        function escapeHTML(s) {
            return String(s)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;");
        }

        function render() {
            if (countEl) countEl.textContent = String(items.length);
            if (!items.length) {
                list.innerHTML =
                    '<p class="mz-empty" style="padding:26px 0">还没有人留言，来写第一条吧。</p>';
                return;
            }
            list.innerHTML = items
                .map(function (c) {
                    return (
                        '<div class="mz-comment-item">' +
                        '<div class="mz-comment-item-head">' +
                        '<span class="mz-comment-author">' + escapeHTML(c.author) + "</span>" +
                        '<span class="mz-comment-time">' + escapeHTML(c.createdAt) + "</span>" +
                        "</div>" +
                        '<p class="mz-comment-body">' + escapeHTML(c.content) + "</p>" +
                        "</div>"
                    );
                })
                .join("");
        }

        if (textInput && submit) {
            textInput.addEventListener("input", function () {
                submit.disabled = !textInput.value.trim();
            });
        }

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            if (!textInput || !textInput.value.trim()) return;
            var now = new Date();
            items.unshift({
                author: (nameInput && nameInput.value.trim()) || "匿名读者",
                content: textInput.value.trim(),
                createdAt:
                    now.getFullYear() +
                    "-" +
                    String(now.getMonth() + 1).padStart(2, "0") +
                    "-" +
                    String(now.getDate()).padStart(2, "0") +
                    " " +
                    String(now.getHours()).padStart(2, "0") +
                    ":" +
                    String(now.getMinutes()).padStart(2, "0"),
            });
            writeJSON(key, items);
            textInput.value = "";
            if (submit) submit.disabled = true;
            render();
            sfx("pop");
            toast("感谢你的思考与评论！（只存在本机）");
        });

        render();
    }

    /* =========================================================
       7. 分享书签卡片
       ========================================================= */
    function initShareCard() {
        var modal = $("#mzShareModal");
        var card = $("#mzShareCard");
        if (!modal || !card) return;

        var title = article.getAttribute("data-mz-title") || document.title;
        var url = article.getAttribute("data-mz-url") || location.href;
        var date = article.getAttribute("data-mz-date") || "";
        var excerpt = article.getAttribute("data-mz-excerpt") || "";
        var author = article.getAttribute("data-mz-author") || "";

        var openers = ["mzShareCardOpen", "mzShareCardOpen2"];
        openers.forEach(function (id) {
            var btn = document.getElementById(id);
            if (!btn) return;
            btn.addEventListener("click", function () {
                sfx("pop");
                if (window.mzOpenModal) window.mzOpenModal(modal);
                else {
                    modal.hidden = false;
                    modal.classList.add("is-open");
                }
            });
        });

        $$("[data-mz-card-theme]", modal).forEach(function (btn) {
            btn.addEventListener("click", function () {
                var theme = btn.getAttribute("data-mz-card-theme");
                card.className = "mz-sharecard is-" + theme;
                $$("[data-mz-card-theme]", modal).forEach(function (b) {
                    b.classList.toggle("is-active", b === btn);
                });
                sfx("click");
            });
        });

        var copyBtn = $("#mzShareCopy");
        if (copyBtn) {
            copyBtn.addEventListener("click", function () {
                var text =
                    "【" + title + "】\n\n“" + excerpt + "”\n\n—— 作者：" + author + " · " + date + "\n阅读全文：" + url;
                var label = copyBtn.querySelector("span");

                function done() {
                    if (label) label.textContent = "已复制卡片图文";
                    copyBtn.classList.add("is-copied");
                    sfx("pop");
                    toast("精美图文卡片文本已复制到剪贴板");
                    window.setTimeout(function () {
                        if (label) label.textContent = "一键复制分享图文";
                        copyBtn.classList.remove("is-copied");
                    }, 2000);
                }

                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text).then(done, done);
                } else {
                    var ta = document.createElement("textarea");
                    ta.value = text;
                    document.body.appendChild(ta);
                    ta.select();
                    try {
                        document.execCommand("copy");
                    } catch (e) {
                        /* 忽略 */
                    }
                    document.body.removeChild(ta);
                    done();
                }
            });
        }
    }

    /* =========================================================
       启动
       ========================================================= */
    function boot() {
        initPrefs();
        initFocusMode();
        initProgress();
        initFinishTime();
        initClaps();
        initComments();
        initShareCard();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
