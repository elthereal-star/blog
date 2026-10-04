/* ============================================================
   elthereal-star 的技术笔记 —— 自定义交互脚本

   纯原生 JS，零依赖。所有动效都尊重 prefers-reduced-motion：
   系统里关掉动画后会自动降级为静态显示，内容不会丢。

   模块：
     1. 吸顶导航栏滚动状态
     2. 顶部阅读进度条
     3. 元素滚动进场（错峰）
     4. 三态主题（纸白 / 玄黑 / 羊皮纸）
     5. Hero 实时时钟
     6. 金句卡随机轮换
     7. 触感微音效（Web Audio）
     8. 书签收藏（localStorage + 弹窗列表）
     9. 弹窗通用逻辑（部署指南 / 我的书签）
    10. 移动端抽屉菜单
    11. 回到顶部
    12. 全文搜索快捷键（⌘K / Ctrl+K / /）
    13. 文章目录 scrollspy
    14. 文章内 SVG 动画（滚进视口才播）
   ============================================================ */

(function () {
    "use strict";

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* =========================================================
       0. 小工具
       ========================================================= */

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
            /* 隐私模式下 localStorage 可能不可用，静默降级 */
        }
        return null;
    }

    /* =========================================================
       1. 吸顶导航栏：滚动后分割线加深
       ========================================================= */
    function initStickyHeader() {
        var header = $("#mzHeader");
        if (!header) return;

        var ticking = false;

        function update() {
            if (window.scrollY > 8) header.classList.add("is-stuck");
            else header.classList.remove("is-stuck");
            ticking = false;
        }

        window.addEventListener(
            "scroll",
            function () {
                if (!ticking) {
                    ticking = true;
                    window.requestAnimationFrame(update);
                }
            },
            { passive: true }
        );

        update();
    }

    /* =========================================================
       2. 顶部阅读进度条
       ========================================================= */
    function initScrollProgress() {
        var bar = $("#scrollProgress");
        if (!bar) return;

        var ticking = false;

        function update() {
            var doc = document.documentElement;
            var max = doc.scrollHeight - doc.clientHeight;
            var ratio = max > 0 ? doc.scrollTop / max : 0;
            ratio = Math.min(1, Math.max(0, ratio));
            bar.style.transform = "scaleX(" + ratio.toFixed(4) + ")";
            ticking = false;
        }

        window.addEventListener(
            "scroll",
            function () {
                if (!ticking) {
                    ticking = true;
                    window.requestAnimationFrame(update);
                }
            },
            { passive: true }
        );

        window.addEventListener("resize", update, { passive: true });
        update();
    }

    /* =========================================================
       3. 滚动进场：进入视口时淡入上移，同屏元素按 DOM 顺序错峰
       ========================================================= */
    function initReveal() {
        var selector = ".post-entry, .archive-entry, .terms-tags li, .mz-hero-inner";
        var items = $$(selector);
        if (!items.length) return;

        if (reduceMotion || !("IntersectionObserver" in window)) {
            items.forEach(function (el) {
                el.classList.add("is-visible");
            });
            return;
        }

        var observer = new IntersectionObserver(
            function (entries) {
                var batch = [];
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        batch.push(entry.target);
                        observer.unobserve(entry.target);
                    }
                });

                batch.sort(function (a, b) {
                    return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
                });

                batch.forEach(function (el, i) {
                    el.style.transitionDelay = i * 55 + "ms";
                    el.classList.add("is-visible");
                    window.setTimeout(function () {
                        el.style.transitionDelay = "";
                    }, 700 + i * 55);
                });
            },
            { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
        );

        items.forEach(function (el) {
            observer.observe(el);
        });
    }

    /* =========================================================
       4. 三态主题：纸白 → 玄黑 → 羊皮纸 → 纸白
       ========================================================= */
    var THEMES = ["light", "dark", "sepia"];
    var THEME_LABEL = { light: "纸白", dark: "玄黑", sepia: "羊皮纸" };
    var THEME_COLOR = { light: "#faf9f6", dark: "#111113", sepia: "#f7f3e8" };

    function applyTheme(theme) {
        var root = document.documentElement;
        // 自定义色板走独立属性，避免和 PaperMod 自己的 data-theme 打架
        root.dataset.mzTheme = theme;
        // 同步一份给主题自带组件（目录 / 表格 / 归档 / 搜索）：羊皮纸是浅色系
        root.dataset.theme = theme === "dark" ? "dark" : "light";
        store("mz-theme", theme);
        // 主题自带的 data-theme 脚本认 pref-theme 这个键，写回去让它保持一致
        store("pref-theme", theme === "dark" ? "dark" : "light");

        var label = THEME_LABEL[theme] || theme;

        var btn = $("#mzThemeBtn");
        if (btn) btn.setAttribute("title", "当前主题：" + label + "（点击切换）");

        var tabLabel = $("#mzTabThemeLabel");
        if (tabLabel) tabLabel.textContent = label;

        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute("content", THEME_COLOR[theme] || "#faf9f6");

        // 让表单控件、滚动条等原生 UI 也跟着切
        root.style.colorScheme = theme === "dark" ? "dark" : "light";
    }

    function currentTheme() {
        var t = document.documentElement.dataset.mzTheme;
        // 兼容早期版本写在 data-theme 上的取值
        if (THEMES.indexOf(t) === -1) t = document.documentElement.dataset.theme;
        return THEMES.indexOf(t) === -1 ? "light" : t;
    }

    function initTheme() {
        applyTheme(currentTheme());

        function cycle() {
            applyTheme(THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length]);
        }

        var btn = $("#mzThemeBtn");
        if (btn) btn.addEventListener("click", cycle);

        var tab = $("#mzTabTheme");
        if (tab) tab.addEventListener("click", cycle);

        // 没手动选过主题时，跟随系统深浅色的实时切换
        if (!store("mz-theme") && window.matchMedia) {
            var mq = window.matchMedia("(prefers-color-scheme: dark)");
            var onChange = function (e) {
                if (store("mz-theme")) return;
                applyTheme(e.matches ? "dark" : "light");
            };
            if (mq.addEventListener) mq.addEventListener("change", onChange);
            else if (mq.addListener) mq.addListener(onChange);
        }
    }

    /* =========================================================
       5. Hero 实时时钟
       ========================================================= */
    function initClock() {
        var el = $("#mzClock");
        if (!el) return;

        function tick() {
            var d = new Date();
            var pad = function (n) {
                return n < 10 ? "0" + n : "" + n;
            };
            el.textContent = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
        }

        tick();
        window.setInterval(tick, 1000);
    }

    /* =========================================================
       6. 金句卡：点刷新换一句，不会连续重复
       ========================================================= */
    function initQuote() {
        var box = $("[data-quotes]");
        var btn = $("#mzQuoteBtn");
        if (!box || !btn) return;

        var quotes;
        try {
            quotes = JSON.parse(box.getAttribute("data-quotes"));
        } catch (e) {
            return;
        }
        if (!quotes || quotes.length < 2) return;

        var textEl = $(".mz-quote-text", box);
        var index = 0;
        var busy = false;

        btn.addEventListener("click", function () {
            if (busy) return;
            busy = true;
            tap();

            var next = index;
            while (next === index) {
                next = Math.floor(Math.random() * quotes.length);
            }
            index = next;

            btn.classList.add("is-spinning");

            if (reduceMotion || !textEl) {
                if (textEl) textEl.textContent = quotes[index];
                window.setTimeout(function () {
                    btn.classList.remove("is-spinning");
                    busy = false;
                }, 250);
                return;
            }

            textEl.style.transition = "opacity .16s ease, transform .16s ease";
            textEl.style.opacity = "0";
            textEl.style.transform = "translateY(-4px)";

            window.setTimeout(function () {
                textEl.textContent = quotes[index];
                textEl.style.transform = "translateY(4px)";
                window.setTimeout(function () {
                    textEl.style.opacity = "1";
                    textEl.style.transform = "none";
                    btn.classList.remove("is-spinning");
                    busy = false;
                }, 40);
            }, 170);
        });
    }

    /* =========================================================
       7. 触感微音效：极短的一声「嗒」，默认开启，可一键静音
       ========================================================= */
    var audioCtx = null;
    var soundOn = store("mz-sound") !== "off";

    function tap() {
        if (!soundOn) return;
        try {
            var Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return;
            if (!audioCtx) audioCtx = new Ctx();
            if (audioCtx.state === "suspended") audioCtx.resume();

            var t = audioCtx.currentTime;
            var osc = audioCtx.createOscillator();
            var gain = audioCtx.createGain();

            osc.type = "triangle";
            osc.frequency.setValueAtTime(1180, t);
            osc.frequency.exponentialRampToValueAtTime(760, t + 0.05);

            // 音量刻意压得很低：是「触感反馈」而不是「提示音」
            gain.gain.setValueAtTime(0.0001, t);
            gain.gain.exponentialRampToValueAtTime(0.03, t + 0.006);
            gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.08);

            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(t);
            osc.stop(t + 0.1);
        } catch (e) {
            /* 浏览器不支持或用户禁用了音频，直接忽略 */
        }
    }

    function initSound() {
        var btn = $("#mzSoundBtn");
        var on = $("[data-sfx-on]", btn || document);
        var off = $("[data-sfx-off]", btn || document);

        function render() {
            if (btn) {
                btn.classList.toggle("is-on", soundOn);
                btn.setAttribute("aria-pressed", soundOn ? "true" : "false");
                btn.setAttribute("title", soundOn ? "触感微音效已开启（点击静音）" : "触感微音效已静音（点击开启）");
            }
            if (on) on.hidden = !soundOn;
            if (off) off.hidden = soundOn;
        }

        render();

        if (btn) {
            btn.addEventListener("click", function () {
                soundOn = !soundOn;
                store("mz-sound", soundOn ? "on" : "off");
                render();
                // 开启时给一声反馈，关闭时保持安静
                if (soundOn) tap();
            });
        }

        // 全局点击反馈：按钮、卡片、导航、页码
        document.addEventListener(
            "click",
            function (e) {
                var t = e.target;
                if (!t || !t.closest) return;
                if (t.closest("#mzSoundBtn")) return;
                if (t.closest(".mz-iconbtn, .mz-btn, .mz-tab, .mz-filter, .mz-card-bookmark, .mz-nav-link, .pagination a, .pagination .page-num, .mz-brand"))
                    tap();
            },
            true
        );
    }

    /* =========================================================
       8. 书签收藏（只存在本机 localStorage）
       ========================================================= */
    var BOOKMARK_KEY = "mz-bookmarks";

    function readBookmarks() {
        try {
            var raw = store(BOOKMARK_KEY);
            var arr = raw ? JSON.parse(raw) : [];
            return Array.isArray(arr) ? arr : [];
        } catch (e) {
            return [];
        }
    }

    function writeBookmarks(list) {
        store(BOOKMARK_KEY, JSON.stringify(list));
        renderBookmarkState();
    }

    function isBookmarked(id) {
        return readBookmarks().some(function (b) {
            return b.id === id;
        });
    }

    function renderBookmarkState() {
        var list = readBookmarks();

        var badge = $("#mzBookmarkCount");
        if (badge) {
            badge.textContent = list.length > 99 ? "99+" : String(list.length);
            badge.classList.toggle("is-shown", list.length > 0);
        }

        $$(".mz-card-bookmark").forEach(function (btn) {
            var saved = isBookmarked(btn.getAttribute("data-bookmark-id"));
            btn.classList.toggle("is-saved", saved);
            btn.setAttribute("aria-pressed", saved ? "true" : "false");
            btn.setAttribute("title", saved ? "已收藏，点击取消" : "收藏到我的书签");
        });

        renderBookmarkModal(list);
    }

    function renderBookmarkModal(list) {
        var box = $("#mzBookmarkList");
        if (!box) return;

        var foot = $("#mzBookmarkFoot");
        if (foot) foot.textContent = "本地存储 · localStorage · " + list.length + " 条";

        if (!list.length) {
            box.innerHTML =
                '<p style="margin:0;color:var(--mz-ink-4);font-size:13px;line-height:1.8">' +
                "还没有收藏任何文章。<br>在任意一张卡片的右上角点一下书签图标就能收藏，" +
                "记录只保存在这台设备上，不会上传。" +
                "</p>";
            return;
        }

        box.innerHTML = "";
        list.forEach(function (item) {
            var row = document.createElement("div");
            row.style.cssText =
                "display:flex;align-items:center;justify-content:space-between;gap:10px;" +
                "padding:10px 12px;border:1px solid var(--mz-line);border-radius:10px;" +
                "background:var(--mz-surface-2)";

            var a = document.createElement("a");
            a.href = item.id;
            a.textContent = item.title;
            a.style.cssText =
                "font-family:var(--mz-serif);font-size:14px;font-weight:600;" +
                "color:var(--mz-ink);text-decoration:none;line-height:1.45";

            var del = document.createElement("button");
            del.type = "button";
            del.textContent = "移除";
            del.style.cssText =
                "flex:none;border:1px solid var(--mz-line);background:none;border-radius:6px;" +
                "padding:3px 9px;font-size:11.5px;color:var(--mz-ink-3);cursor:pointer";
            del.addEventListener("click", function () {
                writeBookmarks(
                    readBookmarks().filter(function (b) {
                        return b.id !== item.id;
                    })
                );
            });

            row.appendChild(a);
            row.appendChild(del);
            box.appendChild(row);
        });
    }

    function initBookmarks() {
        $$(".mz-card-bookmark").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.preventDefault();
                var id = btn.getAttribute("data-bookmark-id");
                var title = btn.getAttribute("data-bookmark-title") || document.title;
                var list = readBookmarks();

                if (isBookmarked(id)) {
                    list = list.filter(function (b) {
                        return b.id !== id;
                    });
                } else {
                    list.push({ id: id, title: title, at: Date.now() });
                }
                writeBookmarks(list);
            });
        });

        var clear = $("#mzBookmarkClear");
        if (clear) {
            clear.addEventListener("click", function () {
                writeBookmarks([]);
            });
        }

        renderBookmarkState();
    }

    /* =========================================================
       9. 弹窗：部署指南 / 我的书签
       ========================================================= */
    var lastFocus = null;

    function openModal(modal) {
        if (!modal) return;
        lastFocus = document.activeElement;
        modal.hidden = false;
        modal.classList.add("is-open");
        document.body.classList.add("mz-modal-open");
        var focusable = $("[data-modal-close]", modal) || modal;
        try {
            focusable.focus({ preventScroll: true });
        } catch (e) {}
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.hidden = true;
        if (!$$(".mz-modal.is-open").length) {
            document.body.classList.remove("mz-modal-open");
        }
        if (lastFocus && lastFocus.focus) {
            try {
                lastFocus.focus({ preventScroll: true });
            } catch (e) {}
        }
    }

    function initModals() {
        var deploy = $("#mzDeployModal");
        var bookmarks = $("#mzBookmarkModal");

        var openers = [
            ["#mzDeployBtn", deploy],
            ["#mzDeployBtnMobile", deploy],
            ["#mzFooterDeploy", deploy],
            ["#mzBookmarkBtn", bookmarks]
        ];

        openers.forEach(function (pair) {
            var el = $(pair[0]);
            if (!el || !pair[1]) return;
            el.addEventListener("click", function (e) {
                e.preventDefault();
                openModal(pair[1]);
            });
        });

        $$("[data-modal-close]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                closeModal(btn.closest(".mz-modal"));
            });
        });

        $$(".mz-modal").forEach(function (modal) {
            modal.addEventListener("click", function (e) {
                if (e.target === modal) closeModal(modal);
            });
        });

        document.addEventListener("keydown", function (e) {
            if (e.key !== "Escape") return;
            var open = $(".mz-modal.is-open");
            if (open) closeModal(open);
        });
    }

    /* =========================================================
       10. 移动端抽屉菜单
       ========================================================= */
    function initDrawer() {
        var burger = $("#mzBurger");
        var drawer = $("#mzDrawer");
        if (!burger || !drawer) return;

        var on = $("[data-burger-open]", burger);
        var off = $("[data-burger-close]", burger);

        function setOpen(open) {
            drawer.classList.toggle("is-open", open);
            burger.setAttribute("aria-expanded", open ? "true" : "false");
            burger.setAttribute("aria-label", open ? "收起菜单" : "展开菜单");
            if (on) on.hidden = open;
            if (off) off.hidden = !open;
        }

        burger.addEventListener("click", function () {
            setOpen(!drawer.classList.contains("is-open"));
        });

        $$("a", drawer).forEach(function (a) {
            a.addEventListener("click", function () {
                setOpen(false);
            });
        });

        window.addEventListener("resize", function () {
            if (window.innerWidth >= 768) setOpen(false);
        });
    }

    /* =========================================================
       11. 回到顶部
       ========================================================= */
    function initBackToTop() {
        var link = $("#top-link");

        if (link) {
            var ticking = false;
            var update = function () {
                var threshold = window.innerHeight * 0.9;
                var y = document.body.scrollTop || document.documentElement.scrollTop;
                link.classList.toggle("hidden", y < threshold);
                ticking = false;
            };
            window.addEventListener(
                "scroll",
                function () {
                    if (!ticking) {
                        ticking = true;
                        window.requestAnimationFrame(update);
                    }
                },
                { passive: true }
            );
            link.addEventListener("click", function (e) {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
                if (history.replaceState) history.replaceState(null, "", " ");
            });
            update();
        }

        var footerTop = $("#mzFooterTop");
        if (footerTop) {
            footerTop.addEventListener("click", function () {
                window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
            });
        }
    }

    /* =========================================================
       12. 搜索快捷键：⌘K / Ctrl+K / /
       ========================================================= */
    function initSearchShortcut() {
        var pill = $(".mz-searchpill");
        if (!pill) return;

        function go() {
            window.location.href = pill.getAttribute("href");
        }

        document.addEventListener("keydown", function (e) {
            var tag = (e.target && e.target.tagName) || "";
            var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(tag) || (e.target && e.target.isContentEditable);

            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                go();
                return;
            }
            if (!typing && e.key === "/") {
                e.preventDefault();
                go();
            }
        });
    }

    /* =========================================================
       13. 文章目录 scrollspy
       ========================================================= */
    function initTocSpy() {
        var toc = $(".toc");
        if (!toc) return;

        var links = $$('a[href^="#"]', toc);
        if (!links.length) return;

        var map = {};
        links.forEach(function (link) {
            var id = decodeURIComponent(link.getAttribute("href").slice(1));
            if (document.getElementById(id)) map[id] = link;
        });

        var headings = Object.keys(map)
            .map(function (id) {
                return document.getElementById(id);
            })
            .filter(Boolean);

        if (!headings.length || !("IntersectionObserver" in window)) return;

        function activate(id) {
            links.forEach(function (l) {
                l.classList.remove("is-active");
            });
            if (map[id]) map[id].classList.add("is-active");
        }

        var observer = new IntersectionObserver(
            function (entries) {
                var visible = entries
                    .filter(function (en) {
                        return en.isIntersecting;
                    })
                    .sort(function (a, b) {
                        return a.boundingClientRect.top - b.boundingClientRect.top;
                    });
                if (visible.length) activate(visible[0].target.id);
            },
            { rootMargin: "-76px 0px -70% 0px", threshold: 0 }
        );

        headings.forEach(function (h) {
            observer.observe(h);
        });
    }

    /* =========================================================
       14. 文章内 SVG 动画：滚进视口时才播一次
           HTML 侧用 data-anim-play 标记，具体动效写在 CSS 里
       ========================================================= */
    function initSvgAnimations() {
        var targets = $$("[data-anim-play]");
        if (!targets.length) return;

        // 兜底：万一观察器没触发，3 秒后也让内容显示出来
        window.setTimeout(function () {
            targets.forEach(function (el) {
                var rect = el.getBoundingClientRect();
                if (rect.top < window.innerHeight && rect.bottom > 0) {
                    el.classList.add("is-playing");
                }
            });
        }, 3000);

        if (reduceMotion || !("IntersectionObserver" in window)) {
            targets.forEach(function (el) {
                el.classList.add("is-playing");
            });
            return;
        }

        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-playing");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.2 }
        );

        targets.forEach(function (el) {
            observer.observe(el);
        });
    }

    /* =========================================================
       启动
       ========================================================= */
    function boot() {
        initStickyHeader();
        initScrollProgress();
        initReveal();
        initTheme();
        initClock();
        initQuote();
        initSound();
        initBookmarks();
        initModals();
        initDrawer();
        initBackToTop();
        initSearchShortcut();
        initTocSpy();
        initSvgAnimations();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
