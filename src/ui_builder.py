import os
import json
from datetime import datetime, timedelta

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>__TITLE__</title>
  <link rel="stylesheet" href="fonts.css">
  <link rel="stylesheet" href="theme.css">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/duotone/style.css">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/bold/style.css">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css">
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
    .quick-chip i[class^="ph-"],
    .quick-chip i[class*=" ph-"],
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

    /* Header Progress & Navigation Hub */
    .header-progress-hub {
      display: flex;
      align-items: center;
      gap: 16px;
      flex: 1;
      justify-content: center;
      max-width: 840px;
    }
    .header-progress-info {
      display: flex;
      flex-direction: column;
      gap: 3px;
      min-width: 190px;
      max-width: 260px;
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
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      flex-shrink: 0;
    }
    .stat-cube-btn {
      background: rgba(0, 0, 0, 0.28);
      border: 1px solid var(--dashboard-edge);
      border-radius: 18px;
      padding: 8px 10px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 2px;
      cursor: pointer;
      min-width: 82px;
      color: var(--dashboard-text);
      text-decoration: none;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.08);
      position: relative;
    }
    .stat-cube-btn:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.35);
      transform: translateY(-2px);
    }
    .stat-cube-btn.active {
      background: linear-gradient(145deg, rgba(220, 255, 114, 0.18), rgba(255, 255, 255, 0.06));
      border-color: var(--dashboard-lime);
      box-shadow: 0 4px 18px rgba(220, 255, 114, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2);
    }
    .stat-cube-btn.active.cube-starred {
      background: linear-gradient(145deg, rgba(251, 191, 36, 0.2), rgba(255, 255, 255, 0.06));
      border-color: var(--dashboard-gold);
      box-shadow: 0 4px 18px rgba(251, 191, 36, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2);
    }
    .stat-cube-btn.active.cube-saved {
      background: linear-gradient(145deg, rgba(137, 244, 231, 0.2), rgba(255, 255, 255, 0.06));
      border-color: var(--dashboard-cyan);
      box-shadow: 0 4px 18px rgba(137, 244, 231, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2);
    }
    .stat-cube-btn.active.cube-rejected {
      background: linear-gradient(145deg, rgba(248, 113, 113, 0.18), rgba(255, 255, 255, 0.06));
      border-color: #fca5a5;
      box-shadow: 0 4px 18px rgba(239, 68, 68, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.2);
    }
    .stat-cube-icon {
      width: 32px;
      height: 32px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 2px;
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.4);
    }
    .stat-cube-icon.lime { background: var(--dashboard-lime); color: #171c12; }
    .stat-cube-icon.gold { background: var(--dashboard-gold); color: #171c12; }
    .stat-cube-icon.cyan { background: var(--dashboard-cyan); color: #171c12; }
    .stat-cube-icon.rose { background: #fca5a5; color: #171c12; }
    .stat-cube-count {
      font-size: 17px;
      font-weight: 700;
      color: #fff;
      line-height: 1.1;
    }
    .stat-cube-label {
      font-size: 11px;
      font-weight: 500;
      color: var(--dashboard-muted);
      white-space: nowrap;
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
    #cardsContainer {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(370px, 1fr));
      gap: 22px;
      margin-bottom: 28px;
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
      gap: 15px;
      border-radius: 26px;
      padding: 22px;
      transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
      position: relative;
      background: var(--dashboard-glass);
      border: 1px solid var(--dashboard-edge);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22);
      height: 100%;
      box-sizing: border-box;
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
    .job-card-topbar-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
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
    .job-company-name {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--dashboard-cyan);
      margin-bottom: 2px;
      letter-spacing: 0.2px;
      overflow-wrap: anywhere;
    }
    .job-title-text {
      font-size: 17.5px;
      font-weight: 600;
      color: #ffffff;
      margin: 0 0 8px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .job-header-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }

    /* One-Tap Quick Filter Chips */
    .quick-filter-strip-wrapper {
      margin-bottom: 20px;
      overflow-x: visible;
      padding-bottom: 0;
    }
    .quick-filter-strip {
      display: flex;
      gap: 5px;
      align-items: center;
      flex-wrap: wrap;
      width: 100%;
    }
    .quick-chip {
      min-height: 30px !important;
      padding: 5px 12px !important;
      border-radius: 999px !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      line-height: 1.2 !important;
      cursor: pointer;
      border: 1px solid var(--dashboard-edge) !important;
      background: linear-gradient(160deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
      color: var(--dashboard-text) !important;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
      transition: all 0.2s ease;
    }
    .quick-chip:hover {
      background: rgba(255, 255, 255, 0.18);
      border-color: rgba(255, 255, 255, 0.35);
    }
    .quick-chip.active {
      background: var(--dashboard-lime) !important;
      color: #11150e !important;
      border-color: var(--dashboard-lime) !important;
      box-shadow: 0 4px 16px rgba(220, 255, 114, 0.3);
      font-weight: 700;
    }
    .quick-chip.active i {
      color: #11150e !important;
    }

    /* Explainable AI & Score Drivers */
    .ai-score-drivers {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      margin: 4px 0 10px;
    }
    .drivers-label {
      font-size: 12px;
      color: var(--dashboard-muted);
      display: inline-flex;
      align-items: center;
      gap: 5px;
      margin-inline-end: 4px;
    }
    .driver-chip {
      font-size: 11px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      border: 1px solid var(--dashboard-edge);
    }
    .driver-chip.lime {
      background: rgba(220, 255, 114, 0.12);
      color: var(--dashboard-lime);
      border-color: rgba(220, 255, 114, 0.35);
    }
    .driver-chip.cyan {
      background: rgba(137, 244, 231, 0.12);
      color: var(--dashboard-cyan);
      border-color: rgba(137, 244, 231, 0.35);
    }
    .driver-chip.gold {
      background: rgba(255, 211, 104, 0.12);
      color: var(--dashboard-gold);
      border-color: rgba(255, 211, 104, 0.35);
    }

    /* Progressive Disclosure & Quick Summary */
    .job-quick-summary {
      background: rgba(137, 244, 231, 0.05);
      border: 1px solid rgba(137, 244, 231, 0.22);
      border-radius: 16px;
      padding: 12px 16px;
      font-size: 14px;
      line-height: 1.55;
      color: var(--dashboard-text);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .quick-summary-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--dashboard-cyan);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .quick-summary-text {
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
    .dashboard-app a.btn-apply,
    .dashboard-app a.btn-apply span,
    .btn-apply,
    .btn-apply span {
      color: #000000 !important;
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
      background: var(--dashboard-lime);
      color: #000000 !important;
      border: 1px solid #ebffab99;
      box-shadow: inset 0 1px 2px #ffffff80, 0 4px 18px rgba(164, 203, 46, 0.28);
      transition: background 0.2s ease;
    }
    .dashboard-app a.btn-apply:hover,
    .dashboard-app a.btn-apply:hover span,
    .btn-apply:hover,
    .btn-apply:hover span {
      background: #e7ff9c;
      color: #000000 !important;
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

    /* Responsive Media Queries (Mobile & iPhone First) */
    @media (max-width: 768px) {
      body, html {
        overflow-x: hidden;
      }
      .dashboard-app {
        padding: 14px 12px 24px;
        overflow-x: hidden;
      }
      .dashboard-sidebar {
        border-radius: 24px;
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        padding: 14px 12px;
      }
      .dashboard-sidebar-brand {
        justify-content: space-between;
        width: 100%;
      }
      .header-progress-hub {
        flex-direction: column;
        width: 100%;
        gap: 10px;
      }
      .header-progress-info {
        width: 100%;
        max-width: 100%;
      }

      /* Compact 4 Header Stat Cubes on iPhone */
      .header-stat-cubes {
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 6px !important;
        padding: 2px 0 !important;
        width: 100% !important;
      }
      .stat-cube-btn {
        min-width: 0 !important;
        padding: 8px 3px !important;
        border-radius: 16px !important;
        height: auto !important;
      }
      .stat-cube-icon {
        width: 22px !important;
        height: 22px !important;
        border-radius: 8px !important;
        margin-bottom: 2px !important;
        font-size: 12px !important;
      }
      .stat-cube-icon i {
        font-size: 12px !important;
      }
      .stat-cube-count {
        font-size: 1.1rem !important;
        line-height: 1.1 !important;
        margin: 2px 0 !important;
        font-weight: 700 !important;
      }
      .stat-cube-label {
        font-size: 0.62rem !important;
        line-height: 1.15 !important;
        white-space: normal !important;
        letter-spacing: -0.2px !important;
        word-break: break-word !important;
      }

      .header-actions-group {
        justify-content: space-between;
        width: 100%;
      }
      .dashboard-topbar {
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
        padding: 0 4px 10px;
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
        padding: 10px 14px 12px !important;
        border-radius: 18px !important;
      }
      .dashboard-stats-grid > .dashboard-card:first-child p {
        display: none !important; /* Hide descriptive paragraph */
      }
      .dashboard-stats-grid > .dashboard-card:first-child > div:first-child {
        display: none !important; /* Hide decorative header tags */
      }
      .dashboard-stats-grid > .dashboard-card:first-child h3 {
        font-size: 14.5px !important;
        margin: 0 0 8px !important;
        color: #ffffff !important;
      }
      .controls-inputs-stack {
        gap: 6px !important;
      }
      .controls-inputs-stack input,
      .controls-inputs-stack select {
        padding: 6px 10px !important;
        font-size: 12.5px !important;
        min-height: 36px !important;
        border-radius: 10px !important;
      }
      .controls-buttons-row {
        gap: 6px !important;
      }
      .controls-buttons-row .tool-btn {
        min-height: 34px !important;
        padding: 5px 10px !important;
        font-size: 11.5px !important;
        border-radius: 10px !important;
      }

      /* 2 Cubes Per Row in Grid Mode on iPhone (Symmetrical, Proportional, No Crammed Words) */
      #cardsContainer:not(.view-list) {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 10px !important;
        margin-bottom: 22px !important;
      }
      #cardsContainer:not(.view-list) .job-card {
        height: 198px !important;
        box-sizing: border-box !important;
        padding: 12px 10px !important;
        border-radius: 20px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        align-items: stretch !important;
        background: rgba(18, 24, 38, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
        cursor: pointer !important;
        position: relative !important;
        overflow: hidden !important;
        transition: transform 0.15s ease, border-color 0.15s ease !important;
      }
      #cardsContainer:not(.view-list) .job-card:active {
        transform: scale(0.97) !important;
        border-color: var(--dashboard-cyan) !important;
      }
      #cardsContainer:not(.view-list) .job-quick-summary,
      #cardsContainer:not(.view-list) .btn-toggle-details,
      #cardsContainer:not(.view-list) .job-details-collapsible,
      #cardsContainer:not(.view-list) .job-actions-bar,
      #cardsContainer:not(.view-list) .ai-score-drivers,
      #cardsContainer:not(.view-list) .job-card-topbar-meta {
        display: none !important;
      }
      #cardsContainer:not(.view-list) .job-card-topbar {
        border-bottom: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        display: flex !important;
      }
      #cardsContainer:not(.view-list) .job-card-topbar-primary {
        width: 100% !important;
        display: flex !important;
        flex-direction: row-reverse !important;
        justify-content: space-between !important;
        align-items: center !important;
      }
      #cardsContainer:not(.view-list) .job-card-topbar-primary > div:first-child .dashboard-chip {
        display: none !important;
      }
      #cardsContainer:not(.view-list) .badge-score {
        font-size: 0 !important;
        padding: 0 8px !important;
        height: 24px !important;
        box-sizing: border-box !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
        box-shadow: none !important;
      }
      #cardsContainer:not(.view-list) .badge-score span {
        font-size: 11px !important;
        font-weight: 700 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 3px !important;
        letter-spacing: -0.2px !important;
      }
      #cardsContainer:not(.view-list) .btn-star {
        width: 24px !important;
        height: 24px !important;
        font-size: 13px !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: var(--dashboard-muted) !important;
        transition: all 0.15s ease !important;
      }
      #cardsContainer:not(.view-list) .btn-star.is-starred {
        background: rgba(255, 211, 104, 0.2) !important;
        border-color: rgba(255, 211, 104, 0.5) !important;
        color: var(--dashboard-gold) !important;
      }
      #cardsContainer:not(.view-list) .job-card-main-header {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        gap: 5px !important;
        width: 100% !important;
        margin: auto 0 !important;
        flex: 1 !important;
        justify-content: center !important;
      }
      #cardsContainer:not(.view-list) .job-company-logo {
        width: 40px !important;
        height: 40px !important;
        border-radius: 12px !important;
        margin: 0 auto !important;
        flex-shrink: 0 !important;
        background: #191e28 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3) !important;
      }
      #cardsContainer:not(.view-list) .job-company-avatar {
        font-size: 14px !important;
        font-weight: 700 !important;
      }
      #cardsContainer:not(.view-list) .job-header-text {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        gap: 2px !important;
      }
      #cardsContainer:not(.view-list) .job-company-name {
        font-size: 11px !important;
        color: var(--dashboard-cyan) !important;
        font-weight: 500 !important;
        max-width: 145px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        text-align: center !important;
        margin: 0 !important;
        line-height: 1.2 !important;
      }
      #cardsContainer:not(.view-list) .job-title-text {
        font-size: 12.5px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        line-height: 1.3 !important;
        height: 33px !important;
        max-height: 33px !important;
        display: -webkit-box !important;
        -webkit-line-clamp: 2 !important;
        -webkit-box-orient: vertical !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        text-align: center !important;
        margin: 0 !important;
        letter-spacing: -0.2px !important;
      }
      #cardsContainer:not(.view-list) .job-header-chips {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin-top: auto !important;
        margin-bottom: 0 !important;
        gap: 0 !important;
      }
      #cardsContainer:not(.view-list) .job-header-chips .dashboard-chip {
        display: none !important;
      }
      #cardsContainer:not(.view-list) .job-header-chips .dashboard-chip:first-child {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        font-size: 10px !important;
        padding: 3px 8px !important;
        border-radius: 999px !important;
        max-width: 145px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        color: var(--dashboard-muted) !important;
        line-height: 1 !important;
      }

      /* Proportional & Symmetrical Mobile List View on iPhone */
      #cardsContainer.view-list {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        margin-bottom: 22px !important;
      }
      #cardsContainer.view-list .job-card {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        height: 72px !important;
        box-sizing: border-box !important;
        padding: 10px 12px !important;
        border-radius: 16px !important;
        background: rgba(18, 24, 38, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25) !important;
        gap: 10px !important;
        cursor: pointer !important;
        transition: background 0.15s ease, transform 0.15s ease !important;
      }
      #cardsContainer.view-list .job-card:active {
        background: rgba(255, 255, 255, 0.06) !important;
        transform: scale(0.99) !important;
      }
      #cardsContainer.view-list .job-quick-summary,
      #cardsContainer.view-list .btn-toggle-details,
      #cardsContainer.view-list .job-details-collapsible,
      #cardsContainer.view-list .job-actions-bar,
      #cardsContainer.view-list .ai-score-drivers,
      #cardsContainer.view-list .job-card-topbar-meta,
      #cardsContainer.view-list .job-header-chips {
        display: none !important;
      }
      #cardsContainer.view-list .job-card-main-header {
        order: 1 !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        flex: 1 !important;
        min-width: 0 !important;
        margin: 0 !important;
      }
      #cardsContainer.view-list .job-company-logo {
        width: 42px !important;
        height: 42px !important;
        border-radius: 12px !important;
        flex-shrink: 0 !important;
        margin: 0 !important;
        background: #191e28 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
      }
      #cardsContainer.view-list .job-company-avatar {
        font-size: 15px !important;
        font-weight: 700 !important;
      }
      #cardsContainer.view-list .job-header-text {
        flex: 1 !important;
        min-width: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        gap: 3px !important;
      }
      #cardsContainer.view-list .job-title-text {
        font-size: 13.5px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        line-height: 1.25 !important;
        margin: 0 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        letter-spacing: -0.2px !important;
      }
      #cardsContainer.view-list .job-company-name {
        font-size: 11.5px !important;
        color: var(--dashboard-cyan) !important;
        margin: 0 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        font-weight: 500 !important;
      }
      #cardsContainer.view-list .job-card-topbar {
        order: 2 !important;
        display: flex !important;
        flex-direction: row-reverse !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 6px !important;
        border-bottom: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: auto !important;
        flex-shrink: 0 !important;
      }
      #cardsContainer.view-list .job-card-topbar-primary {
        display: flex !important;
        flex-direction: row-reverse !important;
        align-items: center !important;
        gap: 6px !important;
        width: auto !important;
      }
      #cardsContainer.view-list .job-card-topbar-primary > div:first-child .dashboard-chip {
        display: none !important;
      }
      #cardsContainer.view-list .badge-score {
        font-size: 0 !important;
        padding: 0 8px !important;
        border-radius: 999px !important;
        line-height: 1 !important;
        height: 24px !important;
        box-sizing: border-box !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
      }
      #cardsContainer.view-list .badge-score span {
        font-size: 11px !important;
        font-weight: 700 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 3px !important;
        letter-spacing: -0.2px !important;
      }
      #cardsContainer.view-list .btn-star {
        width: 26px !important;
        height: 26px !important;
        font-size: 13px !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: var(--dashboard-muted) !important;
      }
      #cardsContainer.view-list .btn-star.is-starred {
        background: rgba(255, 211, 104, 0.2) !important;
        border-color: rgba(255, 211, 104, 0.5) !important;
        color: var(--dashboard-gold) !important;
      }

      /* Force hidden state over all grid and list rules on iPhone */
      #cardsContainer:not(.view-list) .job-card.is-hidden,
      #cardsContainer.view-list .job-card.is-hidden,
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
      .quick-filter-strip-wrapper {
        margin: 0 -12px 14px;
        padding: 0 12px;
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
      #cardsContainer:not(.view-list) {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 10px !important;
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

    /* Star Button & Starred Card Highlight */
    .btn-star {
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
      font-size: 17px;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      flex-shrink: 0;
      position: relative;
    }
    .btn-star::after {
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
      background: var(--dashboard-lime);
      color: #11150e;
      box-shadow: 0 2px 10px rgba(220, 255, 114, 0.25);
    }
    .view-toggle-btn.active i {
      color: #11150e !important;
    }

    /* Proportional & Professional List View Mode */
    #cardsContainer.view-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    #cardsContainer.view-list .job-card {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 240px;
      grid-template-areas:
        "topbar  actions"
        "header  actions"
        "summary actions"
        "toggle  toggle"
        "details details";
      column-gap: 24px;
      row-gap: 12px;
      align-items: center;
      padding: 18px 22px;
      border-radius: 20px;
      background: rgba(17, 24, 39, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22);
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
      height: auto;
      box-sizing: border-box;
    }
    #cardsContainer.view-list .job-card:hover {
      transform: translateX(-4px);
      border-color: rgba(255, 255, 255, 0.3);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }
    #cardsContainer.view-list .job-card-topbar {
      grid-area: topbar;
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      width: 100%;
      flex-wrap: wrap;
    }
    #cardsContainer.view-list .job-card-topbar-primary {
      display: flex;
      align-items: center;
      gap: 10px;
      width: auto;
    }
    #cardsContainer.view-list .job-card-topbar-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-inline-start: auto;
    }
    #cardsContainer.view-list .job-card-main-header {
      grid-area: header;
      display: flex;
      align-items: flex-start;
      gap: 16px;
      margin: 2px 0;
      width: 100%;
    }
    #cardsContainer.view-list .job-company-logo {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      flex-shrink: 0;
      margin-top: 2px;
    }
    #cardsContainer.view-list .job-header-text {
      flex: 1;
      min-width: 0;
    }
    #cardsContainer.view-list .job-company-name {
      font-size: 13px;
      font-weight: 700;
      color: var(--dashboard-cyan);
      margin-bottom: 2px;
    }
    #cardsContainer.view-list .job-title-text {
      font-size: 17.5px;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.3;
      margin: 0 0 6px;
    }
    #cardsContainer.view-list .job-header-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      margin-bottom: 2px;
    }
    #cardsContainer.view-list .ai-score-drivers {
      margin: 4px 0 0;
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      align-items: center;
    }
    #cardsContainer.view-list .job-quick-summary {
      grid-area: summary;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 12px;
      padding: 9px 14px;
      font-size: 13px;
      line-height: 1.5;
      display: flex;
      flex-direction: row;
      align-items: baseline;
      gap: 8px;
      width: 100%;
      box-sizing: border-box;
    }
    #cardsContainer.view-list .quick-summary-label {
      font-size: 12px;
      font-weight: 700;
      color: var(--dashboard-cyan);
      white-space: nowrap;
      flex-shrink: 0;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    #cardsContainer.view-list .quick-summary-text {
      color: #cbd5e1;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }
    #cardsContainer.view-list .job-actions-bar {
      grid-area: actions;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: stretch;
      gap: 10px;
      border-top: none;
      border-inline-start: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 0;
      margin-top: 0;
      padding-inline-start: 22px;
      height: 100%;
      box-sizing: border-box;
      width: 100%;
    }
    #cardsContainer.view-list .btn-apply {
      width: 100%;
      min-height: 42px;
      padding: 9px 14px;
      font-size: 13.5px;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(220, 255, 114, 0.22);
      order: 1;
    }
    #cardsContainer.view-list .action-btn-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      width: 100%;
      order: 2;
    }
    #cardsContainer.view-list .btn-triage {
      min-height: 36px;
      padding: 6px 8px;
      font-size: 11.5px;
      border-radius: 10px;
    }
    #cardsContainer.view-list .btn-toggle-details {
      grid-area: toggle;
      grid-column: 1 / -1;
      min-height: 32px;
      padding: 6px 14px;
      font-size: 12px;
      border-radius: 10px;
      margin-top: 2px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px dashed rgba(255, 255, 255, 0.12);
      width: 100%;
      box-sizing: border-box;
    }
    #cardsContainer.view-list .btn-toggle-details:hover {
      background: rgba(137, 244, 231, 0.06);
      border-color: rgba(137, 244, 231, 0.3);
    }
    #cardsContainer.view-list .job-details-collapsible {
      grid-area: details;
      grid-column: 1 / -1;
      width: 100%;
    }
    #cardsContainer.view-list .job-boxes-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    #cardsContainer.view-list .job-box {
      padding: 12px 16px;
      font-size: 13.5px;
      border-radius: 14px;
    }

    @media (min-width: 769px) and (max-width: 860px) {
      #cardsContainer.view-list .job-card {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px;
      }
      #cardsContainer.view-list .job-card-topbar {
        flex-direction: column;
        align-items: stretch;
      }
      #cardsContainer.view-list .job-card-topbar-primary {
        justify-content: space-between;
        width: 100%;
      }
      #cardsContainer.view-list .job-card-topbar-meta {
        margin-inline-start: 0;
      }
      #cardsContainer.view-list .job-quick-summary {
        flex-direction: column;
        align-items: flex-start;
      }
      #cardsContainer.view-list .job-actions-bar {
        border-inline-start: none;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        padding-inline-start: 0;
        padding-top: 12px;
        height: auto;
      }
      #cardsContainer.view-list .job-boxes-grid {
        grid-template-columns: 1fr;
      }
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
        <span class="brand-title">עידו גל | בקרת משרות</span>
        <span class="brand-subtitle">אנרגיה, גז טבעי ורחפנים</span>
      </div>
    </div>

    <!-- Progress & Category Navigation Hub (Replaces old tabs & includes starred cube) -->
    <div class="header-progress-hub">
      
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
          <div id="progressSegSaved" class="segmented-progress-bar" style="background: var(--dashboard-cyan); width: 0%;"></div>
          <div id="progressSegRejected" class="segmented-progress-bar" style="background: var(--dashboard-gold); width: 0%;"></div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--dashboard-muted);">
          <span id="pctLabelNew">100% חדשות</span>
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
          <div class="stat-cube-count" id="statNewCount">__TOTAL_JOBS__</div>
          <div class="stat-cube-label">משרות חדשות</div>
        </button>

        <button type="button" id="cube_starred" class="stat-cube-btn cube-starred" onclick="setFilter('starred', this)" title="משרות שסומנו בכוכב">
          <div class="stat-cube-icon gold">
            <i class="ph-fill ph-star"></i>
          </div>
          <div class="stat-cube-count" id="statStarredCount">0</div>
          <div class="stat-cube-label">מסומנות בכוכב</div>
        </button>

        <button type="button" id="cube_saved" class="stat-cube-btn cube-saved" onclick="setFilter('saved', this)" title="משרות שנשמרו להגשה">
          <div class="stat-cube-icon cyan">
            <i class="ph-duotone ph-bookmark-simple"></i>
          </div>
          <div class="stat-cube-count" id="statSavedCount">0</div>
          <div class="stat-cube-label">שמורות להגשה</div>
        </button>

        <button type="button" id="cube_rejected" class="stat-cube-btn cube-rejected" onclick="setFilter('rejected', this)" title="משרות שהוסרו מהסבב">
          <div class="stat-cube-icon rose">
            <i class="ph-duotone ph-trash"></i>
          </div>
          <div class="stat-cube-count" id="statRejectedCount">0</div>
          <div class="stat-cube-label">הוסרו מהסבב</div>
        </button>
      </div>

    </div>

    <div class="header-actions-group">
      <div id="cloudSyncStatus" class="dashboard-chip" style="color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); display: flex; align-items: center; gap: 6px;">
        <span class="dashboard-dot"></span>
        <i class="ph-duotone ph-cloud-check"></i>
        <span>ענן מסונכרן</span>
      </div>
      <button onclick="triggerSyncModal()" class="dashboard-settings-link" style="cursor: pointer;" title="פתח הגדרות וסנכרון ענן">
        <i class="ph-duotone ph-cloud-arrow-up"></i> סנכרן
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

    <!-- 2 Overview Cards (Search/Filters, Sector Distribution) -->
    <div class="dashboard-stats-grid">
      
      <!-- Card 1: סינון ואיתור משרות -->
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
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <select id="sectorFilter" onchange="filterCards()" style="flex: 1; min-width: 140px;">
              <option value="all">כל התחומים</option>
              <option value="scada">בקרה ו-SCADA</option>
              <option value="solar">מערכות סולאריות</option>
              <option value="natural_gas">גז טבעי</option>
              <option value="drones">רחפנים וכטב"ם</option>
              <option value="energy_tech">אגירה ו-Energy Tech</option>
              <option value="operations">תפעול ואחזקה</option>
              <option value="energy">אנרגיה כללית</option>
            </select>
            <select id="regionFilter" onchange="filterCards()" style="flex: 1; min-width: 140px;">
              <option value="all">כל האזורים בארץ</option>
              <option value="center">מרכז וירושלים</option>
              <option value="sharon">אזור השרון</option>
              <option value="north">חיפה והצפון</option>
              <option value="south">שפלה ודרום</option>
              <option value="nationwide">פריסה ארצית / שטח</option>
            </select>
          </div>
          <input id="searchInput" type="text" placeholder="חיפוש משרה, חברה או דרישה טכנית..." oninput="filterCards()" />
          
          <div class="controls-buttons-row">
            <button id="sortBtn" onclick="toggleSort()" class="tool-btn" style="flex: 1;" title="לחץ לשינוי סדר המיון">
              <span id="sortIcon"><i class="ph-duotone ph-calendar-blank"></i></span>
              <span id="sortLabel">מיון: התאריך החדש קודם</span>
            </button>
            <button onclick="openDuplicatesModal()" class="tool-btn" style="color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4);" title="סרוק כפילויות משרות">
              <span><i class="ph-duotone ph-magnifying-glass"></i></span>
              <span>בדיקת כפילויות</span>
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

    <!-- Quick Filter Chips Strip (One-Tap Filtering) -->
    <div class="quick-filter-strip-wrapper">
      <div class="quick-filter-strip" id="quickFilterStrip">
        <button type="button" class="quick-chip active" data-chip="all" onclick="selectQuickChip('all')">
          <i class="ph-duotone ph-squares-four"></i>
          <span>כל המשרות</span>
        </button>
        <button type="button" class="quick-chip" data-chip="starred" onclick="selectQuickChip('starred')">
          <i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>
          <span>בכוכב (<span id="countStarred">0</span>)</span>
        </button>
        <button type="button" class="quick-chip" data-chip="top_match" onclick="selectQuickChip('top_match')">
          <i class="ph-duotone ph-star"></i>
          <span>טופ 85%+</span>
        </button>
        <button type="button" class="quick-chip" data-chip="scada" onclick="selectQuickChip('scada')">
          <i class="ph-duotone ph-cpu"></i>
          <span>בקרה ו-SCADA</span>
        </button>
        <button type="button" class="quick-chip" data-chip="solar" onclick="selectQuickChip('solar')">
          <i class="ph-duotone ph-sun"></i>
          <span>סולאר ו-PV</span>
        </button>
        <button type="button" class="quick-chip" data-chip="natural_gas" onclick="selectQuickChip('natural_gas')">
          <i class="ph-duotone ph-flame"></i>
          <span>גז טבעי</span>
        </button>
        <button type="button" class="quick-chip" data-chip="drones" onclick="selectQuickChip('drones')">
          <i class="ph-duotone ph-crosshair"></i>
          <span>רחפנים וכטב"ם</span>
        </button>
        <button type="button" class="quick-chip" data-chip="operations" onclick="selectQuickChip('operations')">
          <i class="ph-duotone ph-wrench"></i>
          <span>תפעול ואחזקה</span>
        </button>
        <button type="button" class="quick-chip" data-chip="salary_verified" onclick="selectQuickChip('salary_verified')">
          <i class="ph-duotone ph-currency-circle-dollar"></i>
          <span>שכר מאומת</span>
        </button>
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

    <!-- Cards View Header (Count & Grid/List Toggle) -->
    <div class="cards-view-header">
      <div class="cards-count-summary">
        <i class="ph-duotone ph-briefcase" style="font-size: 18px; color: var(--dashboard-cyan);"></i>
        <span id="visibleJobsCountText">מציג __TOTAL_JOBS__ משרות</span>
      </div>
      <div class="view-mode-toggle" role="group" aria-label="מצב תצוגה">
        <button type="button" id="viewGridBtn" class="view-toggle-btn active" onclick="setViewMode('grid')" title="תצוגת קוביות (Grid)">
          <i class="ph-bold ph-squares-four"></i> <span>קוביות</span>
        </button>
        <button type="button" id="viewListBtn" class="view-toggle-btn" onclick="setViewMode('list')" title="תצוגת רשימה קומפקטית (List)">
          <i class="ph-bold ph-list-dashes"></i> <span>רשימה</span>
        </button>
      </div>
    </div>

    <!-- Job Cards List -->
    <main id="cardsContainer"></main>

    <!-- Empty State -->
    <div id="emptyState" class="dashboard-card empty-state" style="display: none; text-align: center; padding: 48px 24px;">
      <div id="emptyStateIcon" style="font-size: 44px; margin-bottom: 12px; color: var(--dashboard-cyan);">
        <i class="ph-duotone ph-magnifying-glass"></i>
      </div>
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
  let currentViewMode = 'grid';
  let allJobsMap = {};
  try {
    currentViewMode = localStorage.getItem(VIEW_MODE_KEY) || 'grid';
  } catch(e) {}
  let starredJobs = loadStarredJobs();

  function loadStarredJobs() {
    try {
      return JSON.parse(localStorage.getItem(STARRED_STORAGE_KEY) || '{}');
    } catch(e) {
      return {};
    }
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
          starBtn.innerHTML = isStarred ? '<i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>' : '<i class="ph-bold ph-star"></i>';
        }
        card.classList.toggle('is-starred-card', isStarred);
        card.setAttribute('data-starred', isStarred ? 'true' : 'false');
      }
    });

    updateUI();
  }

  function setViewMode(mode) {
    currentViewMode = mode;
    try {
      localStorage.setItem(VIEW_MODE_KEY, mode);
    } catch(e) {}
    const container = document.getElementById('cardsContainer');
    const gridBtn = document.getElementById('viewGridBtn');
    const listBtn = document.getElementById('viewListBtn');
    if (!container) return;

    if (mode === 'list') {
      container.classList.add('view-list');
      if (gridBtn) gridBtn.classList.remove('active');
      if (listBtn) listBtn.classList.add('active');
    } else {
      container.classList.remove('view-list');
      if (gridBtn) gridBtn.classList.add('active');
      if (listBtn) listBtn.classList.remove('active');
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

  function setCloudSyncStatus(status) {
    const cloudBadge = document.getElementById('cloudSyncStatus');
    if (!cloudBadge) return;
    if (status === 'synced') {
      cloudBadge.className = 'dashboard-chip cloud-synced';
      cloudBadge.style.color = 'var(--dashboard-cyan)';
      cloudBadge.style.borderColor = 'rgba(137, 244, 231, 0.4)';
      cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-cyan); box-shadow: 0 0 8px var(--dashboard-cyan);"></span> <i class="ph-duotone ph-cloud-check"></i> <span>ענן מסונכרן</span>';
    } else if (status === 'syncing') {
      cloudBadge.className = 'dashboard-chip cloud-syncing';
      cloudBadge.style.color = 'var(--dashboard-gold)';
      cloudBadge.style.borderColor = 'rgba(255, 211, 104, 0.4)';
      cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-gold); box-shadow: 0 0 8px var(--dashboard-gold);"></span> <i class="ph-duotone ph-cloud-arrow-up"></i> <span>מעדכן ענן...</span>';
    } else if (status === 'offline' || status === 'error') {
      cloudBadge.className = 'dashboard-chip cloud-offline';
      cloudBadge.style.color = '#f87171';
      cloudBadge.style.borderColor = 'rgba(248, 113, 113, 0.4)';
      cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: #f87171; box-shadow: 0 0 8px rgba(248, 113, 113, 0.6);"></span> <i class="ph-duotone ph-cloud-slash"></i> <span>לא מקוון</span>';
    }
  }

  async function fetchCloudSync() {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
    try {
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
        setCloudSyncStatus('synced');
      }
    } catch (e) {
      setCloudSyncStatus('offline');
    }
  }

  function scheduleCloudPush() {
    if (cloudSyncTimeout) clearTimeout(cloudSyncTimeout);
    cloudSyncTimeout = setTimeout(pushCloudSync, 400);
  }

  async function pushCloudSync() {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
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
        setCloudSyncStatus('synced');
      } else {
        setCloudSyncStatus('offline');
      }
    } catch (e) {
      setCloudSyncStatus('offline');
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
        if (jobStates[link] === 'saved' && !seenLinks.has(link) && historicalCatalog[link]) {
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

  function getExperienceChip(job) {
    const openness = (job.junior_openness || '').toLowerCase();
    const title = (job.title || '').toLowerCase();
    const reqs = (job.company_requirements || '').toLowerCase();
    const fullText = `${openness} ${reqs}`;

    let label = 'ניסיון נדרש לפי מודעה';
    let style = 'color: var(--dashboard-muted); border-color: rgba(255, 255, 255, 0.2); background: rgba(255, 255, 255, 0.05);';
    let icon = 'ph-briefcase';

    if (openness.includes('גבוהה מאוד') || openness.includes('ללא ניסיון') || fullText.includes('ללא ניסיון') || fullText.includes('בוגר טרי') || fullText.includes('הכשרה על חשבון')) {
      label = 'ללא ניסיון / בוגר טרי';
      style = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.45); background: rgba(220, 255, 114, 0.12); font-weight: 600;';
      icon = 'ph-sparkle';
    } else if (openness.includes('גבוהה') || openness.includes("ג'וניור") || openness.includes('מתאים להנדסאי בתחילת') || openness.includes('הסמכה טרייה') || openness.includes('1-2') || openness.includes('שנה ניסיון') || title.includes('junior')) {
      label = "פתוח לג'וניור / 1-2 שנות ניסיון";
      style = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.45); background: rgba(137, 244, 231, 0.12); font-weight: 600;';
      icon = 'ph-user-check';
    } else if (openness.includes('בינוני') || openness.includes('בינונית') || fullText.includes('2-3') || fullText.includes('3 שנים')) {
      label = 'ניסיון בינוני (2-3 שנים)';
      style = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); background: rgba(255, 211, 104, 0.1);';
      icon = 'ph-clock';
    } else if (openness.includes('נמוכה') || fullText.includes('בכיר') || fullText.includes('5+ שנים') || fullText.includes('5 שנים') || title.includes('senior') || title.includes('lead')) {
      label = 'דרוש ניסיון משמעותי (3+ שנים)';
      style = 'color: #fca5a5; border-color: rgba(252, 165, 165, 0.4); background: rgba(239, 68, 68, 0.1);';
      icon = 'ph-medal';
    } else if (job.junior_openness && job.junior_openness.trim().length > 0 && job.junior_openness !== 'N/A') {
      label = stripEmojis(job.junior_openness.replace(/^[^א-תa-zA-Z0-9]+/, '').split('(')[0].trim());
      style = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.08);';
      icon = 'ph-identification-badge';
    }

    return `
      <span class="dashboard-chip exp-chip" style="${style}; font-size: 12px; padding: 3px 10px;" title="רמת ניסיון: ${escapeHtml(job.junior_openness || label)}">
        <i class="ph-duotone ${icon}"></i> ${label}
      </span>
    `;
  }

  function stripEmojis(str) {
    if (!str) return '';
    return str.replace(/\\p{Extended_Pictographic}/gu, '').replace(/[\\u2600-\\u27BF]/g, '').trim();
  }

  function getAiScoreDrivers(job, score, classifiedSector) {
    const text = ((job.title || '') + ' ' + (job.reasoning || '') + ' ' + (job.experience_strengths || '') + ' ' + (job.company_requirements || '') + ' ' + (job.job_summary || '')).toLowerCase();
    const drivers = [];

    // 1. Qualification / Degree
    if (text.includes('הנדסאי') || text.includes('practical engineer')) {
      drivers.push({ label: 'הנדסאי מתאים', icon: 'ph-graduation-cap', type: 'lime' });
    } else if (text.includes('b.sc') || text.includes('תואר') || text.includes('מהנדס')) {
      drivers.push({ label: 'גמישות לתואר B.Sc', icon: 'ph-certificate', type: 'cyan' });
    }

    // 2. Domain / Skill & Control Room Rule
    const isControlRoom = text.includes('חדר בקרה') || text.includes('בקר') || text.includes('משמרות') || (job.title && job.title.includes('בקר'));
    const hasScada = text.includes('scada') || text.includes('בקרה') || classifiedSector === 'בקרה ו-SCADA';
    
    if (isControlRoom) {
      if (hasScada) {
        drivers.push({ label: 'חדר בקרה • SCADA מאומת', icon: 'ph-desktop-tower', type: 'cyan' });
      } else {
        drivers.push({ label: 'בקרת מערכות 24/7', icon: 'ph-gauge', type: 'cyan' });
      }
    } else if (hasScada) {
      drivers.push({ label: 'דרישת SCADA ובקרה', icon: 'ph-cpu', type: 'cyan' });
    } else if (classifiedSector === 'סולאר' || text.includes('סולאר') || text.includes('pv')) {
      drivers.push({ label: 'תשתיות סולאריות ו-PV', icon: 'ph-sun', type: 'lime' });
    } else if (classifiedSector === 'גז טבעי' || text.includes('גז טבעי') || text.includes('תחנת כוח')) {
      drivers.push({ label: 'גז טבעי ותחנות כוח', icon: 'ph-flame', type: 'cyan' });
    } else if (classifiedSector === 'רחפנים' || text.includes('רחפן') || text.includes('כטב') || text.includes('uav')) {
      drivers.push({ label: 'מערכות כטב"ם ורחפנים', icon: 'ph-crosshair', type: 'lime' });
    } else if (classifiedSector === 'תפעול ואחזקה' || text.includes('אינטגרציה')) {
      drivers.push({ label: 'אינטגרציה ותפעול שטח', icon: 'ph-wrench', type: 'gold' });
    }

    // 3. Compensation / Salary
    const salType = job.salary_source_type;
    if (salType === 'company_verified' || salType === 'job_ad') {
      drivers.push({ label: 'שכר מאומת במודעה/חברה', icon: 'ph-currency-circle-dollar', type: 'lime' });
    } else if (job.salary_range && (job.salary_range.includes('15') || job.salary_range.includes('16') || job.salary_range.includes('17') || job.salary_range.includes('18') || job.salary_range.includes('20'))) {
      drivers.push({ label: 'רמת שכר מתגמלת', icon: 'ph-trend-up', type: 'lime' });
    }

    // 4. Score tier
    if (score >= 88) {
      drivers.push({ label: 'התאמת על (Tier 1)', icon: 'ph-star', type: 'lime' });
    }

    return drivers.slice(0, 3);
  }

  function toggleCardDetails(btn) {
    const card = btn.closest('.job-card');
    if (!card) return;
    const details = card.querySelector('.job-details-collapsible');
    if (!details) return;
    const isExpanded = details.classList.contains('expanded');
    if (isExpanded) {
      details.classList.remove('expanded');
      btn.classList.remove('expanded');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '<span>הרחב ניתוח מלא (תקציר, התאמה ורקע חברה)</span> <i class="ph-bold ph-caret-down"></i>';
    } else {
      details.classList.add('expanded');
      btn.classList.add('expanded');
      btn.setAttribute('aria-expanded', 'true');
      btn.innerHTML = '<span>הסתר פירוט מלא</span> <i class="ph-bold ph-caret-up"></i>';
    }
  }

  let activeQuickChip = 'all';

  function selectQuickChip(chipKey) {
    activeQuickChip = chipKey;
    document.querySelectorAll('.quick-chip').forEach(btn => {
      if (btn.getAttribute('data-chip') === chipKey) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    const sectorSelect = document.getElementById('sectorFilter');
    if (['all', 'scada', 'solar', 'natural_gas', 'drones', 'operations'].includes(chipKey)) {
      if (sectorSelect) sectorSelect.value = chipKey;
    } else {
      if (sectorSelect) sectorSelect.value = 'all';
    }

    updateUI();
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
      const company = stripEmojis(job.company || 'חברה');
      const title = stripEmojis(job.title || 'משרה ללא כותרת');
      const link = job.link || '#';
      const secKey = job.sector_key || 'energy';
      const jobDate = job.date || 'היום';
      const classifiedSector = classifyJobSector(job);
      
      let sectorBadge = '<i class="ph-duotone ph-lightning"></i> תשתיות אנרגיה';
      let sectorChipStyle = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); background: rgba(255, 211, 104, 0.1);';
      if (['drones', 'cuas', 'avionics'].includes(secKey)) {
        if (secKey === 'cuas') {
          sectorBadge = '<i class="ph-duotone ph-shield-check"></i> הגנת C-UAS וביטחון';
          sectorChipStyle = 'color: #fca5a5; border-color: rgba(252, 165, 165, 0.4); background: rgba(239, 68, 68, 0.12);';
        } else if (secKey === 'avionics') {
          sectorBadge = '<i class="ph-duotone ph-broadcast"></i> מטע"דים ואוויוניקה';
          sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
        } else {
          sectorBadge = '<i class="ph-duotone ph-crosshair"></i> רחפנים וכטב"ם אוטונומי';
          sectorChipStyle = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.4); background: rgba(220, 255, 114, 0.12);';
        }
      } else if (secKey === 'solar' || classifiedSector === 'סולאר') {
        sectorBadge = '<i class="ph-duotone ph-sun"></i> מערכות סולאריות ו-PV';
        sectorChipStyle = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.4); background: rgba(220, 255, 114, 0.12);';
      } else if (secKey === 'natural_gas' || classifiedSector === 'גז טבעי') {
        sectorBadge = '<i class="ph-duotone ph-flame"></i> גז טבעי ותחנות כוח';
        sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
      } else if (secKey === 'energy_tech' || classifiedSector === 'אגירה') {
        sectorBadge = '<i class="ph-duotone ph-battery-charging"></i> אגירה ו-Energy-Tech';
        sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
      } else if (secKey === 'scada' || classifiedSector === 'בקרה ו-SCADA') {
        sectorBadge = '<i class="ph-duotone ph-cpu"></i> בקרה ו-SCADA';
        sectorChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); background: rgba(137, 244, 231, 0.12);';
      } else if (secKey === 'operations' || classifiedSector === 'תפעול ואחזקה') {
        sectorBadge = '<i class="ph-duotone ph-wrench"></i> תפעול ואחזקה';
        sectorChipStyle = 'color: #b4fcf1; border-color: rgba(180, 252, 241, 0.4); background: rgba(180, 252, 241, 0.12);';
      }

      if (job.sector && job.sector.length > 2 && !job.sector.includes('(')) {
        const cleanText = stripEmojis(job.sector.replace(/^[^א-תa-zA-Z0-9]+/, '').trim());
        let iconTag = '<i class="ph-duotone ph-lightning"></i>';
        if (classifiedSector === 'סולאר') iconTag = '<i class="ph-duotone ph-sun"></i>';
        else if (classifiedSector === 'רחפנים') iconTag = '<i class="ph-duotone ph-crosshair"></i>';
        else if (classifiedSector === 'גז טבעי') iconTag = '<i class="ph-duotone ph-flame"></i>';
        else if (classifiedSector === 'בקרה ו-SCADA') iconTag = '<i class="ph-duotone ph-cpu"></i>';
        else if (classifiedSector === 'אגירה') iconTag = '<i class="ph-duotone ph-battery-charging"></i>';
        else if (classifiedSector === 'תפעול ואחזקה') iconTag = '<i class="ph-duotone ph-wrench"></i>';
        sectorBadge = `${iconTag} ${cleanText}`;
      }

      let scoreClass = 'badge-score-high';
      if (score < 80) scoreClass = 'badge-score-fair';
      else if (score < 90) scoreClass = 'badge-score-med';

      const domain = stripEmojis(job.company_domain_product || job.company_summary || 'חברה מובילה בתחומה');
      const loc = stripEmojis(job.location || 'ישראל / היברידי');
      const jobSum = stripEmojis(job.job_summary || job.company_summary || 'תפקיד משמעותי בתפעול וניטור מערכות מתקדמות.');
      const strengths = stripEmojis(job.experience_strengths || job.reasoning || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.');
      const companyReqs = stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה (פירוט מלא בקישור להגשה).');
      const logoHtml = getCompanyLogoHtml(company, job.logo);

      const salaryRange = stripEmojis(job.salary_range || '12,000 - 15,000 ₪');
      const salaryType = job.salary_source_type || 'sector_benchmark';
      const companyBdi = `<bdi dir="auto">${company}</bdi>`;
      const salaryLabel = stripEmojis(job.salary_source_label || (salaryType === 'company_verified' ? `מבוסס דיווחי שכר ב-${companyBdi}` : (salaryType === 'job_ad' ? 'פורסם במודעת המשרה' : `הערכת ענף`)));
      
      let salaryChipStyle = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.35); background: rgba(255, 211, 104, 0.08);';
      if (salaryType === 'company_verified') {
        salaryChipStyle = 'color: var(--dashboard-lime); border-color: rgba(220, 255, 114, 0.35); background: rgba(220, 255, 114, 0.08);';
      } else if (salaryType === 'job_ad') {
        salaryChipStyle = 'color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.35); background: rgba(137, 244, 231, 0.08);';
      }

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

      // Explainable AI drivers
      const drivers = getAiScoreDrivers(job, score, classifiedSector);
      let driversHtml = '';
      if (drivers.length > 0) {
        const chipsHtml = drivers.map(d => `<span class="driver-chip ${d.type}"><i class="ph-duotone ${d.icon}"></i> ${d.label}</span>`).join('');
        driversHtml = `
          <div class="ai-score-drivers">
            <span class="drivers-label"><i class="ph-duotone ph-sparkle"></i> גורמי התאמה:</span>
            ${chipsHtml}
          </div>
        `;
      }

      const quickInsight = strengths || jobSum;
      const isStarred = Boolean(starredJobs[id]);
      const classifiedRegion = classifyJobRegion(loc);
      const expChipHtml = getExperienceChip(job);

      const card = document.createElement('article');
      card.setAttribute('data-id', id);
      card.setAttribute('data-sector', secKey);
      card.setAttribute('data-classified-sector', classifiedSector);
      card.setAttribute('data-location', loc.toLowerCase());
      card.setAttribute('data-region', classifiedRegion);
      card.setAttribute('data-starred', isStarred ? 'true' : 'false');
      card.setAttribute('data-score', score);
      card.setAttribute('data-salary-verified', (salaryType === 'company_verified' || salaryType === 'job_ad') ? 'true' : 'false');
      card.className = `dashboard-card job-card ${isStarred ? 'is-starred-card' : ''}`;

      card.innerHTML = `
        <!-- Top Meta Row -->
        <div class="job-card-topbar">
          <div class="job-card-topbar-primary">
            <div style="display: flex; align-items: center; gap: 8px;">
              <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar('${id.replace(/'/g, "\\'")}', event)" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
                <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
              </button>
              <span class="dashboard-chip" style="${sectorChipStyle}">${sectorBadge}</span>
            </div>
            <div class="badge-score ${scoreClass}">
              <span><i class="ph-duotone ph-lightning"></i> ${score}%</span> התאמה
            </div>
          </div>
          <div class="job-card-topbar-meta">
            <span class="dashboard-chip" style="color: var(--dashboard-muted); border-color: rgba(255, 255, 255, 0.15); background: rgba(0, 0, 0, 0.2); font-size: 11px; padding: 2px 8px;">
              <i class="ph-duotone ph-calendar-blank"></i> ${jobDate}
            </span>
            <span class="dashboard-chip" style="${sourceChipStyle}; font-size: 11px; padding: 2px 8px;">
              <i class="ph-duotone ${sourceIcon}"></i> ${sourceName}
            </span>
          </div>
        </div>

        <!-- Title & Company Header -->
        <div class="job-card-main-header">
          ${logoHtml}
          <div class="job-header-text">
            <div class="job-company-name" dir="auto">${company}</div>
            <h2 class="job-title-text" dir="auto">${title}</h2>
            <div class="job-header-chips">
              <span class="dashboard-chip" style="font-size: 12px; padding: 3px 10px;">
                <i class="ph-duotone ph-map-pin"></i> ${loc}
              </span>
              <span class="dashboard-chip" style="${salaryChipStyle}; font-size: 12px; padding: 3px 10px;">
                <i class="ph-duotone ph-currency-circle-dollar"></i> ${salaryRange} <small style="display: inline; opacity: 0.85;" dir="ltr"><bdi dir="rtl">(${salaryLabel})</bdi></small>
              </span>
              ${expChipHtml}
            </div>
            ${driversHtml}
          </div>
        </div>

        <!-- Company Requirements Banner (Direct View on Cube) -->
        <div class="job-quick-summary">
          <div class="quick-summary-label">
            <i class="ph-duotone ph-check-square"></i> דרישות החברה עבור המשרה:
          </div>
          <div class="quick-summary-text">${companyReqs}</div>
        </div>

        <!-- Progressive Disclosure Toggle Button -->
        <button type="button" class="btn-toggle-details" onclick="toggleCardDetails(this)" aria-expanded="false">
          <span>הרחב ניתוח מלא (תקציר, התאמה ורקע חברה)</span>
          <i class="ph-bold ph-caret-down"></i>
        </button>

        <!-- Collapsible Full Information Panels -->
        <div class="job-details-collapsible">
          <div class="job-boxes-grid">
            <div class="job-box highlight">
              <strong><i class="ph-duotone ph-sparkle"></i> תמצית התאמה ממוקדת:</strong>
              <span>${quickInsight}</span>
            </div>
            <div class="job-box">
              <strong><i class="ph-duotone ph-buildings"></i> תחום ומוצר החברה:</strong>
              <span>${domain}</span>
            </div>
            <div class="job-box">
              <strong><i class="ph-duotone ph-article"></i> תקציר המשרה:</strong>
              <span>${jobSum}</span>
            </div>
            <div class="job-box highlight">
              <strong><i class="ph-duotone ph-target"></i> נקודות חוזק מהניסיון:</strong>
              <span>${strengths}</span>
            </div>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="job-actions-bar">
          <div class="action-btn-group">
            <button onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'saved')" class="btn-triage action-save-btn">
              <i class="ph-duotone ph-bookmark-simple"></i> <span class="btn-text">שמור להגשה</span>
            </button>
            <button onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'rejected')" class="btn-triage action-reject-btn">
              <i class="ph-duotone ph-x"></i> <span>הסר משרה</span>
            </button>
          </div>
          <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn-apply" style="color: #000000 !important;">
            <span style="color: #000000 !important;">הגש מועמדות</span> <i class="ph-duotone ph-arrow-up-right" style="color: #000000 !important;"></i>
          </a>
        </div>
      `;

      allJobsMap[id] = job;
      card.addEventListener('click', (e) => {
        if (e.target.closest('.btn-star') || e.target.closest('.btn-triage') || e.target.closest('.btn-apply') || e.target.closest('.btn-toggle-details')) {
          return;
        }
        if (window.innerWidth <= 768) {
          openJobModal(id);
        }
      });

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
    const loc = stripEmojis(job.location || 'ישראל / היברידי');
    const jobDate = job.date || 'היום';
    const classifiedSector = classifyJobSector(job);
    const domain = stripEmojis(job.company_domain_product || job.company_summary || 'חברה מובילה בתחומה');
    const jobSum = stripEmojis(job.job_summary || job.company_summary || 'תפקיד משמעותי בתפעול וניטור מערכות מתקדמות.');
    const strengths = stripEmojis(job.experience_strengths || job.reasoning || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.');
    const companyReqs = stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה.');
    const quickInsight = strengths || jobSum;
    const logoHtml = getCompanyLogoHtml(company, job.logo);
    const salaryRange = stripEmojis(job.salary_range || '12,000 - 15,000 ₪');
    const salaryType = job.salary_source_type || 'sector_benchmark';
    const companyBdi = `<bdi dir="auto">${company}</bdi>`;
    const salaryLabel = stripEmojis(job.salary_source_label || (salaryType === 'company_verified' ? `מבוסס דיווחי שכר ב-${companyBdi}` : (salaryType === 'job_ad' ? 'פורסם במודעת המשרה' : `הערכת ענף`)));

    let scoreClass = 'badge-score-high';
    if (score < 80) scoreClass = 'badge-score-fair';
    else if (score < 90) scoreClass = 'badge-score-med';

    const isStarred = Boolean(starredJobs[id]);
    const state = jobStates[id] || 'pending';

    headerActions.innerHTML = `
      <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar('${id.replace(/'/g, "\\'")}', event); updateModalStar('${id.replace(/'/g, "\\'")}');" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
        <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
      </button>
      <div class="badge-score ${scoreClass}" title="ציון התאמה ${score}%">
        <span><i class="ph-duotone ph-lightning"></i> ${score}%</span>
      </div>
    `;

    const drivers = getAiScoreDrivers(job, score, classifiedSector);
    let driversHtml = '';
    if (drivers.length > 0) {
      const chipsHtml = drivers.map(d => `<span class="driver-chip ${d.type}"><i class="ph-duotone ${d.icon}"></i> ${d.label}</span>`).join('');
      driversHtml = `
        <div class="ai-score-drivers" style="margin: 8px 0 0;">
          <span class="drivers-label"><i class="ph-duotone ph-sparkle"></i> גורמי התאמה:</span>
          ${chipsHtml}
        </div>
      `;
    }

    const expChipHtml = getExperienceChip(job);

    body.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 14px;">
        ${logoHtml}
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 13.5px; font-weight: 700; color: var(--dashboard-cyan); margin-bottom: 2px;" dir="auto">${company}</div>
          <h2 style="font-size: 17.5px; font-weight: 700; color: #fff; margin: 0 0 6px; line-height: 1.3;" dir="auto">${title}</h2>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
            <span class="dashboard-chip" style="font-size: 11px; padding: 3px 8px;">
              <i class="ph-duotone ph-map-pin"></i> ${loc}
            </span>
            <span class="dashboard-chip" style="font-size: 11px; padding: 3px 8px; color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.35); background: rgba(255, 211, 104, 0.08);">
              <i class="ph-duotone ph-currency-circle-dollar"></i> ${salaryRange} <small style="display: inline; opacity: 0.85;" dir="ltr"><bdi dir="rtl">(${salaryLabel})</bdi></small>
            </span>
            ${expChipHtml}
          </div>
          ${driversHtml}
        </div>
      </div>

      <div class="job-quick-summary" style="background: rgba(137, 244, 231, 0.05); border: 1px solid rgba(137, 244, 231, 0.22); border-radius: 14px; padding: 12px 14px;">
        <div class="quick-summary-label" style="font-size: 12px; font-weight: 700; color: var(--dashboard-cyan); margin-bottom: 4px;">
          <i class="ph-duotone ph-check-square"></i> דרישות החברה עבור המשרה:
        </div>
        <div style="font-size: 13.5px; line-height: 1.5; color: #e2e8df;">${companyReqs}</div>
      </div>

      <div class="job-boxes-grid" style="grid-template-columns: 1fr; gap: 10px;">
        <div class="job-box highlight">
          <strong><i class="ph-duotone ph-sparkle"></i> תמצית התאמה ממוקדת:</strong>
          <span>${quickInsight}</span>
        </div>
        <div class="job-box">
          <strong><i class="ph-duotone ph-buildings"></i> תחום ומוצר החברה:</strong>
          <span>${domain}</span>
        </div>
        <div class="job-box">
          <strong><i class="ph-duotone ph-article"></i> תקציר המשרה:</strong>
          <span>${jobSum}</span>
        </div>
        <div class="job-box highlight">
          <strong><i class="ph-duotone ph-target"></i> נקודות חוזק מהניסיון:</strong>
          <span>${strengths}</span>
        </div>
      </div>
    `;

    bottomBar.innerHTML = `
      <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn-apply" style="color: #000000 !important;">
        <span style="color: #000000 !important;">הגש מועמדות באתר המשרה</span> <i class="ph-duotone ph-arrow-up-right" style="color: #000000 !important;"></i>
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

  function toggleSort() {
    currentSort = currentSort === 'score_desc' ? 'date_desc' : 'score_desc';
    const icon = document.getElementById('sortIcon');
    const label = document.getElementById('sortLabel');
    if (currentSort === 'score_desc') {
      if (icon) icon.innerHTML = '<i class="ph-duotone ph-sort-descending"></i>';
      if (label) label.textContent = 'מיון: ציון התאמה (מגבוה לנמוך)';
      showToast('ph-sort-descending', 'מיון: ציון התאמה מגבוה לנמוך');
    } else {
      if (icon) icon.innerHTML = '<i class="ph-duotone ph-calendar-blank"></i>';
      if (label) label.textContent = 'מיון: התאריך החדש קודם';
      showToast('ph-calendar-blank', 'מיון: התאריך החדש קודם');
    }
    renderCards();
  }

  function toggleAction(id, action) {
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
    }

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
      else if (currentFilter === 'starred') matchesTab = (Boolean(starredJobs[id]) && state !== 'rejected' && state !== 'purged');
      else if (currentFilter === 'saved') matchesTab = (state === 'saved');
      else if (currentFilter === 'rejected') matchesTab = (state === 'rejected');

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
      
      let matchesQuick = true;
      if (activeQuickChip === 'starred') {
        matchesQuick = Boolean(starredJobs[id]);
      } else if (activeQuickChip === 'top_match') {
        const cScore = Number(card.getAttribute('data-score')) || 0;
        matchesQuick = (cScore >= 85);
      } else if (activeQuickChip === 'salary_verified') {
        matchesQuick = (card.getAttribute('data-salary-verified') === 'true');
      }

      let matchesSearch = true;
      if (searchInput) {
        const cardText = card.textContent.toLowerCase();
        matchesSearch = cardText.includes(searchInput);
      }

      if (matchesTab && matchesSector && matchesRegion && matchesQuick && matchesSearch && state !== 'purged') {
        card.style.display = '';
        card.classList.remove('is-hidden');
        visibleCount++;
      } else {
        card.style.display = 'none';
        card.classList.add('is-hidden');
      }
    });

    const visibleJobsCountEl = document.getElementById('visibleJobsCountText');
    if (visibleJobsCountEl) {
      visibleJobsCountEl.textContent = `מציג ${visibleCount} מתוך ${total} משרות`;
    }

    // Keep Quick Chips in sync
    document.querySelectorAll('.quick-chip').forEach(btn => {
      const c = btn.getAttribute('data-chip');
      if (['top_match', 'salary_verified', 'starred'].includes(activeQuickChip)) {
        btn.classList.toggle('active', c === activeQuickChip);
      } else {
        btn.classList.toggle('active', c === selectedSector);
      }
    });

    const allAvailable = getAllAvailableJobs();
    const totalSavedInStore = allAvailable.filter(j => jobStates[j.link] === 'saved').length;
    const totalRejectedInStore = allAvailable.filter(j => jobStates[j.link] === 'rejected').length;
    const totalStarredInStore = allAvailable.filter(j => Boolean(starredJobs[j.link])).length;
    const pendingInBatch = total - (saved + rejected + purged);

    // Update Counts in Nav & Stats Cards
    const countAllEl = document.getElementById('countAll');
    const countSavedEl = document.getElementById('countSaved');
    const countRejectedEl = document.getElementById('countRejected');
    const countStarredNavEl = document.getElementById('countStarredNav');
    const countStarredEl = document.getElementById('countStarred');
    if (countAllEl) countAllEl.textContent = Math.max(0, pendingInBatch);
    if (countSavedEl) countSavedEl.textContent = totalSavedInStore;
    if (countRejectedEl) countRejectedEl.textContent = totalRejectedInStore;
    if (countStarredNavEl) countStarredNavEl.textContent = totalStarredInStore;
    if (countStarredEl) countStarredEl.textContent = totalStarredInStore;

    const statNewEl = document.getElementById('statNewCount');
    const statStarredEl = document.getElementById('statStarredCount');
    const statSavedEl = document.getElementById('statSavedCount');
    const statRejectedEl = document.getElementById('statRejectedCount');
    if (statNewEl) statNewEl.textContent = Math.max(0, pendingInBatch);
    if (statStarredEl) statStarredEl.textContent = totalStarredInStore;
    if (statSavedEl) statSavedEl.textContent = totalSavedInStore;
    if (statRejectedEl) statRejectedEl.textContent = totalRejectedInStore;

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
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-trash"></i>';
          if (titleEl) titleEl.textContent = `כל ${totalRejectedInStore} המשרות שהוסרו מנוטרלות לצמיתות`;
          if (descEl) descEl.textContent = 'משרות אלו סוננו מחלון ההזדמנויות השבועי ולא ישובו להופיע בדוחות הבאים.';
        } else if (currentFilter === 'saved') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-bookmark-simple"></i>';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות שמורות מתוך מקבץ זה';
          if (descEl) descEl.textContent = 'לחץ על "שמור להגשה" בכל כרטיס משרה שמעניינת אותך.';
        } else if (currentFilter === 'starred') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות בכוכב';
          if (descEl) descEl.textContent = 'לחץ על סמל הכוכב בפינת כל כרטיס משרה כדי להוסיף אותה לרשימת המועדפים שלך.';
        } else {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-sparkle"></i>';
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

    const allAvailableJobs = getAllAvailableJobs();

    let sourceJobs = [];
    const chartTitleEl = document.getElementById('chartTitle');
    const chartChipEl = document.getElementById('chartChip');

    if (currentFilter === 'saved') {
      sourceJobs = allAvailableJobs.filter(j => jobStates[j.link] === 'saved');
      if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות שמורות';
      if (chartChipEl) {
        chartChipEl.innerHTML = `<i class="ph-duotone ph-bookmark-simple"></i> ${sourceJobs.length} שמורות`;
        chartChipEl.style.color = 'var(--dashboard-lime)';
        chartChipEl.style.borderColor = 'rgba(220, 255, 114, 0.4)';
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
      // Default / All: pending jobs in current weekly batch
      sourceJobs = (rawJobsData || []).filter(j => {
        const st = jobStates[j.link] || 'pending';
        return st !== 'saved' && st !== 'rejected' && st !== 'purged';
      });
      if (chartTitleEl) chartTitleEl.textContent = 'התפלגות תחומים';
      if (chartChipEl) {
        if (sourceJobs.length === 0) {
          chartChipEl.innerHTML = '<i class="ph-duotone ph-chart-bar"></i> 0 משרות';
        } else {
          chartChipEl.innerHTML = `<i class="ph-duotone ph-chart-bar"></i> פעיל השבוע (${sourceJobs.length})`;
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
                <i class="ph-duotone ph-lightning"></i> השאר אחת
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
                <a href="${link}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); font-weight: 600; font-size: 13px; text-decoration: underline; text-underline-offset: 3px; display: inline-flex; align-items: center; gap: 4px;">
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
    setViewMode(currentViewMode);
    renderCards();
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
