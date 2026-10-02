/* ============================================================
   elthereal-star 的技术笔记 —— 自定义交互脚本
   纯原生 JS，无任何外部依赖。所有动效都尊重 prefers-reduced-motion：
   用户若在系统里关闭了动画，这里会整体降级为静态显示。

   功能：
   1. 吸顶导航栏滚动状态
   2. 顶部阅读进度条
   3. 元素滚动进场（错峰）
   4. Hero 打字机副标题
   5. 列表卡片 3D 跟随鼠标倾斜
   6. 文章目录 scrollspy 高亮
   ============================================================ */

(function () {
    "use strict";

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

    /* ---------------------------------------------------------
       1. 吸顶导航栏：滚动后加分割线与投影
       --------------------------------------------------------- */
    function initStickyHeader() {
        var header = document.querySelector(".header");
        if (!header) return;

        var ticking = false;

        function update() {
            if (window.scrollY > 8) {
                header.classList.add("is-stuck");
            } else {
                header.classList.remove("is-stuck");
            }
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

    /* ---------------------------------------------------------
       2. 顶部阅读进度条
       --------------------------------------------------------- */
    function initScrollProgress() {
        var bar = document.getElementById("scrollProgress");
        if (!bar) return;

        var ticking = false;

        function update() {
            var doc = document.documentElement;
            var max = doc.scrollHeight - doc.clientHeight;
            var ratio = max > 0 ? doc.scrollTop / max : 0;
            if (ratio < 0) ratio = 0;
            if (ratio > 1) ratio = 1;
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

    /* ---------------------------------------------------------
       3. 滚动进场：元素进入视口时淡入上移，同屏元素错峰出现
       --------------------------------------------------------- */
    function initReveal() {
        var selector = ".post-entry, .archive-entry, .terms-tags li, .home-info.first-entry";
        var items = Array.prototype.slice.call(document.querySelectorAll(selector));
        if (!items.length) return;

        // 不支持 IntersectionObserver 时直接全部显示，避免内容永远藏起来
        if (!("IntersectionObserver" in window)) {
            items.forEach(function (el) {
                el.classList.add("is-visible");
            });
            return;
        }

        var observer = new IntersectionObserver(
            function (entries) {
                // 同一批进入视口的元素，按 DOM 顺序做 60ms 错峰
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
                    if (reduceMotion) {
                        el.classList.add("is-visible");
                    } else {
                        el.style.transitionDelay = i * 60 + "ms";
                        el.classList.add("is-visible");
                        // 动画结束后清掉延迟，避免影响后续 hover 过渡
                        window.setTimeout(function () {
                            el.style.transitionDelay = "";
                        }, 600 + i * 60);
                    }
                });
            },
            { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
        );

        items.forEach(function (el) {
            observer.observe(el);
        });
    }

    /* ---------------------------------------------------------
       4. Hero 打字机
       --------------------------------------------------------- */
    function initTyping() {
        var el = document.querySelector("[data-typing]");
        if (!el) return;

        var phrases;
        try {
            phrases = JSON.parse(el.getAttribute("data-typing"));
        } catch (e) {
            return;
        }
        if (!phrases || !phrases.length) return;

        // 关掉动画时，直接静态显示第一句
        if (reduceMotion) {
            el.textContent = phrases[0];
            return;
        }

        var textEl = document.createElement("span");
        var caret = document.createElement("span");
        caret.className = "caret";
        el.textContent = "";
        el.appendChild(textEl);
        el.appendChild(caret);

        var phraseIndex = 0;
        var charIndex = 0;
        var deleting = false;

        var TYPE_SPEED = 90;   // 逐字打出的速度
        var DELETE_SPEED = 45; // 退格速度
        var HOLD_TIME = 1600;  // 打完整句停留时间

        function tick() {
            var current = phrases[phraseIndex];

            if (!deleting) {
                charIndex++;
                textEl.textContent = current.slice(0, charIndex);

                if (charIndex === current.length) {
                    deleting = true;
                    window.setTimeout(tick, HOLD_TIME);
                    return;
                }
                window.setTimeout(tick, TYPE_SPEED);
            } else {
                charIndex--;
                textEl.textContent = current.slice(0, charIndex);

                if (charIndex === 0) {
                    deleting = false;
                    phraseIndex = (phraseIndex + 1) % phrases.length;
                    window.setTimeout(tick, 320);
                    return;
                }
                window.setTimeout(tick, DELETE_SPEED);
            }
        }

        window.setTimeout(tick, 420);
    }

    /* ---------------------------------------------------------
       5. 卡片 3D 倾斜（仅鼠标设备）
       --------------------------------------------------------- */
    function initTilt() {
        if (reduceMotion || !canHover) return;

        var MAX_TILT = 5; // 最大倾斜角度，太大就会显得廉价

        document.querySelectorAll(".post-entry").forEach(function (card) {
            var frame = null;

            card.addEventListener(
                "pointermove",
                function (e) {
                    if (frame) window.cancelAnimationFrame(frame);
                    frame = window.requestAnimationFrame(function () {
                        var rect = card.getBoundingClientRect();
                        var px = (e.clientX - rect.left) / rect.width - 0.5;
                        var py = (e.clientY - rect.top) / rect.height - 0.5;
                        var ry = (px * MAX_TILT * 2).toFixed(2);
                        var rx = (-py * MAX_TILT * 2).toFixed(2);
                        card.style.transform =
                            "perspective(900px) translateY(-5px) rotateX(" +
                            rx +
                            "deg) rotateY(" +
                            ry +
                            "deg) scale(1.012)";
                    });
                },
                { passive: true }
            );

            card.addEventListener("pointerleave", function () {
                if (frame) window.cancelAnimationFrame(frame);
                card.style.transform = "";
            });
        });
    }

    /* ---------------------------------------------------------
       6. 文章目录 scrollspy：高亮当前正在阅读的章节
       --------------------------------------------------------- */
    function initTocSpy() {
        var toc = document.querySelector(".toc");
        if (!toc) return;

        var links = Array.prototype.slice.call(toc.querySelectorAll('a[href^="#"]'));
        if (!links.length) return;

        var map = {};
        links.forEach(function (link) {
            var id = decodeURIComponent(link.getAttribute("href").slice(1));
            var heading = document.getElementById(id);
            if (heading) map[id] = link;
        });

        var headings = Object.keys(map)
            .map(function (id) {
                return document.getElementById(id);
            })
            .filter(Boolean);

        if (!headings.length) return;

        function activate(id) {
            links.forEach(function (l) {
                l.classList.remove("is-active");
            });
            if (map[id]) map[id].classList.add("is-active");
        }

        if (!("IntersectionObserver" in window)) return;

        var observer = new IntersectionObserver(
            function (entries) {
                // 取当前视口内最靠上的标题作为「正在阅读」
                var visible = entries
                    .filter(function (en) {
                        return en.isIntersecting;
                    })
                    .sort(function (a, b) {
                        return a.boundingClientRect.top - b.boundingClientRect.top;
                    });

                if (visible.length) {
                    activate(visible[0].target.id);
                }
            },
            { rootMargin: "-72px 0px -70% 0px", threshold: 0 }
        );

        headings.forEach(function (h) {
            observer.observe(h);
        });
    }

    /* ---------------------------------------------------------
       启动
       --------------------------------------------------------- */
    function boot() {
        initStickyHeader();
        initScrollProgress();
        initReveal();
        initTyping();
        initTilt();
        initTocSpy();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
