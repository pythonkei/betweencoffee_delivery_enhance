/* ============================================================
   bc-attract.js — 流動選單（c-attract）動畫
   參考 cheesetart.com core.min.js 的 UnifiedEffect 類別（精簡版）：
   - hover：圖層跟隨滑鼠 3D 傾斜（rotateX/rotateY）+ 位移 + 縮放
   - 釋放：elastic.out 彈性回彈
   - 觸控裝置：停用 hover 跟隨（防誤觸）
   相依：GSAP 3.12+（全域載入，見 base.html）
   ============================================================ */
(function () {
    'use strict';

    if (typeof document === 'undefined') {
        return;
    }

    // 觸控裝置註記：保留 CSS 樣式參考，但 hover 跟隨動畫不因裝置主動停用
    // （觸控操作本身不產生 mousemove，無需額外判斷；避免觸控筆電 maxTouchPoints>0 誤停用）

    // ===== UnifiedEffect（精簡版）=====
    function AttractEffect(options) {
        var o = Object.assign({
            container: null,
            layer: '.c-attract__layer',
            rotateRange: 24,
            translate3d: ['2rem', '2rem', '0px'],
            scale: 1.02,
            easeHover: 'power2.out',
            easeRelease: 'elastic.out',
            releaseDuration: 0.6
        }, options);

        this.container = typeof o.container === 'string' ? document.querySelector(o.container) : o.container;
        if (!this.container) {
            return;
        }
        // hitArea：預設 = container；可指定（fixed 元素用外層較可靠）
        this.hitArea = o.hitArea ? (typeof o.hitArea === 'string' ? document.querySelector(o.hitArea) : o.hitArea) : this.container;
        // reference：滑鼠相對位置計算基準（精準框，如按鈕 link）；預設 = hitArea
        this.reference = o.reference ? (typeof o.reference === 'string' ? document.querySelector(o.reference) : o.reference) : this.hitArea;
        this.layers = Array.from(this.container.querySelectorAll(o.layer));
        // 吸引熱區範圍（px）：滑鼠進入此範圍即觸發 hover 動畫
        this.attractRange = o.attractRange || 60;
        this.rotateRange = o.rotateRange;
        this.translate3d = o.translate3d;
        this.scale = o.scale;
        this.easeHover = o.easeHover;
        this.easeRelease = o.easeRelease;
        this.releaseDuration = o.releaseDuration;

        this.isHovering = false;
        this.isAnimating = false;
        this.mouseX = 0;
        this.mouseY = 0;
        this.currentScale = 1;

        this.bindEvents();
    }

    AttractEffect.prototype.bindEvents = function () {
        var self = this;

        // proximityMode：在 document 層級偵測滑鼠，滑鼠靠近 hitArea 中心即觸發
        // （對應 cheesetart --attract 負 margin 熱區效果）
        document.addEventListener('mousemove', function (e) {
            var rect = self.hitArea.getBoundingClientRect();
            // 計算滑鼠與 hitArea 中心的距離（px）
            var dx = e.clientX - (rect.left + rect.width / 2);
            var dy = e.clientY - (rect.top + rect.height / 2);
            var dist = Math.sqrt(dx * dx + dy * dy);
            var range = self.attractRange;

            if (dist <= range && !self.isHovering) {
                self.isHovering = true;
                self.updateMouse(e);
                self.animate();
            } else if (dist > range && self.isHovering) {
                self.isHovering = false;
                self.updateMouse(e);
                self.animate();
            } else if (self.isHovering) {
                self.updateMouse(e);
                self.animate();
            }
        });
    };

    AttractEffect.prototype.updateMouse = function (e) {
        // 用 reference（精準按鈕框）計算滑鼠相對中心位置，避免被 hitArea 負 margin 稀釋
        var rect = this.reference.getBoundingClientRect();
        var x = ((e.clientX - (rect.left + rect.width / 2)) / (rect.width / 2));
        var y = ((e.clientY - (rect.top + rect.height / 2)) / (rect.height / 2));
        this.mouseX = Math.max(-1, Math.min(1, x)) * 100;
        this.mouseY = Math.max(-1, Math.min(1, y)) * 100;
    };

    AttractEffect.prototype.animate = function () {
        var self = this;
        var progress = this.isHovering ? 1 : 0;

        var x = this.mouseX / 100;
        var y = this.mouseY / 100;
        // 整個按鈕位移到游標方向（吸引感）；不做旋轉/縮放變形
        var tx = this.isHovering ? parseFloat(this.translate3d[0]) * x : 0;
        var ty = this.isHovering ? parseFloat(this.translate3d[1]) * y : 0;

        var ease = this.isHovering ? this.easeHover : this.easeRelease;
        var duration = this.isHovering ? 0.35 : this.releaseDuration;

        this.layers.forEach(function (layer) {
            gsap.to(layer, {
                x: tx,
                y: ty,
                duration: duration,
                ease: ease,
                overwrite: 'auto',
                onComplete: function () {
                    if (!self.isHovering) {
                        self.currentScale = 1;
                    }
                }
            });
        });
    };

    // ===== 初始化 =====
    function init() {
        // 確保 GSAP 已載入（defer 時序保護）
        if (!window.gsap) {
            setTimeout(init, 100);
            return;
        }

        // Buy & Order 按鈕（整個按鈕吸引到游標位置；位移為主，不做旋轉變形）
        // hitArea 用 .c-attract（負 margin 擴展熱區，proximity 可靠）
        document.querySelectorAll('.bc-attract-buy').forEach(function (el) {
            new AttractEffect({
                container: el.querySelector('.c-attract'),
                hitArea: el.querySelector('.c-attract'),
                reference: el.querySelector('.bc-attract-buy__link'),
                layer: '.c-attract__layer',
                translate3d: ['48px', '48px', '0px'],   // 位移幅度（吸引感）
                scale: 1,
                attractRange: 60,
                easeHover: 'power2.out',
                easeRelease: 'elastic.out(1, 0.6)',
                releaseDuration: 0.6
            });
        });

        // 個人資料圓形按鈕（2026-08-18：與 Buy & Order 相同的吸引滑鼠動畫）
        document.querySelectorAll('.bc-attract-profile').forEach(function (el) {
            new AttractEffect({
                container: el.querySelector('.c-attract'),
                hitArea: el.querySelector('.c-attract'),
                reference: el.querySelector('.bc-attract-profile__link'),
                layer: '.c-attract__layer',
                translate3d: ['48px', '48px', '0px'],   // 位移幅度（吸引感）
                scale: 1,
                attractRange: 60,
                easeHover: 'power2.out',
                easeRelease: 'elastic.out(1, 0.6)',
                releaseDuration: 0.6
            });
        });

        // 漢堡選單（rotateRange 12 對應 cheesetart menu）
        document.querySelectorAll('.bc-attract-menu').forEach(function (el) {
            new AttractEffect({
                container: el.querySelector('.c-attract'),
                layer: '.c-attract__layer',
                rotateRange: 12,
                translate3d: ['0.5rem', '0.5rem', '0px'],
                scale: 1.05,
                easeHover: 'power2.out',
                easeRelease: 'elastic.out(1, 0.6)',
                releaseDuration: 0.6
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
