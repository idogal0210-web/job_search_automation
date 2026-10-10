import os
import json
from datetime import datetime, timedelta

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__</title>
  <link rel="stylesheet" href="fonts.css">
  <link rel="stylesheet" href="theme.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    /* Custom helper components aligned with So-Me design tokens */
    :root {
      --dashboard-text: #f5f6f0;
      --dashboard-muted: #c0c5be;
      --dashboard-lime: #dcff72;
      --dashboard-cyan: #89f4e7;
      --dashboard-gold: #ffd368;
      --dashboard-edge: #ffffff29;
      --dashboard-glass: linear-gradient(145deg, #ffffff26, #ffffff0e);
      --dashboard-shadow: inset 0 1px 2px #ffffff2b, 0 18px 55px #0000002e;
    }

    * {
      box-sizing: border-box;
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
      width: 7px;
      height: 7px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.2);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.18);
      border-radius: 999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.32);
    }

    /* Header Nav Enhancements */
    .dashboard-sidebar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
    }
    .dashboard-sidebar-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
      text-decoration: none;
    }
    .brand-icon-pill {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: linear-gradient(145deg, rgba(220, 255, 114, 0.28), rgba(255, 255, 255, 0.08));
      border: 1px solid rgba(220, 255, 114, 0.4);
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }
    .brand-titles {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .brand-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--dashboard-text);
      line-height: 1.2;
    }
    .brand-subtitle {
      font-size: 11px;
      color: var(--dashboard-muted);
      letter-spacing: 0.5px;
    }
    .header-actions-group {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    /* Stats Overview Grid */
    .dashboard-stats-grid {
      display: grid;
      grid-template-columns: 1.1fr 1.3fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }
    @media (max-width: 1120px) {
      .dashboard-stats-grid {
        grid-template-columns: 1fr 1fr;
      }
      .dashboard-stats-grid > .dashboard-card:nth-child(3) {
        grid-column: span 2;
      }
    }
    @media (max-width: 750px) {
      .dashboard-stats-grid {
        grid-template-columns: 1fr;
      }
      .dashboard-stats-grid > .dashboard-card:nth-child(3) {
        grid-column: span 1;
      }
    }

    /* Progress Segmented Bar */
    .segmented-progress {
      width: 100%;
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      display: flex;
      overflow: hidden;
      gap: 2px;
      margin: 12px 0 10px;
      box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4);
    }
    .segmented-progress-bar {
      height: 100%;
      transition: width 0.4s ease;
    }
    .stat-squircles-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }
    .stat-squircle-card {
      background: rgba(0, 0, 0, 0.22);
      border: 1px solid var(--dashboard-edge);
      border-radius: 20px;
      padding: 12px 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 4px;
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.08);
    }
    .stat-icon-squircle {
      width: 42px;
      height: 42px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 19px;
      font-weight: 700;
      margin-bottom: 4px;
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.5);
    }
    .stat-icon-squircle.lime { background: var(--dashboard-lime); color: #171c12; }
    .stat-icon-squircle.cyan { background: var(--dashboard-cyan); color: #171c12; }
    .stat-icon-squircle.gold { background: var(--dashboard-gold); color: #171c12; }

    /* Controls Panel */
    .controls-inputs-stack {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .controls-buttons-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .tool-btn {
      min-height: 44px;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: 600;
      border-radius: 999px;
      cursor: pointer;
      border: 1px solid var(--dashboard-edge);
      background: linear-gradient(160deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.07));
      color: var(--dashboard-text);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.2s ease, border-color 0.2s ease;
    }
    .tool-btn:hover {
      background: rgba(255, 255, 255, 0.18);
      border-color: rgba(255, 255, 255, 0.4);
    }

    /* Contextual Action Bars */
    .context-action-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border-radius: 24px;
      padding: 16px 24px;
      margin-bottom: 24px;
      -webkit-backdrop-filter: blur(22px);
      backdrop-filter: blur(22px);
    }
    .context-action-bar.saved {
      background: linear-gradient(145deg, rgba(137, 244, 231, 0.14), rgba(220, 255, 114, 0.08));
      border: 1px solid rgba(137, 244, 231, 0.35);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }
    .context-action-bar.rejected {
      background: linear-gradient(145deg, rgba(239, 68, 68, 0.16), rgba(0, 0, 0, 0.3));
      border: 1px solid rgba(239, 68, 68, 0.35);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    /* Job Card Styling */
    .job-card {
      margin-bottom: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      transition: border-color 0.2s ease, transform 0.2s ease;
      position: relative;
    }
    .job-card:hover {
      border-color: rgba(255, 255, 255, 0.36);
    }
    .job-card-topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .job-card-topbar-tags {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }
    .badge-score {
      padding: 5px 14px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .badge-score-high {
      background: rgba(220, 255, 114, 0.16);
      color: var(--dashboard-lime);
      border: 1px solid rgba(220, 255, 114, 0.38);
      box-shadow: 0 0 16px rgba(220, 255, 114, 0.15);
    }
    .badge-score-med {
      background: rgba(137, 244, 231, 0.16);
      color: var(--dashboard-cyan);
      border: 1px solid rgba(137, 244, 231, 0.38);
      box-shadow: 0 0 16px rgba(137, 244, 231, 0.15);
    }
    .badge-score-fair {
      background: rgba(255, 211, 104, 0.16);
      color: var(--dashboard-gold);
      border: 1px solid rgba(255, 211, 104, 0.38);
      box-shadow: 0 0 16px rgba(255, 211, 104, 0.15);
    }

    /* Job Card Header with Logo */
    .job-card-main-header {
      display: flex;
      align-items: flex-start;
      gap: 16px;
    }
    .job-company-logo {
      width: 50px;
      height: 50px;
      border-radius: 16px;
      background: #191d1b;
      border: 1px solid var(--dashboard-edge);
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      flex-shrink: 0;
      margin-top: 2px;
    }
    .job-company-logo img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      padding: 6px;
    }
    .job-company-avatar {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 15px;
      color: var(--dashboard-text);
      background: linear-gradient(135deg, rgba(220, 255, 114, 0.25), rgba(137, 244, 231, 0.2));
    }
    .job-header-text {
      flex: 1;
      min-width: 0;
    }
    .job-header-text h2 {
      font-size: 20px;
      font-weight: 600;
      color: var(--dashboard-text);
      margin: 0 0 6px;
      line-height: 1.35;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }
    .job-company-name {
      color: #fff;
    }
    .job-title-sep {
      color: var(--dashboard-muted);
      font-weight: 400;
    }
    .job-title-text {
      color: #e5e9e2;
    }
    .job-header-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    /* 4 Structured Information Panels */
    .job-boxes-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }
    .job-box {
      background: rgba(0, 0, 0, 0.24);
      border: 1px solid var(--dashboard-edge);
      border-radius: 20px;
      padding: 14px 18px;
      font-size: 15px;
      line-height: 1.6;
      color: var(--dashboard-text);
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.05);
      overflow-wrap: anywhere;
    }
    .job-box.highlight {
      background: rgba(137, 244, 231, 0.06);
      border-color: rgba(137, 244, 231, 0.28);
    }
    .job-box strong {
      color: var(--dashboard-cyan);
      margin-inline-end: 6px;
      display: inline;
    }
    .job-box.highlight strong {
      color: var(--dashboard-lime);
    }

    /* Job Card Actions Bar */
    .job-actions-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      flex-wrap: wrap;
    }
    .action-btn-group {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .btn-triage {
      min-height: 44px;
      padding: 9px 18px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 999px;
      cursor: pointer;
      border: 1px solid var(--dashboard-edge);
      background: linear-gradient(160deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.06));
      color: var(--dashboard-text);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-triage:hover {
      background: rgba(255, 255, 255, 0.2);
      border-color: rgba(255, 255, 255, 0.4);
    }
    .btn-triage.saved-active {
      background: rgba(137, 244, 231, 0.24);
      color: #b4fcf1;
      border-color: var(--dashboard-cyan);
      box-shadow: 0 0 14px rgba(137, 244, 231, 0.25);
    }
    .btn-triage.rejected-active {
      background: rgba(239, 68, 68, 0.25);
      color: #fca5a5;
      border-color: #ef4444;
      box-shadow: 0 0 14px rgba(239, 68, 68, 0.25);
    }
    .btn-apply {
      min-height: 44px;
      padding: 10px 24px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 999px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--dashboard-lime);
      color: #171c12;
      border: 1px solid #ebffab99;
      box-shadow: inset 0 1px 2px #ffffff80, 0 4px 18px rgba(164, 203, 46, 0.28);
      transition: background 0.2s ease;
    }
    .btn-apply:hover {
      background: #e7ff9c;
    }

    /* Modals and Overlays */
    .dashboard-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(11, 13, 12, 0.78);
      -webkit-backdrop-filter: blur(20px);
      backdrop-filter: blur(20px);
      z-index: 100;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .dashboard-modal-backdrop.hidden {
      display: none !important;
    }
    .dashboard-modal-box {
      max-width: 620px;
      width: 100%;
      max-height: 85vh;
      overflow-y: auto;
      margin-bottom: 0;
    }

    /* Toast Notification */
    .dashboard-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 1000;
      background: rgba(25, 30, 27, 0.95);
      border: 1px solid var(--dashboard-edge);
      box-shadow: 0 16px 45px rgba(0, 0, 0, 0.55);
      -webkit-backdrop-filter: blur(20px);
      backdrop-filter: blur(20px);
      border-radius: 999px;
      padding: 12px 24px;
      color: var(--dashboard-text);
      font-size: 15px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 10px;
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
    }
    .dashboard-toast.show {
      transform: translateY(0);
      opacity: 1;
      pointer-events: auto;
    }

    /* Responsive Media Queries */
    @media (max-width: 750px) {
      body, html {
        overflow-x: hidden;
      }
      .dashboard-app {
        padding: 16px 14px 24px;
        overflow-x: hidden;
      }
      .dashboard-sidebar {
        border-radius: 28px;
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        padding: 14px;
      }
      .dashboard-sidebar-brand {
        justify-content: space-between;
        width: 100%;
      }
      .dashboard-sidebar nav {
        width: 100%;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 4px;
        padding: 4px;
      }
      .dashboard-sidebar nav a {
        font-size: 12px;
        padding: 8px 4px;
        min-height: 42px;
        justify-content: center;
        text-align: center;
      }
      .header-actions-group {
        justify-content: space-between;
        width: 100%;
      }
      .dashboard-topbar {
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
        padding: 0 4px 12px;
      }
      .dashboard-card {
        border-radius: 26px;
        padding: 20px 16px;
      }
      .stat-squircles-row {
        gap: 6px;
      }
      .stat-squircle-card {
        padding: 10px 4px;
      }
      .stat-icon-squircle {
        width: 36px;
        height: 36px;
        font-size: 16px;
      }
      .job-card-topbar {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
      .job-card-topbar-tags {
        width: 100%;
        justify-content: space-between;
      }
      .job-card-main-header {
        gap: 12px;
      }
      .job-header-text h2 {
        font-size: 17px;
      }
      .job-actions-bar {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
      }
      .action-btn-group {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        width: 100%;
      }
      .btn-triage {
        width: 100%;
        justify-content: center;
        min-height: 44px;
      }
      .btn-apply {
        width: 100%;
        justify-content: center;
        min-height: 44px;
      }
      .context-action-bar {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        padding: 16px;
      }
      .context-action-bar button {
        width: 100%;
        justify-content: center;
      }
    }
  </style>
</head>
<body>
<div class="dashboard-app" dir="rtl">

  <!-- Top Navigation Pill (So-Me Pill Header) -->
  <header class="dashboard-sidebar">
    <div class="dashboard-sidebar-brand">
      <div class="brand-icon-pill">🚀</div>
      <div class="brand-titles">
        <span class="brand-title">עידו גל | בקרת משרות</span>
        <span class="brand-subtitle">אנרגיה, גז טבעי ורחפנים</span>
      </div>
    </div>

    <nav>
      <a href="javascript:void(0)" onclick="setFilter('all', this)" class="tab-btn" aria-current="page">
        משרות חדשות (<span id="countAll">__TOTAL_JOBS__</span>)
      </a>
      <a href="javascript:void(0)" onclick="setFilter('saved', this)" class="tab-btn">
        ⭐ שמורות להגשה (<span id="countSaved">0</span>)
      </a>
      <a href="javascript:void(0)" onclick="setFilter('rejected', this)" class="tab-btn">
        ✖️ הוסרו (<span id="countRejected">0</span>)
      </a>
    </nav>

    <div class="header-actions-group">
      <div id="cloudSyncStatus" class="dashboard-chip" style="color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); display: flex; align-items: center; gap: 6px;">
        <span class="dashboard-dot"></span>
        <span>ענן מסונכרן</span>
      </div>
      <button onclick="triggerSyncModal()" class="dashboard-settings-link" style="cursor: pointer;" title="פתח הגדרות וסנכרון ענן">
        ☁️ סנכרן
      </button>
    </div>
  </header>

  <div class="dashboard-main">

    <!-- Sub-header Information Strip -->
    <div class="dashboard-topbar">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="dashboard-dot"></span>
        <span class="dashboard-local">סריקה יומית חכמה • התאמה לפרופיל הנדסאי מכונות, אנרגיה ורחפנים</span>
      </div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <span>תאריך סריקה: <strong>__NOW_STR__</strong></span>
        <span class="dashboard-divider">|</span>
        <span class="dashboard-chip" style="font-size: 11px; padding: 2px 10px;">__REPORT_TYPE_LABEL__</span>
      </div>
    </div>

    <!-- 3 Overview Cards (Progress Statistics, Search/Filters, Sector Distribution) -->
    <div class="dashboard-stats-grid">
      
      <!-- Card 1: סטטיסטיקת סקירה והתקדמות -->
      <div class="dashboard-card" style="margin-bottom: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h3 style="margin: 0; font-size: 18px; font-weight: 600;">התקדמות סקירה</h3>
          <span class="dashboard-chip" id="progressSummaryChip">0% נסקרו</span>
        </div>
        <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 6px;">
          <span id="progressPctText" style="font-size: 38px; font-weight: 700; color: #fff; line-height: 1;">0%</span>
          <span style="font-size: 14px; color: var(--dashboard-muted);">סך הכל מוינו במקבץ השבועי</span>
        </div>

        <!-- 3-Segment Color Progress Bar (Lime, Cyan, Gold) -->
        <div class="segmented-progress">
          <div id="progressSegNew" class="segmented-progress-bar" style="background: var(--dashboard-lime); width: 100%;"></div>
          <div id="progressSegSaved" class="segmented-progress-bar" style="background: var(--dashboard-cyan); width: 0%;"></div>
          <div id="progressSegRejected" class="segmented-progress-bar" style="background: var(--dashboard-gold); width: 0%;"></div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--dashboard-muted); margin-bottom: 12px;">
          <span id="pctLabelNew">100% חדשות</span>
          <span id="pctLabelSaved">0% שמורות</span>
          <span id="pctLabelRejected">0% הוסרו</span>
        </div>

        <!-- 3 Stat Squircles matching the reference screenshot -->
        <div class="stat-squircles-row">
          <div class="stat-squircle-card">
            <div class="stat-icon-squircle lime">🆕</div>
            <div id="statNewCount" style="font-size: 20px; font-weight: 700; color: #fff;">__TOTAL_JOBS__</div>
            <div style="font-size: 12px; color: var(--dashboard-muted);">משרות חדשות</div>
          </div>
          <div class="stat-squircle-card">
            <div class="stat-icon-squircle cyan">⭐</div>
            <div id="statSavedCount" style="font-size: 20px; font-weight: 700; color: #fff;">0</div>
            <div style="font-size: 12px; color: var(--dashboard-muted);">שמורות להגשה</div>
          </div>
          <div class="stat-squircle-card">
            <div class="stat-icon-squircle gold">✖️</div>
            <div id="statRejectedCount" style="font-size: 20px; font-weight: 700; color: #fff;">0</div>
            <div style="font-size: 12px; color: var(--dashboard-muted);">הוסרו מהסבב</div>
          </div>
        </div>
      </div>

      <!-- Card 2: סינון ואיתור משרות -->
      <div class="dashboard-card" style="margin-bottom: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div style="display: flex; gap: 8px;">
            <span class="dashboard-chip">סינון חכם</span>
            <span class="dashboard-chip" style="color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.35); background: rgba(220, 255, 114, 0.1);">סריקה עדכנית</span>
          </div>
          <small style="color: var(--dashboard-muted); font-size: 13px;">מיון ואיסוף</small>
        </div>
        <h3 style="margin: 0 0 6px; font-size: 18px; font-weight: 600;">סינון ואיתור משרות</h3>
        <p style="color: var(--dashboard-muted); font-size: 14px; margin-bottom: 12px;">
          סינון לפי מגזרי אנרגיה ורחפנים, איתור כפילויות ומיון לפי התאמה או תאריך.
        </p>

        <div class="controls-inputs-stack">
          <select id="sectorFilter" onchange="filterCards()">
            <option value="all">🌐 כל התחומים</option>
            <option value="natural_gas">🏭 גז טבעי</option>
            <option value="solar">☀️ מערכות סולאריות</option>
            <option value="energy">⚡ אנרגיה כללית</option>
            <option value="drones">🚁 רחפנים וכטב"ם</option>
            <option value="energy_tech">🔋 אנרג'י טק ואגירה</option>
          </select>
          <input id="searchInput" type="text" placeholder="חיפוש משרה, חברה או דרישה טכנית..." oninput="filterCards()" />
          
          <div class="controls-buttons-row">
            <button id="sortBtn" onclick="toggleSort()" class="tool-btn" style="flex: 1;" title="לחץ לשינוי סדר המיון">
              <span id="sortIcon">📅</span>
              <span id="sortLabel">מיון: התאריך החדש קודם</span>
            </button>
            <button onclick="openDuplicatesModal()" class="tool-btn" style="color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4);" title="סרוק כפילויות משרות">
              <span>🔍</span>
              <span>בדיקת כפילויות</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Card 3: התפלגות לפי תחומים -->
      <div class="dashboard-card" style="margin-bottom: 0; display: flex; flex-direction: column;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h3 style="margin: 0; font-size: 18px; font-weight: 600;">התפלגות תחומים</h3>
          <span class="dashboard-chip" style="color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.35);">פעיל השבוע</span>
        </div>
        <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; min-height: 160px;">
          <canvas id="sectorChart" style="max-height: 160px; width: 100%;"></canvas>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 12px; color: var(--dashboard-muted);">
          <span>מקורות: LinkedIn & Comeet</span>
          <button onclick="shareSyncLink()" class="dashboard-chip" style="cursor: pointer; font-size: 11px; padding: 3px 10px;">
            📲 שיתוף קישור
          </button>
        </div>
      </div>

    </div>

    <!-- Contextual Action Bar for Saved Jobs (Export to Excel) -->
    <div id="savedActionBar" class="context-action-bar saved" style="display: none;">
      <div style="display: flex; align-items: center; gap: 14px;">
        <span style="font-size: 28px;">⭐</span>
        <div>
          <div style="font-size: 16px; font-weight: 600; color: var(--dashboard-cyan);">משרות ששמרת להגשה</div>
          <div style="font-size: 13px; color: var(--dashboard-muted);">ייצוא מהיר של כל המשרות השמורות לקובץ Excel מסודר עם קישורים ישירים ונתוני שכר.</div>
        </div>
      </div>
      <button onclick="exportSavedToExcel()" class="dashboard-primary" style="white-space: nowrap;">
        <span>📊 ייצוא לאקסל (Excel)</span>
      </button>
    </div>

    <!-- Contextual Action Bar for Rejected Jobs (Permanent Delete & Reset) -->
    <div id="rejectedActionBar" class="context-action-bar rejected" style="display: none;">
      <div style="display: flex; align-items: center; gap: 14px;">
        <span style="font-size: 28px;">🗑️</span>
        <div>
          <div style="font-size: 16px; font-weight: 600; color: #fca5a5;">משרות שסומנו להסרה (✖️)</div>
          <div style="font-size: 13px; color: var(--dashboard-muted);">לחיצה על מחיקה תנקה את כל הרשימה לצמיתות מכל המכשירים ותאפס את המספר ל-0.</div>
        </div>
      </div>
      <button onclick="clearAllRejected()" class="btn-triage" style="background: rgba(239, 68, 68, 0.25); color: #fca5a5; border-color: rgba(239, 68, 68, 0.5); white-space: nowrap;">
        <span>🗑️ מחיקה לצמיתות ואיפוס</span>
      </button>
    </div>

    <!-- Job Cards List -->
    <main id="cardsContainer"></main>

    <!-- Empty State -->
    <div id="emptyState" class="dashboard-card" style="display: none; text-align: center; padding: 48px 24px;">
      <div id="emptyStateIcon" style="font-size: 44px; margin-bottom: 12px;">🔍</div>
      <h3 id="emptyStateTitle" style="font-size: 20px; margin-bottom: 8px;">לא נמצאו משרות בהתאם לסינון</h3>
      <p id="emptyStateDesc" style="color: var(--dashboard-muted); font-size: 15px; margin: 0;">נסה לבחור לשונית או תחום אחר.</p>
    </div>

    <!-- Footer -->
    <footer class="dashboard-footer">
      <div>דשבורד משרות אוטומטי • מותאם עבור עידו גל</div>
      <div>מעוצב בהשראת ערכת So-Me Design System • Google Sans & Glass Materials</div>
    </footer>

  </div>

  <!-- Sync Modal -->
  <div id="syncModal" class="dashboard-modal-backdrop hidden" onclick="if(event.target===this)closeSyncModal()">
    <div class="dashboard-card dashboard-modal-box">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="stat-icon-squircle cyan">☁️</div>
          <div>
            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">סנכרון משרות למערכת</h3>
            <small style="color: var(--dashboard-muted);">שמירת משרות שמורות והסרת משרות שנדחו</small>
          </div>
        </div>
        <button onclick="closeSyncModal()" style="min-height: 36px; padding: 6px 14px; font-size: 18px; cursor: pointer; border-radius: 999px;">✕</button>
      </div>

      <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid var(--dashboard-edge); border-radius: 18px; padding: 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <span style="display: flex; align-items: center; gap: 8px;"><span>⭐</span> משרות שמורות להגשה:</span>
          <span id="syncSavedCount" style="font-size: 18px; font-weight: 700; color: var(--dashboard-cyan);">0</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.08);">
          <span style="display: flex; align-items: center; gap: 8px;"><span>✖️</span> משרות שסומנו להסרה:</span>
          <span id="syncRejectedCount" style="font-size: 18px; font-weight: 700; color: #fca5a5;">0</span>
        </div>
      </div>

      <p style="font-size: 14px; color: var(--dashboard-muted); line-height: 1.6; margin-bottom: 18px;">
        הדשבורד שומר ומעדכן את כל המשרות שסימנת באופן רציף. סנכרון ישיר מאפשר לפתוח את הסימונים בכל מכשיר.
      </p>

      <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 20px; padding: 12px 16px; background: rgba(137,244,231,0.06); border: 1px solid rgba(137,244,231,0.2); border-radius: 16px;">
        <span style="font-size: 13px; color: var(--dashboard-muted);">סנכרון מיידי בין מכשירים:</span>
        <button onclick="shareSyncLink()" class="dashboard-chip" style="cursor: pointer; padding: 7px 16px; font-size: 13px;">
          📲 שיתוף קישור סנכרון
        </button>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 12px;">
        <button onclick="closeSyncModal()" class="tool-btn">סגור</button>
        <button id="syncConfirmBtn" onclick="confirmSync()" class="dashboard-primary">
          אשר וסנכרן עכשיו
        </button>
      </div>
    </div>
  </div>

  <!-- Duplicates Modal -->
  <div id="duplicatesModal" class="dashboard-modal-backdrop hidden" onclick="if(event.target===this)closeDuplicatesModal()">
    <div class="dashboard-card dashboard-modal-box" style="max-width: 680px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="stat-icon-squircle gold">🔍</div>
          <div>
            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">בדיקת כפילות משרות</h3>
            <small style="color: var(--dashboard-muted);">זיהוי משרות זהות או דומות לפי כותרת, מזהה וחברה</small>
          </div>
        </div>
        <button onclick="closeDuplicatesModal()" style="min-height: 36px; padding: 6px 14px; font-size: 18px; cursor: pointer; border-radius: 999px;">✕</button>
      </div>

      <div id="duplicatesContent" style="max-height: 55vh; overflow-y: auto; padding-right: 4px; display: flex; flex-direction: column; gap: 14px;">
        <!-- Filled by JS -->
      </div>

      <div style="display: flex; justify-content: flex-end; margin-top: 18px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
        <button onclick="closeDuplicatesModal()" class="tool-btn">סגור</button>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="dashboard-toast">
    <span id="toastIcon">🔔</span>
    <span id="toastMsg">ההודעה עודכנה</span>
  </div>

</div>

<script>
  const rawJobsData = __JOBS_JSON__;
  const historicalCatalog = __CATALOG_JSON__;
  const initialSavedLinks = __INITIAL_SAVED_JSON__;
  const initialRejectedLinks = __INITIAL_REJECTED_JSON__;
  let currentFilter = 'all';
  let currentSort = 'date_desc';
  const STORAGE_KEY = 'ido_job_triage_store';

  function loadTriageState() {
    let state = {};
    if (typeof initialSavedLinks !== 'undefined' && Array.isArray(initialSavedLinks)) {
      initialSavedLinks.forEach(link => { state[link] = 'saved'; });
    }
    if (typeof initialRejectedLinks !== 'undefined' && Array.isArray(initialRejectedLinks)) {
      initialRejectedLinks.forEach(link => { state[link] = 'rejected'; });
    }
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const userState = JSON.parse(stored);
        Object.assign(state, userState);
      }
    } catch (e) {}
    return state;
  }

  const CLOUD_SYNC_URL = 'https://job-finder-auto-default-rtdb.firebaseio.com/triage.json';
  let cloudSyncTimeout = null;
  let cloudLastUpdated = 0;

  async function fetchCloudSync() {
    const cloudBadge = document.getElementById('cloudSyncStatus');
    try {
      const resp = await fetch(CLOUD_SYNC_URL, { cache: 'no-cache' });
      if (resp.ok) {
        const data = await resp.json();
        if (data) {
          if (data.updated_at) {
            cloudLastUpdated = new Date(data.updated_at).getTime();
          }
          let changed = false;
          if (Array.isArray(data.purged)) {
            data.purged.forEach(link => {
              if (jobStates[link] !== 'purged') {
                jobStates[link] = 'purged';
                changed = true;
              }
            });
          }
          if (Array.isArray(data.saved)) {
            data.saved.forEach(link => {
              if (jobStates[link] !== 'saved') {
                jobStates[link] = 'saved';
                changed = true;
              }
            });
          }
          if (Array.isArray(data.rejected)) {
            data.rejected.forEach(link => {
              if (jobStates[link] !== 'purged' && jobStates[link] !== 'saved') {
                if (jobStates[link] !== 'rejected') {
                  jobStates[link] = 'rejected';
                  changed = true;
                }
              }
            });
          }
          if (changed) {
            saveTriageState(jobStates);
            updateUI();
          }
          if (cloudBadge) {
            cloudBadge.innerHTML = '<span class="dashboard-dot"></span> <span>ענן מסונכרן</span>';
          }
        }
      }
    } catch (e) {
      if (cloudBadge) {
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: #94a3b8;"></span> <span>מקומי</span>';
      }
    }
  }

  function scheduleCloudPush() {
    if (cloudSyncTimeout) clearTimeout(cloudSyncTimeout);
    cloudSyncTimeout = setTimeout(pushCloudSync, 400);
  }

  async function pushCloudSync() {
    const cloudBadge = document.getElementById('cloudSyncStatus');
    if (cloudBadge) {
      cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-gold);"></span> <span>מעדכן ענן...</span>';
    }

    try {
      const savedList = Object.keys(jobStates).filter(id => jobStates[id] === 'saved');
      const rejectedList = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
      const purgedList = Object.keys(jobStates).filter(id => jobStates[id] === 'purged');
      
      const timestamp = new Date().toISOString();
      const payload = {
        saved: savedList,
        rejected: rejectedList,
        purged: purgedList,
        updated_at: timestamp
      };

      const resp = await fetch(CLOUD_SYNC_URL, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok && cloudBadge) {
        cloudBadge.innerHTML = '<span class="dashboard-dot"></span> <span>ענן מסונכרן</span>';
      }
    } catch (e) {
      if (cloudBadge) {
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: #94a3b8;"></span> <span>מקומי</span>';
      }
    }
  }

  function extractJobId(link) {
    if (!link) return '';
    const match = link.match(/(\\d{7,12})/);
    return match ? match[1] : link;
  }

  function getSyncDelta() {
    const delta = {};
    const baseSaved = new Set(typeof initialSavedLinks !== 'undefined' && Array.isArray(initialSavedLinks) ? initialSavedLinks : []);
    const baseRejected = new Set(typeof initialRejectedLinks !== 'undefined' && Array.isArray(initialRejectedLinks) ? initialRejectedLinks : []);

    for (const [link, state] of Object.entries(jobStates)) {
      const wasSaved = baseSaved.has(link);
      const wasRejected = baseRejected.has(link);
      if (state === 'saved' && !wasSaved) {
        delta[extractJobId(link)] = 's';
      } else if (state === 'rejected' && !wasRejected) {
        delta[extractJobId(link)] = 'r';
      }
    }
    return delta;
  }

  function checkUrlSync() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const syncData = urlParams.get('sync');
      if (syncData) {
        let incomingDelta = null;
        try {
          incomingDelta = JSON.parse(atob(decodeURIComponent(syncData)));
        } catch(e) {
          try {
            incomingDelta = JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(syncData)))));
          } catch(e2) {
            incomingDelta = JSON.parse(decodeURIComponent(syncData));
          }
        }

        if (incomingDelta && typeof incomingDelta === 'object') {
          let count = 0;
          for (const [idOrLink, val] of Object.entries(incomingDelta)) {
            const fullState = (val === 's' || val === 'saved') ? 'saved' : 'rejected';
            const match = rawJobsData.find(j => j.link && (j.link === idOrLink || j.link.includes(idOrLink)));
            if (match) {
              jobStates[match.link] = fullState;
              count++;
            } else {
              jobStates[idOrLink] = fullState;
              count++;
            }
          }
          saveTriageState(jobStates);
          window.history.replaceState({}, document.title, window.location.pathname);
          setTimeout(() => {
            showToast('🎉', count > 0 ? `סונכרנו בהצלחה ${count} משרות חדשות!` : 'הדשבורד מסונכרן ומעודכן!');
            updateUI();
          }, 300);
        }
      }
    } catch (e) {}
  }

  async function shareSyncLink() {
    const delta = getSyncDelta();
    const deltaKeys = Object.keys(delta);
    let shareUrl = window.location.origin + window.location.pathname;
    if (deltaKeys.length > 0) {
      const payload = encodeURIComponent(btoa(JSON.stringify(delta)));
      shareUrl += '?sync=' + payload;
    }
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'דשבורד משרות - עידו גל',
          text: deltaKeys.length > 0 ? `סנכרון ${deltaKeys.length} משרות חדשות שסימנתי` : 'דשבורד משרות מעודכן',
          url: shareUrl
        });
        showToast('📲', 'הקישור שותף בהצלחה!');
        return;
      } catch (err) {}
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrl).then(() => {
        showToast('🔗', 'קישור סנכרון הועתק! פתח אותו במכשיר השני');
      }).catch(() => {
        prompt('פתח קישור זה במכשיר השני לסנכרון מיידי:', shareUrl);
      });
    } else {
      prompt('פתח קישור זה במכשיר השני לסנכרון מיידי:', shareUrl);
    }
  }

  function saveTriageState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {}
  }

  const KNOWN_COMPANY_DOMAINS = [
    [['elbit', 'אלביט'], 'elbitsystems.com'],
    [['rafael', 'רפאל'], 'rafael.co.il'],
    [['solaredge'], 'solaredge.com'],
    [['applied materials'], 'appliedmaterials.com'],
    [['nova'], 'novami.com'],
    [['ormat'], 'ormat.com'],
    [['iai', 'התעשייה האווירית', 'israel aerospace'], 'iai.co.il'],
    [['tower'], 'towersemi.com'],
    [['intel', 'realsense'], 'intel.com'],
    [['apple'], 'apple.com'],
    [['amazon', 'aws'], 'amazon.com'],
    [['nvidia'], 'nvidia.com'],
    [['cato networks'], 'catonetworks.com'],
    [['check point', 'checkpoint'], 'checkpoint.com'],
    [['palo alto'], 'paloaltonetworks.com'],
    [['cyberark'], 'cyberark.com'],
    [['siemens'], 'siemens.com'],
    [['hitachi'], 'hitachienergy.com'],
    [['schneider'], 'se.com'],
    [['ge vernova', 'ge '], 'gevernova.com'],
    [['icl group'], 'icl-group.com'],
    [['enlight'], 'enlightenergy.co.il'],
    [['energix'], 'energix-group.com'],
    [['doral'], 'doral-energy.com'],
    [['netafim'], 'netafim.com'],
    [['iscar'], 'iscar.com'],
    [['kla'], 'kla.com'],
    [['tesla'], 'tesla.com'],
    [['xtend'], 'xtend.me'],
    [['nextvision'], 'nextvision-sys.com'],
    [['d-fend'], 'd-fendsolutions.com'],
    [['smartshooter', 'smart shooter'], 'smart-shooter.com'],
    [['spearuav'], 'spearuav.com'],
    [['controp'], 'controp.com'],
    [['bird aero'], 'birdaero.com'],
    [['bluebird'], 'bluebird-uav.com'],
    [['airobotics', 'איירובוטיקס'], 'airoboticsdrones.com'],
    [['aerotor'], 'aerotor.com'],
    [['heven'], 'hevenaerotech.com'],
    [['sentrycs'], 'sentrycs.com'],
    [['roboteam'], 'robo-team.com'],
    [['opc energy'], 'opc-energy.com'],
    [['חברת החשמל', 'iec '], 'iec.co.il'],
    [['ashtrom'], 'ashtrom.co.il'],
    [['alstom'], 'alstom.com'],
    [['biocatch'], 'biocatch.com'],
    [['claroty'], 'claroty.com'],
    [['cheq'], 'cheq.ai'],
    [['stratasys'], 'stratasys.com'],
    [['philips'], 'philips.com'],
    [['adama'], 'adama.com'],
    [['airwayz'], 'airwayz.co'],
    [['alumeshet'], 'alumeshet.co.il'],
    [['bet shemesh', 'מנועי בית שמש'], 'bseltd.com'],
    [['bruker'], 'bruker.com'],
    [['fiverr'], 'fiverr.com'],
    [['gett'], 'gett.com'],
    [['lemonade'], 'lemonade.com'],
    [['nestle', 'nestlé'], 'nestle.com'],
    [['pepsico', 'קוקה קולה', 'central bottling'], 'pepsico.com'],
    [["l'oréal", 'loreal'], 'loreal.com'],
    [['manpower'], 'manpower.co.il'],
    [['sqlink'], 'sqlink.com'],
    [['flytrex'], 'flytrex.com'],
    [['percepto'], 'percepto.com'],
    [['parazero'], 'parazero.com'],
    [['sightec'], 'sightec.com'],
    [['regulus'], 'regulus.com'],
    [['rada'], 'drs.com'],
    [['bagira'], 'bagirasys.com'],
    [['aitech'], 'aitechsystems.com'],
    [['acs motion'], 'acsmotioncontrol.com'],
    [['experis'], 'experis.co.il'],
    [['matrix', 'מטריקס'], 'matrix-globals.com'],
    [['ness', 'נס'], 'ness-tech.co.il'],
    [['wix'], 'wix.com'],
    [['monday'], 'monday.com'],
    [['mobileye'], 'mobileye.com'],
    [['shapir'], 'shapir.co.il'],
    [['shikun', 'שיכון ובינוי'], 'shikunbinui.com'],
    [['electra', 'אלקטרה'], 'electra.co.il'],
    [['edf'], 'edf-re.com']
  ];

  function getCompanyLogoHtml(companyName, customLogo) {
    const rawName = (companyName || 'חברה').trim();
    const norm = rawName.toLowerCase();
    
    let domain = null;
    for (const [keys, dom] of KNOWN_COMPANY_DOMAINS) {
      if (keys.some(k => norm.includes(k))) {
        domain = dom;
        break;
      }
    }

    if (!domain) {
      const cleanLatin = rawName.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
      if (cleanLatin.length >= 3 && !['חברה', 'israel', 'group', 'ltd'].includes(cleanLatin)) {
        domain = cleanLatin + '.com';
      }
    }

    let cleanWords = rawName
      .replace(/[()\\[\\]\\-–•,]/g, ' ')
      .split(/\\s+/)
      .filter(w => w && !['בע"מ', 'בע״מ', 'ltd', 'ltd.', 'inc', 'inc.', 'group', 'corp', 'israel', 'ישראל'].includes(w.toLowerCase()));
    if (cleanWords.length === 0) cleanWords = [rawName];
    
    let initials = '';
    if (cleanWords.length >= 2) {
      initials = (cleanWords[0][0] || '') + (cleanWords[1][0] || '');
    } else if (cleanWords.length === 1 && cleanWords[0].length >= 2) {
      initials = cleanWords[0].slice(0, 2);
    } else {
      initials = cleanWords[0] ? cleanWords[0][0] : '🏢';
    }
    initials = initials.toUpperCase();

    const logoUrl = customLogo || (domain ? `https://unavatar.io/${domain}?fallback=false` : null);
    const safeComp = rawName.replace(/"/g, '&quot;');

    if (logoUrl) {
      return `
        <div class="job-company-logo" title="${safeComp}">
          <img src="${logoUrl}" alt="${safeComp}" loading="lazy" onerror="this.style.display='none'; var fb = this.nextElementSibling; if(fb) fb.style.display='flex';" />
          <div class="job-company-avatar" style="display: none;">${initials}</div>
        </div>
      `;
    } else {
      return `
        <div class="job-company-logo" title="${safeComp}">
          <div class="job-company-avatar">${initials}</div>
        </div>
      `;
    }
  }

  let jobStates = loadTriageState();

  function renderCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    if (!rawJobsData || rawJobsData.length === 0) {
      document.getElementById('emptyState').style.display = 'block';
      return;
    }

    const seenLinks = new Set((rawJobsData || []).map(j => j.link));
    let displayJobs = [...(rawJobsData || [])];

    if (typeof historicalCatalog !== 'undefined' && historicalCatalog) {
      Object.keys(jobStates).forEach(link => {
        if (jobStates[link] === 'saved' && !seenLinks.has(link) && historicalCatalog[link]) {
          displayJobs.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
    }

    let sortedJobs = [...displayJobs];
    sortedJobs.sort((a, b) => {
      if (currentSort === 'score_desc') {
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        return scoreB - scoreA;
      } else {
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        if (dateA > dateB) return -1;
        if (dateA < dateB) return 1;
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        return scoreB - scoreA;
      }
    });

    sortedJobs.forEach((job, idx) => {
      const id = job.link || `job_${idx}`;
      const score = Number(job.match_score) || 85;
      const company = job.company || 'חברה';
      const title = job.title || 'משרה ללא כותרת';
      const link = job.link || '#';
      const secKey = job.sector_key || 'energy';
      const jobDate = job.date || 'היום';
      
      let sectorBadge = '⚡ תשתיות אנרגיה ו-SCADA';
      let sectorChipStyle = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); background: rgba(255, 211, 104, 0.1);';
      if (['drones', 'cuas', 'avionics'].includes(secKey)) {
        if (secKey === 'cuas') {
          sectorBadge = '🛡️ מערכות הגנת C-UAS וביטחון';
          sectorChipStyle = 'color: #fca5a5; border-color: rgba(252, 165, 165, 0.4); background: rgba(239, 68, 68, 0.12);';
        } else if (secKey === 'avionics') {
          sectorBadge = '📡 מטע"דים ואוויוניקה';
          sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
        } else {
          sectorBadge = '🚁 רחפנים וכטב"ם אוטונומי';
          sectorChipStyle = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.4); background: rgba(220, 255, 114, 0.12);';
        }
      } else if (secKey === 'solar') {
        sectorBadge = '☀️ מערכות סולאריות ו-PV';
        sectorChipStyle = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.4); background: rgba(220, 255, 114, 0.12);';
      } else if (secKey === 'natural_gas') {
        sectorBadge = '🏭 גז טבעי ותחנות כוח';
        sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
      } else if (secKey === 'energy_tech') {
        sectorBadge = '🔋 אגירת אנרגיה ו-Energy-Tech';
        sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
      }

      let scoreClass = 'badge-score-high';
      if (score < 80) scoreClass = 'badge-score-fair';
      else if (score < 90) scoreClass = 'badge-score-med';

      const domain = job.company_domain_product || job.company_summary || 'חברה מובילה בתחומה';
      const loc = job.location || 'ישראל / היברידי';
      const jobSum = job.job_summary || job.company_summary || 'תפקיד משמעותי בתפעול וניטור מערכות מתקדמות.';
      const strengths = job.experience_strengths || job.reasoning || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.';
      const companyReqs = job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה (פירוט מלא בקישור להגשה).';
      const logoHtml = getCompanyLogoHtml(company, job.logo);

      const salaryRange = job.salary_range || '12,000 - 15,000 ₪';
      const salaryType = job.salary_source_type || 'sector_benchmark';
      const salaryLabel = job.salary_source_label || (salaryType === 'company_verified' ? `מבוסס דיווחי שכר ב-${company}` : (salaryType === 'job_ad' ? 'פורסם במודעת המשרה' : `הערכת ענף`));
      
      let salaryChipStyle = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.35); background: rgba(255, 211, 104, 0.08);';
      if (salaryType === 'company_verified') {
        salaryChipStyle = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.35); background: rgba(220, 255, 114, 0.08);';
      } else if (salaryType === 'job_ad') {
        salaryChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.35); background: rgba(137, 244, 231, 0.08);';
      }

      const card = document.createElement('article');
      card.setAttribute('data-id', id);
      card.setAttribute('data-sector', secKey);
      card.setAttribute('data-location', loc.toLowerCase());
      card.className = 'dashboard-card job-card';

      card.innerHTML = `
        <!-- Top Meta Row -->
        <div class="job-card-topbar">
          <div class="job-card-topbar-tags">
            <span class="dashboard-chip" style="${sectorChipStyle}">${sectorBadge}</span>
            <span class="dashboard-chip" style="color: var(--dashboard-muted); border-color: rgba(255, 255, 255, 0.15); background: rgba(0, 0, 0, 0.2);">📅 ${jobDate}</span>
          </div>
          <div class="badge-score ${scoreClass}">
            <span>⚡ ${score}%</span> התאמה
          </div>
        </div>

        <!-- Title & Company Header -->
        <div class="job-card-main-header">
          ${logoHtml}
          <div class="job-header-text">
            <h2>
              <span class="job-company-name">${company}</span>
              <span class="job-title-sep">—</span>
              <span class="job-title-text">${title}</span>
            </h2>
            <div class="job-header-chips">
              <span class="dashboard-chip" style="font-size: 12px; padding: 3px 10px;">📍 ${loc}</span>
              <span class="dashboard-chip" style="${salaryChipStyle}; font-size: 12px; padding: 3px 10px;">
                💰 ${salaryRange} <small style="display: inline; opacity: 0.85;">(${salaryLabel})</small>
              </span>
            </div>
          </div>
        </div>

        <!-- 4 Structured Information Boxes -->
        <div class="job-boxes-grid">
          <div class="job-box">
            <strong>📌 דרישות החברה עבור המשרה:</strong>
            <span>${companyReqs}</span>
          </div>
          <div class="job-box">
            <strong>🏢 תחום ומוצר החברה:</strong>
            <span>${domain}</span>
          </div>
          <div class="job-box">
            <strong>📋 תקציר המשרה:</strong>
            <span>${jobSum}</span>
          </div>
          <div class="job-box highlight">
            <strong>💪 נקודות חוזק מהניסיון:</strong>
            <span>${strengths}</span>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="job-actions-bar">
          <div class="action-btn-group">
            <button onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'saved')" class="btn-triage action-save-btn">
              <span>✔️</span> <span class="btn-text">שמור להגשה</span>
            </button>
            <button onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'rejected')" class="btn-triage action-reject-btn">
              <span>✖️</span> <span>הסר משרה</span>
            </button>
          </div>
          <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn-apply">
            <span>הגש מועמדות ↗</span>
          </a>
        </div>
      `;
      container.appendChild(card);
    });

    updateUI();
  }

  function toggleSort() {
    currentSort = currentSort === 'score_desc' ? 'date_desc' : 'score_desc';
    const icon = document.getElementById('sortIcon');
    const label = document.getElementById('sortLabel');
    if (currentSort === 'score_desc') {
      if (icon) icon.textContent = '🔽';
      if (label) label.textContent = 'מיון: ציון התאמה (מגבוה לנמוך)';
      showToast('🔽', 'מיון: ציון התאמה מגבוה לנמוך');
    } else {
      if (icon) icon.textContent = '📅';
      if (label) label.textContent = 'מיון: התאריך החדש קודם';
      showToast('📅', 'מיון: התאריך החדש קודם');
    }
    renderCards();
  }

  function toggleAction(id, action) {
    const current = jobStates[id];
    if (current === action) {
      delete jobStates[id];
      showToast('ℹ️', 'הסטטוס אופס למצב ממתין');
    } else {
      jobStates[id] = action;
      if (action === 'saved') {
        showToast('✔️', 'המשרה נשמרה להגשה');
      } else if (action === 'rejected') {
        showToast('✖️', 'המשרה הוסרה ולא תוצג שוב');
      }
    }
    saveTriageState(jobStates);
    updateUI();
    scheduleCloudPush();
  }

  function setFilter(filter, el) {
    currentFilter = filter;
    document.querySelectorAll('.tab-btn').forEach(b => {
      b.removeAttribute('aria-current');
    });
    if (el) el.setAttribute('aria-current', 'page');
    updateUI();
  }

  function filterCards() {
    updateUI();
  }

  function updateUI() {
    const selectedSector = document.getElementById('sectorFilter').value;
    const searchInput = document.getElementById('searchInput') ? document.getElementById('searchInput').value.toLowerCase() : '';
    
    const cards = document.querySelectorAll('.job-card');
    let visibleCount = 0;
    let saved = 0, rejected = 0, purged = 0;
    const total = cards.length;

    cards.forEach(card => {
      const id = card.getAttribute('data-id');
      const sector = card.getAttribute('data-sector');
      const state = jobStates[id] || 'pending';

      if (state === 'saved') saved++;
      if (state === 'rejected') rejected++;
      if (state === 'purged') purged++;

      const saveBtn = card.querySelector('.action-save-btn');
      const rejectBtn = card.querySelector('.action-reject-btn');
      const saveText = saveBtn.querySelector('.btn-text');

      if (state === 'saved') {
        saveBtn.className = "btn-triage action-save-btn saved-active";
        saveText.textContent = "נשמר להגשה";
        rejectBtn.className = "btn-triage action-reject-btn";
      } else if (state === 'rejected') {
        rejectBtn.className = "btn-triage action-reject-btn rejected-active";
        saveBtn.className = "btn-triage action-save-btn";
        saveText.textContent = "שמור להגשה";
      } else {
        saveBtn.className = "btn-triage action-save-btn";
        rejectBtn.className = "btn-triage action-reject-btn";
        saveText.textContent = "שמור להגשה";
      }

      let matchesTab = false;
      if (currentFilter === 'all') matchesTab = (state !== 'saved' && state !== 'rejected' && state !== 'purged');
      else if (currentFilter === 'saved') matchesTab = (state === 'saved');
      else if (currentFilter === 'rejected') matchesTab = (state === 'rejected');

      let matchesSector = (selectedSector === 'all');
      if (!matchesSector) {
        const normSector = sector.toLowerCase().replace(/[ _-]/g, '');
        const normSelected = selectedSector.toLowerCase().replace(/[ _-]/g, '');

        if (normSelected === 'drones') {
          matchesSector = ['drones', 'cuas', 'avionics'].includes(normSector);
        } else if (normSelected === 'energy') {
          const energySet = ['energy', 'naturalgas', 'solar', 'energytech'];
          matchesSector = energySet.includes(normSector);
        } else if (normSelected === 'naturalgas') {
          matchesSector = ['naturalgas', 'gas'].includes(normSector);
        } else {
          matchesSector = normSector === normSelected;
        }
      }
      
      let matchesSearch = true;
      if (searchInput) {
        const cardText = card.textContent.toLowerCase();
        matchesSearch = cardText.includes(searchInput);
      }

      if (matchesTab && matchesSector && matchesSearch && state !== 'purged') {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    const totalSavedInStore = Object.values(jobStates).filter(s => s === 'saved').length;
    const totalRejectedInStore = Object.values(jobStates).filter(s => s === 'rejected').length;
    const pendingInBatch = total - (saved + rejected + purged);

    // Update Counts in Nav & Stats Cards
    const countAllEl = document.getElementById('countAll');
    const countSavedEl = document.getElementById('countSaved');
    const countRejectedEl = document.getElementById('countRejected');
    if (countAllEl) countAllEl.textContent = Math.max(0, pendingInBatch);
    if (countSavedEl) countSavedEl.textContent = totalSavedInStore;
    if (countRejectedEl) countRejectedEl.textContent = totalRejectedInStore;

    const statNewEl = document.getElementById('statNewCount');
    const statSavedEl = document.getElementById('statSavedCount');
    const statRejectedEl = document.getElementById('statRejectedCount');
    if (statNewEl) statNewEl.textContent = Math.max(0, pendingInBatch);
    if (statSavedEl) statSavedEl.textContent = totalSavedInStore;
    if (statRejectedEl) statRejectedEl.textContent = totalRejectedInStore;

    // Progress Bar Calculations
    const triaged = saved + rejected + purged;
    const pct = total > 0 ? Math.round((triaged / total) * 100) : 0;
    
    const pctTextEl = document.getElementById('progressPctText');
    const summaryChipEl = document.getElementById('progressSummaryChip');
    if (pctTextEl) pctTextEl.textContent = pct + '%';
    if (summaryChipEl) summaryChipEl.textContent = pct + '% נסקרו';

    const pNew = total > 0 ? Math.round((Math.max(0, pendingInBatch) / total) * 100) : 0;
    const pSaved = total > 0 ? Math.round((saved / total) * 100) : 0;
    const pRej = Math.max(0, 100 - pNew - pSaved);

    const segNew = document.getElementById('progressSegNew');
    const segSaved = document.getElementById('progressSegSaved');
    const segRej = document.getElementById('progressSegRejected');
    if (segNew) segNew.style.width = pNew + '%';
    if (segSaved) segSaved.style.width = pSaved + '%';
    if (segRej) segRej.style.width = pRej + '%';

    const lblNew = document.getElementById('pctLabelNew');
    const lblSaved = document.getElementById('pctLabelSaved');
    const lblRej = document.getElementById('pctLabelRejected');
    if (lblNew) lblNew.textContent = pNew + '% חדשות';
    if (lblSaved) lblSaved.textContent = pSaved + '% שמורות';
    if (lblRej) lblRej.textContent = pRej + '% הוסרו';

    // Contextual Action Bars
    const savedBar = document.getElementById('savedActionBar');
    const rejectedBar = document.getElementById('rejectedActionBar');
    if (savedBar) {
      savedBar.style.display = (currentFilter === 'saved') ? 'flex' : 'none';
    }
    if (rejectedBar) {
      rejectedBar.style.display = (currentFilter === 'rejected') ? 'flex' : 'none';
    }

    // Empty State Handling
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
      if (visibleCount === 0) {
        const iconEl = document.getElementById('emptyStateIcon');
        const titleEl = document.getElementById('emptyStateTitle');
        const descEl = document.getElementById('emptyStateDesc');
        if (currentFilter === 'rejected') {
          if (iconEl) iconEl.textContent = '🗑️';
          if (titleEl) titleEl.textContent = `כל ${totalRejectedInStore} המשרות שהוסרו מנוטרלות לצמיתות`;
          if (descEl) descEl.textContent = 'משרות אלו סוננו מחלון ההזדמנויות השבועי ולא ישובו להופיע בדוחות הבאים.';
        } else if (currentFilter === 'saved') {
          if (iconEl) iconEl.textContent = '⭐';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות שמורות מתוך מקבץ זה';
          if (descEl) descEl.textContent = 'לחץ על "שמור להגשה" בכל כרטיס משרה שמעניינת אותך.';
        } else {
          if (iconEl) iconEl.textContent = '🎉';
          if (titleEl) titleEl.textContent = 'סיימת לסקור את כל המשרות החדשות!';
          if (descEl) descEl.textContent = 'כל המשרות במקבץ זה כבר מוינו (נשמרו או הוסרו).';
        }
        emptyState.style.display = 'block';
      } else {
        emptyState.style.display = 'none';
      }
    }

    renderSectorChart();
  }

  let sectorChartInstance = null;
  function renderSectorChart() {
    const canvas = document.getElementById('sectorChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const counts = {};
    const sourceJobs = (rawJobsData && rawJobsData.length > 0) ? rawJobsData : [];
    sourceJobs.forEach(job => {
      let sec = job.sector_key || job.sector || 'energy';
      const normSector = sec.toLowerCase().replace(/[ _-]/g, '');
      let label = '⚡ אנרגיה';
      if (['solar', 'pv'].includes(normSector)) label = '☀️ סולאר';
      else if (['naturalgas', 'gas'].includes(normSector)) label = '🏭 גז טבעי';
      else if (['energytech', 'storage', 'bess'].includes(normSector)) label = '🔋 אגירה';
      else if (['drones', 'uav', 'robotics'].includes(normSector)) label = '🚁 רחפנים';
      else if (['cuas', 'defense'].includes(normSector)) label = '🛡️ ביטחון';
      counts[label] = (counts[label] || 0) + 1;
    });

    if (Object.keys(counts).length === 0) {
      counts['ללא משרות'] = 0;
    }

    if (sectorChartInstance) {
      sectorChartInstance.destroy();
    }

    const labels = Object.keys(counts);
    const data = Object.values(counts);
    const barColors = [
      '#dcff72', // Lime
      '#89f4e7', // Cyan
      '#ffd368', // Gold
      '#b4fcf1', // Teal
      '#a0c03e', // Olive Lime
      '#c0c5be'  // Muted
    ];

    sectorChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: barColors.slice(0, labels.length),
          borderRadius: 8,
          borderSkipped: false,
          maxBarThickness: 32
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#191d1b',
            titleColor: '#f5f6f0',
            bodyColor: '#c0c5be',
            borderColor: 'rgba(255, 255, 255, 0.16)',
            borderWidth: 1,
            cornerRadius: 12,
            rtl: true,
            textDirection: 'rtl'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, color: '#c0c5be', font: { family: 'Google Sans', size: 11 } },
            grid: { color: 'rgba(255, 255, 255, 0.08)' }
          },
          x: {
            ticks: { color: '#c0c5be', font: { family: 'Google Sans', size: 11 } },
            grid: { display: false }
          }
        }
      }
    });
  }

  function showToast(icon, msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    document.getElementById('toastIcon').textContent = icon;
    document.getElementById('toastMsg').textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2800);
  }

  function triggerSyncModal() {
    const savedCount = Object.values(jobStates).filter(s => s === 'saved').length;
    const rejectedCount = Object.values(jobStates).filter(s => s === 'rejected').length;
    document.getElementById('syncSavedCount').textContent = savedCount;
    document.getElementById('syncRejectedCount').textContent = rejectedCount;
    document.getElementById('syncModal').classList.remove('hidden');
  }

  function closeSyncModal() {
    document.getElementById('syncModal').classList.add('hidden');
  }

  async function confirmSync() {
    const savedList = Object.keys(jobStates).filter(id => jobStates[id] === 'saved');
    const rejectedList = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
    
    const syncBtn = document.getElementById('syncConfirmBtn');
    if (syncBtn) {
      syncBtn.disabled = true;
      syncBtn.textContent = "סנכרון מתבצע...";
    }

    saveTriageState(jobStates);
    await pushCloudSync();

    closeSyncModal();
    showToast('☁️', `כל הסימונים סונכרנו לענן בהצלחה! (${savedList.length} שמורות, ${rejectedList.length} הוסרו)`);
    if (syncBtn) {
      syncBtn.disabled = false;
      syncBtn.textContent = "אשר וסנכרן עכשיו";
    }
  }

  function openDuplicatesModal() {
    const content = document.getElementById('duplicatesContent');

    function normalize(str) {
      if (!str) return '';
      return str.toLowerCase().replace(/[^א-תa-z0-9]/g, ' ').replace(/  +/g, ' ').trim();
    }

    const seenLinks = new Set((rawJobsData || []).map(j => j.link));
    let allJobs = [...(rawJobsData || [])];
    
    if (typeof historicalCatalog !== 'undefined' && historicalCatalog) {
      Object.keys(jobStates).forEach(link => {
        if (jobStates[link] === 'saved' && !seenLinks.has(link) && historicalCatalog[link]) {
          allJobs.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
    }

    const activeJobs = allJobs.filter(job => {
      const state = jobStates[job.link] || 'pending';
      return state === 'saved' || state === 'pending';
    });

    const groups = {};
    
    function extractJobId(link) {
      if (!link) return null;
      const match = link.match(/(\\d{9,11})(?:[/?#]|$)/);
      if (match) return match[1];
      const comeetMatch = link.match(/([a-zA-Z0-9]+-[a-zA-Z0-9]+)\\/?$/);
      if (comeetMatch && link.includes('comeet')) return comeetMatch[1];
      return null;
    }

    activeJobs.forEach((job, idx) => {
      const titleCompKey = normalize(job.company) + '|' + normalize(job.title);
      let cleanTitle = normalize(job.title).replace(/(israel|remote|hybrid|tel aviv|haifa)$/i, '').trim();
      const cleanTitleCompKey = normalize(job.company) + '|' + cleanTitle;
      const jobId = extractJobId(job.link);
      
      let foundKey = null;
      if (jobId) {
        foundKey = Object.keys(groups).find(k => k.startsWith('ID: ' + jobId));
        if (!foundKey) foundKey = 'ID: ' + jobId + ' | ' + titleCompKey;
      } else {
        foundKey = Object.keys(groups).find(k => k.includes(cleanTitleCompKey)) || titleCompKey;
      }
      
      if (!groups[foundKey]) groups[foundKey] = [];
      groups[foundKey].push({ ...job, _idx: idx });
    });

    const dupGroups = Object.entries(groups).filter(([k, g]) => g.length > 1);

    if (dupGroups.length === 0) {
      content.innerHTML = `
        <div style="text-align: center; padding: 32px 12px;">
          <div style="font-size: 40px; margin-bottom: 12px;">✅</div>
          <div style="font-weight: 700; color: var(--dashboard-lime); font-size: 16px;">לא נמצאו כפילויות!</div>
          <div style="color: var(--dashboard-muted); font-size: 13px; margin-top: 6px;">כל ${activeJobs.length} המשרות הפעילות (שמורות וחדשות) ייחודיות לחלוטין.</div>
        </div>`;
    } else {
      const totalDups = dupGroups.reduce((sum, [k, g]) => sum + g.length - 1, 0);
      let html = `
        <div style="background: rgba(255, 211, 104, 0.12); border: 1px solid rgba(255, 211, 104, 0.35); border-radius: 16px; padding: 12px 16px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
          <div style="display: flex; align-items: center; gap: 8px; font-size: 13px;">
            <span style="font-size: 16px;">⚠️</span>
            <span style="color: var(--dashboard-gold); font-weight: 600;">אותרו <strong>${dupGroups.length}</strong> קבוצות עם <strong>${totalDups}</strong> כפילויות</span>
          </div>
        </div>`;

      dupGroups.forEach(([key, group], gi) => {
        const rep = group[0];
        const encKey = encodeURIComponent(key);
        html += `
          <div style="background: rgba(0, 0, 0, 0.28); border: 1px solid var(--dashboard-edge); border-radius: 18px; padding: 14px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px;">
                <span class="dashboard-chip" style="font-size: 11px; padding: 2px 8px;">#${gi + 1}</span>
                <span style="color: #fff;">${rep.company || '—'} — ${rep.title || '—'}</span>
                <span class="dashboard-chip" style="color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); font-size: 11px; padding: 2px 8px;">${group.length} מופעים</span>
              </div>
              <button onclick="purgeDuplicateGroup('${encKey}')" class="tool-btn" style="min-height: 36px; padding: 6px 14px; font-size: 12px; color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4);" title="שמור מופע אחד ומחק את שאר הכפילויות">
                ⚡ השאר אחת
              </button>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;">`;

        group.forEach((job, ji) => {
          const score = job.match_score || '—';
          const date = job.date || '—';
          const link = job.link || '#';
          const encLink = encodeURIComponent(link);
          const state = jobStates[job.link] || 'pending';
          const isSaved = state === 'saved';
          const statusBadge = isSaved
            ? `<span class="dashboard-chip" style="color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); font-size: 11px; padding: 2px 8px;">⭐ שמורה</span>`
            : `<span class="dashboard-chip" style="color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.4); font-size: 11px; padding: 2px 8px;">🆕 חדשה</span>`;

          html += `
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 10px 14px; gap: 10px;">
              <div style="display: flex; align-items: center; gap: 8px; font-size: 13px;">
                <span style="font-size: 11px; color: var(--dashboard-muted);">#${ji + 1}</span>
                ${statusBadge}
                <span style="font-weight: 700; color: var(--dashboard-lime);">${score}%</span>
                <span style="color: var(--dashboard-muted); font-size: 12px;">${date}</span>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <a href="${link}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); font-weight: 600; font-size: 13px; text-decoration: underline; text-underline-offset: 3px;">
                  פתח ↗
                </a>
                <button onclick="purgeSingleJob('${encLink}')" class="btn-triage" style="min-height: 32px; padding: 4px 10px; font-size: 12px; background: rgba(239, 68, 68, 0.2); color: #fca5a5; border-color: rgba(239, 68, 68, 0.4);" title="מחק כפילות זו">
                  🗑️
                </button>
              </div>
            </div>`;
        });
        html += `</div></div>`;
      });

      content.innerHTML = html;
    }

    document.getElementById('duplicatesModal').classList.remove('hidden');
  }

  function purgeSingleJob(encLink) {
    const link = decodeURIComponent(encLink);
    if (!link) return;
    jobStates[link] = 'purged';
    saveTriageState(jobStates);
    updateUI();
    pushCloudSync();
    showToast('🗑️', 'הכפילות נמחקה בהצלחה');
    openDuplicatesModal();
  }

  function purgeDuplicateGroup(encKey) {
    const targetKey = decodeURIComponent(encKey);
    function normalize(str) {
      if (!str) return '';
      return str.toLowerCase().replace(/[^א-תa-z0-9]/g, ' ').replace(/  +/g, ' ').trim();
    }

    const seenLinks = new Set((rawJobsData || []).map(j => j.link));
    let allJobs = [...(rawJobsData || [])];
    if (typeof historicalCatalog !== 'undefined' && historicalCatalog) {
      Object.keys(jobStates).forEach(link => {
        if (jobStates[link] === 'saved' && !seenLinks.has(link) && historicalCatalog[link]) {
          allJobs.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
    }

    function extractJobId(link) {
      if (!link) return null;
      const match = link.match(/(\\d{9,11})(?:[/?#]|$)/);
      if (match) return match[1];
      const comeetMatch = link.match(/([a-zA-Z0-9]+-[a-zA-Z0-9]+)\\/?$/);
      if (comeetMatch && link.includes('comeet')) return comeetMatch[1];
      return null;
    }
    
    const activeJobs = allJobs.filter(job => {
      const state = jobStates[job.link] || 'pending';
      if (state !== 'saved' && state !== 'pending') return false;
      
      const titleCompKey = normalize(job.company) + '|' + normalize(job.title);
      let cleanTitle = normalize(job.title).replace(/(israel|remote|hybrid|tel aviv|haifa)$/i, '').trim();
      const cleanTitleCompKey = normalize(job.company) + '|' + cleanTitle;
      const jobId = extractJobId(job.link);
      
      if (targetKey.startsWith('ID: ') && jobId) {
        return targetKey.includes(jobId);
      } else {
        return titleCompKey === targetKey || cleanTitleCompKey === targetKey || targetKey.includes(cleanTitleCompKey);
      }
    });

    if (activeJobs.length <= 1) return;

    activeJobs.sort((a, b) => {
      const aSaved = jobStates[a.link] === 'saved' ? 1 : 0;
      const bSaved = jobStates[b.link] === 'saved' ? 1 : 0;
      if (aSaved !== bSaved) return bSaved - aSaved;
      return (Number(b.match_score) || 0) - (Number(a.match_score) || 0);
    });

    const toPurge = activeJobs.slice(1);
    toPurge.forEach(j => {
      jobStates[j.link] = 'purged';
    });

    saveTriageState(jobStates);
    updateUI();
    pushCloudSync();
    showToast('⚡', `הושארה משרה אחת ונמחקו ${toPurge.length} כפילויות`);
    openDuplicatesModal();
  }

  function closeDuplicatesModal() {
    document.getElementById('duplicatesModal').classList.add('hidden');
  }

  function clearAllRejected() {
    const rejectedKeys = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
    if (rejectedKeys.length === 0) {
      showToast('ℹ️', 'אין משרות מוסרות למחיקה');
      return;
    }

    if (!confirm(`האם אתה בטוח שברצונך למחוק לצמיתות ${rejectedKeys.length} משרות שהוסרו ולאפס את המונה?`)) {
      return;
    }

    rejectedKeys.forEach(id => {
      jobStates[id] = 'purged';
    });

    saveTriageState(jobStates);
    updateUI();
    pushCloudSync();
    showToast('🗑️', `כל ${rejectedKeys.length} המשרות שהוסרו נמחקו לצמיתות והמונה אופס ל-0`);
  }

  function exportSavedToExcel() {
    const seenLinks = new Set((rawJobsData || []).map(j => j.link));
    let allPotentialSaved = [...(rawJobsData || [])];
    if (typeof historicalCatalog !== 'undefined' && historicalCatalog) {
      Object.keys(jobStates).forEach(link => {
        if (jobStates[link] === 'saved' && !seenLinks.has(link) && historicalCatalog[link]) {
          allPotentialSaved.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
    }
    const savedJobs = allPotentialSaved.filter(job => jobStates[job.link] === 'saved');
    if (savedJobs.length === 0) {
      showToast('⚠️', 'לא נמצאו משרות שמורות לייצוא');
      return;
    }

    const BOM = '\\uFEFF';
    const headers = [
      'חברה',
      'כותרת משרה',
      'ציון התאמה',
      'תחום',
      'מיקום',
      'טווח שכר צפוי',
      'ביסוס ומקור שכר',
      'דרישות החברה עבור המשרה',
      'תחום ומוצר החברה',
      'תקציר המשרה',
      'נקודות חוזק מהניסיון',
      'דגשים ומודל עבודה',
      'לינק למשרה',
      'תאריך איתור'
    ];

    const escapeCSV = (val) => {
      if (val === null || val === undefined) return '""';
      const str = String(val).replace(/"/g, '""');
      return `"${str}"`;
    };

    const rows = savedJobs.map(job => {
      const score = job.match_score || '';
      const reqs = job.company_requirements || '';
      const domain = job.company_domain_product || job.company_summary || '';
      const summary = job.job_summary || job.company_summary || '';
      const strengths = job.experience_strengths || job.reasoning || '';
      const highlights = job.key_highlights || (job.work_model ? `מודל: ${job.work_model}` : '');
      const date = job.date || '';
      let salaryStr = job.salary_range || 'לא צוין';
      if (job.salary_source_label) {
        salaryStr += ` (${job.salary_source_label})`;
      }
      const salaryEvidence = job.salary_evidence || '';

      return [
        escapeCSV(job.company || ''),
        escapeCSV(job.title || ''),
        escapeCSV(score),
        escapeCSV(job.sector || job.sector_key || ''),
        escapeCSV(job.location || 'ישראל'),
        escapeCSV(salaryStr),
        escapeCSV(salaryEvidence),
        escapeCSV(reqs),
        escapeCSV(domain),
        escapeCSV(summary),
        escapeCSV(strengths),
        escapeCSV(highlights),
        escapeCSV(job.link || ''),
        escapeCSV(date)
      ].join(',');
    });

    const csvContent = BOM + [headers.map(escapeCSV).join(','), ...rows].join(String.fromCharCode(13, 10));
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const dateStr = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `משרות_שמורות_עידו_גל_${dateStr}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('📊', `יוצאו ${savedJobs.length} משרות שמורות לאקסל בהצלחה!`);
  }

  window.onload = () => {
    checkUrlSync();
    renderCards();
    fetchCloudSync();

    const hash = window.location.hash.replace('#', '');
    if (hash === 'saved' || hash === 'rejected') {
      const tabs = document.querySelectorAll('.tab-btn');
      const targetTab = hash === 'saved' ? tabs[1] : tabs[2];
      if (targetTab) setFilter(hash, targetTab);
    }
  };

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      fetchCloudSync();
    }
  });

  window.addEventListener('focus', () => {
    fetchCloudSync();
  });
</script>
</body>
</html>"""

def generate_interactive_html(jobs, rejected_links, title="דוח משרות אינטראקטיבי | עידו גל", is_weekly=False):
    saved_links = []
    
    # Load historical catalog to support rendering of all saved jobs
    project_root = os.path.dirname(os.path.dirname(__file__))
    catalog_path = os.path.join(project_root, "data", "historical_catalog.json")
    catalog_data = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)
        except Exception:
            catalog_data = {}

    total_jobs = len(jobs)
    now_str = datetime.now().strftime("%d.%m.%Y")
    report_type_label = "סיכום שבועי" if is_weekly else "סריקה יומית"

    # Pre-sort jobs by date descending (newest first), then by match_score descending
    def _sort_key(j):
        d = j.get("date", "") or "0000-00-00"
        try:
            s = int(j.get("match_score", 0) or 0)
        except Exception:
            s = 0
        return (d, s)

    sorted_jobs = sorted(jobs, key=_sort_key, reverse=True)
    jobs_json = json.dumps(sorted_jobs, ensure_ascii=False)
    catalog_json = json.dumps(catalog_data, ensure_ascii=False)
    saved_json = json.dumps(list(saved_links) if isinstance(saved_links, (set, list)) else [], ensure_ascii=False)
    rejected_json = json.dumps(list(rejected_links) if isinstance(rejected_links, (set, list)) else [], ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace("__REPORT_TYPE_LABEL__", report_type_label)
    html = html.replace("__NOW_STR__", now_str)
    html = html.replace("__TOTAL_JOBS__", str(total_jobs))
    html = html.replace("__JOBS_JSON__", jobs_json)
    html = html.replace("__CATALOG_JSON__", catalog_json)
    html = html.replace("__INITIAL_SAVED_JSON__", saved_json)
    html = html.replace("__INITIAL_REJECTED_JSON__", rejected_json)
    return html

def build_and_save_docs_app(jobs, rejected_links, project_root, is_weekly=False):
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    out_file = os.path.join(docs_dir, "index.html")
    
    html = generate_interactive_html(jobs, rejected_links, is_weekly=is_weekly)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Successfully generated GitHub Pages interactive web app at: {out_file}")
    return out_file

def update_weekly_archive(new_jobs, archive_file_path, rejected_set):
    archive = []
    if os.path.exists(archive_file_path):
        try:
            with open(archive_file_path, "r", encoding="utf-8") as f:
                archive = json.load(f)
        except Exception:
            archive = []
            
    # Always keep historical catalog updated with all jobs before pruning
    project_root = os.path.dirname(os.path.dirname(archive_file_path))
    catalog_path = os.path.join(project_root, "data", "historical_catalog.json")
    catalog = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            catalog = {}

    for j in archive:
        link = j.get("link")
        if link and link not in catalog:
            catalog[link] = j

    cutoff_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    archive = [j for j in archive if j.get("date", "") >= cutoff_date]
    
    archive = [j for j in archive if j.get("link") not in rejected_set]

    seen_links = {j.get("link") for j in archive}
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if new_jobs:
        for job in new_jobs:
            link = job.get("link")
            if link and link not in seen_links and link not in rejected_set:
                seen_links.add(link)
                job_copy = dict(job)
                job_copy["date"] = today_str
                archive.append(job_copy)
                if link not in catalog:
                    catalog[link] = job_copy
            
    with open(archive_file_path, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    try:
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return archive
