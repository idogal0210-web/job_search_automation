import os
import json
import re
from datetime import datetime, timedelta
from src.state_manager import save_state_atomic

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>__TITLE__</title>
  <link rel="stylesheet" href="fonts.css">
  <link rel="stylesheet" href="theme.css">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/duotone/style.css">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/bold/style.css">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
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

    /* Phosphor Icons Alignment & RTL Duotone Stabilization */
    i[class^="ph-"], i[class*=" ph-"] {
      direction: ltr !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 1em !important;
      height: 1em !important;
      position: relative !important;
      vertical-align: -0.15em !important;
      flex-shrink: 0 !important;
      line-height: 1 !important;
      box-sizing: border-box !important;
    }
    i[class^="ph-"]::before, i[class*=" ph-"]::before,
    i[class^="ph-"]::after, i[class*=" ph-"]::after {
      position: absolute !important;
      top: 0 !important;
      left: 0 !important;
      width: 100% !important;
      height: 100% !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      margin: 0 !important;
      line-height: 1 !important;
    }
    .btn-triage i[class^="ph-"],
    .btn-triage i[class*=" ph-"],
    .tool-btn i[class^="ph-"],
    .tool-btn i[class*=" ph-"],
    .tab-btn i[class^="ph-"],
    .tab-btn i[class*=" ph-"],
    .dashboard-chip i[class^="ph-"],
    .dashboard-chip i[class*=" ph-"],
    .btn-apply i[class^="ph-"],
    .btn-apply i[class*=" ph-"],
    .btn-excel i[class^="ph-"],
    .btn-excel i[class*=" ph-"] {
      font-size: 1.15em;
    }
    .tab-btn, .btn-triage, .tool-btn, .dashboard-chip, .btn-apply {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    body {
      direction: rtl;
      text-align: right;
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
      border-radius: 28px !important;
      padding: 12px 20px !important;
      overflow: hidden !important;
      position: relative;
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
      gap: 3px;
    }
    .brand-title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--dashboard-text);
      line-height: 1.2;
    }
    .header-sync-btn, .header-about-btn {
      width: 44px;
      height: 44px;
      min-width: 44px;
      min-height: 44px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: var(--dashboard-text);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      position: relative;
      transition: all 0.2s ease;
      font-size: 18px;
      padding: 0;
    }
    .header-sync-btn:hover, .header-about-btn:hover {
      background: rgba(255, 255, 255, 0.16);
      border-color: rgba(255, 255, 255, 0.4);
      transform: translateY(-1px);
    }
    .header-sync-btn:focus-visible, .header-about-btn:focus-visible {
      outline: 3px solid var(--dashboard-lime);
      outline-offset: 2px;
    }
    .sync-status-dot {
      position: absolute;
      top: 8px;
      left: 8px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--dashboard-cyan);
      box-shadow: 0 0 6px var(--dashboard-cyan);
      transition: background-color 0.3s ease;
    }
    .sync-status-dot.syncing {
      background: var(--dashboard-gold);
      box-shadow: 0 0 8px var(--dashboard-gold);
    }
    .sync-status-dot.offline {
      background: #f87171;
      box-shadow: 0 0 8px #f87171;
    }
    .sync-time-chip {
      font-size: 11px;
      color: var(--dashboard-muted);
      letter-spacing: 0.3px;
      white-space: nowrap;
    }
    .brand-subtitle-row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
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

    /* Header Progress & Navigation Hub */
    .header-progress-hub {
      display: flex;
      align-items: center;
      gap: 16px;
      flex: 1;
      justify-content: center;
      max-width: 840px;
    }
    .dashboard-app .metrics-summary-toggle,
    .metrics-summary-toggle {
      display: none !important; /* Desktop hidden */
      width: 100%;
      min-height: 44px;
      padding: 8px 14px;
      border-radius: 14px !important;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: var(--dashboard-text);
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s ease;
      box-sizing: border-box;
    }
    .metrics-summary-toggle:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.3);
    }
    .metrics-summary-toggle:focus-visible {
      outline: 3px solid var(--dashboard-lime);
      outline-offset: 2px;
    }
    .metrics-summary-inline {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .metric-summary-pill {
      padding: 2.5px 8px;
      border-radius: 8px;
      font-size: 11.5px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }
    .metric-summary-pill.lime { background: rgba(220, 255, 114, 0.16); color: var(--dashboard-lime); }
    .metric-summary-pill.gold { background: rgba(255, 211, 104, 0.16); color: var(--dashboard-gold); }
    .metric-summary-pill.cyan { background: rgba(137, 244, 231, 0.16); color: var(--dashboard-cyan); }
    .metric-summary-pill.rose { background: rgba(248, 113, 113, 0.16); color: #fca5a5; }
    .metrics-toggle-label {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--dashboard-muted);
      font-size: 11.5px;
      font-weight: 600;
    }
    .dashboard-app .metrics-collapsible-content,
    .metrics-collapsible-content {
      display: flex !important;
      align-items: center;
      gap: 14px;
      flex: 1;
      justify-content: flex-end;
      width: auto;
      min-width: 0;
    }
    .header-progress-info {
      display: flex;
      flex-direction: column;
      gap: 3px;
      min-width: 160px;
      max-width: 220px;
      flex: 1;
    }
    .header-progress-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .header-progress-title {
      font-size: 13.5px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .header-stat-cubes {
      display: grid !important;
      grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
      gap: 8px !important;
      flex-shrink: 0 !important;
    }
    .dashboard-app .stat-cube-btn,
    .stat-cube-btn {
      background: rgba(0, 0, 0, 0.28) !important;
      border: 1px solid var(--dashboard-edge) !important;
      border-radius: 18px !important;
      padding: 7px 12px !important;
      display: flex !important;
      flex-direction: column !important;
      align-items: center !important;
      justify-content: center !important;
      text-align: center !important;
      gap: 3px !important;
      cursor: pointer !important;
      min-width: 82px !important;
      max-width: 98px !important;
      min-height: auto !important;
      height: auto !important;
      box-sizing: border-box !important;
      color: var(--dashboard-text) !important;
      text-decoration: none !important;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.08) !important;
      position: relative !important;
    }
    .stat-cube-btn:hover {
      background: rgba(255, 255, 255, 0.08) !important;
      border-color: rgba(255, 255, 255, 0.35) !important;
      transform: translateY(-2px);
    }
    .stat-cube-btn.active {
      background: linear-gradient(145deg, rgba(220, 255, 114, 0.18), rgba(255, 255, 255, 0.06)) !important;
      border-color: var(--dashboard-lime) !important;
      box-shadow: 0 4px 18px rgba(220, 255, 114, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
    }
    .stat-cube-btn.active.cube-starred {
      background: linear-gradient(145deg, rgba(251, 191, 36, 0.2), rgba(255, 255, 255, 0.06)) !important;
      border-color: var(--dashboard-gold) !important;
      box-shadow: 0 4px 18px rgba(251, 191, 36, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
    }
    .stat-cube-btn.active.cube-saved {
      background: linear-gradient(145deg, rgba(137, 244, 231, 0.2), rgba(255, 255, 255, 0.06)) !important;
      border-color: var(--dashboard-cyan) !important;
      box-shadow: 0 4px 18px rgba(137, 244, 231, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
    }
    .stat-cube-btn.active.cube-rejected {
      background: linear-gradient(145deg, rgba(248, 113, 113, 0.18), rgba(255, 255, 255, 0.06)) !important;
      border-color: #fca5a5 !important;
      box-shadow: 0 4px 18px rgba(239, 68, 68, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
    }
    .stat-cube-icon {
      width: 28px !important;
      height: 28px !important;
      border-radius: 9px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 15px !important;
      font-weight: 700 !important;
      margin-bottom: 2px !important;
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.4) !important;
      flex-shrink: 0 !important;
    }
    .stat-cube-icon.lime { background: var(--dashboard-lime); color: #171c12; }
    .stat-cube-icon.gold { background: var(--dashboard-gold); color: #171c12; }
    .stat-cube-icon.cyan { background: var(--dashboard-cyan); color: #171c12; }
    .stat-cube-icon.rose { background: #fca5a5; color: #171c12; }
    .stat-cube-count {
      font-size: 16px !important;
      font-weight: 700 !important;
      color: #fff !important;
      line-height: 1.1 !important;
    }
    .stat-cube-label {
      font-size: 11px !important;
      font-weight: 600 !important;
      color: var(--dashboard-muted) !important;
      white-space: nowrap !important;
    }

    /* Stats Overview Grid (2 Cards: Search/Filters & Sector Chart) */
    .dashboard-stats-grid {
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }
    @media (max-width: 950px) {
      .dashboard-stats-grid {
        grid-template-columns: 1fr;
      }
    }

    /* Progress Segmented Bar */
    .segmented-progress {
      width: 100%;
      height: 8px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      display: flex;
      overflow: hidden;
      gap: 2px;
      margin: 6px 0;
      box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4);
    }
    .segmented-progress-bar {
      height: 100%;
      transition: width 0.4s ease;
    }

    /* Controls Panel - Proportional Typography and Harmonized Heights */
    .controls-inputs-stack {
      display: flex;
      flex-direction: column;
      gap: 9px;
    }
    .filters-two-col-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      width: 100%;
    }
    .filter-select-field {
      width: 100%;
    }
    .search-sort-compact-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
    }
    .search-sort-compact-bar .search-input-wrapper {
      flex: 1.4;
      min-width: 0;
    }
    .search-sort-compact-bar .sort-select-wrapper {
      flex: 1;
      min-width: 0;
    }
    .tool-btn-compact {
      min-height: 38px;
      min-width: 44px;
      height: 38px;
      padding: 0 12px;
      border-radius: 12px;
      background: rgba(255, 211, 104, 0.1);
      border: 1px solid rgba(255, 211, 104, 0.35);
      color: var(--dashboard-gold);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }
    .tool-btn-compact:hover {
      background: rgba(255, 211, 104, 0.2);
      border-color: var(--dashboard-gold);
    }
    .tool-btn-compact:focus-visible {
      outline: 2px solid var(--dashboard-gold);
      outline-offset: 2px;
    }
    .search-input-wrapper {
      position: relative;
      width: 100%;
      display: flex;
      align-items: center;
    }
    .dashboard-app .search-input-wrapper input {
      padding-inline-start: 12px !important;
      padding-inline-end: 42px !important;
    }
    .btn-clear-search {
      position: absolute;
      left: 6px;
      top: 50%;
      transform: translateY(-50%);
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.12);
      border: none;
      color: var(--dashboard-muted);
      display: none;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 14px;
      padding: 0 !important;
      min-height: 32px !important;
      min-width: 32px !important;
      line-height: 1 !important;
      transition: all 0.18s ease;
      z-index: 2;
    }
    .btn-clear-search::after {
      content: "";
      position: absolute;
      inset: -6px;
      border-radius: 50%;
    }
    .btn-clear-search:hover {
      background: rgba(255, 255, 255, 0.22);
      color: #ffffff;
      transform: translateY(-50%) scale(1.08);
    }
    .btn-clear-search:focus-visible {
      outline: 2px solid var(--dashboard-lime);
    }
    .search-input-wrapper.has-value .btn-clear-search {
      display: flex;
    }
    .dashboard-app .controls-inputs-stack select,
    .dashboard-app .controls-inputs-stack input {
      height: 42px !important;
      min-height: 42px !important;
      padding: 0 14px !important;
      font-size: 13.5px !important;
      font-weight: 500 !important;
      color: var(--dashboard-text) !important;
      background: rgba(0, 0, 0, 0.28) !important;
      border: 1px solid var(--dashboard-edge) !important;
      border-radius: 14px !important;
      box-sizing: border-box !important;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
      line-height: 40px !important;
    }
    .dashboard-app .controls-inputs-stack select:focus,
    .dashboard-app .controls-inputs-stack input:focus {
      outline: none !important;
      border-color: var(--dashboard-cyan) !important;
      box-shadow: 0 0 10px rgba(137, 244, 231, 0.2) !important;
    }
    .dashboard-app .controls-inputs-stack input::placeholder {
      color: rgba(255, 255, 255, 0.65) !important;
      font-size: 13.5px !important;
    }
    .controls-buttons-row {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .sort-select-container {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
      min-width: 160px;
      height: 42px;
    }
    .dashboard-app .sort-select-container select {
      width: 100% !important;
      height: 42px !important;
      min-height: 42px !important;
      border-radius: 999px !important;
      padding: 0 36px 0 14px !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      cursor: pointer !important;
      background: linear-gradient(160deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.06)) !important;
      border: 1px solid var(--dashboard-edge) !important;
      color: var(--dashboard-text) !important;
      text-align: right !important;
      direction: rtl !important;
      box-sizing: border-box !important;
      line-height: 40px !important;
    }
    .dashboard-app .sort-select-container select:hover {
      background: rgba(255, 255, 255, 0.16) !important;
      border-color: rgba(255, 255, 255, 0.38) !important;
    }
    .sort-select-container #sortIcon,
    #sortIcon {
      position: absolute !important;
      right: 12px !important;
      top: 50% !important;
      transform: translateY(-50%) !important;
      pointer-events: none !important;
      color: var(--dashboard-cyan) !important;
      font-size: 15px !important;
      z-index: 5 !important;
      margin: 0 !important;
    }
    .dashboard-app .controls-buttons-row .tool-btn {
      height: 42px !important;
      min-height: 42px !important;
      padding: 0 16px !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      border-radius: 999px !important;
      cursor: pointer !important;
      border: 1px solid var(--dashboard-edge) !important;
      background: linear-gradient(160deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.07)) !important;
      color: var(--dashboard-text) !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      gap: 7px !important;
      box-sizing: border-box !important;
      white-space: nowrap !important;
      line-height: 40px !important;
      transition: background 0.2s ease, border-color 0.2s ease;
    }
    .dashboard-app .controls-buttons-row .tool-btn:hover {
      background: rgba(255, 255, 255, 0.18) !important;
      border-color: rgba(255, 255, 255, 0.4) !important;
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
    .btn-excel {
      background: #107c41 !important;
      color: #ffffff !important;
      border: 1px solid #16a34a !important;
      border-radius: 999px;
      padding: 10px 22px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(16, 124, 65, 0.4);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .btn-excel:hover {
      background: #0d6836 !important;
      border-color: #22c55e !important;
      box-shadow: 0 6px 20px rgba(16, 124, 65, 0.55);
      transform: translateY(-2px);
    }
    .btn-excel i {
      font-size: 19px;
      color: #ffffff !important;
    }

    /* Job Cards Grid Container (Cubes Layout) */
    #cardsContainer.is-hidden-by-map,
    #cardsContainer[style*="display: none"] {
      display: none !important;
    }
    #cardsContainer {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 24px;
      margin-bottom: 32px;
      align-items: stretch;
    }
    @media (max-width: 820px) {
      #cardsContainer {
        grid-template-columns: 1fr;
        gap: 16px;
      }
    }

    /* Job Card Cube Styling */
    .job-card {
      margin-bottom: 0;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      gap: 16px;
      border-radius: 26px;
      padding: 24px;
      transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
      position: relative;
      background: var(--dashboard-glass);
      border: 1px solid var(--dashboard-edge);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22);
      height: 100%;
      box-sizing: border-box;
      contain: layout style;
    }
    .job-card:nth-child(n+7) {
      content-visibility: auto;
      contain-intrinsic-size: auto 340px;
    }
    .job-card:hover {
      border-color: rgba(255, 255, 255, 0.36);
      transform: translateY(-4px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.38);
    }
    .job-card-topbar {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .job-card-topbar-primary {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      width: 100%;
    }
    .job-card-topbar-primary > div:first-child {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
      flex: 1;
      overflow: hidden;
    }
    .job-card-topbar-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .badge-score {
      padding: 5px 12px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 12.5px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      white-space: nowrap !important;
      word-break: keep-all !important;
      flex-shrink: 0 !important;
      line-height: 1.2 !important;
    }
    .badge-score span {
      white-space: nowrap !important;
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
      border-radius: 14px;
      background: #ffffff;
      border: 1px solid var(--dashboard-edge);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
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
      padding: 4px;
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
    .job-company-name {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--dashboard-cyan);
      margin-bottom: 2px;
      letter-spacing: 0.2px;
      overflow-wrap: break-word;
      word-break: normal;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
      text-align: start;
    }
    .job-title-text {
      font-size: 17.5px;
      font-weight: 600;
      color: #ffffff;
      margin: 0 0 8px;
      line-height: 1.35;
      overflow-wrap: break-word;
      word-break: normal;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
      text-align: start;
    }
    /* 2 Distinct Bubbles: Domain & Requirements */
    .job-bubbles-wrapper {
      display: flex;
      flex-direction: column;
      gap: 9px;
      margin: 4px 0 6px 0;
    }
    .job-bubble {
      border-radius: 14px;
      padding: 10px 14px;
      font-size: 13px;
      line-height: 1.55;
      overflow-wrap: break-word;
      word-break: normal;
    }
    .job-bubble-domain {
      background: rgba(137, 244, 231, 0.05);
      border: 1px solid rgba(137, 244, 231, 0.22);
      color: #e2e8df;
    }
    .job-bubble-domain .bubble-title {
      color: var(--dashboard-cyan);
      margin-inline-end: 5px;
      display: inline;
      font-weight: 700;
    }
    .job-bubble-reqs {
      background: rgba(220, 255, 114, 0.04);
      border: 1px solid rgba(220, 255, 114, 0.22);
      color: #e2e8df;
    }
    .job-bubble-reqs .bubble-title {
      color: var(--dashboard-lime);
      margin-inline-end: 5px;
      display: inline;
      font-weight: 700;
    }
    .job-bubble .bubble-content {
      color: #e2e8df;
    }

    .btn-toggle-details {
      width: 100%;
      min-height: 40px;
      padding: 8px 16px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px dashed rgba(255, 255, 255, 0.18);
      color: var(--dashboard-cyan);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
    }
    .btn-toggle-details:hover {
      background: rgba(137, 244, 231, 0.09);
      border-color: rgba(137, 244, 231, 0.35);
    }
    .btn-toggle-details.expanded {
      background: rgba(255, 255, 255, 0.08);
      border-style: solid;
      color: var(--dashboard-muted);
    }

    .job-details-collapsible {
      display: none;
      animation: fadeInDetails 0.22s ease-out;
    }
    .job-details-collapsible.expanded {
      display: block;
    }
    @keyframes fadeInDetails {
      from { opacity: 0; transform: translateY(-5px); }
      to { opacity: 1; transform: translateY(0); }
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
      overflow-wrap: break-word;
      word-break: normal;
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
      flex-direction: column;
      gap: 9px;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      margin-top: auto;
      width: 100%;
    }
    .action-btn-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      width: 100%;
    }
    .btn-triage {
      width: 100%;
      min-height: 40px;
      padding: 8px 10px;
      font-size: 13px;
      font-weight: 600;
      border-radius: 999px;
      cursor: pointer;
      border: 1px solid var(--dashboard-edge);
      background: linear-gradient(160deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.06));
      color: var(--dashboard-text);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
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
    .action-btn-main-group {
      display: flex;
      width: 100%;
    }
    .btn-card-details {
      width: 100%;
      min-height: 44px;
      padding: 9px 12px;
      font-size: 13.5px;
      font-weight: 600;
      border-radius: 999px;
      cursor: pointer;
      border: 1px solid rgba(255, 255, 255, 0.18);
      background: rgba(255, 255, 255, 0.06);
      color: var(--dashboard-text);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
      box-sizing: border-box;
    }
    .btn-card-details:hover {
      background: rgba(255, 255, 255, 0.14);
      border-color: rgba(255, 255, 255, 0.35);
    }
    .btn-card-details:active {
      background: rgba(255, 255, 255, 0.2);
    }
    .dashboard-app a.btn-apply,
    .dashboard-app a.btn-apply span,
    .btn-apply,
    .btn-apply span {
      color: #ffffff !important;
    }
    .btn-apply {
      width: 100%;
      min-height: 44px;
      padding: 9px 18px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 999px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      white-space: nowrap;
      background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
      color: #ffffff !important;
      border: 1px solid rgba(137, 244, 231, 0.4);
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.2), 0 4px 14px rgba(13, 148, 136, 0.3);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dashboard-app a.btn-apply:hover,
    .dashboard-app a.btn-apply:hover span,
    .btn-apply:hover,
    .btn-apply:hover span {
      background: linear-gradient(135deg, #0f766e 0%, #115e59 100%) !important;
      color: #ffffff !important;
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.3), 0 6px 18px rgba(15, 118, 110, 0.4);
      transform: translateY(-1px);
    }

    /* Leaflet Marker Cluster Styles */
    .marker-cluster-custom {
      background: none !important;
      border: none !important;
    }
    .custom-cluster-badge {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 13.5px;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.55), inset 0 1px 2px rgba(255, 255, 255, 0.5);
      border: 2px solid #ffffff;
      color: #0f172a;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .custom-cluster-badge:hover {
      transform: scale(1.1);
    }
    .custom-cluster-badge.small {
      background: var(--dashboard-lime);
    }
    .custom-cluster-badge.medium {
      background: var(--dashboard-cyan);
    }
    .custom-cluster-badge.large {
      background: var(--dashboard-gold);
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
    .job-details-modal-box {
      max-width: 640px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      padding: 0 !important;
      overflow: hidden;
      border-radius: 24px;
      background: #111827;
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
      position: relative;
    }
    .job-modal-header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(17, 24, 39, 0.98);
      flex-shrink: 0;
    }
    .job-modal-close-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #ffffff;
      border-radius: 999px;
      padding: 6px 14px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }
    .job-modal-close-btn:hover {
      background: rgba(255, 255, 255, 0.16);
    }
    .modal-close-btn {
      width: 44px;
      height: 44px;
      min-width: 44px;
      min-height: 44px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 16px;
      transition: all 0.2s ease;
      padding: 0;
    }
    .modal-close-btn:hover {
      background: rgba(255, 255, 255, 0.18);
      border-color: rgba(255, 255, 255, 0.35);
    }
    .modal-close-btn:focus-visible {
      outline: 3px solid var(--dashboard-lime);
      outline-offset: 2px;
    }
    .job-modal-body {
      padding: 18px 20px 24px;
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
      -webkit-overflow-scrolling: touch;
    }
    .job-modal-bottom-bar {
      padding: 12px 18px 16px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(15, 20, 31, 0.98);
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex-shrink: 0;
    }
    .job-modal-bottom-bar .btn-apply {
      width: 100%;
      min-height: 44px;
      font-size: 14.5px;
      font-weight: 700;
    }
    .job-modal-triage-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      width: 100%;
    }
    .job-modal-triage-group .btn-triage {
      min-height: 38px;
      font-size: 12.5px;
    }

    /* Search Query Term Highlight */
    mark.search-highlight {
      background: rgba(137, 244, 231, 0.24) !important;
      color: #ffffff !important;
      border-radius: 4px;
      padding: 0 3px;
      box-shadow: 0 0 8px rgba(137, 244, 231, 0.35);
      font-weight: inherit;
    }

    /* Back To Top Floating Button */
    .btn-back-to-top {
      position: fixed;
      bottom: 26px;
      left: 26px;
      z-index: 99;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(17, 24, 39, 0.85);
      border: 1px solid var(--dashboard-edge);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
      -webkit-backdrop-filter: blur(16px);
      backdrop-filter: blur(16px);
      color: var(--dashboard-cyan);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 19px;
      cursor: pointer;
      opacity: 0;
      visibility: hidden;
      transform: translateY(20px);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      padding: 0 !important;
      min-height: 44px !important;
    }
    .btn-back-to-top.visible {
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
    }
    .btn-back-to-top:hover {
      background: rgba(137, 244, 231, 0.18);
      border-color: var(--dashboard-cyan);
      color: #ffffff;
      transform: translateY(-3px);
      box-shadow: 0 14px 30px rgba(137, 244, 231, 0.25);
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

    /* Hidden card helper (strictly overrides any !important on display in grid/list) */
    .job-card.is-hidden,
    .job-card[style*="display: none"],
    #cardsContainer .job-card.is-hidden,
    #cardsContainer .job-card[style*="display: none"] {
      display: none !important;
    }

    /* Responsive Media Queries (Mobile, iPhone & Tablet) */
    @media (max-width: 880px) {
      body, html {
        overflow-x: hidden;
      }
      .dashboard-app {
        padding: 16px clamp(14px, 4vw, 20px) 28px;
        overflow-x: hidden;
      }
      .dashboard-sidebar {
        border-radius: 24px !important;
        flex-direction: column !important;
        align-items: stretch !important;
        gap: 12px !important;
        padding: 14px 12px !important;
        overflow: hidden !important;
      }
      .dashboard-sidebar-brand {
        justify-content: space-between !important;
        width: 100% !important;
      }
      .header-progress-hub {
        flex-direction: column !important;
        width: 100% !important;
        gap: 10px !important;
      }
      .dashboard-app .metrics-summary-toggle,
      .metrics-summary-toggle {
        display: flex !important;
        width: 100% !important;
        padding: 6px 10px !important;
        min-height: 44px !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 8px !important;
        border-radius: 14px !important;
        box-sizing: border-box !important;
      }
      .metrics-summary-inline {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 4px !important;
        flex: 1 !important;
        min-width: 0 !important;
        align-items: center !important;
      }
      .metric-summary-pill {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 3px !important;
        padding: 4px 2px !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        border-radius: 8px !important;
        text-align: center !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
      }
      @media (max-width: 400px) {
        .metric-summary-pill {
          font-size: 10px !important;
          padding: 3.5px 1px !important;
          gap: 2px !important;
        }
      }
      .metrics-toggle-label {
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        font-size: 11.5px !important;
        font-weight: 600 !important;
        color: var(--dashboard-muted) !important;
        flex-shrink: 0 !important;
        padding-inline-start: 6px !important;
        border-inline-start: 1px solid rgba(255, 255, 255, 0.15) !important;
      }
      .dashboard-app .metrics-collapsible-content,
      .metrics-collapsible-content {
        display: none !important;
        flex-direction: column !important;
        width: 100% !important;
        gap: 10px !important;
      }
      .dashboard-app .metrics-collapsible-content.is-expanded,
      .metrics-collapsible-content.is-expanded {
        display: flex !important;
      }
      .header-progress-info {
        width: 100% !important;
        max-width: 100% !important;
      }
      .header-progress-title-row > div:last-child {
        display: none !important;
      }

      /* Airy, Legible Header Stat Cubes on Mobile */
      .header-stat-cubes {
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 8px !important;
        padding: 4px 0 !important;
        width: 100% !important;
      }
      .dashboard-app .stat-cube-btn,
      .stat-cube-btn {
        min-width: 0 !important;
        max-width: none !important;
        padding: 9px 5px !important;
        border-radius: 16px !important;
        height: auto !important;
        gap: 3px !important;
      }
      .stat-cube-icon {
        width: 24px !important;
        height: 24px !important;
        border-radius: 8px !important;
        margin-bottom: 2px !important;
        font-size: 13px !important;
      }
      .stat-cube-icon i {
        font-size: 13px !important;
      }
      .stat-cube-count {
        font-size: 1.15rem !important;
        line-height: 1.1 !important;
        margin: 1px 0 !important;
        font-weight: 700 !important;
      }
      .stat-cube-label {
        font-size: 11px !important;
        line-height: 1.25 !important;
        white-space: normal !important;
        font-weight: 600 !important;
        letter-spacing: normal !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
      }

      .header-actions-group {
        justify-content: space-between;
        width: 100%;
      }
      .dashboard-topbar {
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        gap: 6px !important;
        padding: 0 4px 10px !important;
      }
      .dashboard-topbar > div {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
      }

      /* Compact Search & Filter Section on Mobile */
      .dashboard-stats-grid {
        grid-template-columns: 1fr !important;
        gap: 8px !important;
        margin-bottom: 12px !important;
      }
      .dashboard-stats-grid > .dashboard-card:nth-child(2) {
        display: none !important; /* Hide sector chart on mobile to save ~250px vertical space */
      }
      .dashboard-stats-grid > .dashboard-card:first-child {
        padding: 16px !important;
        border-radius: 20px !important;
      }
      .dashboard-stats-grid > .dashboard-card:first-child p {
        display: none !important; /* Hide descriptive paragraph */
      }
      .dashboard-stats-grid > .dashboard-card:first-child > div:first-child {
        display: none !important; /* Hide decorative header tags */
      }
      .dashboard-stats-grid > .dashboard-card:first-child h3 {
        font-size: 15px !important;
        margin: 0 0 10px !important;
        color: #ffffff !important;
      }
      .controls-inputs-stack {
        gap: 10px !important;
      }
      .filters-two-col-row {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 9px !important;
        width: 100% !important;
      }
      .filters-two-col-row select {
        width: 100% !important;
        height: 42px !important;
        min-height: 42px !important;
        padding: 0 24px 0 10px !important;
        font-size: 13px !important;
        border-radius: 14px !important;
      }
      .search-sort-compact-bar {
        display: grid !important;
        grid-template-columns: 1fr auto !important;
        gap: 9px !important;
        width: 100% !important;
      }
      .search-sort-compact-bar .search-input-wrapper {
        grid-column: 1 / -1 !important;
        width: 100% !important;
        position: relative !important;
      }
      .search-sort-compact-bar .search-input-wrapper input {
        width: 100% !important;
        height: 42px !important;
        min-height: 42px !important;
        padding: 0 14px 0 42px !important;
        font-size: 13px !important;
        border-radius: 14px !important;
      }
      .search-sort-compact-bar .sort-select-wrapper {
        grid-column: 1 !important;
        min-width: 0 !important;
        width: 100% !important;
      }
      .search-sort-compact-bar .sort-select-container {
        min-width: 0 !important;
        width: 100% !important;
        height: 42px !important;
      }
      .search-sort-compact-bar .sort-select-container select {
        width: 100% !important;
        height: 42px !important;
        min-height: 42px !important;
        font-size: 12.5px !important;
        padding: 0 34px 0 12px !important;
        border-radius: 14px !important;
        line-height: 40px !important;
      }
      .search-sort-compact-bar .tool-btn-compact {
        grid-column: 2 !important;
        height: 42px !important;
        min-height: 42px !important;
        min-width: 44px !important;
        flex-shrink: 0 !important;
        padding: 0 14px !important;
        border-radius: 14px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        font-size: 12.5px !important;
      }
      .btn-clear-search {
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        min-width: 36px !important;
        left: 4px !important;
      }

      /* Upgraded Single Column Feed on Mobile (Balanced Preview, High Contrast Tags, AI Rationale & Quick Actions) */
      #cardsContainer.is-hidden-by-map,
      #cardsContainer[style*="display: none"] {
        display: none !important;
      }
      #cardsContainer {
        display: flex !important;
        flex-direction: column !important;
        gap: 16px !important;
        margin-bottom: 28px !important;
      }
      #cardsContainer .job-card {
        min-height: auto !important;
        height: auto !important;
        width: 100% !important;
        box-sizing: border-box !important;
        padding: 18px 16px !important;
        border-radius: 22px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        gap: 13px !important;
        background: rgba(18, 24, 38, 0.90) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35) !important;
        cursor: default !important;
        position: relative !important;
        overflow: hidden !important;
        transition: transform 0.15s ease, border-color 0.15s ease !important;
      }
      #cardsContainer .job-card:nth-child(n+5) {
        content-visibility: auto;
        contain-intrinsic-size: auto 280px;
      }
      #cardsContainer .job-card:active {
        transform: scale(0.99) !important;
        border-color: var(--dashboard-cyan) !important;
      }
      #cardsContainer .job-card-topbar-meta {
        display: none !important;
      }
      #cardsContainer .job-card-topbar {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 0 0 11px 0 !important;
        margin: 0 0 10px 0 !important;
        width: 100% !important;
        display: flex !important;
      }
      #cardsContainer .job-card-topbar-primary {
        width: 100% !important;
        display: flex !important;
        flex-direction: row-reverse !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 10px !important;
      }
      #cardsContainer .badge-score {
        font-size: 0 !important;
        padding: 0 11px !important;
        height: 28px !important;
        box-sizing: border-box !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
        box-shadow: none !important;
      }
      #cardsContainer .badge-score span {
        font-size: 12px !important;
        font-weight: 700 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        letter-spacing: -0.2px !important;
      }
      #cardsContainer .btn-star {
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        font-size: 16px !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        color: var(--dashboard-muted) !important;
        transition: all 0.15s ease !important;
        position: relative !important;
      }
      #cardsContainer .btn-star.is-starred {
        background: rgba(255, 211, 104, 0.2) !important;
        border-color: rgba(255, 211, 104, 0.5) !important;
        color: var(--dashboard-gold) !important;
      }
      #cardsContainer .btn-copy-link {
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        font-size: 15px !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: var(--dashboard-muted) !important;
      }
      #cardsContainer .job-card-main-header {
        display: flex !important;
        flex-direction: row !important;
        align-items: flex-start !important;
        text-align: start !important;
        gap: 14px !important;
        width: 100% !important;
        margin: 0 0 10px 0 !important;
      }
      #cardsContainer .job-company-logo {
        width: 48px !important;
        height: 48px !important;
        border-radius: 13px !important;
        margin: 0 !important;
        flex-shrink: 0 !important;
        background: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3) !important;
      }
      #cardsContainer .job-company-avatar {
        font-size: 16px !important;
        font-weight: 700 !important;
      }
      #cardsContainer .job-header-text {
        flex: 1 !important;
        min-width: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        text-align: start !important;
        gap: 4px !important;
      }
      #cardsContainer .job-company-name {
        font-size: 12.5px !important;
        color: var(--dashboard-cyan) !important;
        font-weight: 600 !important;
        max-width: 100% !important;
        display: block !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        text-align: start !important;
        margin: 0 !important;
        line-height: 1.35 !important;
      }
      #cardsContainer .job-title-text {
        font-size: 15.5px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        line-height: 1.38 !important;
        height: auto !important;
        min-height: auto !important;
        display: -webkit-box !important;
        -webkit-line-clamp: 2 !important;
        -webkit-box-orient: vertical !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        text-align: start !important;
        margin: 0 0 5px 0 !important;
        letter-spacing: -0.1px !important;
        overflow-wrap: break-word !important;
      }
      #cardsContainer .job-bubbles-wrapper {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        margin: 8px 0 10px 0 !important;
        width: 100% !important;
      }
      #cardsContainer .job-bubble {
        border-radius: 14px !important;
        padding: 10px 14px !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
      }
      #cardsContainer .job-actions-bar {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 100% !important;
        margin-top: auto !important;
        padding-top: 12px !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
      }
      #cardsContainer .action-btn-group {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 8px !important;
        width: 100% !important;
      }
      #cardsContainer .action-btn-main-group {
        display: flex !important;
        width: 100% !important;
      }
      #cardsContainer .btn-triage {
        min-height: 44px !important;
        height: 44px !important;
        font-size: 13px !important;
      }
      #cardsContainer .btn-card-details {
        min-height: 44px !important;
        height: 44px !important;
        font-size: 13px !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 999px !important;
        color: var(--dashboard-text) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        white-space: nowrap !important;
        box-sizing: border-box !important;
      }
      #cardsContainer .btn-card-details:active {
        background: rgba(255, 255, 255, 0.12) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
      }
      #cardsContainer .btn-apply {
        display: inline-flex !important;
        min-height: 44px !important;
        height: 44px !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        background: linear-gradient(135deg, rgba(220, 255, 114, 0.22), rgba(137, 244, 231, 0.25)) !important;
        border: 1px solid rgba(220, 255, 114, 0.45) !important;
        border-radius: 999px !important;
        color: #ffffff !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        text-decoration: none !important;
        cursor: pointer !important;
        box-shadow: 0 2px 10px rgba(220, 255, 114, 0.15) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        white-space: nowrap !important;
        box-sizing: border-box !important;
      }
      #cardsContainer .btn-apply:active {
        transform: scale(0.98) !important;
        box-shadow: 0 0 14px rgba(220, 255, 114, 0.3) !important;
      }

      /* Force hidden state over all grid rules on iPhone */
      #cardsContainer .job-card.is-hidden,
      #cardsContainer .job-card[style*="display: none"],
      .job-card.is-hidden {
        display: none !important;
      }

      /* Modal Sheet Styling on iPhone */
      #jobDetailsModal {
        padding: 0 !important;
        align-items: flex-end !important;
      }
      .job-details-modal-box {
        max-width: 100% !important;
        width: 100% !important;
        max-height: 94vh !important;
        height: 94vh !important;
        border-radius: 24px 24px 0 0 !important;
        border-bottom: none !important;
      }
      .job-modal-body {
        padding: 14px 16px 20px !important;
      }
      .job-modal-bottom-bar {
        padding-bottom: calc(16px + env(safe-area-inset-bottom, 0px)) !important;
      }
      .dashboard-toast {
        bottom: calc(24px + env(safe-area-inset-bottom, 0px)) !important;
        right: 16px !important;
        left: 16px !important;
        max-width: calc(100% - 32px) !important;
      }

      /* Duplicates Modal Sheet on iPhone */
      #duplicatesModal {
        padding: 0 !important;
        align-items: flex-end !important;
      }
      #duplicatesModal .dashboard-modal-box {
        max-width: 100% !important;
        width: 100% !important;
        max-height: 88vh !important;
        border-radius: 24px 24px 0 0 !important;
        border-bottom: none !important;
        margin: 0 !important;
        padding: 18px 16px calc(18px + env(safe-area-inset-bottom, 0px)) !important;
        animation: slideUpModal 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }

      /* Compact Modal Score Badge on Mobile */
      #jobModalTopActions .badge-score {
        padding: 4px 10px !important;
        font-size: 0 !important;
        white-space: nowrap !important;
      }
      #jobModalTopActions .badge-score span {
        font-size: 12px !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
      }

      /* Mobile Empty State */
      #emptyState {
        padding: 32px 16px !important;
        border-radius: 20px !important;
        margin: 12px 0 24px !important;
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

    /* Mobile Landscape Adaptation (iPhone 14 / SE / Pro Max in Landscape) */
    @media (max-height: 500px) and (orientation: landscape) {
      .dashboard-sidebar {
        padding: 8px 14px !important;
        border-radius: 18px !important;
        margin-bottom: 12px !important;
      }
      .header-stat-cubes {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 8px !important;
        margin: 8px 0 !important;
      }
      .stat-cube-btn {
        height: 64px !important;
        padding: 4px 6px !important;
        border-radius: 14px !important;
      }
      .stat-cube-btn .stat-icon {
        width: 16px !important;
        height: 16px !important;
        margin-bottom: 2px !important;
      }
      .stat-cube-btn .stat-number {
        font-size: 15px !important;
        margin-bottom: 1px !important;
      }
      .stat-cube-btn .stat-label {
        font-size: 9px !important;
        line-height: 1.1 !important;
      }
      #cardsContainer {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 12px !important;
      }
      .job-details-modal-box {
        max-height: 96vh !important;
        height: 96vh !important;
      }
      .job-modal-body {
        max-height: calc(96vh - 120px) !important;
      }
      #duplicatesModal .dashboard-modal-box {
        max-height: 92vh !important;
      }
    }

    /* Star & Copy Link Buttons */
    .btn-star,
    .btn-copy-link {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: var(--dashboard-muted);
      width: 32px;
      height: 32px;
      border-radius: 10px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 16px;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      flex-shrink: 0;
      position: relative;
    }
    .btn-star::after,
    .btn-copy-link::after {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 44px;
      height: 44px;
      min-width: 44px;
      min-height: 44px;
      pointer-events: auto;
    }
    .btn-star:hover {
      background: rgba(251, 191, 36, 0.15);
      border-color: rgba(251, 191, 36, 0.5);
      color: var(--dashboard-gold);
      transform: scale(1.08);
    }
    .btn-copy-link:hover {
      background: rgba(137, 244, 231, 0.15);
      border-color: rgba(137, 244, 231, 0.5);
      color: var(--dashboard-cyan);
      transform: scale(1.08);
    }
    .btn-star.is-starred {
      background: rgba(251, 191, 36, 0.22);
      border-color: rgba(251, 191, 36, 0.7);
      color: var(--dashboard-gold);
      box-shadow: 0 0 14px rgba(251, 191, 36, 0.35);
    }
    .btn-star.is-starred i {
      color: var(--dashboard-gold) !important;
    }
    .job-card.is-starred-card {
      border-color: rgba(251, 191, 36, 0.45);
      box-shadow: 0 6px 24px rgba(251, 191, 36, 0.12);
    }

    /* Cards View Toolbar Header */
    .cards-view-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .cards-count-summary {
      font-size: 14px;
      font-weight: 600;
      color: var(--dashboard-muted);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .view-mode-toggle {
      display: inline-flex;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--dashboard-edge);
      border-radius: 999px;
      padding: 3px;
      gap: 3px;
    }
    .view-toggle-btn {
      background: transparent;
      border: none;
      color: var(--dashboard-muted);
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }
    .view-toggle-btn:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.08);
    }
    .view-toggle-btn.active {
      background: linear-gradient(135deg, rgba(137, 244, 231, 0.2), rgba(45, 212, 191, 0.25));
      color: var(--dashboard-cyan);
      border: 1px solid rgba(137, 244, 231, 0.45);
      box-shadow: 0 2px 10px rgba(137, 244, 231, 0.2);
    }
    .view-toggle-btn.active i {
      color: var(--dashboard-cyan) !important;
    }

    /* Live Jobs Map Mode */
    #mapViewContainer {
      border: 1px solid var(--dashboard-edge);
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(14px);
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 14px 40px rgba(0, 0, 0, 0.45);
      margin-bottom: 30px;
    }
    #liveJobsMap {
      width: 100%;
      height: 640px;
      z-index: 1;
    }
    @media (max-width: 768px) {
      #liveJobsMap {
        height: 500px;
      }
    }
    .leaflet-popup-content-wrapper {
      background: rgba(15, 23, 42, 0.96) !important;
      color: var(--dashboard-text) !important;
      border: 1px solid var(--dashboard-edge) !important;
      border-radius: 16px !important;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65) !important;
      backdrop-filter: blur(14px) !important;
      padding: 0 !important;
    }
    .leaflet-popup-tip {
      background: rgba(15, 23, 42, 0.96) !important;
    }
    .leaflet-popup-content {
      margin: 12px 14px !important;
      line-height: 1.4 !important;
      font-family: 'Assistant', sans-serif !important;
      direction: rtl !important;
      text-align: right !important;
    }
    .glass-leaflet-popup .leaflet-popup-content .btn-apply,
    .glass-leaflet-popup .leaflet-popup-content .btn-triage {
      flex: 1 1 0% !important;
      width: auto !important;
      min-height: 34px !important;
      height: 34px !important;
      padding: 6px 10px !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      border-radius: 999px !important;
      box-sizing: border-box !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      gap: 5px !important;
      white-space: nowrap !important;
    }
    .leaflet-container {
      font-family: 'Assistant', sans-serif !important;
      background: #0f172a !important;
    }
    .leaflet-control-zoom a {
      background: rgba(15, 23, 42, 0.9) !important;
      color: #fff !important;
      border-color: var(--dashboard-edge) !important;
    }
    .leaflet-control-zoom a:hover {
      background: rgba(30, 41, 59, 1) !important;
      color: var(--dashboard-cyan) !important;
    }
    .leaflet-control-attribution {
      background: rgba(15, 23, 42, 0.75) !important;
      color: var(--dashboard-muted) !important;
      font-size: 11px !important;
    }
    .leaflet-control-attribution a {
      color: var(--dashboard-cyan) !important;
    }
    .custom-map-marker {
      background: transparent !important;
      border: none !important;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 96px !important;
      height: 70px !important;
      pointer-events: auto;
    }
    .custom-map-marker:hover {
      z-index: 10000 !important;
    }
    .custom-map-marker-inner {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.6));
      transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), filter 0.22s ease;
      will-change: transform;
      transform-origin: center bottom;
      pointer-events: auto;
    }
    .custom-map-marker:hover .custom-map-marker-inner {
      transform: scale(1.12) translateY(-4px);
      filter: drop-shadow(0 12px 24px rgba(0, 0, 0, 0.85));
    }
    .map-pin-logo-bubble {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #0f172a;
      border: 2.5px solid var(--dashboard-cyan);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: visible;
      box-sizing: border-box;
      flex-shrink: 0;
    }
    .map-pin-logo-img {
      width: 24px;
      height: 24px;
      object-fit: contain;
      border-radius: 6px;
      display: block;
    }
    .map-pin-avatar-fallback {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 800;
      color: #fff;
      background: linear-gradient(135deg, rgba(220, 255, 114, 0.3), rgba(137, 244, 231, 0.25));
    }
    .map-pin-score-badge {
      position: absolute;
      top: -5px;
      right: -7px;
      font-size: 9.5px;
      font-weight: 800;
      border-radius: 999px;
      padding: 1px 4.5px;
      line-height: 1.1;
      border: 1.5px solid #0f172a;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.7);
      white-space: nowrap;
    }
    .map-pin-pointer {
      width: 0;
      height: 0;
      border-left: 5px solid transparent;
      border-right: 5px solid transparent;
      border-top: 5px solid var(--dashboard-cyan);
      margin-top: -1px;
      margin-bottom: 2px;
    }
    .map-pin-company-name {
      background: rgba(15, 23, 42, 0.92);
      border: 1px solid rgba(255, 255, 255, 0.16);
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.6);
      border-radius: 8px;
      padding: 1.5px 7px;
      font-size: 11px;
      font-weight: 700;
      color: #f1f5f9;
      max-width: 96px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      text-align: center;
      line-height: 1.35;
      backdrop-filter: blur(6px);
      letter-spacing: 0.2px;
    }

    /* Silky-Smooth Leaflet Zoom Animations */
    .leaflet-zoom-animated {
      transition: transform 0.28s cubic-bezier(0.25, 0.1, 0.25, 1) !important;
      will-change: transform;
    }
    .leaflet-tile-container {
      will-change: transform, opacity;
    }

  </style>
</head>
<body dir="rtl">
<div class="dashboard-app" dir="rtl">

  <!-- Top Navigation Pill (So-Me Pill Header) -->
  <header class="dashboard-sidebar">
    <div class="dashboard-sidebar-brand">
      <div class="brand-icon-pill">
        <i class="ph-duotone ph-rocket-launch" style="font-size: 22px; color: #000;"></i>
      </div>
      <div class="brand-titles">
        <div class="brand-title-row">
          <span class="brand-title">עידו גל | בקרת משרות</span>
          <button type="button" id="headerSyncBtn" class="header-sync-btn" onclick="triggerSyncModal()" title="סנכרון נתונים עם הענן" aria-label="סנכרון נתונים עם הענן">
            <i class="ph-duotone ph-cloud-arrow-up" id="headerSyncIcon"></i>
            <span class="sync-status-dot" id="headerSyncDot" role="status" aria-live="polite"></span>
          </button>
          <button type="button" class="header-about-btn" onclick="openAboutModal()" title="אודות המערכת" aria-label="אודות המערכת">
            <i class="ph-duotone ph-info"></i>
          </button>
        </div>
        <div class="brand-subtitle-row">
          <span class="brand-subtitle">אנרגיה, גז טבעי ורחפנים</span>
          <span class="sync-time-chip" id="lastSyncTimeChip" title="מועד סנכרון אחרון">עודכן: __NOW_STR__</span>
        </div>
      </div>
    </div>

    <!-- Progress & Category Navigation Hub (Compact single-row summary, expandable on mobile) -->
    <div class="header-progress-hub">

      <!-- Mobile Collapsible Summary Toggle Button -->
      <button type="button" class="metrics-summary-toggle" id="metricsToggleBtn" onclick="toggleMetricsExpand()" aria-expanded="false" aria-controls="collapsibleMetricsContent" aria-label="הרחב או צמצם פירוט מטריקות">
        <div class="metrics-summary-inline">
          <span class="metric-summary-pill lime"><span id="summaryNewCount">__TOTAL_NEW_JOBS__</span> חדשות</span>
          <span class="metric-summary-pill gold"><span id="summaryStarredCount">__TOTAL_STARRED_JOBS__</span> בכוכב</span>
          <span class="metric-summary-pill cyan"><span id="summarySavedCount">__TOTAL_SAVED_JOBS__</span> שמורות</span>
          <span class="metric-summary-pill rose"><span id="summaryRejectedCount">__TOTAL_REJECTED_JOBS__</span> הוסרו</span>
        </div>
        <div class="metrics-toggle-label">
          <span id="metricsToggleText">פירוט</span>
          <i class="ph-bold ph-caret-down" id="metricsToggleIcon"></i>
        </div>
      </button>

      <div id="collapsibleMetricsContent" class="metrics-collapsible-content">
        <!-- Progress Summary Info -->
        <div class="header-progress-info">
          <div class="header-progress-title-row">
            <div style="display: flex; align-items: center; gap: 7px;">
              <span class="header-progress-title">
                <i class="ph-duotone ph-chart-pie-slice" style="color: var(--dashboard-cyan); font-size: 16px;"></i>
                התקדמות סקירה
              </span>
              <span class="dashboard-chip" id="progressSummaryChip" style="font-size: 11px; padding: 2px 8px;">0% נסקרו</span>
            </div>
            <div style="font-size: 12px; color: var(--dashboard-muted);">
              <strong id="progressPctText" style="color: #fff; font-size: 14px;">0%</strong> מוינו
            </div>
          </div>

          <!-- Segmented Progress Bar -->
          <div class="segmented-progress">
            <div id="progressSegNew" class="segmented-progress-bar" style="background: var(--dashboard-lime); width: 100%;"></div>
            <div id="progressSegStarred" class="segmented-progress-bar" style="background: var(--dashboard-gold); width: 0%;"></div>
            <div id="progressSegSaved" class="segmented-progress-bar" style="background: var(--dashboard-cyan); width: 0%;"></div>
            <div id="progressSegRejected" class="segmented-progress-bar" style="background: #fca5a5; width: 0%;"></div>
          </div>

          <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--dashboard-muted);">
            <span id="pctLabelNew">100% חדשות</span>
            <span id="pctLabelStarred">0% כוכב</span>
            <span id="pctLabelSaved">0% שמורות</span>
            <span id="pctLabelRejected">0% הוסרו</span>
          </div>
        </div>

        <!-- 4 Interactive Category Cubes -->
        <div class="header-stat-cubes">
          <button type="button" id="cube_all" class="stat-cube-btn active" onclick="setFilter('all', this)" title="משרות חדשות שטרם נסקרו">
            <div class="stat-cube-icon lime">
              <i class="ph-duotone ph-sparkle"></i>
            </div>
            <div class="stat-cube-count" id="statNewCount">__TOTAL_NEW_JOBS__</div>
            <div class="stat-cube-label">משרות חדשות</div>
          </button>

          <button type="button" id="cube_starred" class="stat-cube-btn cube-starred" onclick="setFilter('starred', this)" title="משרות שסומנו בכוכב">
            <div class="stat-cube-icon gold">
              <i class="ph-fill ph-star"></i>
            </div>
            <div class="stat-cube-count" id="statStarredCount">__TOTAL_STARRED_JOBS__</div>
            <div class="stat-cube-label">מסומנות בכוכב</div>
          </button>

          <button type="button" id="cube_saved" class="stat-cube-btn cube-saved" onclick="setFilter('saved', this)" title="משרות שנשמרו להגשה">
            <div class="stat-cube-icon cyan">
              <i class="ph-duotone ph-bookmark-simple"></i>
            </div>
            <div class="stat-cube-count" id="statSavedCount">__TOTAL_SAVED_JOBS__</div>
            <div class="stat-cube-label">שמורות להגשה</div>
          </button>

          <button type="button" id="cube_rejected" class="stat-cube-btn cube-rejected" onclick="setFilter('rejected', this)" title="משרות שהוסרו מהסבב">
            <div class="stat-cube-icon rose">
              <i class="ph-duotone ph-trash"></i>
            </div>
            <div class="stat-cube-count" id="statRejectedCount">__TOTAL_REJECTED_JOBS__</div>
            <div class="stat-cube-label">הוסרו מהסבב</div>
          </button>
        </div>
      </div>
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

    <!-- 2 Overview Cards (Search/Filters, Sector Distribution) -->
    <div class="dashboard-stats-grid">
      
      <!-- Card 1: סינון ואיתור משרות -->
      <div class="dashboard-card" style="margin-bottom: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div style="display: flex; gap: 8px;">
            <span class="dashboard-chip" style="font-size: 11.5px; padding: 3px 9px;">סינון חכם</span>
            <span class="dashboard-chip" style="font-size: 11.5px; padding: 3px 9px; color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.35); background: rgba(220, 255, 114, 0.1);">סריקה עדכנית</span>
          </div>
          <small style="color: var(--dashboard-muted); font-size: 12px;">מיון ואיסוף</small>
        </div>
        <h3 style="margin: 0 0 5px; font-size: 17px; font-weight: 700;">סינון ואיתור משרות</h3>
        <p style="color: var(--dashboard-muted); font-size: 13px; line-height: 1.45; margin-bottom: 12px;">
          סינון לפי מגזרי אנרגיה ורחפנים, איתור כפילויות ומיון לפי התאמה, שכר או תאריך.
        </p>

        <div class="controls-inputs-stack">
          <!-- Row 1: Two Column Layout for Sectors and Regions -->
          <div class="filters-two-col-row">
            <div class="filter-select-field">
              <label for="sectorFilter" class="sr-only" style="display:none;">תחום משרה</label>
              <select id="sectorFilter" onchange="filterCards()" aria-label="כל התחומים" title="סינון לפי תחום">
                <option value="all">כל התחומים</option>
                <option value="scada">בקרה ו-SCADA</option>
                <option value="solar">מערכות סולאריות</option>
                <option value="natural_gas">גז טבעי</option>
                <option value="drones">רחפנים וכטב"ם</option>
                <option value="energy_tech">אגירה ו-Energy Tech</option>
                <option value="operations">תפעול ואחזקה</option>
                <option value="energy">אנרגיה כללית</option>
              </select>
            </div>
            <div class="filter-select-field">
              <label for="regionFilter" class="sr-only" style="display:none;">אזור בארץ</label>
              <select id="regionFilter" onchange="filterCards()" aria-label="כל האזורים בארץ" title="סינון לפי אזור בארץ">
                <option value="all">כל האזורים בארץ</option>
                <option value="center">מרכז וירושלים</option>
                <option value="sharon">אזור השרון</option>
                <option value="north">חיפה והצפון</option>
                <option value="south">שפלה ודרום</option>
                <option value="nationwide">פריסה ארצית / שטח</option>
              </select>
            </div>
          </div>

          <!-- Row 2: Search field and Sorting control within one compact bar -->
          <div class="search-sort-compact-bar">
            <div class="search-input-wrapper" id="searchInputWrapper">
              <label for="searchInput" class="sr-only" style="display:none;">חיפוש משרה</label>
              <input id="searchInput" type="text" placeholder="חיפוש משרה, חברה או דרישה..." oninput="onSearchInput(this.value)" aria-label="חיפוש משרה, חברה או דרישה טכנית" />
              <button type="button" class="btn-clear-search" onclick="clearSearchInput()" title="נקה חיפוש" aria-label="נקה חיפוש">
                <i class="ph-bold ph-x"></i>
              </button>
            </div>
            
            <div class="sort-select-wrapper">
              <label for="sortSelect" class="sr-only" style="display:none;">אפשרות מיון</label>
              <div class="sort-select-container">
                <i id="sortIcon" class="ph-duotone ph-calendar-blank"></i>
                <select id="sortSelect" onchange="changeSort(this.value)" title="בחר אפשרות מיון משרות" aria-label="בחר אפשרות מיון משרות">
                  <option value="date_desc" style="background: #171c12; color: #fff;">חדש קודם</option>
                  <option value="score_desc" style="background: #171c12; color: #fff;">ציון התאמה</option>
                  <option value="salary_desc" style="background: #171c12; color: #fff;">רמת שכר</option>
                  <option value="company_asc" style="background: #171c12; color: #fff;">שם חברה (א-ת)</option>
                </select>
              </div>
            </div>

            <button type="button" onclick="openDuplicatesModal()" class="tool-btn-compact" title="סרוק כפילויות משרות" aria-label="בדיקת כפילויות משרות">
              <i class="ph-duotone ph-copy"></i>
              <span>כפילויות</span>
            </button>
          </div>

          <!-- Bottom Control Hub: Realtime Result Summary & Quick Reset -->
          <div class="filter-card-footer" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 12px; color: var(--dashboard-muted); min-height: 31px;">
            <div id="filterResultSummary" style="display: flex; align-items: center; gap: 6px; font-weight: 500;">
              <span class="dashboard-dot" style="background: var(--dashboard-cyan); width: 6px; height: 6px; border-radius: 50%; display: inline-block;"></span>
              <span id="filterStatusText">מוצגות כל המשרות הפעילות</span>
            </div>
            <button type="button" id="btnResetFilters" onclick="resetAllFilters()" class="dashboard-chip" style="cursor: pointer; font-size: 11px; padding: 3px 10px; border-color: rgba(255, 255, 255, 0.2); background: rgba(255, 255, 255, 0.04); color: var(--dashboard-muted); display: inline-flex; align-items: center; gap: 4px;" title="איפוס כל המסננים והחיפוש">
              <i class="ph-duotone ph-arrow-counter-clockwise"></i>
              <span>איפוס מסננים</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Card 3: התפלגות לפי תחומים -->
      <div class="dashboard-card" style="margin-bottom: 0; display: flex; flex-direction: column;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h3 id="chartTitle" style="margin: 0; font-size: 18px; font-weight: 600;">התפלגות תחומים</h3>
          <span id="chartChip" class="dashboard-chip" style="color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.35);">פעיל השבוע</span>
        </div>
        <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; min-height: 160px;">
          <canvas id="sectorChart" style="max-height: 160px; width: 100%;"></canvas>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 12px; color: var(--dashboard-muted);">
          <span>מקורות: LinkedIn, Drushim & Comeet</span>
          <button onclick="shareSyncLink()" class="dashboard-chip" style="cursor: pointer; font-size: 11px; padding: 3px 10px;">
            <i class="ph-duotone ph-share-network"></i> שיתוף קישור
          </button>
        </div>
      </div>

    </div>

    <!-- Contextual Action Bar for Saved Jobs (Export to Excel) -->
    <div id="savedActionBar" class="context-action-bar saved" style="display: none;">
      <div style="display: flex; align-items: center; gap: 14px;">
        <div class="stat-icon-squircle cyan" style="width: 44px; height: 44px; font-size: 24px;">
          <i class="ph-duotone ph-bookmark-simple"></i>
        </div>
        <div>
          <div style="font-size: 16px; font-weight: 600; color: var(--dashboard-cyan);">משרות ששמרת להגשה</div>
          <div style="font-size: 13px; color: var(--dashboard-muted);">ייצוא מהיר של כל המשרות השמורות לקובץ Excel מסודר עם קישורים ישירים ונתוני שכר.</div>
        </div>
      </div>
      <button onclick="exportSavedToExcel()" class="btn-excel" style="white-space: nowrap;" title="הורד קובץ Excel מסודר עם כל המשרות השמורות">
        <i class="ph-duotone ph-file-xls"></i> <span>ייצוא לאקסל (Excel)</span>
      </button>
    </div>

    <!-- Contextual Action Bar for Rejected Jobs (Permanent Delete & Reset) -->
    <div id="rejectedActionBar" class="context-action-bar rejected" style="display: none;">
      <div style="display: flex; align-items: center; gap: 14px;">
        <div class="stat-icon-squircle gold" style="width: 44px; height: 44px; font-size: 24px; color: #fca5a5;">
          <i class="ph-duotone ph-trash"></i>
        </div>
        <div>
          <div style="font-size: 16px; font-weight: 600; color: #fca5a5;">משרות שסומנו להסרה</div>
          <div style="font-size: 13px; color: var(--dashboard-muted);">לחיצה על מחיקה תנקה את כל הרשימה לצמיתות מכל המכשירים ותאפס את המספר ל-0.</div>
        </div>
      </div>
      <button onclick="clearAllRejected()" class="btn-triage" style="background: rgba(239, 68, 68, 0.25); color: #fca5a5; border-color: rgba(239, 68, 68, 0.5); white-space: nowrap;">
        <i class="ph-duotone ph-trash-simple"></i> <span>מחיקה לצמיתות ואיפוס</span>
      </button>
    </div>

    <!-- Cards View Header (Count & Grid/Map Toggle) -->
    <div class="cards-view-header">
      <div class="cards-count-summary">
        <i class="ph-duotone ph-briefcase" style="font-size: 18px; color: var(--dashboard-cyan);"></i>
        <span id="visibleJobsCountText">סה״כ משרות חדשות: __TOTAL_JOBS__</span>
      </div>
      <div class="view-mode-toggle" role="group" aria-label="מצב תצוגה">
        <button type="button" id="viewGridBtn" class="view-toggle-btn active" onclick="setViewMode('grid')" title="תצוגת קוביות (Grid)">
          <i class="ph-bold ph-squares-four"></i> <span>קוביות</span>
        </button>
        <button type="button" id="viewMapBtn" class="view-toggle-btn" onclick="setViewMode('map')" title="תצוגת מפה חיה (Map)">
          <i class="ph-bold ph-map-trifold"></i> <span>מפה</span>
        </button>
      </div>
    </div>

    <!-- Job Cards List -->
    <main id="cardsContainer"></main>

    <!-- Map View Container -->
    <div id="mapViewContainer" style="display: none;">
      <div id="mapHeaderBar" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; background: rgba(15, 23, 42, 0.75); border-bottom: 1px solid var(--dashboard-edge); font-size: 13px; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px; color: var(--dashboard-cyan); font-weight: 700;">
          <i class="ph-duotone ph-map-pin" style="font-size: 18px;"></i>
          <span id="mapMarkersCountText">מציג משרות על המפה</span>
        </div>
        <div style="font-size: 12px; color: var(--dashboard-muted); display: flex; align-items: center; gap: 6px;">
          <i class="ph-duotone ph-hand-pointing"></i>
          <span>בחרו סמן לצפייה בפרטי המשרה</span>
        </div>
      </div>
      <div id="liveJobsMap"></div>
    </div>

    <!-- Empty State -->
    <div id="emptyState" class="dashboard-card empty-state" style="display: none; text-align: center; padding: 48px 24px;">
      <div id="emptyStateIcon" style="font-size: 44px; margin-bottom: 12px; color: var(--dashboard-cyan);">
        <i class="ph-duotone ph-magnifying-glass"></i>
      </div>
      <h3 id="emptyStateTitle" style="font-size: 20px; margin-bottom: 8px;">לא נמצאו משרות בהתאם לסינון</h3>
      <p id="emptyStateDesc" style="color: var(--dashboard-muted); font-size: 15px; margin: 0;">נסה לבחור לשונית או תחום אחר.</p>
    </div>

  </div>

  <!-- About System Modal -->
  <div id="aboutModal" class="dashboard-modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="aboutModalTitle" onclick="if(event.target===this)closeAboutModal()">
    <div class="dashboard-card dashboard-modal-box">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
        <h3 id="aboutModalTitle" style="margin: 0; font-size: 18px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <i class="ph-duotone ph-info" style="color: var(--dashboard-cyan); font-size: 22px;"></i>
          <span>אודות מערכת בקרת המשרות</span>
        </h3>
        <button type="button" onclick="closeAboutModal()" class="modal-close-btn" aria-label="סגור חלון אודות">
          <i class="ph-bold ph-x"></i>
        </button>
      </div>
      <div style="font-size: 14px; line-height: 1.6; color: var(--dashboard-text);">
        <p style="margin-bottom: 12px;">דשבורד משרות אינטראקטיבי אוטומטי מותאם אישית עבור <strong>עידו גל</strong>, במיקוד על הנדסת מכונות, אנרגיה, גז טבעי ומערכות רחפנים וכטב"ם.</p>
        <p style="margin-bottom: 12px; color: var(--dashboard-muted);">שפת עיצוב ורכיבים: בהשראת <strong>So-Me Design System</strong>, חומרים שקופים (Glassmorphism) וטיפוגרפיית Google Sans.</p>
        <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px 14px; margin-bottom: 16px; font-size: 12.5px;">
          <div style="margin-bottom: 6px;"><strong>מקורות מידע:</strong> LinkedIn Jobs, דרושים (Drushim), ומערכות Comeet</div>
          <div style="margin-bottom: 6px;"><strong>מנוע הערכה:</strong> מודלי Google Gemini עם ניתוח התאמה מדויק</div>
          <div><strong>סנכרון ענן:</strong> Firebase Realtime Database לשימור משרות שמורות והסרת מנוטרלות</div>
        </div>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button type="button" onclick="closeAboutModal()" class="tool-btn" style="padding: 9px 22px; border-radius: 999px; min-height: 44px; min-width: 80px;">סגור</button>
      </div>
    </div>
  </div>

  <!-- Sync Modal -->
  <div id="syncModal" class="dashboard-modal-backdrop hidden" onclick="if(event.target===this)closeSyncModal()">
    <div class="dashboard-card dashboard-modal-box">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="stat-icon-squircle cyan">
            <i class="ph-duotone ph-cloud-arrow-up"></i>
          </div>
          <div>
            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">סנכרון משרות למערכת</h3>
            <small style="color: var(--dashboard-muted);">שמירת משרות שמורות והסרת משרות שנדחו</small>
          </div>
        </div>
        <button onclick="closeSyncModal()" class="tool-btn" style="min-height: 36px; padding: 6px 12px; font-size: 16px; cursor: pointer; border-radius: 999px;" aria-label="סגור"><i class="ph-bold ph-x"></i></button>
      </div>

      <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid var(--dashboard-edge); border-radius: 18px; padding: 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <span style="display: flex; align-items: center; gap: 8px;">
            <i class="ph-duotone ph-bookmark-simple" style="color: var(--dashboard-lime);"></i> משרות שמורות להגשה:
          </span>
          <span id="syncSavedCount" style="font-size: 18px; font-weight: 700; color: var(--dashboard-cyan);">0</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.08);">
          <span style="display: flex; align-items: center; gap: 8px;">
            <i class="ph-duotone ph-trash" style="color: #fca5a5;"></i> משרות שסומנו להסרה:
          </span>
          <span id="syncRejectedCount" style="font-size: 18px; font-weight: 700; color: #fca5a5;">0</span>
        </div>
      </div>

      <p style="font-size: 14px; color: var(--dashboard-muted); line-height: 1.6; margin-bottom: 18px;">
        הדשבורד שומר ומעדכן את כל המשרות שסימנת באופן רציף. סנכרון ישיר מאפשר לפתוח את הסימונים בכל מכשיר.
      </p>

      <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 20px; padding: 12px 16px; background: rgba(137,244,231,0.06); border: 1px solid rgba(137,244,231,0.2); border-radius: 16px;">
        <span style="font-size: 13px; color: var(--dashboard-muted);">סנכרון מיידי בין מכשירים:</span>
        <button onclick="shareSyncLink()" class="dashboard-chip" style="cursor: pointer; padding: 7px 16px; font-size: 13px;">
          <i class="ph-duotone ph-share-network"></i> שיתוף קישור סנכרון
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
          <div class="stat-icon-squircle gold">
            <i class="ph-duotone ph-magnifying-glass"></i>
          </div>
          <div>
            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">בדיקת כפילות משרות</h3>
            <small style="color: var(--dashboard-muted);">זיהוי משרות זהות או דומות לפי כותרת, מזהה וחברה</small>
          </div>
        </div>
        <button onclick="closeDuplicatesModal()" class="tool-btn" style="min-height: 36px; padding: 6px 12px; font-size: 16px; cursor: pointer; border-radius: 999px;" aria-label="סגור"><i class="ph-bold ph-x"></i></button>
      </div>

      <div id="duplicatesContent" style="max-height: 55vh; overflow-y: auto; padding-right: 4px; display: flex; flex-direction: column; gap: 14px;">
        <!-- Filled by JS -->
      </div>

      <div style="display: flex; justify-content: flex-end; margin-top: 18px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
        <button onclick="closeDuplicatesModal()" class="tool-btn">סגור</button>
      </div>
    </div>
  </div>

  <!-- Dedicated Mobile Job Details Modal / Screen -->
  <div id="jobDetailsModal" class="dashboard-modal-backdrop hidden" onclick="if(event.target===this)closeJobModal()">
    <div class="dashboard-card dashboard-modal-box job-details-modal-box" id="jobModalBox">
      <!-- Modal Header Bar -->
      <div class="job-modal-header-bar">
        <button type="button" onclick="closeJobModal()" class="job-modal-close-btn" title="סגור וחזור לרשימת המשרות">
          <i class="ph-bold ph-arrow-right"></i>
          <span>חזור למשרות</span>
        </button>
        <div id="jobModalTopActions" style="display: flex; align-items: center; gap: 8px;">
          <!-- Dynamically populated: Star button and Match score badge -->
        </div>
      </div>

      <!-- Scrollable Modal Body -->
      <div id="jobModalBody" class="job-modal-body">
        <!-- Dynamically populated: Full job info, drivers, analysis boxes, and requirements -->
      </div>

      <!-- Sticky Bottom Action Hub -->
      <div id="jobModalBottomBar" class="job-modal-bottom-bar">
        <!-- Dynamically populated: Apply link and Save/Reject buttons -->
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="dashboard-toast">
    <span id="toastIcon"><i class="ph-duotone ph-bell-simple"></i></span>
    <span id="toastMsg">ההודעה עודכנה</span>
  </div>

  <!-- Back to Top Floating Button -->
  <button id="btnBackToTop" class="btn-back-to-top" onclick="scrollToTop()" title="חזרה לראש העמוד" aria-label="חזרה לראש העמוד">
    <i class="ph-bold ph-arrow-up"></i>
  </button>

</div>

<script>
  const rawJobsData = __JOBS_JSON__;
  const historicalCatalog = __CATALOG_JSON__;
  const initialSavedLinks = __INITIAL_SAVED_JSON__;
  const initialRejectedLinks = __INITIAL_REJECTED_JSON__;
  let currentFilter = 'all';
  let currentSort = 'date_desc';
  const STORAGE_KEY = 'ido_job_triage_store';
  const STARRED_STORAGE_KEY = 'ido_job_starred_store';
  const VIEW_MODE_KEY = 'ido_job_view_mode';
  const SORT_STORAGE_KEY = 'ido_job_sort_mode';
  let currentViewMode = 'grid';
  let allJobsMap = {};
  try {
    const savedView = localStorage.getItem(VIEW_MODE_KEY);
    if (savedView === 'map') {
      currentViewMode = 'map';
    } else {
      currentViewMode = 'grid';
    }
  } catch(e) {
    currentViewMode = 'grid';
  }
  try {
    currentSort = localStorage.getItem(SORT_STORAGE_KEY) || 'date_desc';
  } catch(e) {}
  let starredJobs = loadStarredJobs();

  function loadStarredJobs() {
    let stars = {};
    try {
      stars = JSON.parse(localStorage.getItem(STARRED_STORAGE_KEY) || '{}');
      if (typeof stars !== 'object' || stars === null) stars = {};
    } catch(e) {
      stars = {};
    }

    // Auto-remediation: strip out any saved jobs that were accidentally injected into stars
    if (typeof initialSavedLinks !== 'undefined' && Array.isArray(initialSavedLinks) && initialSavedLinks.length > 0) {
      const savedSet = new Set(initialSavedLinks);
      let matchCount = 0;
      Object.keys(stars).forEach(k => {
        if (savedSet.has(k)) matchCount++;
      });
      if (matchCount >= 20) {
        savedSet.forEach(k => {
          delete stars[k];
        });
        try {
          localStorage.setItem(STARRED_STORAGE_KEY, JSON.stringify(stars));
        } catch(e) {}
      }
    }

    return stars;
  }

  function saveStarredJobs(stars) {
    try {
      localStorage.setItem(STARRED_STORAGE_KEY, JSON.stringify(stars));
    } catch(e) {}
  }

  function toggleStar(id, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    if (starredJobs[id]) {
      delete starredJobs[id];
      showToast('ph-star', 'הוסר מהמשרות המסומנות בכוכב');
    } else {
      starredJobs[id] = true;
      showToast('ph-fill ph-star', 'המשרה סומנה בכוכב בהצלחה');
    }
    saveStarredJobs(starredJobs);
    
    document.querySelectorAll('.job-card').forEach(card => {
      if (card.getAttribute('data-id') === id) {
        const starBtn = card.querySelector('.btn-star');
        const isStarred = Boolean(starredJobs[id]);
        if (starBtn) {
          starBtn.className = isStarred ? 'btn-star is-starred' : 'btn-star';
          starBtn.setAttribute('title', isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
          starBtn.setAttribute('aria-label', isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
          starBtn.innerHTML = isStarred ? '<i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>' : '<i class="ph-bold ph-star"></i>';
        }
        card.classList.toggle('is-starred-card', isStarred);
        card.setAttribute('data-starred', isStarred ? 'true' : 'false');
      }
    });

    const currentCardCount = document.querySelectorAll('.job-card').length;
    const availableCount = getAllAvailableJobs().length;
    if (currentCardCount !== availableCount) {
      renderCards();
      return;
    }

    updateUI();
  }

  function setViewMode(mode) {
    currentViewMode = (mode === 'map') ? 'map' : 'grid';
    try {
      localStorage.setItem(VIEW_MODE_KEY, currentViewMode);
    } catch(e) {}
    const container = document.getElementById('cardsContainer');
    const mapContainer = document.getElementById('mapViewContainer');
    const gridBtn = document.getElementById('viewGridBtn');
    const mapBtn = document.getElementById('viewMapBtn');
    if (!container || !mapContainer) return;

    if (currentViewMode === 'map') {
      container.classList.add('is-hidden-by-map');
      container.style.display = 'none';
      mapContainer.style.display = 'block';
      if (gridBtn) gridBtn.classList.remove('active');
      if (mapBtn) mapBtn.classList.add('active');

      if (!liveJobsMapInstance) {
        initLiveJobsMap();
      }
      setTimeout(() => {
        if (liveJobsMapInstance) {
          liveJobsMapInstance.invalidateSize();
        }
      }, 150);
      updateMapMarkers();
    } else {
      mapContainer.style.display = 'none';
      container.classList.remove('is-hidden-by-map');
      container.style.display = '';
      if (gridBtn) gridBtn.classList.add('active');
      if (mapBtn) mapBtn.classList.remove('active');
    }
  }

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

    // Deduplicate / canonicalize pure numeric IDs to full URLs
    Object.keys(state).forEach(key => {
      if (/^\\d+$/.test(key)) {
        const matchingLink = Object.keys(state).find(k => k !== key && k.includes(key));
        if (matchingLink) {
          if (state[key] === 'saved' && state[matchingLink] !== 'saved') {
            state[matchingLink] = 'saved';
          }
          delete state[key];
        }
      }
    });

    return state;
  }

  const CLOUD_SYNC_URL = 'https://job-finder-auto-default-rtdb.firebaseio.com/triage.json';
  let cloudSyncTimeout = null;
  let cloudLastUpdated = 0;
  let isSyncInProgress = false;

  function formatSyncTime(ts) {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
    } catch(e) {
      return '';
    }
  }

  function setCloudSyncStatus(status, timestamp) {
    const cloudBadge = document.getElementById('cloudSyncStatus');
    const headerDot = document.getElementById('headerSyncDot');
    const headerIcon = document.getElementById('headerSyncIcon');
    const lastSyncEl = document.getElementById('lastSyncTimeChip');

    if (timestamp && lastSyncEl) {
      const timeStr = formatSyncTime(timestamp);
      if (timeStr) lastSyncEl.textContent = `סונכרן: ${timeStr}`;
    }

    if (status === 'synced') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot synced';
        headerDot.title = 'ענן מסונכרן';
      }
      if (headerIcon) headerIcon.classList.remove('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-synced';
        cloudBadge.style.color = 'var(--dashboard-cyan)';
        cloudBadge.style.borderColor = 'rgba(137, 244, 231, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-cyan); box-shadow: 0 0 8px var(--dashboard-cyan);"></span> <i class="ph-duotone ph-cloud-check"></i> <span>ענן מסונכרן</span>';
      }
    } else if (status === 'syncing') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot syncing';
        headerDot.title = 'מעדכן ענן...';
      }
      if (headerIcon) headerIcon.classList.add('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-syncing';
        cloudBadge.style.color = 'var(--dashboard-gold)';
        cloudBadge.style.borderColor = 'rgba(255, 211, 104, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-gold); box-shadow: 0 0 8px var(--dashboard-gold);"></span> <i class="ph-duotone ph-cloud-arrow-up"></i> <span>מעדכן ענן...</span>';
      }
    } else if (status === 'offline' || status === 'error') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot offline';
        headerDot.title = 'לא מקוון / שגיאת סנכרון';
      }
      if (headerIcon) headerIcon.classList.remove('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-offline';
        cloudBadge.style.color = '#f87171';
        cloudBadge.style.borderColor = 'rgba(248, 113, 113, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: #f87171; box-shadow: 0 0 8px rgba(248, 113, 113, 0.6);"></span> <i class="ph-duotone ph-cloud-slash"></i> <span>לא מקוון</span>';
      }
    }
  }

  async function fetchCloudSync() {
    if (isSyncInProgress) return;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
    isSyncInProgress = true;
    try {
      setCloudSyncStatus('syncing');
      const resp = await fetch(CLOUD_SYNC_URL, { cache: 'no-cache' });
      if (!resp.ok) {
        throw new Error('Sync status: ' + resp.status);
      }
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
            if (/^\\d+$/.test(link) && data.saved.some(s => s !== link && s.includes(link))) {
              return;
            }
            if (jobStates[link] !== 'saved') {
              jobStates[link] = 'saved';
              changed = true;
            }
          });
        }
        Object.keys(jobStates).forEach(key => {
          if (/^\\d+$/.test(key)) {
            const matchingLink = Object.keys(jobStates).find(k => k !== key && k.includes(key));
            if (matchingLink) {
              delete jobStates[key];
              changed = true;
            }
          }
        });
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
          renderCards();
          updateUI();
        }
        setCloudSyncStatus('synced', cloudLastUpdated || Date.now());
      } else {
        setCloudSyncStatus('synced', Date.now());
      }
    } catch (e) {
      setCloudSyncStatus('offline');
    } finally {
      isSyncInProgress = false;
    }
  }

  function scheduleCloudPush() {
    if (cloudSyncTimeout) clearTimeout(cloudSyncTimeout);
    cloudSyncTimeout = setTimeout(pushCloudSync, 400);
  }

  async function pushCloudSync() {
    if (isSyncInProgress) return;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
    isSyncInProgress = true;
    setCloudSyncStatus('syncing');

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
      if (resp.ok) {
        cloudLastUpdated = Date.now();
        setCloudSyncStatus('synced', cloudLastUpdated);
      } else {
        setCloudSyncStatus('offline');
      }
    } catch (e) {
      setCloudSyncStatus('offline');
    } finally {
      isSyncInProgress = false;
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => { fetchCloudSync(); });
    window.addEventListener('offline', () => { setCloudSyncStatus('offline'); });
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
            showToast('ph-check-circle', count > 0 ? `סונכרנו בהצלחה ${count} משרות חדשות!` : 'הדשבורד מסונכרן ומעודכן!');
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
        showToast('ph-share-network', 'הקישור שותף בהצלחה!');
        return;
      } catch (err) {}
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrl).then(() => {
        showToast('ph-link', 'קישור סנכרון הועתק! פתח אותו במכשיר השני');
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
    // Energy / Gas / Solar / Infrastructure
    [['iec', 'חברת החשמל', 'חברת חשמל'], 'iec.co.il'],
    [['energean', "אנרג'יאן", "אנרג׳יאן", "אנרג'אן"], 'energean.com'],
    [['alumenergy', "אלומאנרג'י", "אלומנרג'י", "אלומנרג׳י", 'אלומוט'], 'alumenergy.co.il'],
    [['opc', 'או פי סי', 'רותם', 'חדרה'], 'opc-energy.com'],
    [['bazan', 'בזן', 'בז״ן', 'בתי זיקוק'], 'bazan.co.il'],
    [['supergas', 'סופרגז'], 'supergas.co.il'],
    [['paz', 'פז'], 'paz.co.il'],
    [['amisragas', 'אמישראגז', 'אמישרא גז'], 'amisragas.co.il'],
    [['delek', 'דלק'], 'delek.co.il'],
    [['newmed', 'ניומד'], 'newmedenergy.com'],
    [['ratio', 'רציו'], 'ratio-petroleum.com'],
    [['sonol', 'סונול'], 'sonol.co.il'],
    [['dor alon', 'דור אלון'], 'doralon.co.il'],
    [['solaredge', "סולאראדג'", "סולאראדג׳"], 'solaredge.com'],
    [['enlight', 'אנלייט'], 'enlightenergy.co.il'],
    [['energix', "אנרג'יקס", "אנרג׳יקס"], 'energix-group.com'],
    [['doral', 'דוראל'], 'doral-energy.com'],
    [['nofar', 'נופר אנרגיה', 'נופר'], 'nofar-energy.com'],
    [['al-mor', 'אל-מור', 'אל מור', 'אלמור'], 'almor.co.il'],
    [['shikun & binui', 'שיכון ובינוי'], 'shikunbinui.com'],
    [['econergy', 'אקונרגיה', 'אקונרג׳י', "אקונרג'י"], 'econergy-international.com'],
    [['teralight', 'טראלייט'], 'teralight-energy.com'],
    [['meshek energy', 'משק אנרגיה', 'סולגרין'], 'meshek-energy.co.il'],
    [['prime energy', 'פריים אנרגיה', "פריים אנרג'י"], 'prime-energy.co.il'],
    [['nextpower', 'נקסטפאוור'], 'nextpower.com'],
    [['nextcom', 'נקסטקום'], 'nextcomgroup.com'],
    [['h2pro'], 'h2pro.co'],
    [['storedot'], 'store-dot.com'],
    [['electreon', 'אלקטריאון'], 'electreon.com'],
    [['mprest', 'אמפרסט'], 'mprest.com'],
    [['phinergy', 'פינרגיה', "פינרג'י"], 'phinergy.com'],
    [['brenmiller', 'ברנמילר', 'brenx'], 'bren-energy.com'],
    [['augwind', 'אוגווינד', 'airangy'], 'aug-wind.com'],
    [['addionics'], 'addionics.com'],
    [['zooz power', 'zooz', "צ'אקראטק"], 'zoozpower.com'],
    [['isramco', 'ישראמקו'], 'isramco.co.il'],
    [['edeltech', 'אדלטק'], 'edeltech.co.il'],
    [['dalia', 'דליה אנרגיות', 'צפית'], 'dalia-energy.co.il'],
    [['navitas', 'נאוויטס'], 'navitaspet.com'],
    [['tamar petroleum', 'תמר פטרוליום'], 'tamarpetroleum.co.il'],
    [['rimon', 'רימון'], 'rimon.co.il'],
    [['raycatch', "רייקאץ'", 'רייקאץ׳'], 'raycatch.com'],
    [['augury', 'אוגורי'], 'augury.com'],
    [['airtouch', 'איירטאץ', 'איירטאץ׳'], 'airtouchsolar.com'],
    [['ecoppia', 'אקופיה'], 'ecoppia.com'],
    [['gencell', "ג'נסל"], 'gencellenergy.com'],
    [['driivz', 'דרייבז'], 'driivz.com'],
    [['solcold', 'סולקולד'], 'solcold.com'],
    [['nostromo', 'נוסטרומו'], 'nostromo.energy'],
    [['zutacore'], 'zutacore.com'],
    [['eco wave power'], 'ecowavepower.com'],
    [['siemens energy', 'סימנס אנרגיה', 'siemens-energy'], 'siemens-energy.com'],
    [['siemens', 'סימנס'], 'siemens.com'],
    [['ge vernova', 'ge ', "ג'נרל אלקטריק"], 'gevernova.com'],
    [['schneider', 'שניידר'], 'se.com'],
    [['hitachi', "היטאצ'י"], 'hitachienergy.com'],
    [['ormat', 'אורמת'], 'ormat.com'],
    [['edf', 'אי די אף'], 'edf-re.com'],
    [['jinko', "ג'ינקו"], 'jinkosolar.com'],
    [['nt-tao', 'nt tao', 'נו טאו'], 'nt-tao.com'],
    [['concentric power', 'concentric'], 'concentricpower.com'],
    [['plant supervision'], 'plantsupervision.com'],
    [['solar solutions', 'פתרונות סולאריים'], 'solarsolutions.co.il'],
    [['saltworks', 'סולטוורקס'], 'saltworkstech.com'],
    [['x-cooling', 'x cooling', 'אקס קולינג'], 'x-cooling.com'],
    [['allpha innovation', 'allpha'], 'allpha.com'],

    // Defense / Aerospace / UAV / Drones
    [['elbit', 'אלביט'], 'elbitsystems.com'],
    [['rafael', 'רפאל'], 'rafael.co.il'],
    [['iai', 'התעשייה האווירית', 'התעשיה האווירית', 'israel aerospace'], 'iai.co.il'],
    [['tomer', 'תומר', 'תומר חברה ממשלתית'], 'tomer-israel.co.il'],
    [['amarel', 'אמארל', 'אמרל'], 'amarel.net'],
    [['controp', 'קונטרופ'], 'controp.com'],
    [['xtend'], 'xtend.me'],
    [['percepto', 'פרספטו'], 'percepto.com'],
    [['airobotics', 'איירובוטיקס'], 'airoboticsdrones.com'],
    [['bluebird', 'בלובירד'], 'bluebird-uav.com'],
    [['spearuav', 'ספיר'], 'spearuav.com'],
    [['parazero', 'manta air', 'פארזרו'], 'parazero.com'],
    [['flytrex'], 'flytrex.com'],
    [['d-fend', 'די פנד', 'די-פנד'], 'd-fendsolutions.com'],
    [['robotican', 'רובוטיקאן'], 'robotican.co'],
    [['high lander', 'היי לנדר', 'highlander'], 'highlander.io'],
    [['steadicopter', 'סטדיקופטר'], 'steadicopter.com'],
    [['third eye', 'עין שלישית'], 'thirdeye-systems.com'],
    [['smartshooter', 'smart shooter'], 'smart-shooter.com'],
    [['nextvision'], 'nextvision-sys.com'],
    [['birdaero', 'bird aero'], 'birdaero.com'],
    [['aerotor'], 'aerotor.com'],
    [['heven'], 'hevenaerotech.com'],
    [['sentrycs'], 'sentrycs.com'],
    [['roboteam'], 'robo-team.com'],
    [['sightec'], 'sightec.com'],
    [['regulus'], 'regulus.com'],
    [['rada', 'דראס', 'drs rada', 'drs'], 'drs.com'],
    [['bagira', 'בגירה'], 'bagirasys.com'],
    [['aitech'], 'aitechsystems.com'],
    [['airwayz'], 'airwayz.co'],
    [['bet shemesh', 'מנועי בית שמש'], 'bseltd.com'],
    [['uvision', 'יוויז׳ן', "יוויז'ן"], 'uvisionuav.com'],
    [['imco', 'אימקו'], 'imco-ind.com'],

    // Industry / Engineering / Infrastructure
    [['electra', 'אלקטרה'], 'electra.co.il'],
    [['netafim', 'נטפים'], 'netafim.com'],
    [['iscar', 'ישקר'], 'iscar.com'],
    [['tower', 'טאוור'], 'towersemi.com'],
    [['applied materials', 'אפלייד'], 'appliedmaterials.com'],
    [['nova', 'נובה'], 'novami.com'],
    [['kla', 'קיי אל איי'], 'kla.com'],
    [['icl group', 'כימיקלים לישראל', 'כי״ל', 'כיל'], 'icl-group.com'],
    [['adama', 'אדמה'], 'adama.com'],
    [['alumeshet', 'אלומושת'], 'alumeshet.co.il'],
    [['stratasys', 'סטראטסיס'], 'stratasys.com'],
    [['acs motion', 'acs'], 'acsmotioncontrol.com'],
    [['ashtrom', 'אשטרום'], 'ashtrom.co.il'],
    [['shapir', 'שפיר'], 'shapir.co.il'],
    [['shikun', 'שיכון ובינוי'], 'shikunbinui.com'],
    [['danya cebus', 'דניה סיבוס', 'דניה'], 'danya-cebus.co.il'],
    [['baran', 'ברן'], 'baran-group.com'],
    [['alstom', 'אלסטום'], 'alstom.com'],
    [['teva', 'טבע'], 'teva.co.il'],
    [['bruker'], 'bruker.com'],
    [['philips', 'פיליפס'], 'philips.com'],
    [['edwards vacuum', 'edwards'], 'edwardsvacuum.com'],
    [['ultra clean technology', 'uct'], 'uct.com'],
    [['assatec robotics', 'assatec', 'אסאטק'], 'assatec.com'],
    [['e2e solutions', 'e2e'], 'e2e-il.com'],
    [['michlol solutions', 'מיכלול'], 'michlol-sol.co.il'],
    [['advance eng', 'אדוונס הנדסה', 'אדוונס'], 'advance-eng.co.il'],
    [['orion', 'ב.מ. אוריון', 'אוריון ושות', 'אוריון'], 'bmorion.com'],
    [['scheidt & bachmann', 'שיידט את בכמן', 'scheidt'], 'scheidt-bachmann.com'],
    [['snorkel', 'שנייר ליפט', 'שנייר'], 'snorkellifts.com'],
    [['niga', 'ניגא שף', 'ניגא'], 'niga.co.il'],
    [['vpg', 'וי פי ג׳י'], 'vpgsensors.com'],
    [['zoll', 'זול מדיקל'], 'zoll.com'],
    [['robokit', 'רובוקיט'], 'robokit.co.il'],
    [['colmobil', 'כלמוביל'], 'colmobil.co.il'],
    [['pb israel', 'wsp'], 'wsp.com'],
    [['swissport', 'סוויספורט', 'סוויספורט שרותי מטען'], 'swissport.com'],
    [['sheba', 'שיבא', 'מרכז רפואי שיבא', 'תל השומר'], 'sheba.co.il'],
    [['jll', "ג'ונס לאנג"], 'jll.com'],
    [['merck', 'מרק'], 'merckgroup.com'],
    [['flex', 'פלקס'], 'flex.com'],
    [['jacobs', "ג'ייקובס"], 'jacobs.com'],

    // Tech / Software / Staffing
    [['jobsseek', "ג'ובסיק"], 'jobsseek.co.il'],
    [['job space', "ג'וב ספייס"], 'jobspace.co.il'],
    [['shidrug', 'שדרוג מיון והשמה', 'שדרוג'], 'shidrug.co.il'],
    [['dataway', 'דאטה וויי', 'דאטהווי'], 'dataway.co.il'],
    [['entrypoint', 'אנטריפוינט'], 'entrypoint.co.il'],
    [['mertens', 'מרטנס', 'מלם תים', 'malam'], 'malamteam.com'],
    [['zofen', 'צופן'], 'zofen.com'],
    [['cross river', 'קרוס ריבר', 'confidential careers'], 'crossriver.com'],
    [['partner', 'פרטנר'], 'partner.co.il'],
    [['intel', 'realsense', 'אינטל'], 'intel.com'],
    [['apple', 'אפל'], 'apple.com'],
    [['amazon', 'aws', 'אמזון'], 'amazon.com'],
    [['nvidia', 'אנבידיה'], 'nvidia.com'],
    [['tesla', 'טסלה'], 'tesla.com'],
    [['mobileye', 'מובילאיי'], 'mobileye.com'],
    [['cato networks', 'קאטו'], 'catonetworks.com'],
    [['check point', 'checkpoint', "צ'ק פוינט"], 'checkpoint.com'],
    [['palo alto', 'פאלו אלטו'], 'paloaltonetworks.com'],
    [['cyberark', 'סייברארק'], 'cyberark.com'],
    [['biocatch'], 'biocatch.com'],
    [['claroty'], 'claroty.com'],
    [['cheq'], 'cheq.ai'],
    [['wix', 'וויקס'], 'wix.com'],
    [['monday', 'מאנדיי'], 'monday.com'],
    [['fiverr', 'פייבר'], 'fiverr.com'],
    [['gett', 'גט'], 'gett.com'],
    [['lemonade'], 'lemonade.com'],
    [['matrix', 'מטריקס'], 'matrix-globals.com'],
    [['ness', 'נס'], 'ness-tech.co.il'],
    [['manpower', 'מנפאואר'], 'manpower.co.il'],
    [['experis'], 'experis.co.il'],
    [['sqlink'], 'sqlink.com'],
    [['elad software', 'אלעד מערכות', 'אלעד'], 'eladsoft.com'],
    [['michlol', 'מכלול'], 'michlolltd.co.il'],
    [['e2e solutions', 'e2e'], 'e2eil.co.il'],
    [['assatec', 'אסאטק'], 'assatec.co.il'],
    [['nyga', 'ניגא שף', 'ניגא'], 'nyga-chef.co.il'],
    [['mechanical devices', 'm.d. mechanical'], 'mechanical-devices.com'],
    [['microsoft', 'מיקרוסופט'], 'microsoft.com'],
    [['zoll'], 'zoll.com'],
    [['linked magic'], 'linkedmagic.com'],
    [['or holdings', 'אור אחזקות', 'ר.א אור'], 'or-holdings.co.il'],
    [['nestle', 'אסם'], 'nestle.com'],
    [['pepsico', 'קוקה קולה', 'החברה המרכזית'], 'pepsico.com'],
    [['strauss', 'שטראוס'], 'strauss-group.com'],
    [['tnuva', 'תנובה'], 'tnuva.co.il'],
    [["l'oréal", 'loreal', 'לוריאל'], 'loreal.com']
  ];

  function matchCompanyWord(text, keyword) {
    if (!text || !keyword) return false;
    const t = text.toLowerCase().trim();
    const k = keyword.toLowerCase().trim();
    if (t === k) return true;
    const escaped = k.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
    const regex = new RegExp('(?:^|[^a-zA-Z0-9א-ת])' + escaped + '(?:$|[^a-zA-Z0-9א-ת])', 'i');
    return regex.test(t);
  }

  function cleanCompanyName(name) {
    if (!name) return 'חברה';
    let s = name.trim();
    s = s.replace(/^[+\\-~|•\\s]+|[+\\-~|•\\s]+$/g, '');
    return s.trim() || 'חברה';
  }

  function getCompanyBrandColor(str) {
    const palette = [
      ['rgba(0, 229, 255, 0.15)', '#00e5ff'],
      ['rgba(16, 185, 129, 0.15)', '#10b981'],
      ['rgba(99, 102, 241, 0.15)', '#818cf8'],
      ['rgba(245, 158, 11, 0.15)', '#f59e0b'],
      ['rgba(236, 72, 153, 0.15)', '#ec4899'],
      ['rgba(139, 92, 246, 0.15)', '#a78bfa']
    ];
    let hash = 0;
    const s = str || 'חברה';
    for (let i = 0; i < s.length; i++) {
      hash = (hash << 5) - hash + s.charCodeAt(i);
      hash |= 0;
    }
    const idx = Math.abs(hash) % palette.length;
    return palette[idx];
  }

  function getCompanyLogoInfo(companyName, customLogo) {
    const rawName = cleanCompanyName(companyName);
    const norm = rawName.toLowerCase();
    
    let domain = null;
    for (const [keys, dom] of KNOWN_COMPANY_DOMAINS) {
      if (keys.some(k => matchCompanyWord(norm, k))) {
        domain = dom;
        break;
      }
    }

    let cleanWords = rawName
      .replace(/[()[\\]\\-–•,|~+]/g, ' ')
      .split(/\\s+/)
      .filter(w => w && !['בע"מ', 'בע״מ', 'בעמ', 'ltd', 'ltd.', 'inc', 'inc.', 'group', 'corp', 'israel', 'ישראל', 'בעל'].includes(w.toLowerCase()));
    if (cleanWords.length === 0) cleanWords = [rawName];
    
    let initials = '';
    let isIcon = false;
    if (cleanWords.length >= 2) {
      initials = (cleanWords[0][0] || '') + (cleanWords[1][0] || '');
    } else if (cleanWords.length === 1 && cleanWords[0].length >= 2) {
      initials = cleanWords[0].slice(0, 2);
    } else if (cleanWords.length === 1 && cleanWords[0].length === 1) {
      initials = cleanWords[0][0];
    } else {
      initials = '<i class="ph-duotone ph-buildings" style="font-size: 20px;"></i>';
      isIcon = true;
    }
    if (!isIcon) initials = initials.toUpperCase();

    let primaryUrl = customLogo || null;
    let initialStep = 0;
    if (!primaryUrl && domain) {
      primaryUrl = 'https://www.google.com/s2/favicons?domain=' + encodeURIComponent(domain) + '&sz=128';
      initialStep = 1;
    }

    return { rawName, domain, initials, isIcon, primaryUrl, initialStep };
  }

  function handleCompanyLogoError(img, domain) {
    if (!domain) {
      showCompanyLogoAvatar(img);
      return;
    }
    const step = parseInt(img.dataset.step || '0', 10);
    if (step === 0) {
      img.dataset.step = '1';
      img.src = 'https://www.google.com/s2/favicons?domain=' + encodeURIComponent(domain) + '&sz=128';
    } else if (step === 1) {
      img.dataset.step = '2';
      img.src = 'https://unavatar.io/' + encodeURIComponent(domain) + '?fallback=false';
    } else if (step === 2) {
      img.dataset.step = '3';
      img.src = 'https://icons.duckduckgo.com/ip3/' + encodeURIComponent(domain) + '.ico';
    } else {
      showCompanyLogoAvatar(img);
    }
  }

  function handleCompanyLogoLoad(img, domain) {
    const step = parseInt(img.dataset.step || '0', 10);
    if (img.naturalWidth <= 16 && img.naturalHeight <= 16 && step === 1 && domain) {
      handleCompanyLogoError(img, domain);
    }
  }

  function showCompanyLogoAvatar(img) {
    img.style.display = 'none';
    const parent = img.parentElement;
    if (parent) {
      const avatar = parent.querySelector('.job-company-avatar');
      if (avatar) avatar.style.display = 'flex';
    }
  }

  function getCompanyLogoHtml(companyName, customLogo) {
    const info = getCompanyLogoInfo(companyName, customLogo);
    const safeComp = info.rawName.replace(/"/g, '&quot;');
    const safeDom = (info.domain || '').replace(/"/g, '&quot;');
    const brandColor = getCompanyBrandColor(info.rawName);

    if (info.primaryUrl) {
      return `
        <div class="job-company-logo" title="${safeComp}">
          <img src="${info.primaryUrl}" 
               alt="${safeComp}" 
               loading="lazy" 
               decoding="async" 
               data-step="${info.initialStep}"
               onload="handleCompanyLogoLoad(this, '${safeDom}')" 
               onerror="handleCompanyLogoError(this, '${safeDom}')" />
          <div class="job-company-avatar" style="display: none; background: ${brandColor[0]}; color: ${brandColor[1]};">${info.initials}</div>
        </div>
      `;
    } else {
      return `
        <div class="job-company-logo" title="${safeComp}">
          <div class="job-company-avatar" style="background: ${brandColor[0]}; color: ${brandColor[1]};">${info.initials}</div>
        </div>
      `;
    }
  }

  // Israeli Geolocation Coordinate Dictionary (Latitude, Longitude)
  const ISRAEL_LOCATIONS_GEO = {
    // Tel Aviv & Dan
    'תל אביב': [32.0853, 34.7818],
    'tel aviv': [32.0853, 34.7818],
    'גוש דן': [32.0853, 34.7818],
    'רמת גן': [32.0822, 34.8143],
    'ramat gan': [32.0822, 34.8143],
    'שיבא': [32.0460, 34.8430],
    'תל השומר': [32.0460, 34.8430],
    'גבעתיים': [32.0722, 34.8089],
    'בני ברק': [32.0833, 34.8333],
    'פתח תקווה': [32.0840, 34.8878],
    'petah tikva': [32.0840, 34.8878],
    'פתח תקוה': [32.0840, 34.8878],
    'חולון': [32.0158, 34.7874],
    'holon': [32.0158, 34.7874],
    'בת ים': [32.0194, 34.7500],
    'bat yam': [32.0194, 34.7500],
    'ראשון לציון': [31.9730, 34.7925],
    'rishon': [31.9730, 34.7925],
    'אור יהודה': [32.0294, 34.8572],
    'קריית אונו': [32.0536, 34.8586],
    'יהוד': [32.0333, 34.8833],
    
    // Center & Shfela & Airport
    'נתב"ג': [32.0005, 34.8707],
    'נתב״ג': [32.0005, 34.8707],
    'לוד': [31.9519, 34.8967],
    'lod': [31.9519, 34.8967],
    'רמלה': [31.9284, 34.8687],
    'ramla': [31.9284, 34.8687],
    'איירפורט סיטי': [32.0120, 34.9220],
    'airport city': [32.0120, 34.9220],
    'נמל תעופה': [32.0005, 34.8707],
    'מודיעין': [31.8986, 35.0104],
    'modiin': [31.8986, 35.0104],
    'שוהם': [31.9986, 34.9458],
    'נס ציונה': [31.9317, 34.7981],
    'נס-ציונה': [31.9317, 34.7981],
    'רחובות': [31.8928, 34.8113],
    'rehovot': [31.8928, 34.8113],
    'יבנה': [31.8781, 34.7397],
    'yavne': [31.8781, 34.7397],
    'שפלה': [31.8928, 34.8113],
    'מרכז': [32.0853, 34.7818],
    'center': [32.0853, 34.7818],
    'מרכז הארץ': [32.0853, 34.7818],

    // Sharon
    'הרצליה': [32.1624, 34.8447],
    'herzliya': [32.1624, 34.8447],
    'רעננה': [32.1848, 34.8713],
    'raanana': [32.1848, 34.8713],
    'כפר סבא': [32.1750, 34.9069],
    'kfar saba': [32.1750, 34.9069],
    'הוד השרון': [32.1528, 34.8878],
    'hod hasharon': [32.1528, 34.8878],
    'נתניה': [32.3215, 34.8532],
    'netanya': [32.3215, 34.8532],
    'פולג': [32.2783, 34.8572],
    'חדרה': [32.4340, 34.9197],
    'hadera': [32.4340, 34.9197],
    'קיסריה': [32.5020, 34.9350],
    'caesarea': [32.5020, 34.9350],
    'עמק חפר': [32.3850, 34.9000],
    'שרון': [32.1848, 34.8713],
    'sharon': [32.1848, 34.8713],

    // South & Ashdod / Ashkelon / Negev
    'אשדוד': [31.8014, 34.6435],
    'ashdod': [31.8014, 34.6435],
    'נמל אשדוד': [31.8260, 34.6530],
    'נמל הדרום': [31.8260, 34.6530],
    'אשקלון': [31.6688, 34.5743],
    'ashkelon': [31.6688, 34.5743],
    'קריית גת': [31.6100, 34.7642],
    'kiryat gat': [31.6100, 34.7642],
    'באר שבע': [31.2529, 34.7915],
    'beer sheva': [31.2529, 34.7915],
    'beersheba': [31.2529, 34.7915],
    'דימונה': [31.0667, 35.0333],
    'dimona': [31.0667, 35.0333],
    'נאות חובב': [31.1350, 34.7890],
    'רמת חובב': [31.1350, 34.7890],
    'ערד': [31.2589, 35.2128],
    'שדרות': [31.5211, 34.5967],
    'קריית מלאכי': [31.7289, 34.7456],
    'אילת': [29.5577, 34.9519],
    'דרום': [31.2529, 34.7915],
    'south': [31.2529, 34.7915],
    'נגב': [31.2529, 34.7915],

    // North & Haifa & Valleys & Galilee
    'חיפה': [32.7940, 34.9896],
    'haifa': [32.7940, 34.9896],
    'מת״ם': [32.7880, 34.9580],
    'מתם': [32.7880, 34.9580],
    'קריות': [32.8300, 35.0700],
    'קריית אתא': [32.8028, 35.1075],
    'קריית ביאליק': [32.8272, 35.0847],
    'קריית מוצקין': [32.8347, 35.0778],
    'קריית ים': [32.8464, 35.0686],
    'נשר': [32.7667, 35.0333],
    'טירת כרמל': [32.7611, 34.9722],
    'עכו': [32.9278, 35.0817],
    'akko': [32.9278, 35.0817],
    'acre': [32.9278, 35.0817],
    'נהריה': [33.0059, 35.0941],
    'nahariya': [33.0059, 35.0941],
    'כרמיאל': [32.9199, 35.2901],
    'karmiel': [32.9199, 35.2901],
    'תפן': [32.9772, 35.2683],
    'יקנעם': [32.6595, 35.1102],
    'yokneam': [32.6595, 35.1102],
    'יקנעם עילית': [32.6595, 35.1102],
    'מגדל העמק': [32.6738, 35.2415],
    'migdal haemek': [32.6738, 35.2415],
    'עפולה': [32.6078, 35.2894],
    'afula': [32.6078, 35.2894],
    'אלון תבור': [32.6517, 35.3524],
    'alon tavor': [32.6517, 35.3524],
    'נצרת': [32.6996, 35.3035],
    'נוף הגליל': [32.7050, 35.3350],
    'ציפורית': [32.7600, 35.3400],
    'טבריה': [32.7922, 35.5312],
    'קריית שמונה': [33.2075, 35.5697],
    'kiryat shmona': [33.2075, 35.5697],
    'קצרין': [32.9917, 35.6900],
    'משגב': [32.8600, 35.2500],
    'צפון': [32.7940, 34.9896],
    'north': [32.7940, 34.9896],
    'גליל': [32.9199, 35.2901],
    'עמקים': [32.6078, 35.2894],

    // Jerusalem & Judea
    'ירושלים': [31.7683, 35.2137],
    'jerusalem': [31.7683, 35.2137],
    'בית שמש': [31.7470, 34.9881],
    'beit shemesh': [31.7470, 34.9881],
    'מעלה אדומים': [31.7917, 35.2972],

    // General Countrywide / Default
    'ישראל': [32.0853, 34.7818],
    'israel': [32.0853, 34.7818],
    'ארצי': [32.0853, 34.7818],
    'היברידי': [32.0853, 34.7818],
    'remote': [32.0853, 34.7818],
    'מרוחק': [32.0853, 34.7818]
  };

  // Company Headquarters & Primary Campuses Geolocation Dictionary
  const COMPANY_HQ_LOCATIONS_GEO = [
    // Semiconductors & High-Tech Hardware
    [['tower semiconductor', 'טאואר', 'towersemi'], [32.6738, 35.2415], 'מגדל העמק'],
    [['ultra clean', 'uct'], [32.6738, 35.2415], 'מגדל העמק'],
    [['kla', 'קיי אל איי'], [32.6738, 35.2415], 'מגדל העמק'],
    [['applied materials', 'אפלייד מטיריאלס', 'אפלייד'], [31.9077, 34.8080], 'פארק המדע רחובות'],
    [['nova', 'נובה'], [31.9055, 34.8075], 'פארק המדע רחובות'],
    [['stratasys', 'סטראטסיס'], [31.9055, 34.8075], 'פארק המדע רחובות'],
    [['merck', 'מרק'], [31.9055, 34.8075], 'פארק המדע רחובות'],
    [['edwards vacuum', 'edwards', 'אדוורדס'], [31.6100, 34.7642], 'קריית גת'],
    [['intel', 'אינטל'], [31.6100, 34.7642], 'קריית גת'],

    // Energy, Gas, Solar, Utilities & CleanTech
    [['siemens energy', 'סימנס אנרגיה', 'siemens'], [32.0833, 34.9572], 'פארק אפק, ראש העין'],
    [['alumenergy', 'אלומאנרג׳י', 'אלומאנרגי', 'אלומושת'], [32.6517, 35.3524], 'אלון תבור'],
    [['nt-tao', 'compact fusion'], [32.1528, 34.8878], 'הוד השרון'],
    [['solaredge', 'סולאראדג'], [32.1624, 34.8080], 'הרצליה פיתוח'],
    [['enlight', 'אנלייט'], [32.0833, 34.9572], 'ראש העין'],
    [['energix', 'אנרג׳יקס', 'אנרגיקס'], [32.0822, 34.8020], 'בורסת רמת גן'],
    [['doral', 'דוראל'], [32.0822, 34.8050], 'רמת גן'],
    [['ormat', 'אורמת'], [31.8781, 34.7397], 'יבנה'],
    [['jinko', 'ג׳ינקו', 'גינקו'], [32.1624, 34.8447], 'הרצליה'],
    [['solar solutions', 'פתרונות סולאריים'], [32.3850, 34.9000], 'עמק חפר'],
    [['plant supervision'], [32.6517, 35.3524], 'אלון תבור'],
    [['bazan', 'בז״ן', 'בזן', 'בתי זיקוק'], [32.7980, 35.0450], 'מפרץ חיפה'],
    [['paz', 'פז'], [32.2530, 34.8450], 'יקום'],
    [['sonol', 'סונול'], [32.2783, 34.8572], 'פולג, נתניה'],
    [['delek', 'דלק', 'ניו-מד', 'newmed'], [32.1624, 34.8080], 'הרצליה'],
    [['isramco', 'ישראמקו', 'נפטא'], [32.0840, 34.8650], 'פתח תקווה'],

    // Defense, Aerospace, UAVs, Drones & Robotics
    [['elbit', 'אלביט'], [32.7880, 34.9580], 'מת״ם חיפה'],
    [['iai', 'התעשייה האווירית', 'התעשיה האווירית', 'אלתא', 'elta'], [32.0030, 34.8850], 'נתב״ג / לוד'],
    [['rafael', 'רפאל'], [32.8650, 35.0850], 'מכון דוד, קריות'],
    [['controp', 'קונטרופ'], [32.1528, 34.8878], 'הוד השרון'],
    [['assatec', 'אסאטק'], [32.9278, 35.0817], 'עכו / נהריה'],
    [['allpha', 'אלפא אינוביישן'], [32.8120, 35.0340], 'מספנות חיפה'],
    [['bagira', 'בגירה'], [32.0158, 34.7874], 'חולון'],
    [['israel shipyards', 'מספנות ישראל'], [32.8120, 35.0340], 'נמל חיפה'],
    [['airobotics', 'איירובוטיקס'], [32.0910, 34.8650], 'פתח תקווה'],
    [['percepto', 'פרספטו'], [31.8986, 35.0104], 'פארק טכנולוגי מודיעין'],
    [['hevendrones', 'הוונדרונס'], [32.6100, 35.0500], 'פארק מבוא כרמל'],
    [['steadicopter', 'סטדיקופטר'], [32.6738, 35.2415], 'מגדל העמק'],
    [['bluebird', 'בלובריד'], [32.2850, 34.9150], 'קדימה-צורן'],
    [['aeronautics', 'אירונאוטיקס'], [31.8781, 34.7397], 'יבנה'],
    [['copterpix', 'קופטרפיקס'], [31.9986, 34.9458], 'שוהם'],

    // Aviation, Logistics & Transportation
    [['swissport', 'סוויספורט'], [32.0005, 34.8707], 'נתב״ג'],
    [['alstom', 'אלסטום'], [32.0628, 34.7865], 'תל אביב'],
    [['pb', 'parsons brinckerhoff'], [32.0120, 34.9220], 'איירפורט סיטי'],

    // Infrastructure, Water, AgTech & Construction
    [['netafim', 'נטפים'], [32.0715, 34.7930], 'תל אביב'],
    [['nextcom', 'נקסטקום'], [32.6595, 35.1102], 'יקנעם עילית'],
    [['shikun', 'שיכון ובינוי'], [32.0120, 34.9220], 'איירפורט סיטי'],
    [['adama', 'אדמה'], [32.0120, 34.9220], 'איירפורט סיטי'],
    [['danya', 'דניה סיבוס', 'דניה'], [32.0294, 34.8572], 'אור יהודה'],
    [['electra', 'אלקטרה'], [31.9850, 34.7750], 'ראשון לציון'],
    [['ashtrom', 'אשטרום'], [32.0620, 34.7870], 'תל אביב'],
    [['shapir', 'שפיר'], [32.0840, 34.8650], 'פתח תקווה'],
    [['baran', 'ברן'], [32.0020, 34.8290], 'בית דגן'],
    [['icl', 'כי״ל', 'כימיקלים לישראל', 'כיל'], [31.2589, 34.8050], 'באר שבע'],

    // Tech, Telecom, Software, Hospitals & Services
    [['michlol', 'מכלול'], [32.0910, 34.8650], 'פתח תקווה'],
    [['e2e solutions', 'e2e'], [32.1100, 34.8350], 'רמת החייל, תל אביב'],
    [['elad', 'אלעד מערכות'], [32.1100, 34.8350], 'רמת החייל, תל אביב'],
    [['sheba', 'שיבא', 'תל השומר'], [32.0460, 34.8430], 'רמת גן'],
    [['mobileye', 'מובילאיי'], [31.8020, 35.2150], 'הר חוצבים, ירושלים'],
    [['check point', 'checkpoint', "צ'ק פוינט"], [32.0720, 34.7950], 'תל אביב'],
    [['cross river'], [31.8020, 35.2150], 'הר חוצבים, ירושלים'],
    [['jll'], [32.0715, 34.7930], 'תל אביב'],
    [['wix', 'וויקס'], [32.1000, 34.7750], 'נמל תל אביב'],
    [['monday', 'מאנדיי'], [32.0650, 34.7750], 'שדרות רוטשילד, תל אביב'],
    [['fiverr', 'פייבר'], [32.0600, 34.7750], 'תל אביב']
  ];

  const GENERIC_LOCATION_TERMS = new Set([
    'ישראל', 'israel', 'ארצי', 'היברידי', 'remote', 'מרוחק', 'כל הארץ', 
    'מרכז הארץ', 'מרכז', 'center', 'שרון', 'sharon', 'דרום', 'south', 
    'צפון', 'north', 'שפלה', 'סדנה ויציאה לשטח', 'בשטח'
  ]);

  function getJobLatLng(job) {
    const rawLoc = (job.location || '').toLowerCase();
    const rawComp = (job.company || '').toLowerCase();
    
    // Deterministic jitter based on job link / ID
    let hash = 0;
    const linkStr = job.link || job.id || (rawComp + rawLoc);
    for (let i = 0; i < linkStr.length; i++) {
      hash = ((hash << 5) - hash) + linkStr.charCodeAt(i);
      hash |= 0;
    }
    const jitterLat = (((Math.abs(hash) % 100) - 50) / 50) * 0.014;
    const jitterLng = (((Math.abs(hash * 31) % 100) - 50) / 50) * 0.014;

    // Step 1: Check if the job location mentions a SPECIFIC municipality or industrial site
    // (excluding generic national/regional terms)
    for (const [key, coords] of Object.entries(ISRAEL_LOCATIONS_GEO)) {
      if (!GENERIC_LOCATION_TERMS.has(key) && rawLoc.includes(key)) {
        return [coords[0] + jitterLat, coords[1] + jitterLng];
      }
    }

    // Step 2: Company Headquarters & Main Campus Geo-Mapping
    // If location is generic or unspecified, resolve by company HQ!
    for (const [keys, coords, desc] of COMPANY_HQ_LOCATIONS_GEO) {
      if (keys.some(k => rawComp.includes(k))) {
        return [coords[0] + jitterLat, coords[1] + jitterLng];
      }
    }

    // Step 3: Regional location matches (e.g., 'שרון', 'שפלה', 'צפון', 'דרום', 'מרכז')
    for (const [key, coords] of Object.entries(ISRAEL_LOCATIONS_GEO)) {
      if (rawLoc.includes(key)) {
        return [coords[0] + jitterLat, coords[1] + jitterLng];
      }
    }

    // Step 4: Fallback to Central Israel (Tel Aviv)
    return [32.0853 + jitterLat, 34.7818 + jitterLng];
  }

  let liveJobsMapInstance = null;
  let markersClusterGroup = null;

  function initLiveJobsMap() {
    const mapEl = document.getElementById('liveJobsMap');
    if (!mapEl || liveJobsMapInstance) return;

    try {
      liveJobsMapInstance = L.map('liveJobsMap', {
        scrollWheelZoom: true,
        zoomControl: true,
        zoomSnap: 0.5,
        zoomDelta: 0.5,
        wheelPxPerZoomLevel: 120,
        wheelDebounceTime: 40,
        zoomAnimation: true,
        zoomAnimationThreshold: 8,
        fadeAnimation: true,
        markerZoomAnimation: true
      }).setView([32.0853, 34.85], 8);

      // Official Google Maps tile layer in English (hl=en)
      L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&hl=en', {
        maxZoom: 19,
        keepBuffer: 6,
        updateWhenZooming: false,
        updateWhenIdle: true,
        attribution: '&copy; Google Maps'
      }).addTo(liveJobsMapInstance);

      if (typeof L.markerClusterGroup === 'function') {
        markersClusterGroup = L.markerClusterGroup({
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          zoomToBoundsOnClick: true,
          maxClusterRadius: 40,
          spiderfyDistanceMultiplier: 1.4,
          iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            let sizeClass = 'small';
            if (count > 25) sizeClass = 'large';
            else if (count > 8) sizeClass = 'medium';
            return L.divIcon({
              html: `<div class="custom-cluster-badge ${sizeClass}"><span>${count}</span></div>`,
              className: 'marker-cluster-custom',
              iconSize: L.point(40, 40)
            });
          }
        });
        liveJobsMapInstance.addLayer(markersClusterGroup);
      } else {
        markersClusterGroup = L.layerGroup().addTo(liveJobsMapInstance);
      }
    } catch(e) {
      console.error('Error initializing Live Jobs Map:', e);
    }
  }

  function updateMapMarkers() {
    if (!liveJobsMapInstance || !markersClusterGroup) return;

    markersClusterGroup.clearLayers();

    const visibleCards = document.querySelectorAll('.job-card:not(.is-hidden)');
    const totalVisible = visibleCards.length;
    let mappedCount = 0;

    const latLngBounds = [];

    visibleCards.forEach(card => {
      const id = card.getAttribute('data-id');
      const job = allJobsMap[id];
      if (!job) return;

      const [lat, lng] = getJobLatLng(job);
      if (lat && lng) {
        mappedCount++;
        latLngBounds.push([lat, lng]);
      }

      const score = Number(job.match_score) || 85;
      const scoreColor = score >= 85 ? 'var(--dashboard-cyan)' : (score >= 70 ? 'var(--dashboard-lime)' : 'var(--dashboard-gold)');
      const scoreBorder = score >= 85 ? 'rgba(137, 244, 231, 0.8)' : (score >= 70 ? 'rgba(220, 255, 114, 0.8)' : 'rgba(255, 211, 104, 0.8)');

      const companyNameClean = stripEmojis(job.company || 'חברה');
      const titleClean = stripEmojis(job.title || 'משרה');
      const salaryRangeStr = (job.salary_range && job.salary_range !== 'לא צוין') ? stripEmojis(job.salary_range) : 'ללא ציון שכר במודעה';

      const logoInfo = getCompanyLogoInfo(job.company, job.logo);
      const safeComp = companyNameClean.replace(/"/g, '&quot;');
      const safeTitle = titleClean.replace(/"/g, '&quot;');
      const safeLink = job.link || '#';
      const safeId = encodeURIComponent(id);

      const markerLogoInner = logoInfo.logoUrl ? `
        <img src="${logoInfo.logoUrl}" alt="${safeComp}" loading="lazy" class="map-pin-logo-img"
             onload="if(this.naturalWidth <= 16 && this.naturalHeight <= 16){ this.style.display='none'; var fb = this.nextElementSibling; if(fb) fb.style.display='flex'; }"
             onerror="if(this.dataset.fallbackTried !== '1' && '${logoInfo.fallbackUrl}'){ this.dataset.fallbackTried = '1'; this.src = '${logoInfo.fallbackUrl}'; } else { this.style.display='none'; var fb = this.nextElementSibling; if(fb) fb.style.display='flex'; }" />
        <div class="map-pin-avatar-fallback" style="display: none;">${logoInfo.initials}</div>
      ` : `
        <div class="map-pin-avatar-fallback">${logoInfo.initials}</div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-map-marker',
        html: `
          <div class="custom-map-marker-inner" title="${safeComp} - ${safeTitle}">
            <div class="map-pin-logo-bubble" style="border-color: ${scoreBorder};">
              <span class="map-pin-score-badge" style="background: ${scoreColor}; color: #0f172a;">${score}%</span>
              ${markerLogoInner}
            </div>
            <div class="map-pin-pointer" style="border-top-color: ${scoreBorder};"></div>
            <div class="map-pin-company-name" dir="auto">${companyNameClean}</div>
          </div>
        `,
        iconSize: [96, 70],
        iconAnchor: [48, 45],
        popupAnchor: [0, -45]
      });

      const marker = L.marker([lat, lng], { icon: customIcon });

      const logoHtml = getCompanyLogoHtml(job.company, job.logo);

      const popupHtml = `
        <div style="direction: rtl; text-align: right; min-width: 220px; max-width: 280px; font-family: 'Assistant', sans-serif;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <div style="flex-shrink: 0;">${logoHtml}</div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-size: 11px; color: var(--dashboard-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" dir="auto"><bdi>${safeComp}</bdi></div>
              <div style="font-size: 13px; font-weight: 700; color: #fff; line-height: 1.25; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" dir="auto"><bdi>${safeTitle}</bdi></div>
            </div>
          </div>
          <div style="font-size: 11.5px; color: var(--dashboard-muted); display: flex; flex-direction: column; gap: 3px; margin-bottom: 10px;">
            <span><i class="ph-duotone ph-map-pin"></i> ${job.location || 'ישראל'}</span>
            <span style="color: var(--dashboard-lime);"><i class="ph-duotone ph-coins"></i> ${salaryRangeStr}</span>
            <span style="color: ${scoreColor}; font-weight: 700;"><i class="ph-duotone ph-chart-line-up"></i> התאמה ${score}%</span>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 4px;">
            <button onclick="openJobModal(decodeURIComponent('${safeId}'))" class="btn-triage" style="flex: 1; width: auto; min-height: 34px; height: 34px; padding: 6px 10px; font-size: 12px; font-weight: 600; justify-content: center; background: rgba(137, 244, 231, 0.15); color: var(--dashboard-cyan); border: 1px solid rgba(137, 244, 231, 0.4); border-radius: 999px; box-sizing: border-box;">
              <i class="ph-duotone ph-eye" style="font-size: 14px;"></i> צפה בכרטיס
            </button>
            <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply" style="flex: 1; width: auto; min-height: 34px; height: 34px; padding: 6px 10px; font-size: 12px; font-weight: 600; justify-content: center; text-decoration: none; border-radius: 999px; box-sizing: border-box;">
              <i class="ph-bold ph-arrow-square-out" style="font-size: 14px;"></i> הגש
            </a>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml, {
        maxWidth: 300,
        className: 'glass-leaflet-popup'
      });

      marker.addTo(markersClusterGroup);
    });

    const markerCountEl = document.getElementById('mapMarkersCountText');
    if (markerCountEl) {
      if (mappedCount === 0) {
        markerCountEl.textContent = 'אין משרות להצגה על המפה';
      } else if (mappedCount === 1) {
        markerCountEl.textContent = (totalVisible > 1) ? `מוצגת משרה אחת מתוך ${totalVisible} משרות על המפה` : 'מוצגת משרה אחת על המפה';
      } else {
        markerCountEl.textContent = (mappedCount < totalVisible) ? `מוצגות ${mappedCount} מתוך ${totalVisible} משרות על המפה` : `מוצגות ${mappedCount} משרות על המפה`;
      }
    }

    if (latLngBounds.length > 0) {
      try {
        const bounds = L.latLngBounds(latLngBounds);
        liveJobsMapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
      } catch(e) {}
    }
  }

  function classifyJobSector(job) {
    if (!job) return 'אנרגיה';
    const secKey = (job.sector_key || '').toLowerCase().trim();
    const sec = (job.sector || '').toLowerCase().trim();
    const title = (job.title || '').toLowerCase().trim();

    // 1. Solar
    if (secKey === 'solar' || ['סולאר', 'solar', 'pv'].some(k => sec.includes(k))) {
      return 'סולאר';
    }
    // 2. Drones / Defense / Avionics
    if (['drones', 'cuas', 'avionics'].includes(secKey) || ['רחפן', 'כטב', 'drone', 'uav', 'אוויוניקה', 'תעופה', 'ביטחון'].some(k => sec.includes(k))) {
      return 'רחפנים';
    }
    // 3. Natural Gas
    if (['natural_gas', 'naturalgas', 'gas'].includes(secKey) || ['גז טבעי', ' גז', 'gas'].some(k => sec.includes(k))) {
      return 'גז טבעי';
    }
    // 4. SCADA & Control (Combined into one column as requested by user)
    if (['scada', 'control', 'automation'].includes(secKey) || 
        ['scada', 'בקרה', 'control', 'אוטומציה', 'noc'].some(k => sec.includes(k)) || 
        ['scada', 'בקרה', 'control room', 'noc operator', 'בקר'].some(k => title.includes(k))) {
      return 'בקרה ו-SCADA';
    }
    // 5. Storage & Energy Tech
    if (['energy_tech', 'energytech', 'storage', 'bess'].includes(secKey) || ['אגירה', 'storage', 'bess', "אנרג'י"].some(k => sec.includes(k))) {
      return 'אגירה';
    }
    // 6. Operations & Maintenance
    if (['operations', 'maintenance'].includes(secKey) || ['תפעול', 'אחזקה', 'מכונות', 'ייצור'].some(k => sec.includes(k))) {
      return 'תפעול ואחזקה';
    }
    // 7. Energy General
    return 'אנרגיה';
  }

  let jobStates = loadTriageState();

  function getAllAvailableJobs() {
    const seenLinks = new Set((rawJobsData || []).map(j => j.link));
    const all = [...(rawJobsData || [])];
    if (typeof historicalCatalog !== 'undefined' && historicalCatalog) {
      Object.keys(jobStates).forEach(link => {
        if ((jobStates[link] === 'saved' || jobStates[link] === 'rejected') && !seenLinks.has(link) && historicalCatalog[link]) {
          all.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
      Object.keys(starredJobs).forEach(link => {
        if (starredJobs[link] && !seenLinks.has(link) && historicalCatalog[link]) {
          all.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
    }
    return all;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function sanitizeUrl(rawUrl) {
    if (!rawUrl) return '#';
    const trimmed = String(rawUrl).trim();
    if (/^(?:https?:\\/\\/|mailto:)/i.test(trimmed)) {
      return trimmed;
    }
    return '#';
  }

  function classifyJobRegion(locStr) {
    if (!locStr) return 'center';
    const loc = locStr.toLowerCase();
    if (loc.includes('צפון') || loc.includes('חיפה') || loc.includes('קריות') || loc.includes('נשר') || 
        loc.includes('יקנעם') || loc.includes('מגדל העמק') || loc.includes('כרמיאל') || loc.includes('גליל') || 
        loc.includes('דלתון') || loc.includes('יזרעאל') || loc.includes('עפולה') || loc.includes('טבריה') || 
        loc.includes('לוחמי הגטאות')) {
      return 'north';
    }
    if (loc.includes('שרון') || loc.includes('נתניה') || loc.includes('הרצליה') || loc.includes('רעננה') || 
        loc.includes('כפר סבא') || loc.includes('הוד השרון') || loc.includes('עמק חפר') || loc.includes('חדרה')) {
      return 'sharon';
    }
    if (loc.includes('דרום') || loc.includes('אשדוד') || loc.includes('אשקלון') || loc.includes('באר שבע') || 
        loc.includes('קריית גת') || loc.includes('קרית גת') || loc.includes('נאות חובב') || loc.includes('דימונה') || 
        loc.includes('להבים') || loc.includes('נגב') || loc.includes('שפלה')) {
      return 'south';
    }
    if (loc.includes('ארצי') || loc.includes('שטח') || loc.includes('פריסה ארצית') || loc.includes('תחנות כוח')) {
      return 'nationwide';
    }
    return 'center';
  }

  function stripEmojis(str) {
    if (!str) return '';
    return str.replace(/\\p{Extended_Pictographic}/gu, '').replace(/[\\u2600-\\u27BF]/g, '').trim();
  }

  function toggleCardDetails(btn, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    const card = btn.closest('.job-card');
    if (!card) return;
    const details = card.querySelector('.job-details-collapsible');
    if (!details) return;
    const isExpanded = details.classList.contains('expanded');
    if (isExpanded) {
      details.classList.remove('expanded');
      btn.classList.remove('expanded');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '<span>הרחב ניתוח מלא</span> <i class="ph-bold ph-caret-down"></i>';
    } else {
      details.classList.add('expanded');
      btn.classList.add('expanded');
      btn.setAttribute('aria-expanded', 'true');
      btn.innerHTML = '<span>הסתר ניתוח מלא</span> <i class="ph-bold ph-caret-up"></i>';
    }
  }

  function getJobSalaryVal(job) {
    if (!job) return 0;
    if (typeof job.p50 === 'number' && !isNaN(job.p50) && job.p50 > 0) return job.p50;
    if (typeof job.p75 === 'number' && !isNaN(job.p75) && job.p75 > 0) return job.p75;
    if (typeof job.p25 === 'number' && !isNaN(job.p25) && job.p25 > 0) return job.p25;
    if (job.salary_range && typeof job.salary_range === 'string' && job.salary_range !== 'לא צוין במודעה') {
      const clean = job.salary_range.replace(/,/g, '');
      const matches = clean.match(/\\d{4,6}/g);
      if (matches && matches.length > 0) {
        if (matches.length >= 2) {
          return (Number(matches[0]) + Number(matches[1])) / 2;
        }
        return Number(matches[0]);
      }
    }
    return 0;
  }

  function renderCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    const displayJobs = getAllAvailableJobs();
    if (!displayJobs || displayJobs.length === 0) {
      document.getElementById('emptyState').style.display = 'block';
      return;
    }

    let sortedJobs = [...displayJobs];
    sortedJobs.sort((a, b) => {
      if (currentSort === 'score_desc') {
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        return dateB.localeCompare(dateA);
      } else if (currentSort === 'salary_desc') {
        const salA = getJobSalaryVal(a);
        const salB = getJobSalaryVal(b);
        if (salB !== salA) return salB - salA;
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        return dateB.localeCompare(dateA);
      } else if (currentSort === 'company_asc') {
        const compA = (a.company || '').trim();
        const compB = (b.company || '').trim();
        const compDiff = compA.localeCompare(compB, 'he', { sensitivity: 'base' });
        if (compDiff !== 0) return compDiff;
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        return dateB.localeCompare(dateA);
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
      const company = stripEmojis(job.company || 'חברה');
      const title = stripEmojis(job.title || 'משרה ללא כותרת');
      const link = job.link || '#';
      const secKey = job.sector_key || 'energy';
      const jobDate = job.date || 'היום';
      const classifiedSector = classifyJobSector(job);

      let scoreClass = 'badge-score-high';
      if (score < 80) scoreClass = 'badge-score-fair';
      else if (score < 90) scoreClass = 'badge-score-med';

      const domain = escapeHtml(stripEmojis(job.company_domain_product || job.company_summary || 'חברה מובילה בתחומה'));
      const loc = escapeHtml(stripEmojis(job.location || 'ישראל / היברידי'));
      const jobSum = escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'תפקיד משמעותי בתפעול וניטור מערכות מתקדמות.'));
      const strengths = escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.'));
      const quickInsight = escapeHtml(stripEmojis(job.reasoning || job.experience_strengths || job.job_summary || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.'));
      const companyReqs = escapeHtml(stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה (פירוט מלא בקישור להגשה).'));
      const safeCompany = escapeHtml(company);
      const safeTitle = escapeHtml(title);
      const safeLink = sanitizeUrl(link);
      const logoHtml = getCompanyLogoHtml(company, job.logo);

      // Source detection & styling
      let sourceName = job.source;
      if (!sourceName) {
        if (link.includes('drushim.co.il')) sourceName = 'דרושים';
        else if (link.includes('comeet.com') || link.includes('comeet')) sourceName = 'Comeet';
        else if (link.includes('linkedin.com')) sourceName = 'LinkedIn';
        else sourceName = 'LinkedIn';
      }

      let sourceChipStyle = 'color: #38bdf8; border-color: rgba(56, 189, 248, 0.35); background: rgba(56, 189, 248, 0.1);';
      let sourceIcon = 'ph-linkedin-logo';
      if (sourceName.toLowerCase().includes('drushim') || sourceName.includes('דרושים')) {
        sourceChipStyle = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); background: rgba(255, 211, 104, 0.12);';
        sourceIcon = 'ph-briefcase';
      } else if (sourceName.toLowerCase().includes('comeet')) {
        sourceChipStyle = 'color: #c084fc; border-color: rgba(192, 132, 252, 0.4); background: rgba(192, 132, 252, 0.12);';
        sourceIcon = 'ph-buildings';
      }

      const isStarred = Boolean(starredJobs[id]);
      const classifiedRegion = classifyJobRegion(loc);

      const card = document.createElement('article');
      card.setAttribute('data-id', id);
      card.setAttribute('data-sector', secKey);
      card.setAttribute('data-classified-sector', classifiedSector);
      card.setAttribute('data-location', loc.toLowerCase());
      card.setAttribute('data-region', classifiedRegion);
      card.setAttribute('data-starred', isStarred ? 'true' : 'false');
      card.setAttribute('data-score', score);
      card.className = `dashboard-card job-card ${isStarred ? 'is-starred-card' : ''}`;

      card.innerHTML = `
        <!-- Top Meta Row -->
        <div class="job-card-topbar">
          <div class="job-card-topbar-primary">
            <div style="display: flex; align-items: center; gap: 8px;">
              <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar('${id.replace(/'/g, "\\'")}', event)" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}" aria-label="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
                <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
              </button>
              <button type="button" class="btn-copy-link" onclick="copyJobLink('${safeLink.replace(/'/g, "\\'")}', event)" title="העתק קישור למשרה" aria-label="העתק קישור למשרה">
                <i class="ph-bold ph-share-network"></i>
              </button>
            </div>
            <div class="badge-score ${scoreClass}">
              <span><i class="ph-duotone ph-lightning"></i> ${score}%</span> התאמה
            </div>
          </div>
        </div>

        <!-- Title & Company Header -->
        <div class="job-card-main-header">
          ${logoHtml}
          <div class="job-header-text">
            <div class="job-company-name" dir="auto" title="${safeCompany}"><bdi>${safeCompany}</bdi></div>
            <h2 class="job-title-text" dir="auto" title="${safeTitle}"><bdi>${safeTitle}</bdi></h2>
          </div>
        </div>

        <!-- 2 Distinct Bubbles: Domain & Requirements -->
        <div class="job-bubbles-wrapper">
          <div class="job-bubble job-bubble-domain">
            <strong class="bubble-title"><i class="ph-duotone ph-buildings"></i> תחום ומוצר:</strong>
            <span class="bubble-content">${domain}</span>
          </div>
          <div class="job-bubble job-bubble-reqs">
            <strong class="bubble-title"><i class="ph-duotone ph-check-square"></i> דרישות המשרה:</strong>
            <span class="bubble-content">${companyReqs}</span>
          </div>
        </div>

        <!-- Progressive Disclosure Toggle Button -->
        <button type="button" class="btn-toggle-details" onclick="toggleCardDetails(this, event)" aria-expanded="false">
          <span>הרחב ניתוח מלא</span>
          <i class="ph-bold ph-caret-down"></i>
        </button>

        <!-- Collapsible Full Information Panels -->
        <div class="job-details-collapsible">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; font-size: 11.5px; color: var(--dashboard-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 8px;">
            <span><i class="ph-duotone ph-calendar-blank"></i> פורסם: ${escapeHtml(jobDate)}</span>
            <span><i class="ph-duotone ph-map-pin"></i> ${loc}</span>
            <span><i class="ph-duotone ${sourceIcon}"></i> מקור: ${escapeHtml(sourceName)}</span>
          </div>
          <div class="job-boxes-grid">
            <div class="job-box">
              <strong><i class="ph-duotone ph-article"></i> תקציר המשרה:</strong>
              <span>${jobSum}</span>
            </div>
            <div class="job-box highlight">
              <strong><i class="ph-duotone ph-sparkle"></i> תמצית התאמה ממוקדת:</strong>
              <span>${quickInsight}</span>
            </div>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="job-actions-bar">
          <div class="action-btn-group">
            <button type="button" onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'saved', event)" class="btn-triage action-save-btn">
              <i class="ph-duotone ph-bookmark-simple"></i> <span class="btn-text">שמור להגשה</span>
            </button>
            <button type="button" onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'rejected', event)" class="btn-triage action-reject-btn">
              <i class="ph-duotone ph-x"></i> <span>הסר משרה</span>
            </button>
          </div>
          <div class="action-btn-main-group">
            <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply" onclick="event.stopPropagation()">
              <span>הגש מועמדות</span> <i class="ph-duotone ph-arrow-up-right"></i>
            </a>
          </div>
        </div>
      `;

      allJobsMap[id] = job;
      container.appendChild(card);
    });

    updateUI();
  }

  function openJobModal(id) {
    const job = allJobsMap[id];
    if (!job) return;

    const modal = document.getElementById('jobDetailsModal');
    const headerActions = document.getElementById('jobModalTopActions');
    const body = document.getElementById('jobModalBody');
    const bottomBar = document.getElementById('jobModalBottomBar');
    if (!modal || !headerActions || !body || !bottomBar) return;

    const score = Number(job.match_score) || 85;
    const company = stripEmojis(job.company || 'חברה');
    const title = stripEmojis(job.title || 'משרה ללא כותרת');
    const link = job.link || '#';
    const safeCompany = escapeHtml(company);
    const safeTitle = escapeHtml(title);
    const safeLink = sanitizeUrl(link);
    const loc = escapeHtml(stripEmojis(job.location || 'ישראל / היברידי'));
    const jobDate = escapeHtml(job.date || 'היום');
    const classifiedSector = classifyJobSector(job);
    const domain = escapeHtml(stripEmojis(job.company_domain_product || job.company_summary || 'חברה מובילה בתחומה'));
    const jobSum = escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'תפקיד משמעותי בתפעול וניטור מערכות מתקדמות.'));
    const strengths = escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.'));
    const companyReqs = escapeHtml(stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה.'));
    const quickInsight = escapeHtml(stripEmojis(job.reasoning || job.experience_strengths || job.job_summary || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.'));
    const logoHtml = getCompanyLogoHtml(company, job.logo);
    let salaryRange = escapeHtml(stripEmojis(job.salary_range || ''));
    let salaryType = job.salary_source_type || '';
    const companyBdi = `<bdi dir="auto">${safeCompany}</bdi>`;
    let salaryLabel = escapeHtml(stripEmojis(job.salary_source_label || ''));
    const salaryEvidence = escapeHtml(stripEmojis(job.salary_evidence || ''));
    const salaryUrl = sanitizeUrl(job.salary_source_url || '');

    if (!salaryRange || salaryRange === 'לא צוין' || salaryType === 'none') {
      salaryRange = 'לא צוין במודעה';
      salaryLabel = 'לא צוין שכר';
      salaryType = 'none';
    }

    let scoreClass = 'badge-score-high';
    if (score < 80) scoreClass = 'badge-score-fair';
    else if (score < 90) scoreClass = 'badge-score-med';

    const isStarred = Boolean(starredJobs[id]);
    const state = jobStates[id] || 'pending';

    headerActions.innerHTML = `
      <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar('${id.replace(/'/g, "\\'")}', event); updateModalStar('${id.replace(/'/g, "\\'")}');" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}" aria-label="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
        <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
      </button>
      <button type="button" class="btn-copy-link" onclick="copyJobLink('${safeLink.replace(/'/g, "\\'")}', event)" title="העתק קישור למשרה" aria-label="העתק קישור למשרה">
        <i class="ph-bold ph-share-network"></i>
      </button>
      <div class="badge-score ${scoreClass}" title="ציון התאמה ${score}%">
        <span><i class="ph-duotone ph-lightning"></i> ${score}%</span>
      </div>
    `;

    body.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 14px;">
        ${logoHtml}
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 13.5px; font-weight: 700; color: var(--dashboard-cyan); margin-bottom: 2px;" dir="auto" title="${safeCompany}"><bdi>${safeCompany}</bdi></div>
          <h2 style="font-size: 17.5px; font-weight: 700; color: #fff; margin: 0 0 6px; line-height: 1.3;" dir="auto" title="${safeTitle}"><bdi>${safeTitle}</bdi></h2>
          <div style="font-size: 12px; color: var(--dashboard-muted); display: flex; align-items: center; gap: 12px;">
            <span><i class="ph-duotone ph-map-pin"></i> ${loc}</span>
            <span><i class="ph-duotone ph-calendar-blank"></i> ${escapeHtml(jobDate)}</span>
          </div>
        </div>
      </div>

      <!-- 2 Distinct Bubbles: Domain & Requirements -->
      <div class="job-bubbles-wrapper" style="margin: 4px 0 6px;">
        <div class="job-bubble job-bubble-domain" style="padding: 10px 14px; font-size: 13.5px;">
          <strong class="bubble-title"><i class="ph-duotone ph-buildings"></i> תחום ומוצר:</strong>
          <span class="bubble-content">${domain}</span>
        </div>
        <div class="job-bubble job-bubble-reqs" style="padding: 10px 14px; font-size: 13.5px;">
          <strong class="bubble-title"><i class="ph-duotone ph-check-square"></i> דרישות המשרה:</strong>
          <span class="bubble-content">${companyReqs}</span>
        </div>
      </div>

      <div class="job-boxes-grid" style="grid-template-columns: 1fr; gap: 10px;">
        <div class="job-box highlight" style="border-color: rgba(137, 244, 231, 0.35); background: rgba(137, 244, 231, 0.05);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <strong style="color: var(--dashboard-cyan);"><i class="ph-duotone ph-currency-circle-dollar"></i> הערכת שכר ואמינות מקור:</strong>
            <span style="font-size: 11.5px; font-weight: 600; color: var(--dashboard-cyan);">${salaryLabel}</span>
          </div>
          <div style="font-size: 15px; font-weight: 700; color: #ffffff; margin-bottom: 2px;">
            ${salaryRange}
          </div>
          <div style="font-size: 11px; color: var(--dashboard-muted); margin-bottom: 6px;">
            בסיס נתונים: שכר חודשי ברוטו למשרה מלאה (100% משרה)
          </div>
          ${salaryEvidence ? `<div style="font-size: 12.5px; color: #cbd5e1; line-height: 1.45; margin-bottom: 6px;">${salaryEvidence}</div>` : ''}
          ${salaryUrl !== '#' ? `<a href="${salaryUrl}" target="_blank" rel="noopener noreferrer" style="font-size: 11.5px; color: var(--dashboard-cyan); text-decoration: underline; display: inline-flex; align-items: center; gap: 4px;"><span>עיון בטבלת שכר ענפית מוסמכת</span> <i class="ph-duotone ph-arrow-square-out"></i></a>` : ''}
        </div>
        <div class="job-box">
          <strong><i class="ph-duotone ph-article"></i> תקציר המשרה:</strong>
          <span>${jobSum}</span>
        </div>
        <div class="job-box highlight">
          <strong><i class="ph-duotone ph-sparkle"></i> תמצית התאמה ממוקדת:</strong>
          <span>${quickInsight}</span>
        </div>
      </div>
    `;

    bottomBar.innerHTML = `
      <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply">
        <span>הגש מועמדות באתר המשרה</span> <i class="ph-duotone ph-arrow-up-right"></i>
      </a>
      <div class="job-modal-triage-group">
        <button id="modalSaveBtn" onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'saved'); updateModalTriageButtons('${id.replace(/'/g, "\\'")}');" class="btn-triage action-save-btn ${state === 'saved' ? 'saved-active' : ''}">
          <i class="ph-duotone ph-bookmark-simple"></i> <span>${state === 'saved' ? 'נשמר להגשה' : 'שמור להגשה'}</span>
        </button>
        <button id="modalRejectBtn" onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'rejected'); updateModalTriageButtons('${id.replace(/'/g, "\\'")}');" class="btn-triage action-reject-btn ${state === 'rejected' ? 'rejected-active' : ''}">
          <i class="ph-duotone ph-x"></i> <span>הסר משרה</span>
        </button>
      </div>
    `;

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function updateModalStar(id) {
    const isStarred = Boolean(starredJobs[id]);
    const starBtn = document.querySelector('#jobModalTopActions .btn-star');
    if (starBtn) {
      starBtn.className = `btn-star ${isStarred ? 'is-starred' : ''}`;
      starBtn.setAttribute('title', isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
      starBtn.setAttribute('aria-label', isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
      starBtn.innerHTML = `<i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>`;
    }
  }

  function updateModalTriageButtons(id) {
    const state = jobStates[id] || 'pending';
    const saveBtn = document.getElementById('modalSaveBtn');
    const rejectBtn = document.getElementById('modalRejectBtn');
    if (saveBtn) {
      saveBtn.className = `btn-triage action-save-btn ${state === 'saved' ? 'saved-active' : ''}`;
      saveBtn.querySelector('span').textContent = state === 'saved' ? 'נשמר להגשה' : 'שמור להגשה';
    }
    if (rejectBtn) {
      rejectBtn.className = `btn-triage action-reject-btn ${state === 'rejected' ? 'rejected-active' : ''}`;
    }
  }

  function closeJobModal() {
    const modal = document.getElementById('jobDetailsModal');
    if (modal) modal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  function updateSortIconAndToast(sortVal, showUserToast = true) {
    const icon = document.getElementById('sortIcon');
    const select = document.getElementById('sortSelect');
    if (select && select.value !== sortVal) {
      select.value = sortVal;
    }
    let iconClass = 'ph-calendar-blank';
    let toastMsg = 'מיון: התאריך החדש קודם';

    if (sortVal === 'score_desc') {
      iconClass = 'ph-sort-descending';
      toastMsg = 'מיון: ציון התאמה מגבוה לנמוך';
    } else if (sortVal === 'salary_desc') {
      iconClass = 'ph-currency-circle-dollar';
      toastMsg = 'מיון: רמת שכר מגבוה לנמוך';
    } else if (sortVal === 'company_asc') {
      iconClass = 'ph-buildings';
      toastMsg = 'מיון: שם חברה מא׳ עד ת׳';
    } else {
      iconClass = 'ph-calendar-blank';
      toastMsg = 'מיון: התאריך החדש קודם';
    }

    if (icon) {
      icon.className = `ph-duotone ${iconClass}`;
    }
    if (showUserToast) {
      showToast(iconClass, toastMsg);
    }
  }

  function changeSort(sortVal) {
    currentSort = sortVal;
    try {
      localStorage.setItem(SORT_STORAGE_KEY, sortVal);
    } catch(e) {}
    updateSortIconAndToast(sortVal, true);
    renderCards();
  }

  function toggleSort() {
    const cycle = ['date_desc', 'score_desc', 'salary_desc', 'company_asc'];
    const currentIdx = cycle.indexOf(currentSort);
    const nextSort = cycle[(currentIdx + 1) % cycle.length];
    changeSort(nextSort);
  }

  function toggleAction(id, action, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    const current = jobStates[id];
    if (current === action) {
      delete jobStates[id];
      showToast('ph-arrow-counter-clockwise', 'הסטטוס אופס למצב ממתין');
    } else {
      jobStates[id] = action;
      if (action === 'saved') {
        showToast('ph-bookmark-simple', 'המשרה נשמרה להגשה');
      } else if (action === 'rejected') {
        showToast('ph-trash', 'המשרה הוסרה ולא תוצג שוב');
      }
    }
    saveTriageState(jobStates);
    updateUI();
    scheduleCloudPush();
  }

  function setFilter(filter, el) {
    currentFilter = filter;

    const sectorSelect = document.getElementById('sectorFilter');
    if (sectorSelect) sectorSelect.value = 'all';
    const regionSelect = document.getElementById('regionFilter');
    if (regionSelect) regionSelect.value = 'all';

    document.querySelectorAll('.stat-cube-btn').forEach(b => {
      b.classList.remove('active');
      b.removeAttribute('aria-current');
    });
    const targetEl = el || document.getElementById('cube_' + filter);
    if (targetEl) {
      targetEl.classList.add('active');
      targetEl.setAttribute('aria-current', 'page');
    }

    const currentCardCount = document.querySelectorAll('.job-card').length;
    const availableCount = getAllAvailableJobs().length;
    if (currentCardCount !== availableCount) {
      renderCards();
    } else {
      updateUI();
    }
  }

  let searchDebounceTimer = null;
  function onSearchInput(val) {
    const wrapper = document.getElementById('searchInputWrapper');
    if (wrapper) {
      wrapper.classList.toggle('has-value', Boolean(val && val.trim().length > 0));
    }
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    searchDebounceTimer = setTimeout(() => {
      filterCards();
    }, 250);
  }

  function clearSearchInput() {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    const input = document.getElementById('searchInput');
    const wrapper = document.getElementById('searchInputWrapper');
    if (input) {
      input.value = '';
      input.focus();
    }
    if (wrapper) {
      wrapper.classList.remove('has-value');
    }
    filterCards();
  }

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
  }

  function highlightSearchTerms(el, terms) {
    if (!el) return;
    if (!el.__originalHtml) {
      el.__originalHtml = el.innerHTML;
    }
    if (!terms || terms.length === 0) {
      el.innerHTML = el.__originalHtml;
      return;
    }

    let html = el.__originalHtml;
    terms.forEach(term => {
      const regex = new RegExp(`(?![^<]*>)(${escapeRegex(term)})`, 'gi');
      html = html.replace(regex, '<mark class="search-highlight">$1</mark>');
    });
    el.innerHTML = html;
  }

  function copyJobLink(link, event) {
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }
    if (!link) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(() => {
        showToast('ph-share-network', 'הקישור למשרה הועתק ללוח בהצלחה!');
      }).catch(() => {
        fallbackCopy(link);
      });
    } else {
      fallbackCopy(link);
    }
  }

  function fallbackCopy(text) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      showToast('ph-share-network', 'הקישור למשרה הועתק ללוח בהצלחה!');
    } catch(e) {
      showToast('ph-link', 'לא ניתן להעתיק אוטומטית');
    }
  }

  function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }

  function resetAllFilters() {
    const sec = document.getElementById('sectorFilter');
    const reg = document.getElementById('regionFilter');
    const inp = document.getElementById('searchInput');
    const wrap = document.getElementById('searchInputWrapper');

    if (sec) sec.value = 'all';
    if (reg) reg.value = 'all';
    if (inp) inp.value = '';
    if (wrap) wrap.classList.remove('has-value');

    filterCards();
    showToast('ph-arrow-counter-clockwise', 'המסננים וחיפוש המשרות אופסו בהצלחה');
  }

  function filterCards() {
    updateUI();
  }

  function updateUI() {
    const selectedSector = document.getElementById('sectorFilter').value;
    const searchRaw = document.getElementById('searchInput') ? document.getElementById('searchInput').value.trim() : '';
    const searchInput = searchRaw.toLowerCase();
    const searchTerms = searchRaw.split(/\\s+/).filter(t => t.length >= 2);
    
    const wrapper = document.getElementById('searchInputWrapper');
    if (wrapper) {
      wrapper.classList.toggle('has-value', Boolean(searchRaw.length > 0));
    }
    
    const cards = document.querySelectorAll('.job-card');
    const rawJobLinks = new Set((rawJobsData || []).map(j => j.link));
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
      const saveText = saveBtn ? saveBtn.querySelector('.btn-text') : null;

      if (saveBtn && saveText) {
        if (state === 'saved') {
          saveBtn.className = "btn-triage action-save-btn saved-active";
          saveText.textContent = "נשמר להגשה";
          if (rejectBtn) rejectBtn.className = "btn-triage action-reject-btn";
        } else if (state === 'rejected') {
          if (rejectBtn) rejectBtn.className = "btn-triage action-reject-btn rejected-active";
          saveBtn.className = "btn-triage action-save-btn";
          saveText.textContent = "שמור להגשה";
        } else {
          saveBtn.className = "btn-triage action-save-btn";
          if (rejectBtn) rejectBtn.className = "btn-triage action-reject-btn";
          saveText.textContent = "שמור להגשה";
        }
      }

      const isStarred = Boolean(starredJobs[id]);
      const isCurrentBatchJob = rawJobLinks.has(id);

      let matchesTab = false;
      if (currentFilter === 'all') {
        matchesTab = isCurrentBatchJob && (state !== 'rejected' && state !== 'purged');
      } else if (currentFilter === 'starred') {
        matchesTab = (isStarred && state !== 'rejected' && state !== 'purged');
      } else if (currentFilter === 'saved') {
        matchesTab = (state === 'saved' && state !== 'rejected' && state !== 'purged');
      } else if (currentFilter === 'rejected') {
        matchesTab = (state === 'rejected');
      }

      let matchesSector = (selectedSector === 'all');
      if (!matchesSector) {
        const classifiedSector = card.getAttribute('data-classified-sector');
        if (selectedSector === 'scada') {
          matchesSector = (classifiedSector === 'בקרה ו-SCADA');
        } else if (selectedSector === 'solar') {
          matchesSector = (classifiedSector === 'סולאר');
        } else if (selectedSector === 'natural_gas') {
          matchesSector = (classifiedSector === 'גז טבעי');
        } else if (selectedSector === 'drones') {
          matchesSector = (classifiedSector === 'רחפנים');
        } else if (selectedSector === 'energy_tech') {
          matchesSector = (classifiedSector === 'אגירה');
        } else if (selectedSector === 'operations') {
          matchesSector = (classifiedSector === 'תפעול ואחזקה');
        } else if (selectedSector === 'energy') {
          matchesSector = (classifiedSector === 'אנרגיה');
        } else {
          matchesSector = true;
        }
      }

      const selectedRegion = document.getElementById('regionFilter') ? document.getElementById('regionFilter').value : 'all';
      let matchesRegion = (selectedRegion === 'all');
      if (!matchesRegion) {
        const cardRegion = card.getAttribute('data-region') || 'center';
        matchesRegion = (cardRegion === selectedRegion);
      }

      let matchesSearch = true;
      if (searchInput) {
        const cardText = card.textContent.toLowerCase();
        matchesSearch = cardText.includes(searchInput);
      }

      if (matchesTab && matchesSector && matchesRegion && matchesSearch && state !== 'purged') {
        card.style.display = '';
        card.classList.remove('is-hidden');
        visibleCount++;

        // Apply highlighting to key visible text elements when search is active
        const titleEl = card.querySelector('.job-title-text');
        const compEl = card.querySelector('.job-company-name');
        const domainEl = card.querySelector('.job-bubble-domain .bubble-content');
        const reqsEl = card.querySelector('.job-bubble-reqs .bubble-content');

        if (titleEl) highlightSearchTerms(titleEl, searchTerms);
        if (compEl) highlightSearchTerms(compEl, searchTerms);
        if (domainEl) highlightSearchTerms(domainEl, searchTerms);
        if (reqsEl) highlightSearchTerms(reqsEl, searchTerms);
      } else {
        card.style.display = 'none';
        card.classList.add('is-hidden');
      }
    });

    const allAvailable = getAllAvailableJobs();
    let totalNewInStore = 0;
    let totalStarredInStore = 0;
    let totalSavedInStore = 0;
    let totalRejectedInStore = 0;

    allAvailable.forEach(j => {
      const st = jobStates[j.link] || 'pending';
      const isSt = Boolean(starredJobs[j.link]);
      if (st === 'purged') {
        return;
      }
      if (rawJobLinks.has(j.link) && st !== 'rejected') {
        totalNewInStore++;
      }
      if (isSt && st !== 'rejected') {
        totalStarredInStore++;
      }
      if (st === 'saved' && st !== 'rejected') {
        totalSavedInStore++;
      }
      if (st === 'rejected') {
        totalRejectedInStore++;
      }
    });

    let tabTotal = 0;
    let tabLabel = '';
    let tabNoun = '';
    if (currentFilter === 'saved') {
      tabTotal = totalSavedInStore;
      tabLabel = `סה״כ משרות שנשמרו: ${tabTotal}`;
      tabNoun = 'משרות שנשמרו';
    } else if (currentFilter === 'starred') {
      tabTotal = totalStarredInStore;
      tabLabel = `סה״כ משרות שסומנו בכוכב: ${tabTotal}`;
      tabNoun = 'משרות שסומנו בכוכב';
    } else if (currentFilter === 'rejected') {
      tabTotal = totalRejectedInStore;
      tabLabel = `סה״כ משרות שהוסרו: ${tabTotal}`;
      tabNoun = 'משרות שהוסרו';
    } else {
      tabTotal = totalNewInStore;
      tabLabel = `סה״כ משרות חדשות: ${tabTotal}`;
      tabNoun = 'משרות חדשות';
    }

    const visibleJobsCountEl = document.getElementById('visibleJobsCountText');
    if (visibleJobsCountEl) {
      if (visibleCount === tabTotal) {
        visibleJobsCountEl.textContent = tabLabel;
      } else {
        visibleJobsCountEl.textContent = `מציג ${visibleCount} מתוך סה״כ ${tabTotal} ${tabNoun}`;
      }
    }

    // Update Filter Card Footer Result Summary
    const isFiltered = (selectedSector !== 'all' || (document.getElementById('regionFilter') && document.getElementById('regionFilter').value !== 'all') || searchRaw.length > 0);
    const filterStatusTextEl = document.getElementById('filterStatusText');
    if (filterStatusTextEl) {
      if (isFiltered) {
        filterStatusTextEl.textContent = `נמצאו ${visibleCount} משרות תואמות`;
      } else {
        filterStatusTextEl.textContent = `מוצגות כל ${visibleCount} המשרות הפעילות`;
      }
    }

    // Update Counts in Nav & Stats Cards
    const countAllEl = document.getElementById('countAll');
    const countSavedEl = document.getElementById('countSaved');
    const countRejectedEl = document.getElementById('countRejected');
    const countStarredNavEl = document.getElementById('countStarredNav');
    if (countAllEl) countAllEl.textContent = totalNewInStore;
    if (countSavedEl) countSavedEl.textContent = totalSavedInStore;
    if (countRejectedEl) countRejectedEl.textContent = totalRejectedInStore;
    if (countStarredNavEl) countStarredNavEl.textContent = totalStarredInStore;

    const statNewEl = document.getElementById('statNewCount');
    const statStarredEl = document.getElementById('statStarredCount');
    const statSavedEl = document.getElementById('statSavedCount');
    const statRejectedEl = document.getElementById('statRejectedCount');
    if (statNewEl) statNewEl.textContent = totalNewInStore;
    if (statStarredEl) statStarredEl.textContent = totalStarredInStore;
    if (statSavedEl) statSavedEl.textContent = totalSavedInStore;
    if (statRejectedEl) statRejectedEl.textContent = totalRejectedInStore;

    const summaryNew = document.getElementById('summaryNewCount');
    const summaryStarred = document.getElementById('summaryStarredCount');
    const summarySaved = document.getElementById('summarySavedCount');
    const summaryRejected = document.getElementById('summaryRejectedCount');
    if (summaryNew) summaryNew.textContent = totalNewInStore;
    if (summaryStarred) summaryStarred.textContent = totalStarredInStore;
    if (summarySaved) summarySaved.textContent = totalSavedInStore;
    if (summaryRejected) summaryRejected.textContent = totalRejectedInStore;

    // Ensure Active Cube Highlights Match currentFilter
    const activeCube = document.getElementById('cube_' + currentFilter);
    if (activeCube && !activeCube.classList.contains('active')) {
      document.querySelectorAll('.stat-cube-btn').forEach(b => {
        b.classList.remove('active');
        b.removeAttribute('aria-current');
      });
      activeCube.classList.add('active');
      activeCube.setAttribute('aria-current', 'page');
    }

    // Progress Bar Calculations
    const activeBatchCount = totalNewInStore + totalStarredInStore + totalSavedInStore + totalRejectedInStore;
    const triaged = totalStarredInStore + totalSavedInStore + totalRejectedInStore;
    const pct = activeBatchCount > 0 ? Math.round((triaged / activeBatchCount) * 100) : 0;
    
    const pctTextEl = document.getElementById('progressPctText');
    const summaryChipEl = document.getElementById('progressSummaryChip');
    if (pctTextEl) pctTextEl.textContent = pct + '%';
    if (summaryChipEl) summaryChipEl.textContent = pct + '% מוינו';

    const pNew = activeBatchCount > 0 ? Math.round((totalNewInStore / activeBatchCount) * 100) : 0;
    const pStarred = activeBatchCount > 0 ? Math.round((totalStarredInStore / activeBatchCount) * 100) : 0;
    const pSaved = activeBatchCount > 0 ? Math.round((totalSavedInStore / activeBatchCount) * 100) : 0;
    const pRej = Math.max(0, 100 - pNew - pStarred - pSaved);

    const segNew = document.getElementById('progressSegNew');
    const segStarred = document.getElementById('progressSegStarred');
    const segSaved = document.getElementById('progressSegSaved');
    const segRej = document.getElementById('progressSegRejected');
    if (segNew) segNew.style.width = pNew + '%';
    if (segStarred) segStarred.style.width = pStarred + '%';
    if (segSaved) segSaved.style.width = pSaved + '%';
    if (segRej) segRej.style.width = pRej + '%';

    const lblNew = document.getElementById('pctLabelNew');
    const lblStarred = document.getElementById('pctLabelStarred');
    const lblSaved = document.getElementById('pctLabelSaved');
    const lblRej = document.getElementById('pctLabelRejected');
    if (lblNew) lblNew.textContent = pNew + '% חדשות';
    if (lblStarred) lblStarred.textContent = pStarred + '% כוכב';
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
        if (isFiltered) {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-magnifying-glass"></i>';
          if (titleEl) titleEl.textContent = 'לא נמצאו משרות בהתאם לסינון';
          if (descEl) descEl.innerHTML = 'נסה לבחור אזור אחר, לשנות את מילת החיפוש או <button type="button" onclick="resetAllFilters()" style="background:none;border:none;color:var(--dashboard-cyan);cursor:pointer;text-decoration:underline;font:inherit;padding:0;">לאפס את כל המסננים</button>.';
        } else if (currentFilter === 'rejected') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-trash"></i>';
          if (titleEl) titleEl.textContent = totalRejectedInStore > 0 ? `כל ${totalRejectedInStore} המשרות שהוסרו מנוטרלות לצמיתות` : 'אין כרגע משרות שהוסרו מהסבב';
          if (descEl) descEl.textContent = totalRejectedInStore > 0 ? 'משרות אלו סוננו מחלון ההזדמנויות השבועי ולא ישובו להופיע בדוחות הבאים.' : 'כאשר תסיר משרה מהסבב, היא תופיע כאן.';
        } else if (currentFilter === 'saved') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-bookmark-simple"></i>';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות שמורות מתוך מקבץ זה';
          if (descEl) descEl.textContent = 'לחץ על "שמור להגשה" בכל כרטיס משרה שמעניינת אותך.';
        } else if (currentFilter === 'starred') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות בכוכב';
          if (descEl) descEl.textContent = 'לחץ על סמל הכוכב בפינת כל כרטיס משרה כדי להעביר אותה לכאן.';
        } else {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-sparkle"></i>';
          if (titleEl) titleEl.textContent = 'סיימת לסקור את כל המשרות החדשות!';
          if (descEl) descEl.textContent = 'כל המשרות במקבץ זה כבר מוינו (נשמרו, סומנו בכוכב או הוסרו).';
        }
        emptyState.style.display = 'block';
      } else {
        emptyState.style.display = 'none';
      }
    }

    renderSectorChart();

    if (liveJobsMapInstance || currentViewMode === 'map') {
      updateMapMarkers();
    }
  }

  let sectorChartInstance = null;
  function renderSectorChart() {
    try {
      const canvas = document.getElementById('sectorChart');
      if (!canvas || typeof Chart === 'undefined') return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const allAvailableJobs = getAllAvailableJobs();
      const rawJobLinks = new Set((rawJobsData || []).map(j => j.link));

      let sourceJobs = [];
      const chartTitleEl = document.getElementById('chartTitle');
      const chartChipEl = document.getElementById('chartChip');

      if (currentFilter === 'saved') {
        sourceJobs = allAvailableJobs.filter(j => jobStates[j.link] === 'saved' && jobStates[j.link] !== 'rejected' && jobStates[j.link] !== 'purged');
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות שמורות';
        if (chartChipEl) {
          chartChipEl.innerHTML = `<i class="ph-duotone ph-bookmark-simple"></i> ${sourceJobs.length} שמורות`;
          chartChipEl.style.color = 'var(--dashboard-lime)';
          chartChipEl.style.borderColor = 'rgba(220, 255, 114, 0.4)';
        }
      } else if (currentFilter === 'starred') {
        sourceJobs = allAvailableJobs.filter(j => Boolean(starredJobs[j.link]) && jobStates[j.link] !== 'rejected' && jobStates[j.link] !== 'purged');
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות בכוכב';
        if (chartChipEl) {
          chartChipEl.innerHTML = `<i class="ph-fill ph-star"></i> ${sourceJobs.length} בכוכב`;
          chartChipEl.style.color = 'var(--dashboard-gold)';
          chartChipEl.style.borderColor = 'rgba(255, 211, 104, 0.4)';
        }
      } else if (currentFilter === 'rejected') {
        sourceJobs = allAvailableJobs.filter(j => jobStates[j.link] === 'rejected');
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות שהוסרו';
        if (chartChipEl) {
          chartChipEl.innerHTML = `<i class="ph-duotone ph-trash"></i> ${sourceJobs.length} הוסרו`;
          chartChipEl.style.color = '#fca5a5';
          chartChipEl.style.borderColor = 'rgba(252, 165, 165, 0.4)';
        }
      } else {
        // Default / All: active jobs from current scan
        sourceJobs = (allAvailableJobs || []).filter(j => {
          const st = jobStates[j.link] || 'pending';
          return rawJobLinks.has(j.link) && st !== 'rejected' && st !== 'purged';
        });
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות חדשות';
        if (chartChipEl) {
          if (sourceJobs.length === 0) {
            chartChipEl.innerHTML = '<i class="ph-duotone ph-chart-bar"></i> 0 משרות';
          } else {
            chartChipEl.innerHTML = `<i class="ph-duotone ph-chart-bar"></i> חדשות (${sourceJobs.length})`;
          }
          chartChipEl.style.color = 'var(--dashboard-cyan)';
          chartChipEl.style.borderColor = 'rgba(137, 244, 231, 0.35)';
        }
      }

      const counts = {};
      sourceJobs.forEach(job => {
        const label = classifyJobSector(job);
        counts[label] = (counts[label] || 0) + 1;
      });

      if (Object.keys(counts).length === 0) {
        ['סולאר', 'רחפנים', 'תפעול ואחזקה', 'בקרה ו-SCADA', 'גז טבעי', 'אגירה'].forEach(s => {
          counts[s] = 0;
        });
      }

      if (sectorChartInstance) {
        sectorChartInstance.destroy();
        sectorChartInstance = null;
      }

      const labels = Object.keys(counts);
      const data = Object.values(counts);

      const colorMap = {
        'סולאר': '#ffd368',
        'בקרה ו-SCADA': '#89f4e7',
        'רחפנים': '#dcff72',
        'תפעול ואחזקה': '#b4fcf1',
        'אגירה': '#a0c03e',
        'גז טבעי': '#fca5a5',
        'אנרגיה': '#38bdf8',
        'אין משרות להצגה': '#c0c5be'
      };

      const barColors = labels.map(l => colorMap[l] || '#89f4e7');

      sectorChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: barColors,
            borderRadius: 8,
            borderSkipped: false,
            maxBarThickness: 32
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 350
          },
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
              textDirection: 'rtl',
              callbacks: {
                label: function(ctx) {
                  return ` ${ctx.raw} משרות`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              suggestedMax: 5,
              ticks: { stepSize: 1, color: '#c0c5be', font: { family: 'Google Sans', size: 11 } },
              grid: { color: 'rgba(255, 255, 255, 0.08)' }
            },
            x: {
              ticks: { color: '#c0c5be', font: { family: 'Google Sans', size: 10 } },
              grid: { display: false }
            }
          }
        }
      });
    } catch(e) {
      console.warn('renderSectorChart error:', e);
    }
  }

  function showToast(icon, msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    const iconEl = document.getElementById('toastIcon');
    if (iconEl) {
      if (typeof icon === 'string' && icon.startsWith('ph-')) {
        iconEl.innerHTML = `<i class="ph-duotone ${icon}"></i>`;
      } else {
        iconEl.innerHTML = icon;
      }
    }
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

  let aboutModalPrevFocus = null;
  function openAboutModal() {
    aboutModalPrevFocus = document.activeElement;
    const modal = document.getElementById('aboutModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    const closeBtn = modal.querySelector('.modal-close-btn');
    if (closeBtn) closeBtn.focus();
  }

  function closeAboutModal() {
    const modal = document.getElementById('aboutModal');
    if (!modal) return;
    modal.classList.add('hidden');
    if (aboutModalPrevFocus && typeof aboutModalPrevFocus.focus === 'function') {
      aboutModalPrevFocus.focus();
    }
  }

  function toggleMetricsExpand() {
    const content = document.getElementById('collapsibleMetricsContent');
    const btn = document.getElementById('metricsToggleBtn');
    const label = document.getElementById('metricsToggleText');
    const icon = document.getElementById('metricsToggleIcon');
    if (!content) return;
    const isExpanded = content.classList.toggle('is-expanded');
    if (btn) btn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
    if (label) label.textContent = isExpanded ? 'צמצם' : 'פירוט';
    if (icon) {
      icon.className = isExpanded ? 'ph-bold ph-caret-up' : 'ph-bold ph-caret-down';
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeAboutModal();
        closeSyncModal();
        closeDuplicatesModal();
        if (typeof closeJobModal === 'function') closeJobModal();
      }
    });
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
    showToast('ph-cloud-check', `כל הסימונים סונכרנו לענן בהצלחה! (${savedList.length} שמורות, ${rejectedList.length} הוסרו)`);
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

    const allJobs = getAllAvailableJobs();

    const activeJobs = allJobs.filter(job => {
      const state = jobStates[job.link] || 'pending';
      return state === 'saved' || state === 'pending';
    });

    const groups = {};
    
    function extractJobId(link) {
      if (!link) return null;
      const drushimMatch = link.match(/\\/job\\/(\\d+)\\//);
      if (drushimMatch) return 'drushim-' + drushimMatch[1];
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
          <div style="font-size: 40px; margin-bottom: 12px; color: var(--dashboard-lime);"><i class="ph-duotone ph-check-circle"></i></div>
          <div style="font-weight: 700; color: var(--dashboard-lime); font-size: 16px;">לא נמצאו כפילויות!</div>
          <div style="color: var(--dashboard-muted); font-size: 13px; margin-top: 6px;">כל ${activeJobs.length} המשרות הפעילות (שמורות וחדשות) ייחודיות לחלוטין.</div>
        </div>`;
    } else {
      const totalDups = dupGroups.reduce((sum, [k, g]) => sum + g.length - 1, 0);
      let html = `
        <div style="background: rgba(255, 211, 104, 0.12); border: 1px solid rgba(255, 211, 104, 0.35); border-radius: 16px; padding: 12px 16px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
          <div style="display: flex; align-items: center; gap: 8px; font-size: 13px;">
            <span style="font-size: 18px; color: var(--dashboard-gold);"><i class="ph-duotone ph-warning"></i></span>
            <span style="color: var(--dashboard-gold); font-weight: 600;">אותרו <strong>${dupGroups.length}</strong> קבוצות עם <strong>${totalDups}</strong> כפילויות</span>
          </div>
        </div>`;

      dupGroups.forEach(([key, group], gi) => {
        const rep = group[0];
        const safeComp = escapeHtml(rep.company || '—');
        const safeTitle = escapeHtml(rep.title || '—');
        const encKey = encodeURIComponent(key);
        html += `
          <div style="background: rgba(0, 0, 0, 0.28); border: 1px solid var(--dashboard-edge); border-radius: 18px; padding: 14px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px;">
                <span class="dashboard-chip" style="font-size: 11px; padding: 2px 8px;">#${gi + 1}</span>
                <span style="color: #fff;">${safeComp} — ${safeTitle}</span>
                <span class="dashboard-chip" style="color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); font-size: 11px; padding: 2px 8px;">${group.length} מופעים</span>
              </div>
              <button onclick="purgeDuplicateGroup('${encKey}')" class="tool-btn" style="min-height: 36px; padding: 6px 14px; font-size: 12px; color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4);" title="שמור מופע אחד ומחק את שאר הכפילויות">
                <i class="ph-duotone ph-lightning"></i> השאר אחת
              </button>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;">`;

        group.forEach((job, ji) => {
          const score = job.match_score || '—';
          const date = escapeHtml(job.date || '—');
          const link = job.link || '#';
          const safeLink = sanitizeUrl(link);
          const encLink = encodeURIComponent(link);
          const state = jobStates[job.link] || 'pending';
          const isSaved = state === 'saved';
          const statusBadge = isSaved
            ? `<span class="dashboard-chip" style="color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); font-size: 11px; padding: 2px 8px;"><i class="ph-duotone ph-bookmark-simple"></i> שמורה</span>`
            : `<span class="dashboard-chip" style="color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.4); font-size: 11px; padding: 2px 8px;"><i class="ph-duotone ph-sparkle"></i> חדשה</span>`;

          html += `
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 10px 14px; gap: 10px;">
              <div style="display: flex; align-items: center; gap: 8px; font-size: 13px;">
                <span style="font-size: 11px; color: var(--dashboard-muted);">#${ji + 1}</span>
                ${statusBadge}
                <span style="font-weight: 700; color: var(--dashboard-lime);">${score}%</span>
                <span style="color: var(--dashboard-muted); font-size: 12px;">${date}</span>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <a href="${safeLink}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); font-weight: 600; font-size: 13px; text-decoration: underline; text-underline-offset: 3px; display: inline-flex; align-items: center; gap: 4px;">
                  פתח <i class="ph-duotone ph-arrow-up-right"></i>
                </a>
                <button onclick="purgeSingleJob('${encLink}')" class="btn-triage" style="min-height: 32px; padding: 4px 10px; font-size: 14px; background: rgba(239, 68, 68, 0.2); color: #fca5a5; border-color: rgba(239, 68, 68, 0.4);" title="מחק כפילות זו">
                  <i class="ph-duotone ph-trash"></i>
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
    showToast('ph-trash', 'הכפילות נמחקה בהצלחה');
    openDuplicatesModal();
  }

  function purgeDuplicateGroup(encKey) {
    const targetKey = decodeURIComponent(encKey);
    function normalize(str) {
      if (!str) return '';
      return str.toLowerCase().replace(/[^א-תa-z0-9]/g, ' ').replace(/  +/g, ' ').trim();
    }

    const allJobs = getAllAvailableJobs();

    function extractJobId(link) {
      if (!link) return null;
      const drushimMatch = link.match(/\\/job\\/(\\d+)\\//);
      if (drushimMatch) return 'drushim-' + drushimMatch[1];
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
    showToast('ph-lightning', `הושארה משרה אחת ונמחקו ${toPurge.length} כפילויות`);
    openDuplicatesModal();
  }

  function closeDuplicatesModal() {
    document.getElementById('duplicatesModal').classList.add('hidden');
  }

  function clearAllRejected() {
    const rejectedKeys = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
    if (rejectedKeys.length === 0) {
      showToast('ph-info', 'אין משרות מוסרות למחיקה');
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
    showToast('ph-trash', `כל ${rejectedKeys.length} המשרות שהוסרו נמחקו לצמיתות והמונה אופס ל-0`);
  }

  function exportSavedToExcel() {
    const allPotentialSaved = getAllAvailableJobs();
    const savedJobs = allPotentialSaved.filter(job => jobStates[job.link] === 'saved');
    if (savedJobs.length === 0) {
      showToast('ph-warning', 'לא נמצאו משרות שמורות לייצוא');
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

    showToast('ph-file-xls', `יוצאו ${savedJobs.length} משרות שמורות לאקסל בהצלחה!`);
  }

  window.onload = () => {
    checkUrlSync();
    updateSortIconAndToast(currentSort, false);
    renderCards();
    setViewMode(currentViewMode);
    fetchCloudSync();

    const hash = window.location.hash.replace('#', '');
    if (hash === 'saved' || hash === 'rejected' || hash === 'starred') {
      const cubeEl = document.getElementById('cube_' + hash);
      setFilter(hash, cubeEl);
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

  window.addEventListener('scroll', () => {
    const btn = document.getElementById('btnBackToTop');
    if (!btn) return;
    if (window.scrollY > 380) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }, { passive: true });
</script>
</body>
</html>"""

def generate_interactive_html(jobs, rejected_links, title="דוח משרות אינטראקטיבי | עידו גל", is_weekly=False):
    saved_links = []
    try:
        import requests
        r = requests.get("https://job-finder-auto-default-rtdb.firebaseio.com/triage.json", timeout=3)
        if r.status_code == 200:
            cdata = r.json()
            if cdata and isinstance(cdata.get("saved"), list):
                raw_s = cdata["saved"]
                saved_links = [s for s in raw_s if not (s.isdigit() and any(x != s and s in x for x in raw_s))]
    except Exception:
        pass
    
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
    def _strip_emojis_recursive(obj):
        if isinstance(obj, dict):
            return {k: _strip_emojis_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_strip_emojis_recursive(x) for x in obj]
        elif isinstance(obj, str):
            return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf]', '', obj)
        return obj

    def _safe_json_embed(obj):
        clean_obj = _strip_emojis_recursive(obj)
        return json.dumps(clean_obj, ensure_ascii=False).replace("</", "<\\/")

    jobs_json = _safe_json_embed(sorted_jobs)
    catalog_json = _safe_json_embed(catalog_data)
    saved_json = _safe_json_embed(list(saved_links) if isinstance(saved_links, (set, list)) else [])
    rejected_json = _safe_json_embed(list(rejected_links) if isinstance(rejected_links, (set, list)) else [])

    total_new = len(jobs)
    total_saved = len(saved_links) if isinstance(saved_links, (list, set)) else 0
    total_rejected = len(rejected_links) if isinstance(rejected_links, (list, set)) else 0
    total_starred = 0

    html = HTML_TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace("__REPORT_TYPE_LABEL__", report_type_label)
    html = html.replace("__NOW_STR__", now_str)
    html = html.replace("__TOTAL_JOBS__", str(total_new))
    html = html.replace("__TOTAL_NEW_JOBS__", str(total_new))
    html = html.replace("__TOTAL_SAVED_JOBS__", str(total_saved))
    html = html.replace("__TOTAL_STARRED_JOBS__", str(total_starred))
    html = html.replace("__TOTAL_REJECTED_JOBS__", str(total_rejected))
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
            
    save_state_atomic(archive_file_path, archive)

    try:
        # Retention policy: prune historical catalog to max 1500 items if needed, preserving newest
        if len(catalog) > 1500:
            sorted_items = sorted(catalog.items(), key=lambda kv: kv[1].get("date", ""), reverse=True)
            catalog = dict(sorted_items[:1500])
        save_state_atomic(catalog_path, catalog)
    except Exception as e:
        print(f"[WARN] Failed to atomically save historical catalog: {e}")

    return archive
