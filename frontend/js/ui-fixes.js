/**
 * UI & RTL Auto-Fixer for Job Control Dashboard
 */
(function initDashboardUIFixes() {
  let isApplyingFixes = false;

  // 1. תיקון טווחי שכר הפוכים (למשל: "₪ 21,000 - 16,000" -> "16,000 - 21,000 ₪")
  function fixSalaryRanges() {
    const elements = document.querySelectorAll('span, div, badge');
    const salaryRegex = /₪?\s*(\d{1,3}(?:,\d{3})+)\s*-\s*(\d{1,3}(?:,\d{3})+)\s*₪?/;

    elements.forEach((el) => {
      if (el.children.length === 0 && el.textContent.includes('₪') && el.textContent.includes('-')) {
        const match = el.textContent.match(salaryRegex);
        if (match) {
          const num1 = parseInt(match[1].replace(/,/g, ''), 10);
          const num2 = parseInt(match[2].replace(/,/g, ''), 10);
          const min = Math.min(num1, num2).toLocaleString('en-US');
          const max = Math.max(num1, num2).toLocaleString('en-US');
          const targetText = `${min} - ${max} ₪`;

          if (el.textContent !== targetText) {
            el.setAttribute('dir', 'ltr');
            el.classList.add('ltr-range');
            el.textContent = targetText;
          }
        }
      }
    });
  }

  // 2. ניקוי כפילויות בשמות ערים (למשל: "Tampa, Tampa, FL" -> "Tampa, FL")
  function deduplicateLocations() {
    const textNodes = document.querySelectorAll('span, div, p');
    textNodes.forEach((el) => {
      if (el.children.length <= 1 && el.textContent.includes(',')) {
        const cleaned = el.textContent.replace(/\b([A-Za-z\s]+),\s*\1\b/g, '$1');
        if (cleaned !== el.textContent) {
          el.textContent = cleaned;
        }
      }
    });
  }

  // 3. תיקון תווית "בקרה ו-SCADA" בגרף
  function fixBidiChartLabels() {
    const labels = document.querySelectorAll('span, div, text');
    labels.forEach((el) => {
      if (el.children.length === 0 && el.textContent.includes('SCADA')) {
        const targetText = 'בקרה ו-\u200ESCADA';
        if (el.textContent !== targetText) {
          el.style.unicodeBidi = 'plaintext';
          el.textContent = targetText;
        }
      }
    });
  }

  // 4. החלפת קוביות לוגו לבנות ריקות בראשי תיבות של החברה (Fallback)
  function fixCompanyLogos() {
    // טיפול בתמונות שבורות או ריקות
    document.querySelectorAll('img').forEach((img) => {
      const handleBrokenLogo = () => {
        if (!img.isConnected) return;
        const card = img.closest('article, .job-card, [class*="card"]');
        const companyName = extractCompanyName(card) || 'CO';
        const initials = companyName.slice(0, 2).toUpperCase();

        const placeholder = document.createElement('div');
        placeholder.className = 'logo-placeholder';
        placeholder.textContent = initials;
        img.replaceWith(placeholder);
      };

      if (!img.getAttribute('src') || img.getAttribute('src').trim() === '') {
        handleBrokenLogo();
      } else if (!img.dataset.brokenHandled) {
        img.dataset.brokenHandled = 'true';
        img.addEventListener('error', handleBrokenLogo, { once: true });
      }
    });

    // טיפול בריבועי div לבנים ריקים שמשמשים כמקום ללוגו (כמו ב-XTEND)
    document.querySelectorAll('div, span').forEach((box) => {
      const style = window.getComputedStyle(box);
      const isWhiteBox =
        (style.backgroundColor === 'rgb(255, 255, 255)' || style.backgroundColor === '#ffffff') &&
        box.offsetWidth >= 32 &&
        box.offsetWidth <= 64 &&
        box.offsetHeight >= 32 &&
        box.offsetHeight <= 64;

      if (isWhiteBox && box.children.length === 0 && box.textContent.trim() === '') {
        const card = box.closest('article, .job-card, [class*="card"]');
        const companyName = extractCompanyName(card) || 'XT';
        box.classList.add('logo-placeholder');
        box.textContent = companyName.slice(0, 2).toUpperCase();
      }
    });
  }

  function extractCompanyName(card) {
    if (!card) return '';
    const candidates = card.querySelectorAll('span, h4, h5, p, div');
    for (const el of candidates) {
      const txt = el.textContent.trim();
      if (/^[A-Za-z0-9\-\s&.]{2,25}$/.test(txt) && !txt.includes('2026')) {
        return txt;
      }
    }
    return '';
  }

  // 5. הצגה/הסתרה דינמית של כפתור הניקוי (X) בשדה החיפוש
  function setupSearchClearButton() {
    const searchInput = document.querySelector('input[placeholder*="חיפוש"]');
    if (!searchInput) return;

    const container = searchInput.parentElement;
    const clearBtn = Array.from(container.querySelectorAll('button, span, div')).find(
      (el) =>
        el.textContent.trim().toLowerCase() === 'x' ||
        el.classList.contains('search-clear-btn') ||
        el.classList.contains('btn-clear-search') ||
        Boolean(el.querySelector && el.querySelector('.ph-x'))
    );

    if (clearBtn && !clearBtn.dataset.uiFixBound) {
      clearBtn.dataset.uiFixBound = 'true';
      clearBtn.classList.add('search-clear-btn');
      const toggleClearBtn = () => {
        if (searchInput.value.trim().length > 0) {
          clearBtn.classList.remove('is-hidden');
        } else {
          clearBtn.classList.add('is-hidden');
        }
      };

      searchInput.addEventListener('input', toggleClearBtn);
      clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        toggleClearBtn();
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      });

      toggleClearBtn();
    }
  }

  // הרצה ראשונית ומעקב אחר שינויים דינמיים בסינון המשרות
  function applyAllFixes() {
    if (isApplyingFixes) return;
    isApplyingFixes = true;
    try {
      fixSalaryRanges();
      deduplicateLocations();
      fixBidiChartLabels();
      fixCompanyLogos();
      setupSearchClearButton();
    } finally {
      isApplyingFixes = false;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyAllFixes);
  } else {
    applyAllFixes();
  }

  if (typeof MutationObserver !== 'undefined' && document.body) {
    const observer = new MutationObserver(() => {
      applyAllFixes();
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }
})();
