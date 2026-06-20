import json
import textwrap

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="中文 Stroop 测试",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def build_experiment_html(collector_url: str = "") -> str:
    html = textwrap.dedent(
        r"""
        <!doctype html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <style>
            :root {
              color-scheme: light;
              --ink: #172026;
              --muted: #5d6b73;
              --line: #d7dee2;
              --paper: #f8fafb;
              --panel: #ffffff;
              --accent: #006d77;
              --accent-2: #b23a48;
              --green: #238551;
              --blue: #1e5cc8;
              --red: #ca2d2d;
              --shadow: 0 18px 45px rgba(23, 32, 38, 0.12);
            }

            * { box-sizing: border-box; }

            html,
            body {
              margin: 0;
              min-height: 100%;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC",
                "PingFang SC", "Microsoft YaHei", sans-serif;
              background:
                radial-gradient(circle at 20% 10%, rgba(0, 109, 119, 0.12), transparent 28rem),
                linear-gradient(135deg, #f5f7f8 0%, #edf3f2 55%, #f8fafb 100%);
              color: var(--ink);
            }

            body {
              display: flex;
              justify-content: center;
              padding: 24px;
            }

            button,
            input {
              font: inherit;
            }

            .app {
              width: min(1120px, 100%);
              min-height: 820px;
              display: grid;
              grid-template-rows: auto 1fr;
              gap: 16px;
            }

            .topbar {
              display: flex;
              justify-content: space-between;
              align-items: center;
              gap: 16px;
              padding: 14px 18px;
              border: 1px solid rgba(215, 222, 226, 0.9);
              border-radius: 8px;
              background: rgba(255, 255, 255, 0.82);
              box-shadow: 0 10px 28px rgba(23, 32, 38, 0.08);
              backdrop-filter: blur(10px);
            }

            .brand {
              display: flex;
              align-items: baseline;
              gap: 12px;
              min-width: 0;
            }

            .brand h1 {
              margin: 0;
              font-size: 22px;
              line-height: 1.15;
              letter-spacing: 0;
            }

            .brand span {
              color: var(--muted);
              font-size: 14px;
              white-space: nowrap;
            }

            .status {
              display: flex;
              align-items: center;
              gap: 10px;
              color: var(--muted);
              font-size: 14px;
              white-space: nowrap;
            }

            .dot {
              width: 9px;
              height: 9px;
              border-radius: 50%;
              background: var(--accent);
              box-shadow: 0 0 0 4px rgba(0, 109, 119, 0.12);
            }

            .screen {
              border: 1px solid rgba(215, 222, 226, 0.92);
              border-radius: 8px;
              background: rgba(255, 255, 255, 0.92);
              box-shadow: var(--shadow);
              overflow: hidden;
              min-height: 720px;
            }

            .landing {
              display: grid;
              grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
              min-height: 720px;
            }

            .intro {
              padding: 42px;
              display: flex;
              flex-direction: column;
              justify-content: space-between;
              gap: 28px;
              background:
                linear-gradient(180deg, rgba(0, 109, 119, 0.08), rgba(255, 255, 255, 0)),
                var(--paper);
              border-right: 1px solid var(--line);
            }

            .intro h2 {
              margin: 0 0 12px;
              font-size: 34px;
              line-height: 1.16;
              letter-spacing: 0;
            }

            .intro p {
              margin: 0;
              color: var(--muted);
              font-size: 16px;
              line-height: 1.8;
            }

            .info-grid {
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
              gap: 12px;
            }

            .info {
              border: 1px solid var(--line);
              border-radius: 8px;
              padding: 14px;
              background: rgba(255, 255, 255, 0.78);
            }

            .info strong {
              display: block;
              margin-bottom: 6px;
              font-size: 14px;
            }

            .info span {
              color: var(--muted);
              font-size: 13px;
              line-height: 1.5;
            }

            .form {
              padding: 42px;
              display: flex;
              flex-direction: column;
              justify-content: center;
              gap: 22px;
            }

            .field {
              display: grid;
              gap: 8px;
            }

            label {
              font-size: 14px;
              color: var(--muted);
            }

            input {
              width: 100%;
              border: 1px solid #c8d1d6;
              border-radius: 8px;
              padding: 13px 14px;
              font-size: 16px;
              color: var(--ink);
              background: #fff;
              outline: none;
            }

            input:focus {
              border-color: var(--accent);
              box-shadow: 0 0 0 4px rgba(0, 109, 119, 0.12);
            }

            .keys {
              display: grid;
              grid-template-columns: repeat(3, 1fr);
              gap: 10px;
            }

            .key {
              border: 1px solid var(--line);
              border-radius: 8px;
              padding: 12px;
              text-align: center;
              background: #fff;
            }

            .key b {
              display: block;
              margin-bottom: 4px;
              font-size: 22px;
              letter-spacing: 0;
            }

            .key span {
              font-size: 14px;
              color: var(--muted);
            }

            .error {
              min-height: 22px;
              color: var(--accent-2);
              font-size: 14px;
            }

            .primary,
            .secondary,
            .download-link {
              border: 0;
              border-radius: 8px;
              padding: 13px 18px;
              cursor: pointer;
              text-decoration: none;
              display: inline-flex;
              align-items: center;
              justify-content: center;
              gap: 8px;
              min-height: 48px;
            }

            .primary {
              color: #fff;
              background: var(--accent);
              box-shadow: 0 10px 24px rgba(0, 109, 119, 0.24);
            }

            .primary:disabled {
              cursor: not-allowed;
              opacity: 0.62;
              box-shadow: none;
            }

            .secondary,
            .download-link {
              color: var(--ink);
              background: #fff;
              border: 1px solid var(--line);
            }

            .run {
              min-height: 720px;
              display: grid;
              grid-template-rows: auto 1fr auto;
              background: #fbfcfd;
            }

            .progress-row {
              display: grid;
              grid-template-columns: 1fr auto;
              align-items: center;
              gap: 18px;
              padding: 18px 24px;
              border-bottom: 1px solid var(--line);
              position: sticky;
              top: 0;
              z-index: 20;
              background: rgba(251, 252, 253, 0.96);
              backdrop-filter: blur(8px);
              box-shadow: 0 8px 18px rgba(23, 32, 38, 0.06);
            }

            .key-reminder {
              display: flex;
              gap: 10px;
              flex-wrap: wrap;
              justify-content: flex-end;
            }

            .key-reminder span {
              min-width: 64px;
              padding: 7px 10px;
              border: 1px solid var(--line);
              border-radius: 8px;
              background: #fff;
              color: var(--ink);
              text-align: center;
              font-weight: 700;
            }

            .progress-meta {
              display: flex;
              gap: 14px;
              flex-wrap: wrap;
              color: var(--muted);
              font-size: 14px;
            }

            .bar {
              height: 10px;
              border-radius: 999px;
              background: #e5ebee;
              overflow: hidden;
              margin-top: 10px;
            }

            .bar span {
              display: block;
              width: 0%;
              height: 100%;
              background: linear-gradient(90deg, var(--accent), #2a9d8f);
              transition: width 0.22s ease;
            }

            .stage {
              display: grid;
              place-items: center;
              padding: 36px 24px;
              min-height: 520px;
            }

            .stimulus {
              font-size: clamp(72px, 13vw, 164px);
              font-weight: 800;
              line-height: 1;
              letter-spacing: 0;
              user-select: none;
            }

            .fixation,
            .blank-message {
              color: #7a8790;
              font-size: 22px;
              letter-spacing: 0;
              text-align: center;
              line-height: 1.7;
            }

            .pause-card,
            .done-card,
            .practice-card {
              width: min(620px, 100%);
              border: 1px solid var(--line);
              border-radius: 8px;
              padding: 28px;
              background: #fff;
              box-shadow: 0 12px 32px rgba(23, 32, 38, 0.08);
              text-align: center;
            }

            .pause-card h2,
            .done-card h2,
            .practice-card h2 {
              margin: 0 0 10px;
              font-size: 26px;
              letter-spacing: 0;
            }

            .pause-card p,
            .done-card p,
            .practice-card p {
              margin: 0 0 18px;
              color: var(--muted);
              line-height: 1.7;
            }

            .countdown {
              font-size: 58px;
              font-weight: 800;
              color: var(--accent);
              line-height: 1.1;
              margin: 16px 0 8px;
            }

            .feedback {
              padding: 16px 24px 24px;
              text-align: center;
              min-height: 72px;
              color: var(--muted);
              font-size: 18px;
            }

            .feedback.correct { color: var(--green); }
            .feedback.wrong { color: var(--accent-2); }

            .downloads {
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
              gap: 12px;
              margin-top: 18px;
            }

            .small {
              color: var(--muted);
              font-size: 13px;
              line-height: 1.6;
            }

            .hidden {
              display: none !important;
            }

            @media (max-width: 820px) {
              body { padding: 12px; }
              .topbar { align-items: flex-start; flex-direction: column; }
              .status { white-space: normal; }
              .landing { grid-template-columns: 1fr; }
              .intro { border-right: 0; border-bottom: 1px solid var(--line); padding: 28px; }
              .form { padding: 28px; }
              .info-grid, .downloads { grid-template-columns: 1fr; }
              .keys { grid-template-columns: 1fr; }
              .progress-row { grid-template-columns: 1fr; }
            }
          </style>
        </head>
        <body>
          <main class="app">
            <header class="topbar">
              <div class="brand">
                <h1>中文 Stroop 测试</h1>
                <span>本地计时与导出</span>
              </div>
              <div class="status"><span class="dot"></span><span id="topStatus">等待开始</span></div>
            </header>

            <section class="screen">
              <div id="landing" class="landing">
                <div class="intro">
                  <div>
                    <h2>请根据字体颜色按键，而不是根据字义按键</h2>
                    <p>
                      本测试用于测量在颜色词干扰下的反应速度与准确性。测试包含一次练习和三个正式 block。
                      请在安静环境中完成，双手放在键盘附近，尽量快速且准确地反应。
                    </p>
                  </div>

                  <div class="info-grid">
                    <div class="info"><strong>练习阶段</strong><span>30 个试次，提供按键反馈，不进入正式分析。</span></div>
                    <div class="info"><strong>正式阶段</strong><span>3 个 block，每个 96 个试次，共 288 个试次。</span></div>
                    <div class="info"><strong>休息规则</strong><span>block 之间固定休息 60 秒，程序自动继续。</span></div>
                    <div class="info"><strong>伦理说明</strong><span>数据仅用于课程或研究分析，可随时关闭页面退出。</span></div>
                  </div>
                </div>

                <div class="form">
                  <div class="field">
                    <label for="participantName">姓名</label>
                    <input id="participantName" autocomplete="name" placeholder="请输入姓名" />
                  </div>
                  <div class="field">
                    <label for="studentId">学号</label>
                    <input id="studentId" autocomplete="off" placeholder="请输入学号" />
                  </div>

                  <div>
                    <label>按键映射</label>
                    <div class="keys" aria-label="按键映射">
                      <div class="key"><b>F</b><span style="color: var(--red);">红色</span></div>
                      <div class="key"><b>J</b><span style="color: var(--blue);">蓝色</span></div>
                      <div class="key"><b>K</b><span style="color: var(--green);">绿色</span></div>
                    </div>
                  </div>

                  <div class="small">
                    正式测试结束后不会显示成绩。请下载结果文件并按老师要求提交。
                  </div>
                  <div id="error" class="error"></div>
                  <button id="startBtn" class="primary" type="button">开始练习</button>
                </div>
              </div>

              <div id="run" class="run hidden">
                <div class="progress-row">
                  <div>
                    <div class="progress-meta">
                      <span id="phaseLabel">练习</span>
                      <span id="trialLabel">0 / 30</span>
                      <span id="conditionLabel">请看字体颜色</span>
                    </div>
                    <div class="bar"><span id="progressBar"></span></div>
                  </div>
                  <div class="key-reminder" aria-label="按键说明"><span>F = 红</span><span>J = 蓝</span><span>K = 绿</span></div>
                </div>
                <div id="stage" class="stage"></div>
                <div id="feedback" class="feedback"></div>
              </div>
            </section>
          </main>

          <script>
            const COLORS = {
              "红": { css: "#ca2d2d", key: "f", label: "red" },
              "蓝": { css: "#1e5cc8", key: "j", label: "blue" },
              "绿": { css: "#238551", key: "k", label: "green" },
            };
            const WORDS = Object.keys(COLORS);
            const RESPONSE_LABEL = { f: "红", j: "蓝", k: "绿" };
            const ISI_MS = 750;
            const ITI_MS = 500;
            const BREAK_MS = 60000;
            const COLLECTOR_URL = __COLLECTOR_URL_JSON__;

            const state = {
              participantName: "",
              studentId: "",
              sessionId: "",
              currentPhase: "landing",
              practiceTrials: [],
              formalTrials: [],
              trialPointer: 0,
              formalPointer: 0,
              completedBreakBlocks: new Set(),
              awaitingResponse: false,
              stimulusOnset: 0,
              records: [],
            };

            const el = {
              landing: document.getElementById("landing"),
              run: document.getElementById("run"),
              stage: document.getElementById("stage"),
              feedback: document.getElementById("feedback"),
              startBtn: document.getElementById("startBtn"),
              error: document.getElementById("error"),
              name: document.getElementById("participantName"),
              sid: document.getElementById("studentId"),
              topStatus: document.getElementById("topStatus"),
              phaseLabel: document.getElementById("phaseLabel"),
              trialLabel: document.getElementById("trialLabel"),
              conditionLabel: document.getElementById("conditionLabel"),
              progressBar: document.getElementById("progressBar"),
            };

            function shuffle(items) {
              const arr = items.slice();
              for (let i = arr.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [arr[i], arr[j]] = [arr[j], arr[i]];
              }
              return arr;
            }

            function makeCongruent(countPerColor, block) {
              const trials = [];
              WORDS.forEach((word) => {
                for (let i = 0; i < countPerColor; i++) {
                  trials.push({
                    block,
                    condition: "congruent",
                    stimulus: word,
                    fontColor: word,
                    correctResponse: COLORS[word].key,
                  });
                }
              });
              return trials;
            }

            function makeIncongruent(repetitionsPerPair, block, totalNeeded = null) {
              const pairs = [];
              WORDS.forEach((word) => {
                WORDS.forEach((fontColor) => {
                  if (word !== fontColor) pairs.push([word, fontColor]);
                });
              });
              let trials = [];
              pairs.forEach(([word, fontColor]) => {
                for (let i = 0; i < repetitionsPerPair; i++) {
                  trials.push({
                    block,
                    condition: "incongruent",
                    stimulus: word,
                    fontColor,
                    correctResponse: COLORS[fontColor].key,
                  });
                }
              });
              if (totalNeeded !== null) {
                const pool = shuffle(pairs);
                while (trials.length < totalNeeded) {
                  const [word, fontColor] = pool[trials.length % pool.length];
                  trials.push({
                    block,
                    condition: "incongruent",
                    stimulus: word,
                    fontColor,
                    correctResponse: COLORS[fontColor].key,
                  });
                }
                trials = trials.slice(0, totalNeeded);
              }
              return trials;
            }

            function createTrials() {
              const practice = shuffle([
                ...makeCongruent(5, "practice"),
                ...makeIncongruent(2, "practice", 15),
              ]).map((trial, index) => ({ ...trial, phaseTrialIndex: index + 1, formalTrialIndex: "" }));

              let formal = [];
              for (let block = 1; block <= 3; block++) {
                const blockTrials = shuffle([
                  ...makeCongruent(16, block),
                  ...makeIncongruent(8, block),
                ]).map((trial, index) => ({
                  ...trial,
                  phaseTrialIndex: index + 1,
                  formalTrialIndex: (block - 1) * 96 + index + 1,
                }));
                formal = formal.concat(blockTrials);
              }
              return { practice, formal };
            }

            function cleanFilePart(value) {
              return value.trim().replace(/[^\u4e00-\u9fa5a-zA-Z0-9_-]+/g, "_").slice(0, 32) || "participant";
            }

            function nowStamp() {
              const d = new Date();
              const pad = (n) => String(n).padStart(2, "0");
              return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
            }

            function setScreen(name) {
              el.landing.classList.toggle("hidden", name !== "landing");
              el.run.classList.toggle("hidden", name === "landing");
              state.currentPhase = name;
            }

            function startExperiment() {
              const participantName = el.name.value.trim();
              const studentId = el.sid.value.trim();
              if (!participantName || !studentId) {
                el.error.textContent = "请先填写姓名和学号。";
                return;
              }
              el.error.textContent = "";
              const trials = createTrials();
              state.participantName = participantName;
              state.studentId = studentId;
              state.sessionId = `${cleanFilePart(studentId)}_${Date.now()}`;
              state.practiceTrials = trials.practice;
              state.formalTrials = trials.formal;
              state.trialPointer = 0;
              state.formalPointer = 0;
              state.completedBreakBlocks = new Set();
              state.records = [];
              setScreen("practice");
              el.topStatus.textContent = "练习阶段";
              showReadyCard("练习即将开始", "请根据字体颜色按 F、J、K。练习阶段会显示反馈。", "开始", runNextPracticeTrial);
            }

            function showReadyCard(title, text, buttonText, onClick) {
              state.awaitingResponse = false;
              el.feedback.textContent = "";
              el.feedback.className = "feedback";
              el.stage.innerHTML = `
                <div class="practice-card">
                  <h2>${title}</h2>
                  <p>${text}</p>
                  <button class="primary" type="button" id="readyButton">${buttonText}</button>
                </div>
              `;
              document.getElementById("readyButton").addEventListener("click", onClick, { once: true });
            }

            function updateProgress(phase, current, total, condition = "请看字体颜色") {
              const label = phase === "practice" ? "练习" : `正式 Block ${phase}`;
              el.phaseLabel.textContent = label;
              el.trialLabel.textContent = `${current} / ${total}`;
              el.conditionLabel.textContent = condition;
              el.progressBar.style.width = `${Math.max(0, Math.min(100, (current / total) * 100))}%`;
            }

            function showFixation(callback) {
              state.awaitingResponse = false;
              el.stage.innerHTML = `<div class="fixation">+</div>`;
              setTimeout(callback, ISI_MS);
            }

            function presentTrial(trial, phase) {
              updateProgress(
                phase === "practice" ? "practice" : trial.block,
                trial.phaseTrialIndex,
                phase === "practice" ? 30 : 96,
                trial.condition === "congruent" ? "一致条件" : "不一致条件"
              );
              el.feedback.textContent = "";
              el.feedback.className = "feedback";
              el.stage.innerHTML = `<div class="stimulus" style="color: ${COLORS[trial.fontColor].css};">${trial.stimulus}</div>`;
              state.awaitingResponse = true;
              state.stimulusOnset = performance.now();
              state.activeTrial = trial;
              state.activePhase = phase;
            }

            function recordResponse(key, rt) {
              const trial = state.activeTrial;
              const accuracy = key === trial.correctResponse ? 1 : 0;
              const isTooFast = rt < 200 ? 1 : 0;
              const isTooSlow = rt > 3000 ? 1 : 0;
              const isFormal = state.activePhase === "formal";
              state.records.push({
                participant_name: state.participantName,
                participant_student_id: state.studentId,
                session_id: state.sessionId,
                phase: state.activePhase,
                block: trial.block,
                trial_index: isFormal ? trial.formalTrialIndex : "",
                phase_trial_index: trial.phaseTrialIndex,
                condition: trial.condition,
                stimulus: trial.stimulus,
                font_color: trial.fontColor,
                font_color_label: COLORS[trial.fontColor].label,
                correct_response: trial.correctResponse.toUpperCase(),
                response_key: key.toUpperCase(),
                response_color: RESPONSE_LABEL[key] || "",
                accuracy,
                RT_ms: Math.round(rt),
                rt_lt_200_excluded: isTooFast,
                rt_gt_3000_excluded: isTooSlow,
                valid_for_analysis: accuracy === 1 && !isTooFast && !isTooSlow ? 1 : 0,
                missed_trial: 0,
                timestamp_iso: new Date().toISOString(),
              });
              return accuracy;
            }

            function handleKeydown(event) {
              if (!state.awaitingResponse) return;
              const key = event.key.toLowerCase();
              if (!["f", "j", "k"].includes(key)) return;
              event.preventDefault();
              state.awaitingResponse = false;
              const rt = performance.now() - state.stimulusOnset;
              const accuracy = recordResponse(key, rt);
              el.stage.innerHTML = `<div class="blank-message"></div>`;
              if (state.activePhase === "practice") {
                el.feedback.textContent = accuracy ? "正确" : `错误，正确按键是 ${state.activeTrial.correctResponse.toUpperCase()}`;
                el.feedback.className = `feedback ${accuracy ? "correct" : "wrong"}`;
              } else {
                el.feedback.textContent = "";
                el.feedback.className = "feedback";
              }
              setTimeout(() => {
                if (state.activePhase === "practice") {
                  runNextPracticeTrial();
                } else {
                  runNextFormalTrial();
                }
              }, ITI_MS + ISI_MS);
            }

            function runNextPracticeTrial() {
              if (state.trialPointer >= state.practiceTrials.length) {
                el.topStatus.textContent = "正式测试准备";
                showReadyCard(
                  "练习结束",
                  "接下来进入正式测试。正式阶段不会显示每题反馈，也不会在结束后显示成绩。",
                  "开始正式测试",
                  () => {
                    setScreen("formal");
                    el.topStatus.textContent = "正式 Block 1";
                    showFixation(runNextFormalTrial);
                  }
                );
                return;
              }
              const trial = state.practiceTrials[state.trialPointer++];
              showFixation(() => presentTrial(trial, "practice"));
            }

            function runNextFormalTrial() {
              if (state.formalPointer >= state.formalTrials.length) {
                finishExperiment();
                return;
              }
              const justFinishedBlock = state.formalPointer > 0 && state.formalPointer % 96 === 0;
              if (justFinishedBlock) {
                const completedBlock = state.formalPointer / 96;
                if (completedBlock < 3 && !state.completedBreakBlocks.has(completedBlock)) {
                  state.completedBreakBlocks.add(completedBlock);
                  showBreak(completedBlock);
                  return;
                }
              }
              const trial = state.formalTrials[state.formalPointer++];
              el.topStatus.textContent = `正式 Block ${trial.block}`;
              showFixation(() => presentTrial(trial, "formal"));
            }

            function showBreak(completedBlock) {
              state.awaitingResponse = false;
              let remaining = BREAK_MS / 1000;
              el.topStatus.textContent = `休息 ${remaining} 秒`;
              updateProgress(completedBlock + 1, 0, 96, "固定休息");
              el.feedback.textContent = "";
              el.stage.innerHTML = `
                <div class="pause-card">
                  <h2>Block ${completedBlock} 已完成</h2>
                  <p>请休息片刻。倒计时结束后，下一组测试会自动开始。</p>
                  <div class="countdown" id="breakCount">${remaining}</div>
                  <p class="small">请不要关闭页面。</p>
                </div>
              `;
              const counter = document.getElementById("breakCount");
              const timer = setInterval(() => {
                remaining -= 1;
                counter.textContent = remaining;
                el.topStatus.textContent = `休息 ${remaining} 秒`;
                if (remaining <= 0) {
                  clearInterval(timer);
                  el.topStatus.textContent = `正式 Block ${completedBlock + 1}`;
                  showFixation(runNextFormalTrial);
                }
              }, 1000);
            }

            function mean(values) {
              if (!values.length) return "";
              return values.reduce((a, b) => a + b, 0) / values.length;
            }

            function round(value) {
              return value === "" || Number.isNaN(value) ? "" : Math.round(value * 100) / 100;
            }

            function formalRecords() {
              return state.records.filter((r) => r.phase === "formal");
            }

            function validFormalRecords() {
              return formalRecords().filter((r) => r.valid_for_analysis === 1);
            }

            function computeSessionSummary() {
              const formal = formalRecords();
              const valid = validFormalRecords();
              const congruent = valid.filter((r) => r.condition === "congruent").map((r) => r.RT_ms);
              const incongruent = valid.filter((r) => r.condition === "incongruent").map((r) => r.RT_ms);
              const meanCongruent = mean(congruent);
              const meanIncongruent = mean(incongruent);
              const accuracy = mean(formal.map((r) => r.accuracy));
              return [{
                participant_name: state.participantName,
                participant_student_id: state.studentId,
                session_id: state.sessionId,
                formal_trials: formal.length,
                valid_trials_for_analysis: valid.length,
                missed_trials: formal.filter((r) => r.missed_trial === 1).length,
                error_rate: round(1 - accuracy),
                mean_accuracy: round(accuracy),
                mean_RT_ms: round(mean(valid.map((r) => r.RT_ms))),
                mean_RT_congruent_correct_ms: round(meanCongruent),
                mean_RT_incongruent_correct_ms: round(meanIncongruent),
                IC_score_ms: meanCongruent === "" || meanIncongruent === "" ? "" : round(meanIncongruent - meanCongruent),
                rt_lt_200_count: formal.filter((r) => r.rt_lt_200_excluded === 1).length,
                rt_gt_3000_count: formal.filter((r) => r.rt_gt_3000_excluded === 1).length,
                completed_at_iso: new Date().toISOString(),
              }];
            }

            function computeBlockSummary() {
              const rows = [];
              [1, 2, 3].forEach((block) => {
                ["congruent", "incongruent"].forEach((condition) => {
                  const formal = formalRecords().filter((r) => Number(r.block) === block && r.condition === condition);
                  const valid = formal.filter((r) => r.valid_for_analysis === 1);
                  rows.push({
                    participant_name: state.participantName,
                    participant_student_id: state.studentId,
                    session_id: state.sessionId,
                    block,
                    condition,
                    n_trials: formal.length,
                    valid_trials_for_analysis: valid.length,
                    mean_RT_ms: round(mean(valid.map((r) => r.RT_ms))),
                    accuracy: round(mean(formal.map((r) => r.accuracy))),
                    error_rate: round(1 - mean(formal.map((r) => r.accuracy))),
                  });
                });
              });
              return rows;
            }

            function csvEscape(value) {
              if (value === null || value === undefined) return "";
              const s = String(value);
              if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
              return s;
            }

            function toCsv(rows) {
              if (!rows.length) return "";
              const headers = Object.keys(rows[0]);
              const lines = [headers.join(",")];
              rows.forEach((row) => {
                lines.push(headers.map((h) => csvEscape(row[h])).join(","));
              });
              return lines.join("\n");
            }

            function makeDownloadUrl(content, mime) {
              return URL.createObjectURL(new Blob([content], { type: `${mime};charset=utf-8` }));
            }

            function downloadLink(content, filename, label, mime = "text/csv") {
              const url = makeDownloadUrl(content, mime);
              return `<a class="download-link" href="${url}" download="${filename}">${label}</a>`;
            }

            async function autoSubmitResults(payload) {
              if (!COLLECTOR_URL) {
                return { enabled: false, ok: false, message: "未配置自动汇总。请下载结果文件并提交。" };
              }

              try {
                await fetch(COLLECTOR_URL, {
                  method: "POST",
                  mode: "no-cors",
                  headers: { "Content-Type": "text/plain;charset=utf-8" },
                  body: JSON.stringify(payload),
                });
                return { enabled: true, ok: true, message: "已自动提交到老师的数据表。仍建议下载备份文件。" };
              } catch (error) {
                return { enabled: true, ok: false, message: "自动提交失败。请下载结果文件并按要求提交。" };
              }
            }

            function finishExperiment() {
              state.awaitingResponse = false;
              const fileBase = `stroop_${cleanFilePart(state.studentId)}_${cleanFilePart(state.participantName)}_${nowStamp()}`;
              const rawCsv = "\ufeff" + toCsv(state.records);
              const sessionRows = computeSessionSummary();
              const blockRows = computeBlockSummary();
              const sessionCsv = "\ufeff" + toCsv(sessionRows);
              const blockCsv = "\ufeff" + toCsv(blockRows);
              const resultPayload = {
                raw_data: state.records,
                session_summary: sessionRows,
                block_summary: blockRows,
                analysis_plan: {
                  trial_level_exclusion: "RT < 200 ms and RT > 3000 ms are removed first.",
                  subject_level_ic_score: "IC_score = mean RT(incongruent correct valid) - mean RT(congruent correct valid).",
                  formal_analysis_only: true,
                  practice_excluded_from_formal_analysis: true,
                },
              };
              const json = JSON.stringify(resultPayload, null, 2);

              el.topStatus.textContent = "测试完成";
              el.feedback.textContent = "";
              el.stage.innerHTML = `
                <div class="done-card">
                  <h2>测试已完成</h2>
                  <p id="submitStatus">${COLLECTOR_URL ? "正在自动提交到老师的数据表..." : "正式成绩不在页面显示。请下载下方结果文件，并按老师要求提交。"}</p>
                  <div class="downloads">
                    ${downloadLink(rawCsv, `${fileBase}_raw_trials.csv`, "下载 trial-level CSV")}
                    ${downloadLink(sessionCsv, `${fileBase}_session_summary.csv`, "下载 session CSV")}
                    ${downloadLink(blockCsv, `${fileBase}_block_summary.csv`, "下载 block CSV")}
                    ${downloadLink(json, `${fileBase}_all_results.json`, "下载 JSON 备份", "application/json")}
                  </div>
                  <p class="small">请至少保留下载备份。不要刷新页面，刷新后本次结果会丢失。</p>
                </div>
              `;
              updateProgress(3, 96, 96, "完成");
              autoSubmitResults(resultPayload).then((result) => {
                const submitStatus = document.getElementById("submitStatus");
                if (submitStatus) submitStatus.textContent = result.message;
              });
            }

            el.startBtn.addEventListener("click", startExperiment);
            document.addEventListener("keydown", handleKeydown);
          </script>
        </body>
        </html>
        """
    )
    return html.replace("__COLLECTOR_URL_JSON__", json.dumps(collector_url.strip()))


try:
    collector_url = st.secrets.get("COLLECTOR_URL", "")
except Exception:
    collector_url = ""


st.markdown(
    """
    <style>
      .block-container {
        max-width: 1220px;
        padding-top: 1.25rem;
        padding-bottom: 1rem;
      }
      header[data-testid="stHeader"] {
        background: transparent;
      }
      #MainMenu, footer {
        visibility: hidden;
      }
      iframe {
        border-radius: 8px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(build_experiment_html(collector_url), height=900, scrolling=True)
