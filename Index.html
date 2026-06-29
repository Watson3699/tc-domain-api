<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PRECEPT Scout — Multi-Hazard Precursor Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:        #080B0F;
    --panel:     #0A1628;
    --panel2:    #0D1F3C;
    --border:    #1A2F50;
    --cyan:      #00D4FF;
    --cyan-dim:  #0088AA;
    --green:     #00FF88;
    --amber:     #FF8C00;
    --red:       #FF3333;
    --purple:    #8B5CF6;
    --text:      #C8D8E8;
    --text-dim:  #4A6080;
    --mono:      'JetBrains Mono', monospace;
    --sans:      'Inter', sans-serif;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 13px;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* ── GATE ── */
  #gate {
    position: fixed; inset: 0;
    background: rgba(8,11,15,0.97);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(8px);
  }
  .gate-box {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 48px 56px;
    width: 480px;
    text-align: center;
  }
  .gate-logo {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.3em;
    color: var(--cyan);
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .gate-title {
    font-family: var(--mono);
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 6px;
    letter-spacing: 0.05em;
  }
  .gate-sub {
    color: var(--text-dim);
    font-size: 12px;
    margin-bottom: 40px;
    line-height: 1.6;
  }
  .gate-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    text-align: left;
    margin-bottom: 8px;
  }
  .gate-input {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--cyan);
    font-family: var(--mono);
    font-size: 14px;
    letter-spacing: 0.15em;
    padding: 14px 16px;
    outline: none;
    margin-bottom: 16px;
    text-transform: uppercase;
  }
  .gate-input:focus { border-color: var(--cyan); }
  .gate-btn {
    width: 100%;
    background: var(--cyan);
    color: var(--bg);
    border: none;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.2em;
    padding: 14px;
    cursor: pointer;
    text-transform: uppercase;
    transition: opacity 0.15s;
  }
  .gate-btn:hover { opacity: 0.85; }
  .gate-error {
    color: var(--red);
    font-family: var(--mono);
    font-size: 11px;
    margin-top: 10px;
    letter-spacing: 0.1em;
    min-height: 16px;
  }
  .gate-footer {
    margin-top: 32px;
    color: var(--text-dim);
    font-size: 10px;
    line-height: 1.8;
  }

  /* ── HEADER ── */
  header {
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    padding: 0 20px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .header-brand {
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.08em;
  }
  .header-brand span { color: var(--cyan); }
  .header-tag {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    border: 1px solid var(--border);
    padding: 2px 8px;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
  }
  .live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    display: inline-block;
    margin-right: 6px;
    animation: pulse-dot 2s infinite;
  }
  @keyframes pulse-dot {
    0%,100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  .header-time {
    color: var(--cyan);
    font-size: 11px;
  }

  /* ── MAIN LAYOUT ── */
  .app {
    display: grid;
    grid-template-columns: 220px 1fr 280px;
    flex: 1;
    overflow: hidden;
  }

  /* ── SIDEBAR ── */
  .sidebar {
    background: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }
  .sidebar-section {
    padding: 16px;
    border-bottom: 1px solid var(--border);
  }
  .sidebar-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .domain-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: none;
    border: 1px solid transparent;
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 11px;
    cursor: pointer;
    width: 100%;
    text-align: left;
    margin-bottom: 4px;
    letter-spacing: 0.05em;
    transition: all 0.15s;
  }
  .domain-btn:hover { border-color: var(--border); color: var(--text); }
  .domain-btn.active {
    background: rgba(0,212,255,0.08);
    border-color: var(--cyan-dim);
    color: var(--cyan);
  }
  .domain-icon { font-size: 14px; }
  .asset-item {
    padding: 8px 12px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    border-left: 2px solid var(--border);
    margin-bottom: 4px;
    cursor: pointer;
    transition: all 0.15s;
    letter-spacing: 0.05em;
  }
  .asset-item:hover { border-color: var(--cyan-dim); color: var(--text); }
  .asset-item.active { border-color: var(--cyan); color: var(--cyan); }
  .asset-status {
    float: right;
    font-size: 8px;
    letter-spacing: 0.1em;
  }
  .status-nominal { color: var(--green); }
  .status-advisory { color: #FFD700; }
  .status-warning { color: var(--amber); }
  .status-critical { color: var(--red); }

  /* ── CENTER PANEL ── */
  .center {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg);
  }

  .center-top {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 0;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  /* ── RADAR DIAL ── */
  .radar-panel {
    padding: 24px;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .radar-title {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 16px;
    align-self: flex-start;
  }
  .radar-wrap {
    position: relative;
    width: 200px;
    height: 200px;
  }
  .radar-svg { width: 100%; height: 100%; }

  /* Radar sweep animation */
  @keyframes radar-sweep {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  .radar-sweep-group {
    transform-origin: 100px 100px;
    animation: radar-sweep 3s linear infinite;
  }

  .radar-cci-label {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    pointer-events: none;
  }
  .radar-cci-value {
    font-family: var(--mono);
    font-size: 32px;
    font-weight: 700;
    color: #fff;
    line-height: 1;
  }
  .radar-cci-sub {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-top: 4px;
  }

  .alert-badge {
    margin-top: 16px;
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    padding: 6px 20px;
    border: 1px solid;
    text-align: center;
    width: 100%;
  }
  .badge-nominal  { color: var(--green);  border-color: var(--green);  background: rgba(0,255,136,0.05); }
  .badge-advisory { color: #FFD700;       border-color: #FFD700;       background: rgba(255,215,0,0.05); }
  .badge-warning  { color: var(--amber);  border-color: var(--amber);  background: rgba(255,140,0,0.08); }
  .badge-critical {
    color: var(--red); border-color: var(--red);
    background: rgba(255,51,51,0.1);
    animation: critical-pulse 1s infinite;
  }
  @keyframes critical-pulse {
    0%,100% { background: rgba(255,51,51,0.10); }
    50%      { background: rgba(255,51,51,0.22); }
  }

  /* ── METRICS PANEL ── */
  .metrics-panel {
    padding: 20px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    align-content: start;
  }
  .metric-card {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 14px;
  }
  .metric-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .metric-value {
    font-family: var(--mono);
    font-size: 20px;
    font-weight: 600;
    color: #fff;
    line-height: 1;
  }
  .metric-value.cyan  { color: var(--cyan); }
  .metric-value.green { color: var(--green); }
  .metric-value.amber { color: var(--amber); }
  .metric-value.red   { color: var(--red); }
  .metric-value.purple { color: var(--purple); }
  .metric-sub {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    margin-top: 4px;
  }

  /* ── CHANNELS ── */
  .channels-panel {
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
  }
  .channels-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .channel-row {
    display: grid;
    grid-template-columns: 160px 1fr 60px 80px;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(26,47,80,0.5);
  }
  .channel-name {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text);
    letter-spacing: 0.05em;
  }
  .channel-name .ch-id {
    color: var(--text-dim);
    font-size: 9px;
    display: block;
    margin-bottom: 2px;
  }
  .channel-bar-wrap {
    height: 4px;
    background: rgba(26,47,80,0.8);
    border-radius: 0;
    overflow: hidden;
  }
  .channel-bar {
    height: 100%;
    transition: width 1.2s cubic-bezier(0.4,0,0.2,1);
  }
  .channel-score {
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 600;
    text-align: right;
  }
  .channel-status {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.15em;
    text-align: right;
    text-transform: uppercase;
  }
  .ch-pass    { color: var(--green); }
  .ch-rising  { color: #FFD700; }
  .ch-confirm { color: var(--amber); }
  .ch-alert   { color: var(--red); }

  /* ── RIGHT PANEL ── */
  .right-panel {
    background: var(--panel);
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .right-section {
    border-bottom: 1px solid var(--border);
    padding: 16px;
  }
  .right-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
  }

  /* Runway */
  .runway-value {
    font-family: var(--mono);
    font-size: 28px;
    font-weight: 700;
    color: var(--amber);
    line-height: 1;
    margin-bottom: 4px;
  }
  .runway-label {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    margin-bottom: 12px;
  }
  .runway-trend {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--amber);
    margin-bottom: 8px;
  }
  .action-box {
    background: rgba(255,140,0,0.06);
    border: 1px solid rgba(255,140,0,0.2);
    padding: 10px 12px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text);
    line-height: 1.6;
    letter-spacing: 0.02em;
  }
  .action-box .action-head {
    color: var(--amber);
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  /* Gate check rows */
  .gate-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid rgba(26,47,80,0.4);
    font-family: var(--mono);
    font-size: 10px;
  }
  .gate-row:last-child { border-bottom: none; }
  .gate-row-label { color: var(--text-dim); letter-spacing: 0.05em; }
  .gate-pass    { color: var(--green);  font-size: 9px; letter-spacing: 0.15em; }
  .gate-rising  { color: #FFD700;       font-size: 9px; letter-spacing: 0.15em; }
  .gate-confirm { color: var(--amber);  font-size: 9px; letter-spacing: 0.15em; }
  .gate-alert   { color: var(--red);    font-size: 9px; letter-spacing: 0.15em; }

  /* Timeline */
  .timeline {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }
  .tl-item {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
    position: relative;
  }
  .tl-item::before {
    content: '';
    position: absolute;
    left: 5px; top: 18px;
    width: 1px;
    height: calc(100% + 8px);
    background: var(--border);
  }
  .tl-item:last-child::before { display: none; }
  .tl-dot {
    width: 11px; height: 11px;
    border-radius: 50%;
    border: 2px solid;
    flex-shrink: 0;
    margin-top: 3px;
    background: var(--bg);
    position: relative;
    z-index: 1;
  }
  .tl-content {}
  .tl-time {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    margin-bottom: 2px;
  }
  .tl-text {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text);
    line-height: 1.5;
  }

  /* Footer bar */
  footer {
    background: var(--panel);
    border-top: 1px solid var(--border);
    padding: 6px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
  .footer-left {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
  }
  .footer-right {
    display: flex;
    gap: 16px;
  }
  .footer-btn {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.15em;
    color: var(--cyan);
    background: none;
    border: 1px solid var(--cyan-dim);
    padding: 4px 12px;
    cursor: pointer;
    text-transform: uppercase;
    transition: all 0.15s;
  }
  .footer-btn:hover { background: rgba(0,212,255,0.08); }

  /* Scan button */
  .scan-btn {
    margin-top: 12px;
    width: 100%;
    background: none;
    border: 1px solid var(--cyan-dim);
    color: var(--cyan);
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.2em;
    padding: 10px;
    cursor: pointer;
    text-transform: uppercase;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
  }
  .scan-btn:hover {
    background: rgba(0,212,255,0.08);
    border-color: var(--cyan);
  }
  .scan-btn.scanning {
    color: var(--text-dim);
    border-color: var(--border);
    cursor: not-allowed;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); }

  /* Executive Mode button */
  .exec-mode-btn {
    font-family: var(--mono);
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.15em;
    color: var(--purple);
    background: none;
    border: 1px solid rgba(139,92,246,0.4);
    padding: 5px 14px;
    cursor: pointer;
    text-transform: uppercase;
    transition: all 0.15s;
  }
  .exec-mode-btn:hover { background: rgba(139,92,246,0.08); }
  .exec-mode-btn.active {
    background: rgba(139,92,246,0.15);
    border-color: var(--purple);
    color: #fff;
  }

  /* Executive Mode overlay */
  #exec-overlay {
    display: none;
    position: fixed;
    inset: 48px 0 0 0;
    background: #080B0F;
    z-index: 90;
    overflow-y: auto;
    padding: 40px;
  }
  #exec-overlay.open { display: block; }

  .exec-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  .exec-brand {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .exec-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--paper, #E8E2D6);
    letter-spacing: -0.01em;
  }
  .exec-meta {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    text-align: right;
    line-height: 1.8;
  }

  .exec-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  .exec-card {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 28px 24px;
  }
  .exec-card-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .exec-card-value {
    font-family: var(--mono);
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 6px;
  }
  .exec-card-sub {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 0.06em;
  }

  .exec-action {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 28px 32px;
    margin-bottom: 24px;
  }
  .exec-action-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .exec-action-text {
    font-size: 16px;
    color: #fff;
    line-height: 1.6;
    font-weight: 400;
  }

  .exec-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 11px;
  }
  .exec-row:last-child { border-bottom: none; }
  .exec-row-label { color: var(--text-dim); letter-spacing: 0.06em; }
  .exec-row-value { color: var(--text); }

  .exec-btns {
    display: flex;
    gap: 12px;
    margin-top: 32px;
    flex-wrap: wrap;
  }
  .exec-btn {
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.18em;
    padding: 14px 28px;
    cursor: pointer;
    text-transform: uppercase;
    border: none;
    transition: opacity 0.15s;
  }
  .exec-btn-primary { background: var(--cyan); color: var(--bg); }
  .exec-btn-secondary { background: none; border: 1px solid var(--border); color: var(--text); }
  .exec-btn:hover { opacity: 0.85; }

  .exec-disclaimer {
    margin-top: 32px;
    padding: 16px 20px;
    border: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.06em;
    line-height: 1.8;
  }

  .exec-no-scan {
    text-align: center;
    padding: 80px 0;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
  }

  /* Audit hash */
  .audit-row {
    font-family: var(--mono);
    font-size: 8px;
    color: var(--text-dim);
    letter-spacing: 0.05em;
    word-break: break-all;
    line-height: 1.6;
    margin-top: 8px;
  }
  .audit-row span { color: var(--text-dim); }

  /* Confidence ring */
  .confidence-ring-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 8px;
  }
  .conf-svg { width: 48px; height: 48px; }
  .conf-info { flex: 1; }
  .conf-pct {
    font-family: var(--mono);
    font-size: 18px;
    font-weight: 700;
    color: var(--purple);
  }
  .conf-label {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    margin-top: 2px;
  }

  @media (max-width: 900px) {
    .app { grid-template-columns: 1fr; }
    .sidebar, .right-panel { display: none; }
    .center-top { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<!-- GATE -->
<div id="gate">
  <div class="gate-box">
    <div class="gate-logo">AW IP Holdings Inc.</div>
    <div class="gate-title">PRECEPT Scout</div>
    <div class="gate-sub">Multi-Hazard Precursor Intelligence Platform<br>Authorized access only — NDA required for full disclosure</div>
    <div class="gate-label">Access Code</div>
    <input class="gate-input" id="gate-input" type="text" placeholder="XXXX-XXXXX" autocomplete="off" spellcheck="false">
    <button class="gate-btn" onclick="checkGate()">Initialize Session</button>
    <div class="gate-error" id="gate-error"></div>
    <div class="gate-footer">
      PRECEPT Scout Edition — Evaluation License<br>
      Engine: SENTINEL · Build: TC-ENGINE-2025-V3-PROD<br>
      © 2025 AW IP Holdings Inc. All rights reserved.
    </div>
  </div>
</div>

<!-- HEADER -->
<header>
  <div class="header-left">
    <div class="header-brand"><span>PRECEPT</span> SCOUT</div>
    <div class="header-tag">Multi-Hazard Intelligence</div>
    <div class="header-tag">TC-ENGINE-2025-V3-PROD</div>
  </div>
  <div class="header-right">
    <span><span class="live-dot"></span>ENGINE LIVE</span>
    <span class="header-time" id="clock">--:--:-- UTC</span>
    <button class="exec-mode-btn" id="exec-btn" onclick="toggleExecMode()">⬛ EXECUTIVE MODE</button>
    <span>SESSION ACTIVE</span>
  </div>
</header>

<!-- APP -->
<div class="app">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">Domain</div>
      <button class="domain-btn active" onclick="setDomain('seismic',this)">
        <span class="domain-icon">🌍</span> Seismic
      </button>
      <button class="domain-btn" onclick="setDomain('volcanic',this)">
        <span class="domain-icon">🌋</span> Volcanic
      </button>
      <button class="domain-btn" onclick="setDomain('structural',this)">
        <span class="domain-icon">🏗️</span> Structural
      </button>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-label">Monitored Targets — Demo</div>
      <div class="asset-item active" onclick="setAsset(this,'FAULT-CASCADE-01')">
        FAULT-CASCADE-01 <span class="asset-status status-warning">WARN</span>
      </div>
      <div class="asset-item" onclick="setAsset(this,'FAULT-PACIFIC-07')">
        FAULT-PACIFIC-07 <span class="asset-status status-nominal">NOM</span>
      </div>
      <div class="asset-item" onclick="setAsset(this,'NETWORK-ARRAY-B')">
        NETWORK-ARRAY-B <span class="asset-status status-advisory">ADV</span>
      </div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-label">Engine Status</div>
      <div class="gate-row">
        <span class="gate-row-label">Persistence Gate</span>
        <span class="gate-pass" id="sb-persist">ACTIVE</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Surrogate Check</span>
        <span class="gate-pass" id="sb-surr">ACTIVE</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Domain Weights</span>
        <span class="gate-pass">LOADED</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Channels</span>
        <span class="gate-pass">5 / 5</span>
      </div>
    </div>
    <div class="sidebar-section" style="flex:1">
      <div class="sidebar-label">Disclaimer</div>
      <div style="font-size:9px;color:var(--text-dim);line-height:1.7;font-family:var(--mono);">
        Scout Edition runs controlled demonstration scenarios for interface review. Operational deployment requires empirical validation against approved instrument datasets.
      </div>
    </div>
  </div>

  <!-- CENTER -->
  <div class="center">
    <div class="center-top">

      <!-- RADAR -->
      <div class="radar-panel">
        <div class="radar-title">Coherence Convergence Index</div>
        <div class="radar-wrap">
          <svg class="radar-svg" viewBox="0 0 200 200" id="radar-svg">
            <!-- Grid rings -->
            <circle cx="100" cy="100" r="90" fill="none" stroke="#1A2F50" stroke-width="1"/>
            <circle cx="100" cy="100" r="67" fill="none" stroke="#1A2F50" stroke-width="0.5"/>
            <circle cx="100" cy="100" r="45" fill="none" stroke="#1A2F50" stroke-width="0.5"/>
            <circle cx="100" cy="100" r="22" fill="none" stroke="#1A2F50" stroke-width="0.5"/>
            <!-- Grid lines -->
            <line x1="10" y1="100" x2="190" y2="100" stroke="#1A2F50" stroke-width="0.5"/>
            <line x1="100" y1="10" x2="100" y2="190" stroke="#1A2F50" stroke-width="0.5"/>
            <line x1="36" y1="36" x2="164" y2="164" stroke="#1A2F50" stroke-width="0.5"/>
            <line x1="164" y1="36" x2="36" y2="164" stroke="#1A2F50" stroke-width="0.5"/>
            <!-- Threshold arcs -->
            <path id="arc-advisory" d="" fill="none" stroke="#FFD70033" stroke-width="2"/>
            <path id="arc-warning"  d="" fill="none" stroke="#FF8C0033" stroke-width="2"/>
            <path id="arc-critical" d="" fill="none" stroke="#FF333333" stroke-width="2"/>
            <!-- CCI fill arc -->
            <path id="cci-arc" d="" fill="rgba(0,212,255,0.06)" stroke="none"/>
            <path id="cci-arc-border" d="" fill="none" stroke="#00D4FF" stroke-width="1.5"/>
            <!-- Sweep -->
            <g class="radar-sweep-group">
              <defs>
                <radialGradient id="sweepGrad" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#00D4FF" stop-opacity="0.0"/>
                  <stop offset="100%" stop-color="#00D4FF" stop-opacity="0.18"/>
                </radialGradient>
              </defs>
              <path d="M100,100 L100,10 A90,90 0 0,1 163.6,136.4 Z" fill="url(#sweepGrad)"/>
              <line x1="100" y1="100" x2="100" y2="10" stroke="#00D4FF" stroke-width="1" opacity="0.6"/>
            </g>
            <!-- Threshold labels -->
            <text x="150" y="68" fill="#FFD70066" font-size="7" font-family="JetBrains Mono">0.65</text>
            <text x="156" y="52" fill="#FF8C0066" font-size="7" font-family="JetBrains Mono">0.78</text>
            <text x="148" y="38" fill="#FF333366" font-size="7" font-family="JetBrains Mono">0.88</text>
          </svg>
          <div class="radar-cci-label">
            <div class="radar-cci-value" id="cci-display">—</div>
            <div class="radar-cci-sub">CCI</div>
          </div>
        </div>
        <div class="alert-badge badge-nominal" id="alert-badge">— INITIALIZING —</div>
        <button class="scan-btn" id="scan-btn" onclick="runScan()">▶ RUN PRECURSOR SCAN</button>
      </div>

      <!-- METRICS -->
      <div class="metrics-panel">
        <div class="metric-card">
          <div class="metric-label">Confidence</div>
          <div class="metric-value purple" id="met-conf">—</div>
          <div class="metric-sub">composite score</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Persistence</div>
          <div class="metric-value cyan" id="met-persist">—</div>
          <div class="metric-sub">gate satisfaction</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Surrogate Z</div>
          <div class="metric-value green" id="met-z">—</div>
          <div class="metric-sub">σ above noise floor</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Raw Alert</div>
          <div class="metric-value amber" id="met-raw">—</div>
          <div class="metric-sub">pre-gate level</div>
        </div>
        <div class="metric-card" style="grid-column:1/-1">
          <div class="metric-label">Audit Hash</div>
          <div class="audit-row" id="met-hash">Awaiting scan...</div>
        </div>
      </div>

    </div>

    <!-- CHANNELS -->
    <div class="channels-panel">
      <div class="channels-label">Engine Channels — 5-Channel CCI</div>
      <div id="channel-rows">
        <div style="font-family:var(--mono);font-size:10px;color:var(--text-dim);padding:20px 0;">
          Run a precursor scan to initialize channel scoring.
        </div>
      </div>
    </div>
  </div>

  <!-- RIGHT PANEL -->
  <div class="right-panel">

    <!-- Runway -->
    <div class="right-section">
      <div class="right-label">Estimated Runway</div>
      <div class="runway-value" id="runway-value">—</div>
      <div class="runway-label" id="runway-label">awaiting scan</div>
      <div class="runway-trend" id="runway-trend"></div>
      <div class="action-box" id="action-box">
        <div class="action-head">Recommended Action</div>
        <div id="action-text">Initialize scan to generate assessment.</div>
      </div>
    </div>

    <!-- Gate checks -->
    <div class="right-section">
      <div class="right-label">Validation Gates</div>
      <div class="gate-row">
        <span class="gate-row-label">Geometry Drift</span>
        <span id="gc-drift" class="gate-pass">—</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Phase Coupling</span>
        <span id="gc-plv" class="gate-pass">—</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Spectral Stress</span>
        <span id="gc-bval" class="gate-pass">—</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Persistence Gate</span>
        <span id="gc-persist" class="gate-pass">—</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Surrogate Check</span>
        <span id="gc-surr" class="gate-pass">—</span>
      </div>
      <div class="gate-row">
        <span class="gate-row-label">Domain Consensus</span>
        <span id="gc-domain" class="gate-pass">—</span>
      </div>
    </div>

    <!-- Timeline -->
    <div class="timeline" id="timeline">
      <div class="right-label">Event Timeline</div>
      <div id="tl-items">
        <div style="font-family:var(--mono);font-size:10px;color:var(--text-dim);">
          No events recorded.
        </div>
      </div>
    </div>

  </div>
</div>

<!-- EXECUTIVE MODE OVERLAY -->
<div id="exec-overlay">
  <div id="exec-content">
    <div class="exec-no-scan" id="exec-no-scan">
      RUN A PRECURSOR SCAN TO GENERATE EXECUTIVE ASSESSMENT
    </div>
    <div id="exec-data" style="display:none">
      <div class="exec-header">
        <div>
          <div class="exec-brand">PRECEPT Scout · AW IP Holdings Inc. · Executive Assessment</div>
          <div class="exec-title" id="exec-title">Risk Assessment</div>
        </div>
        <div class="exec-meta" id="exec-meta"></div>
      </div>

      <div class="exec-grid">
        <div class="exec-card">
          <div class="exec-card-label">Risk Level</div>
          <div class="exec-card-value" id="exec-risk">—</div>
          <div class="exec-card-sub" id="exec-risk-sub">—</div>
        </div>
        <div class="exec-card">
          <div class="exec-card-label">Confidence</div>
          <div class="exec-card-value" id="exec-conf" style="color:var(--purple)">—</div>
          <div class="exec-card-sub">composite score</div>
        </div>
        <div class="exec-card">
          <div class="exec-card-label">Estimated Runway</div>
          <div class="exec-card-value" id="exec-runway" style="font-size:24px">—</div>
          <div class="exec-card-sub" id="exec-runway-sub">—</div>
        </div>
      </div>

      <div class="exec-action">
        <div class="exec-action-label">Recommended Action</div>
        <div class="exec-action-text" id="exec-action-text">—</div>
      </div>

      <div style="background:var(--panel);border:1px solid var(--border);padding:20px 24px">
        <div class="exec-row">
          <span class="exec-row-label">Domain</span>
          <span class="exec-row-value" id="exec-domain">—</span>
        </div>
        <div class="exec-row">
          <span class="exec-row-label">Asset</span>
          <span class="exec-row-value" id="exec-asset">—</span>
        </div>
        <div class="exec-row">
          <span class="exec-row-label">CCI Score</span>
          <span class="exec-row-value" id="exec-cci">—</span>
        </div>
        <div class="exec-row">
          <span class="exec-row-label">Trend</span>
          <span class="exec-row-value" id="exec-trend">—</span>
        </div>
        <div class="exec-row">
          <span class="exec-row-label">Timestamp</span>
          <span class="exec-row-value" id="exec-ts">—</span>
        </div>
        <div class="exec-row">
          <span class="exec-row-label">Audit Hash</span>
          <span class="exec-row-value" id="exec-hash" style="font-size:9px;letter-spacing:0.04em">—</span>
        </div>
      </div>

      <div class="exec-btns">
        <button class="exec-btn exec-btn-primary" onclick="exportReport()">⬇ Export Report</button>
        <button class="exec-btn exec-btn-primary" onclick="exportCAP()">⬇ Demo CAP XML</button>
        <button class="exec-btn exec-btn-secondary" onclick="acknowledgeAlert()">✓ Acknowledge Alert</button>
        <button class="exec-btn exec-btn-secondary" onclick="toggleExecMode()">← Technical View</button>
      </div>

      <div class="exec-disclaimer">
        PRECEPT Scout · TC-ENGINE-2025-V3-PROD · AW IP Holdings Inc.<br>
        Scout Edition runs controlled demonstration scenarios for interface review.<br>
        Operational deployment requires empirical validation against approved instrument datasets.<br>
        Not for emergency use without validation, configuration, and authority approval.
      </div>
    </div>
  </div>
</div>

<!-- FOOTER -->
<footer>
  <div class="footer-left">
    PRECEPT SCOUT · AW IP Holdings Inc. · Evaluation License ·
    <span id="domain-display">SEISMIC</span> ·
    <span id="asset-display">FAULT-CASCADE-01</span>
  </div>
  <div class="footer-right">
    <button class="footer-btn" onclick="exportReport()">⬇ Export Report</button>
    <button class="footer-btn" onclick="exportCAP()">⬇ Demo CAP XML</button>
    <button class="footer-btn" onclick="acknowledgeAlert()">✓ Acknowledge</button>
  </div>
</footer>

<script>
// ── STATE ──────────────────────────────────────────────────────────────────
let currentDomain = 'seismic';
let currentAsset  = 'FAULT-CASCADE-01';
let lastResult    = null;
let scanCount     = 0;
let tlEvents      = [];

// ── GATE ───────────────────────────────────────────────────────────────────
// Access gate — demo codes for interface review only.
// Not a security boundary. Real access control requires server-side authentication.
const VALID_CODES = ['PRECEPT-SCOUT', 'PRECEPT30', 'AWIP-DEMO'];

function checkGate() {
  const val = document.getElementById('gate-input').value.trim().toUpperCase();
  if (VALID_CODES.includes(val)) {
    document.getElementById('gate').style.opacity = '0';
    document.getElementById('gate').style.transition = 'opacity 0.5s';
    setTimeout(() => document.getElementById('gate').style.display = 'none', 500);
    addTimeline('SESSION INITIALIZED', `Domain: ${currentDomain.toUpperCase()} · Asset: ${currentAsset}`, 'cyan');
  } else {
    document.getElementById('gate-error').textContent = 'INVALID ACCESS CODE — CONTACT AW IP HOLDINGS INC.';
    document.getElementById('gate-input').style.borderColor = 'var(--red)';
    setTimeout(() => {
      document.getElementById('gate-error').textContent = '';
      document.getElementById('gate-input').style.borderColor = 'var(--border)';
    }, 3000);
  }
}
document.getElementById('gate-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') checkGate();
});

// ── CLOCK ──────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent =
    now.toISOString().replace('T',' ').substring(0,19) + ' UTC';
}
setInterval(updateClock, 1000);
updateClock();

// ── DOMAIN / ASSET ─────────────────────────────────────────────────────────
function setDomain(d, btn) {
  currentDomain = d;
  document.querySelectorAll('.domain-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('domain-display').textContent = d.toUpperCase();

  const assets = {
    seismic:    ['FAULT-CASCADE-01','FAULT-PACIFIC-07','NETWORK-ARRAY-B'],
    volcanic:   ['VOLCANO-ALPHA-01','TREMOR-ARRAY-03','VENT-MONITOR-07'],
    structural: ['BRIDGE-HWY401-N','DAM-NIAGARA-S','TUNNEL-BORE-12'],
  };
  const statuses = ['WARN','NOM','ADV'];
  const scls = ['status-warning','status-nominal','status-advisory'];
  const assetDiv = document.querySelector('.sidebar .sidebar-section:nth-child(2)');
  assetDiv.innerHTML = `<div class="sidebar-label">Monitored Targets — Demo</div>`;
  assets[d].forEach((a,i) => {
    const el = document.createElement('div');
    el.className = 'asset-item' + (i===0?' active':'');
    el.innerHTML = `${a} <span class="asset-status ${scls[i]}">${statuses[i]}</span>`;
    el.onclick = () => setAsset(el, a);
    assetDiv.appendChild(el);
  });
  currentAsset = assets[d][0];
  document.getElementById('asset-display').textContent = assets[d][0];
}

function setAsset(el, name) {
  currentAsset = name;
  document.querySelectorAll('.asset-item').forEach(a => a.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('asset-display').textContent = name;
}

// ── RADAR ARC ──────────────────────────────────────────────────────────────
function polarToCart(cx, cy, r, angleDeg) {
  const a = (angleDeg - 90) * Math.PI / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function arcPath(cx, cy, r, startDeg, endDeg) {
  const s = polarToCart(cx, cy, r, startDeg);
  const e = polarToCart(cx, cy, r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M${s.x.toFixed(2)},${s.y.toFixed(2)} A${r},${r} 0 ${large},1 ${e.x.toFixed(2)},${e.y.toFixed(2)}`;
}

function cciArcPath(cx, cy, maxR, cci) {
  const r = maxR * cci;
  const pts = [];
  for (let a = 0; a <= 360; a += 5) {
    const p = polarToCart(cx, cy, r, a);
    pts.push(`${a===0?'M':'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`);
  }
  return pts.join(' ') + ' Z';
}

function initRadar() {
  document.getElementById('arc-advisory').setAttribute('d', arcPath(100,100,60.75,0,360));
  document.getElementById('arc-warning').setAttribute('d',  arcPath(100,100,70.2,0,360));
  document.getElementById('arc-critical').setAttribute('d', arcPath(100,100,79.2,0,360));
}
initRadar();

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function updateRadar(cci) {
  const path = cciArcPath(100, 100, 90, cci);
  document.getElementById('cci-arc').setAttribute('d', path);
  document.getElementById('cci-arc-border').setAttribute('d', path);

  let color = '#00FF88';
  if (cci >= 0.88) color = '#FF3333';
  else if (cci >= 0.78) color = '#FF8C00';
  else if (cci >= 0.65) color = '#FFD700';
  document.getElementById('cci-arc-border').setAttribute('stroke', color);
  document.getElementById('cci-arc').setAttribute('fill', hexToRgba(color, 0.06));
}

// ── DEMO DATA GENERATOR ────────────────────────────────────────────────────
function getDemoData(domain, scanNum) {
  const profiles = {
    seismic: [
      { cci:0.42, alert:'NOMINAL',  conf:0.61, persist:0.20, z:2.1 },
      { cci:0.58, alert:'NOMINAL',  conf:0.64, persist:0.40, z:3.4 },
      { cci:0.67, alert:'ADVISORY', conf:0.68, persist:0.60, z:4.8 },
      { cci:0.74, alert:'ADVISORY', conf:0.72, persist:0.80, z:6.2 },
      { cci:0.81, alert:'WARNING',  conf:0.79, persist:1.00, z:8.7 },
      { cci:0.86, alert:'WARNING',  conf:0.83, persist:1.00, z:10.3 },
      { cci:0.91, alert:'CRITICAL', conf:0.88, persist:1.00, z:13.1 },
    ],
    volcanic: [
      { cci:0.38, alert:'NOMINAL',  conf:0.55, persist:0.20, z:1.8 },
      { cci:0.52, alert:'NOMINAL',  conf:0.60, persist:0.40, z:2.9 },
      { cci:0.69, alert:'ADVISORY', conf:0.65, persist:0.60, z:4.1 },
      { cci:0.77, alert:'ADVISORY', conf:0.71, persist:0.80, z:6.8 },
      { cci:0.83, alert:'WARNING',  conf:0.78, persist:1.00, z:9.2 },
    ],
    structural: [
      { cci:0.44, alert:'NOMINAL',  conf:0.58, persist:0.20, z:2.3 },
      { cci:0.61, alert:'ADVISORY', conf:0.66, persist:0.60, z:4.4 },
      { cci:0.79, alert:'WARNING',  conf:0.76, persist:1.00, z:7.9 },
      { cci:0.89, alert:'CRITICAL', conf:0.85, persist:1.00, z:11.6 },
    ],
  };
  const p = profiles[domain];
  const idx = Math.min(scanNum, p.length - 1);
  const base = p[idx];

  const jitter = (v, range) => Math.max(0, Math.min(1, v + (Math.random()-0.5)*range));

  const channels = {
    seismic: [
      { id:'CH-01', name:'Spectral Stress', label:'b_value' },
      { id:'CH-02', name:'Kalman Geometry', label:'kappa' },
      { id:'CH-03', name:'Attractor Drift', label:'attractor_drift' },
      { id:'CH-04', name:'Phase Coupling',  label:'plv' },
      { id:'CH-05', name:'Temporal Cluster',label:'ljung_box' },
    ],
    volcanic: [
      { id:'CH-01', name:'Tremor Stress',   label:'b_value' },
      { id:'CH-02', name:'Kalman Geometry', label:'kappa' },
      { id:'CH-03', name:'Attractor Drift', label:'attractor_drift' },
      { id:'CH-04', name:'Phase Coupling',  label:'plv' },
      { id:'CH-05', name:'Temporal Cluster',label:'ljung_box' },
    ],
    structural: [
      { id:'CH-01', name:'AE Stress Index', label:'b_value' },
      { id:'CH-02', name:'Kalman Geometry', label:'kappa' },
      { id:'CH-03', name:'Attractor Drift', label:'attractor_drift' },
      { id:'CH-04', name:'Phase Coupling',  label:'plv' },
      { id:'CH-05', name:'Temporal Cluster',label:'ljung_box' },
    ],
  };

  const chScores = channels[domain].map((c,i) => {
    const base_score = jitter(base.cci + (i%3===0?0.05:-0.04), 0.12);
    return { ...c, score: Math.max(0,Math.min(1, base_score)) };
  });

  return {
    ...base,
    cci: jitter(base.cci, 0.03),
    channels: chScores,
    hash: Array.from({length:32}, () => Math.floor(Math.random()*16).toString(16)).join(''),
    domain,
    asset: currentAsset,
    timestamp: new Date().toISOString(),
  };
}

// ── RUNWAY LOGIC ───────────────────────────────────────────────────────────
function getRunway(alert, domain) {
  const runways = {
    NOMINAL:  { value:'No Actionable Precursor', label:'Baseline stable across all channels', trend:'', action:'Continue baseline monitoring. No operator action required.', color:'green' },
    ADVISORY: { value:'Monitoring Window', label:'Early instability emerging — watch closely', trend:'↗ RISING', action:'Increase sampling frequency. Alert duty operator. Begin precautionary review.', color:'amber' },
    WARNING:  { value:'Escalation Window', label:'Multi-channel convergence confirmed', trend:'↑ ACCELERATING', action:'Restrict access. Notify operations lead. Escalate to emergency protocol if trend continues.', color:'amber' },
    CRITICAL: { value:'Immediate Review Required', label:'Strong pre-bifurcation signal detected', trend:'⚠ ACCELERATING', action:'Escalate immediately. Notify operations lead. Restrict zone access. Export alert and log to audit trail.', color:'red' },
  };
  return runways[alert] || runways.NOMINAL;
}

// ── CHANNEL STATUS LABEL ───────────────────────────────────────────────────
function channelStatus(score) {
  if (score >= 0.80) return { label:'ALERT',    cls:'ch-alert' };
  if (score >= 0.65) return { label:'RISING',   cls:'ch-rising' };
  if (score >= 0.45) return { label:'WATCH',    cls:'ch-confirm' };
  return                    { label:'STABLE',   cls:'ch-pass' };
}
function channelColor(score) {
  if (score >= 0.80) return '#FF3333';
  if (score >= 0.65) return '#FFD700';
  if (score >= 0.45) return '#FF8C00';
  return '#00FF88';
}

// ── GATE STATUS ────────────────────────────────────────────────────────────
function gateLabel(val, thresholds) {
  if (val >= thresholds[1]) return { label:'CONFIRMED', cls:'gate-confirm' };
  if (val >= thresholds[0]) return { label:'RISING',    cls:'gate-rising' };
  return                           { label:'PASS',      cls:'gate-pass' };
}
function alertGateLabel(alert) {
  if (alert === 'CRITICAL') return { label:'CONFIRMED', cls:'gate-confirm' };
  if (alert === 'WARNING')  return { label:'RISING',    cls:'gate-rising' };
  if (alert === 'ADVISORY') return { label:'WATCH',     cls:'gate-confirm' };
  return                           { label:'PASS',      cls:'gate-pass' };
}

// ── SCAN ───────────────────────────────────────────────────────────────────
function runScan() {
  const btn = document.getElementById('scan-btn');
  btn.classList.add('scanning');
  btn.textContent = '⟳ SCANNING...';

  setTimeout(() => {
    const data = getDemoData(currentDomain, scanCount);
    scanCount++;
    lastResult = data;
    renderResult(data);
    btn.classList.remove('scanning');
    btn.textContent = '▶ RUN PRECURSOR SCAN';
  }, 1800);
}

function renderResult(data) {
  // CCI dial
  document.getElementById('cci-display').textContent = data.cci.toFixed(3);
  updateRadar(data.cci);

  // Alert badge
  const badge = document.getElementById('alert-badge');
  const badgeClasses = { NOMINAL:'badge-nominal', ADVISORY:'badge-advisory', WARNING:'badge-warning', CRITICAL:'badge-critical' };
  badge.className = 'alert-badge ' + (badgeClasses[data.alert] || 'badge-nominal');
  badge.textContent = data.alert;

  // Metrics
  document.getElementById('met-conf').textContent    = (data.conf * 100).toFixed(0) + '%';
  document.getElementById('met-persist').textContent = (data.persist * 100).toFixed(0) + '%';
  document.getElementById('met-z').textContent       = data.z.toFixed(1) + 'σ';
  document.getElementById('met-raw').textContent     = data.alert;
  document.getElementById('met-hash').textContent    = data.hash;

  // Channels
  const ch = document.getElementById('channel-rows');
  ch.innerHTML = '';
  data.channels.forEach(c => {
    const st = channelStatus(c.score);
    const color = channelColor(c.score);
    const row = document.createElement('div');
    row.className = 'channel-row';
    row.innerHTML = `
      <div class="channel-name">
        <span class="ch-id">${c.id} · ${c.label}</span>
        ${c.name}
      </div>
      <div class="channel-bar-wrap">
        <div class="channel-bar" style="width:0%;background:${color}" data-target="${c.score*100}"></div>
      </div>
      <div class="channel-score" style="color:${color}">${c.score.toFixed(3)}</div>
      <div class="channel-status ${st.cls}">${st.label}</div>
    `;
    ch.appendChild(row);
  });
  // Animate bars
  setTimeout(() => {
    document.querySelectorAll('.channel-bar').forEach(b => {
      b.style.width = b.dataset.target + '%';
    });
  }, 50);

  // Runway
  const rw = getRunway(data.alert, data.domain);
  document.getElementById('runway-value').textContent  = rw.value;
  document.getElementById('runway-value').className    = 'runway-value ' + rw.color;
  document.getElementById('runway-label').textContent  = rw.label;
  document.getElementById('runway-trend').textContent  = rw.trend;
  document.getElementById('action-text').textContent   = rw.action;
  document.getElementById('action-box').style.borderColor =
    rw.color === 'red' ? 'rgba(255,51,51,0.3)' :
    rw.color === 'amber' ? 'rgba(255,140,0,0.2)' : 'rgba(0,255,136,0.2)';

  // Gate checks
  const ch3 = data.channels.find(c=>c.label==='attractor_drift');
  const ch4 = data.channels.find(c=>c.label==='plv');
  const ch1 = data.channels.find(c=>c.label==='b_value');
  const ag = alertGateLabel(data.alert);

  function setGate(id, score) {
    const g = gateLabel(score, [0.45, 0.65]);
    const el = document.getElementById(id);
    el.textContent = g.label;
    el.className = g.cls;
  }
  setGate('gc-drift',  ch3 ? ch3.score : 0);
  setGate('gc-plv',    ch4 ? ch4.score : 0);
  setGate('gc-bval',   ch1 ? ch1.score : 0);

  const pg = document.getElementById('gc-persist');
  pg.textContent = data.persist >= 1.0 ? 'CONFIRMED' : data.persist >= 0.5 ? 'BUILDING' : 'ACCUMULATING';
  pg.className = data.persist >= 1.0 ? 'gate-confirm' : 'gate-rising';

  const sg = document.getElementById('gc-surr');
  sg.textContent = data.z >= 2.0 ? 'PASSED' : 'MARGINAL';
  sg.className = data.z >= 2.0 ? 'gate-pass' : 'gate-rising';

  const dc = document.getElementById('gc-domain');
  dc.textContent = ag.label;
  dc.className = ag.cls;

  // Timeline
  addTimeline(
    `${data.alert} · CCI ${data.cci.toFixed(3)}`,
    `${data.domain.toUpperCase()} · ${data.asset} · conf ${(data.conf*100).toFixed(0)}% · z=${data.z.toFixed(1)}σ`,
    data.alert === 'CRITICAL' ? 'red' :
    data.alert === 'WARNING'  ? 'amber' :
    data.alert === 'ADVISORY' ? 'advisory' : 'green'
  );
}

// ── TIMELINE ───────────────────────────────────────────────────────────────
function addTimeline(title, detail, type) {
  const colors = { red:'#FF3333', amber:'#FF8C00', advisory:'#FFD700', green:'#00FF88', cyan:'#00D4FF' };
  const color = colors[type] || '#00D4FF';
  const now = new Date().toISOString().replace('T',' ').substring(11,19);
  tlEvents.unshift({ title, detail, color, time: now });
  if (tlEvents.length > 12) tlEvents.pop();
  renderTimeline();
}

function renderTimeline() {
  const container = document.getElementById('tl-items');
  container.innerHTML = '';
  tlEvents.forEach(e => {
    const item = document.createElement('div');
    item.className = 'tl-item';
    item.innerHTML = `
      <div class="tl-dot" style="border-color:${e.color}"></div>
      <div class="tl-content">
        <div class="tl-time">${e.time} UTC</div>
        <div class="tl-text" style="color:${e.color}">${e.title}</div>
        <div class="tl-text" style="color:var(--text-dim);font-size:9px;margin-top:2px">${e.detail}</div>
      </div>
    `;
    container.appendChild(item);
  });
}

// ── EXPORT ─────────────────────────────────────────────────────────────────
function exportReport() {
  if (!lastResult) { alert('Run a scan first.'); return; }
  const d = lastResult;
  const lines = [
    'PRECEPT SCOUT — DIAGNOSTIC REPORT',
    '=====================================',
    `AW IP Holdings Inc. | CONFIDENTIAL`,
    `Engine: TC-ENGINE-2025-V3-PROD`,
    `Timestamp: ${d.timestamp}`,
    `Domain: ${d.domain.toUpperCase()}`,
    `Asset: ${d.asset}`,
    '',
    `CCI: ${d.cci.toFixed(4)}`,
    `Alert Level: ${d.alert}`,
    `Confidence: ${(d.conf*100).toFixed(1)}%`,
    `Persistence: ${(d.persist*100).toFixed(1)}%`,
    `Surrogate Z-Score: ${d.z.toFixed(2)}σ`,
    '',
    'CHANNEL SCORES',
    '--------------',
    ...d.channels.map(c => `  ${c.id} ${c.name}: ${c.score.toFixed(4)}`),
    '',
    `Audit Hash: ${d.hash}`,
    '',
    'DISCLAIMER',
    'Scout Edition uses controlled demonstration scenarios.',
    'Operational deployment requires empirical validation against approved instrument datasets.',
    'Not for emergency use without validation, configuration, and authority approval.',
  ];
  const blob = new Blob([lines.join('\n')], {type:'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `PRECEPT-REPORT-${d.asset}-${Date.now()}.txt`;
  a.click();
}

function exportCAP() {
  if (!lastResult) { alert('Run a scan first.'); return; }
  const d = lastResult;
  const urgency = { CRITICAL:'Immediate', WARNING:'Expected', ADVISORY:'Future', NOMINAL:'Unknown' };
  const severity = { CRITICAL:'Extreme', WARNING:'Severe', ADVISORY:'Moderate', NOMINAL:'Minor' };
  const cap = `<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>PRECEPT-${d.domain.toUpperCase()}-${Date.now()}</identifier>
  <sender>AWIP-PRECEPT-SCOUT</sender>
  <sent>${d.timestamp}</sent>
  <status>Test</status>
  <msgType>Alert</msgType>
  <source>PRECEPT Scout · TC-ENGINE-2025-V3-PROD</source>
  <scope>Restricted</scope>
  <note>Synthetic demo data. Not for operational use.</note>
  <info>
    <language>en-CA</language>
    <category>Geo</category>
    <event>${d.domain.toUpperCase()} Precursor Alert</event>
    <urgency>${urgency[d.alert]}</urgency>
    <severity>${severity[d.alert]}</severity>
    <certainty>Likely</certainty>
    <headline>PRECEPT ${d.alert}: ${d.domain.toUpperCase()} precursor detected · CCI ${d.cci.toFixed(4)}</headline>
    <description>Asset ${d.asset} · Confidence ${(d.conf*100).toFixed(1)}% · Surrogate Z=${d.z.toFixed(2)}σ · AuditHash:${d.hash}</description>
    <instruction>${getRunway(d.alert,d.domain).action}</instruction>
  </info>
</alert>`;
  const blob = new Blob([cap], {type:'application/xml'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `PRECEPT-CAP-${d.asset}-${Date.now()}.xml`;
  a.click();
}

function acknowledgeAlert() {
  if (!lastResult) return;
  addTimeline('ALERT ACKNOWLEDGED', `${lastResult.asset} · ${lastResult.alert} · operator confirmed`, 'cyan');
}

// ── EXECUTIVE MODE ─────────────────────────────────────────────────────
let execModeActive = false;

function toggleExecMode() {
  execModeActive = !execModeActive;
  const overlay = document.getElementById('exec-overlay');
  const btn     = document.getElementById('exec-btn');

  if (execModeActive) {
    overlay.classList.add('open');
    btn.classList.add('active');
    btn.textContent = '⬛ EXECUTIVE MODE ON';
    renderExecMode();
  } else {
    overlay.classList.remove('open');
    btn.classList.remove('active');
    btn.textContent = '⬛ EXECUTIVE MODE';
  }
}

function renderExecMode() {
  const noScan  = document.getElementById('exec-no-scan');
  const data    = document.getElementById('exec-data');

  if (!lastResult) {
    noScan.style.display = 'block';
    data.style.display   = 'none';
    return;
  }

  noScan.style.display = 'none';
  data.style.display   = 'block';

  const d  = lastResult;
  const rw = getRunway(d.alert, d.domain);

  // Colors by alert
  const colors = { NOMINAL:'#00FF88', ADVISORY:'#FFD700', WARNING:'#FF8C00', CRITICAL:'#FF3333' };
  const color  = colors[d.alert] || '#00FF88';

  document.getElementById('exec-title').textContent =
    `${d.domain.toUpperCase()} · ${d.asset}`;

  document.getElementById('exec-meta').innerHTML =
    `${new Date().toISOString().replace('T',' ').substring(0,19)} UTC<br>` +
    `Engine: TC-ENGINE-2025-V3-PROD<br>` +
    `Session scan #${scanCount}`;

  document.getElementById('exec-risk').textContent     = d.alert;
  document.getElementById('exec-risk').style.color     = color;
  document.getElementById('exec-risk-sub').textContent = d.alert === 'NOMINAL' ? 'No precursor detected' :
    d.alert === 'ADVISORY' ? 'Monitor closely' :
    d.alert === 'WARNING'  ? 'Escalated — action required' : 'IMMEDIATE ACTION REQUIRED';

  document.getElementById('exec-conf').textContent     = (d.conf * 100).toFixed(0) + '%';
  document.getElementById('exec-runway').textContent   = rw.value;
  document.getElementById('exec-runway').style.color   = color;
  document.getElementById('exec-runway-sub').textContent = rw.label;
  document.getElementById('exec-action-text').textContent = rw.action;
  document.getElementById('exec-action-text').style.color = color;

  document.getElementById('exec-domain').textContent  = d.domain.toUpperCase();
  document.getElementById('exec-asset').textContent   = d.asset;
  document.getElementById('exec-cci').textContent     = d.cci.toFixed(4);
  document.getElementById('exec-trend').textContent   = rw.trend || 'STABLE';
  document.getElementById('exec-ts').textContent      = d.timestamp.replace('T',' ').substring(0,19) + ' UTC';
  document.getElementById('exec-hash').textContent    = d.hash;
}

// Re-render exec view after each scan if active
const _origRender = renderResult;
renderResult = function(data) {
  _origRender(data);
  if (execModeActive) renderExecMode();
};
</script>
</body>
</html>
