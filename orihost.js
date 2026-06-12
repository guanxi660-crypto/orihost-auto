// ==UserScript==
// @name         Orihost & Linkvertise Auto-Claim (Docker Optimized)
// @namespace    http://tampermonkey.net/
// @version      8.0
// @description  专为 Orihost 设计，自动完成 Renew 与 Linkvertise 任务，Docker 环境强力版，优化跳转与页面关闭
// @author       Michael & Gemini
// @match        *://panel.orihost.com/*
// @match        *://*.linkvertise.com/*
// @grant        window.close
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    console.log('[Auto] Orihost 专用优化脚本 v8.0 已注入...');

    // 内存守护：30分钟刷新一次
    const RELOAD_INTERVAL = 30 * 60 * 1000;
    setTimeout(() => { location.reload(); }, RELOAD_INTERVAL);

    const clickCooldowns = {
        get_link: 0,
        renew_button: 0,
        open_linkvertise: 0,
        continue_btn: 0
    };

    // =========================================================
    // 工具函数
    // =========================================================

    function findByText(selector, text) {
        const elements = document.querySelectorAll(selector);
        for (let i = 0; i < elements.length; i++) {
            const txt = (elements[i].innerText || elements[i].textContent || '').trim().toLowerCase();
            if (txt.includes(text.toLowerCase())) return elements[i];
        }
        return null;
    }

    function isInteractable(el) {
        if (!el || el.disabled) return false;
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
    }

    function extremeClick(el, logText = '') {
        if (!el) return false;
        try {
            el.style.pointerEvents = 'auto';
            el.style.zIndex = '999999';

            // 移除可能遮挡的层
            const overlays = document.querySelectorAll('div[class*="overlay"], div[class*="mask"], .modal-backdrop');
            overlays.forEach(ov => { ov.style.display = 'none'; });

            if (typeof el.click === 'function') el.click();
            const opts = { bubbles: true, cancelable: true, view: window };
            el.dispatchEvent(new MouseEvent('mousedown', opts));
            el.dispatchEvent(new MouseEvent('mouseup', opts));
            el.dispatchEvent(new MouseEvent('click', opts));

            console.log('[Auto] 成功点击 ->', logText);
            return true;
        } catch (err) {
            console.error('[Auto] 点击异常 ->', logText, err);
            return false;
        }
    }

    // =========================================================
    // 主循环
    // =========================================================

    let isProcessing = false;

    const mainLoop = setInterval(() => {
        if (isProcessing) return;
        isProcessing = true;

        try {
            const url = location.href;
            const now = Date.now();

            // 1. Orihost 页面处理
            if (url.includes('panel.orihost.com')) {
                const targetServerUrl = 'https://panel.orihost.com/server/670475f5';

                // 如果在主页，自动跳转到目标服务器页面
                if (url === 'https://panel.orihost.com/' || url === 'https://panel.orihost.com') {
                    console.log('[Auto] 检测到 Orihost 主页，自动跳转到目标服务器页面...');
                    location.href = targetServerUrl;
                    isProcessing = false;
                    return;
                }

                // 只有在目标服务器页面才执行后续操作
                if (url.includes(targetServerUrl)) {
                    // 检测限制提示
                    if (document.body.innerText.includes('Renew Limit Reached')) {
                        console.log('[Auto] 检测到 Renew Limit Reached，10天后重试...');
                        clearInterval(mainLoop);
                        setTimeout(() => { location.reload(); }, 10 * 24 * 60 * 60 * 1000);
                        isProcessing = false;
                        return;
                    }

                    // A. 尝试寻找弹窗中的 Open Linkvertise (优先级最高)
                    const openBtn = findByText('button', 'Open Linkvertise') || findByText('a', 'Open Linkvertise');
                    if (isInteractable(openBtn)) {
                        if (now - clickCooldowns.open_linkvertise > 10000) {
                            clickCooldowns.open_linkvertise = now;
                            extremeClick(openBtn, 'Orihost: Open Linkvertise (Popup)');
                            // 点击后关闭当前 Orihost 页面，防止重复点击
                            setTimeout(() => { window.close(); }, 2000);
                        }
                        isProcessing = false;
                        return;
                    }

                    // B. 尝试寻找 Renew 按钮
                    const renewBtn = findByText('button', 'Renew');
                    if (isInteractable(renewBtn)) {
                        if (now - clickCooldowns.renew_button > 15000) { // 增加冷却，防止连点
                            clickCooldowns.renew_button = now;
                            extremeClick(renewBtn, 'Orihost: Renew Button');
                        }
                    }
                }
            }

            // 2. Linkvertise 页面处理
            if (url.includes('linkvertise.com')) {
                // --- Get Link ---
                const getLink = findByText('button', 'Get Link') || findByText('a', 'Get Link');
                if (isInteractable(getLink) && !getLink.disabled) {
                    if (now - clickCooldowns.get_link > 10000) {
                        clickCooldowns.get_link = now;
                        setTimeout(() => { extremeClick(getLink, 'Linkvertise: Get Link'); }, 1500);
                    }
                }

                // --- Access / Watch Ads ---
                if (url.includes('/access/')) {
                    const wrappers = document.querySelectorAll('[dusk="lv-lib-membership-price-plan-wrapper-btn"]');
                    let watchAds = null;
                    for (const w of wrappers) { if (w.innerText.includes('Watch Ads')) { watchAds = w; break; } }

                    if (watchAds) {
                        const priceBox = watchAds.closest('.membership-price');
                        if (priceBox && !priceBox.classList.contains('active')) {
                            extremeClick(watchAds, 'Watch Ads Box');
                        } else {
                            const contBtn = findByText('button', 'Continue');
                            if (isInteractable(contBtn) && (now - clickCooldowns.continue_btn > 5000)) {
                                clickCooldowns.continue_btn = now;
                                extremeClick(contBtn, 'Continue');
                            }
                        }
                    }

                    if (findByText('div', 'Wait') || findByText('span', 'Wait')) {
                        setTimeout(() => { location.reload(); }, 300000);
                        isProcessing = false;
                        return;
                    }
                }

                // --- Skip Ad ---
                const skip = findByText('button', 'Skip Ad') || findByText('span', 'Skip Ad');
                if (isInteractable(skip)) extremeClick(skip, 'Skip Ad');

                // --- Success ---
                if (url.includes('/success')) {
                    const open = Array.from(document.querySelectorAll('[data-testid="lv-button"]'))
                                    .find(b => b.innerText.includes('Open'));
                    if (isInteractable(open)) {
                        setTimeout(() => {
                            extremeClick(open, 'Open');
                            setTimeout(() => { window.close(); }, 2000);
                        }, 1500);
                    }
                }
            }
        } catch (err) {}

        isProcessing = false;
    }, 2000);

})();
