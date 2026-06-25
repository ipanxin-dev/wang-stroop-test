const CONFIG = {
  githubPagesHost: "ipanxin-dev.github.io",
  submitUrl: "",
};

const COLORS = [
  { word: "红", color: "red", css: "#d92d20", key: "d", keyLabel: "D" },
  { word: "蓝", color: "blue", css: "#1769e0", key: "f", keyLabel: "F" },
  { word: "绿", color: "green", css: "#16803c", key: "j", keyLabel: "J" },
  { word: "黄", color: "yellow", css: "#c58a00", key: "k", keyLabel: "K" },
];

const NEUTRAL_WORDS = ["桌", "山", "门", "云"];
const FIXATION_DURATIONS = [500, 625, 750, 875, 1000];
const FORMAL_BLOCKS = 3;
const FORMAL_TRIALS_PER_BLOCK = 72;
const PRACTICE_TRIALS = 10;
const RESPONSE_KEYS = COLORS.map((item) => item.key);
const PRIMARY_BUTTON_HTML = (choice) => `<button class="primary">${choice}</button>`;

let participant = {};
let startedAt = "";
let startedPerf = 0;
let events = [];
let summary = null;
let saveState = "pending";
let formalTrialCounter = 0;

function nowIso() {
  return new Date().toISOString();
}

function timestampCompact(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    "_",
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shuffle(items) {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function colorByWord(word) {
  return COLORS.find((item) => item.word === word);
}

function responseColor(key) {
  const item = COLORS.find((color) => color.key === key);
  return item ? item.word : "";
}

function trialStimulus(trial) {
  return `
    ${progressHtml(trial)}
    <div class="stimulus" style="color:${trial.ink.css};">${escapeHtml(trial.word)}</div>
  `;
}

function progressHtml(trial) {
  if (trial.block_type === "practice") {
    const pct = Math.round(((trial.trial_in_block - 1) / PRACTICE_TRIALS) * 100);
    return `
      <div class="progress">
        <div class="progress-meta"><span>练习阶段</span><span>${trial.trial_in_block} / ${PRACTICE_TRIALS}</span></div>
        <div class="bar"><span style="width:${pct}%"></span></div>
      </div>
    `;
  }
  const pct = Math.round(((trial.trial_in_block - 1) / FORMAL_TRIALS_PER_BLOCK) * 100);
  return `
    <div class="progress">
      <div class="progress-meta"><span>正式实验 ${trial.block_index} / ${FORMAL_BLOCKS}</span><span>${trial.trial_in_block} / ${FORMAL_TRIALS_PER_BLOCK}</span></div>
      <div class="bar"><span style="width:${pct}%"></span></div>
    </div>
  `;
}

function makeTrial({ condition, word, ink, blockType, blockIndex, trialInBlock, fixationMs }) {
  return {
    block_type: blockType,
    block_index: blockIndex,
    trial_in_block: trialInBlock,
    condition,
    word,
    ink,
    correct_key: ink.key,
    fixation_ms: fixationMs,
  };
}

function buildFormalCandidates() {
  const candidates = [];

  COLORS.forEach((ink) => {
    for (let i = 0; i < 6; i += 1) {
      candidates.push({ condition: "congruent", word: ink.word, ink });
    }
  });

  COLORS.forEach((ink) => {
    const otherWords = COLORS.filter((color) => color.word !== ink.word).map((color) => color.word);
    otherWords.forEach((word) => {
      for (let i = 0; i < 2; i += 1) {
        candidates.push({ condition: "incongruent", word, ink });
      }
    });
  });

  COLORS.forEach((ink) => {
    const words = shuffle([...NEUTRAL_WORDS, ...NEUTRAL_WORDS]).slice(0, 6);
    words.forEach((word) => candidates.push({ condition: "neutral", word, ink }));
  });

  return candidates;
}

function buildPracticeCandidates() {
  const fixed = [
    { condition: "neutral", word: "桌", ink: COLORS[0] },
    { condition: "congruent", word: COLORS[1].word, ink: COLORS[1] },
    { condition: "incongruent", word: COLORS[2].word, ink: COLORS[3] },
    { condition: "neutral", word: "山", ink: COLORS[2] },
    { condition: "congruent", word: COLORS[3].word, ink: COLORS[3] },
    { condition: "incongruent", word: COLORS[0].word, ink: COLORS[1] },
    { condition: "congruent", word: COLORS[2].word, ink: COLORS[2] },
    { condition: "neutral", word: "门", ink: COLORS[3] },
    { condition: "incongruent", word: COLORS[1].word, ink: COLORS[0] },
    { condition: "congruent", word: COLORS[0].word, ink: COLORS[0] },
  ];
  return fixed;
}

function violatesRun(candidate, ordered) {
  const previous = ordered[ordered.length - 1];
  if (previous) {
    if (previous.word === candidate.word) return true;
    if (previous.ink.word === candidate.ink.word) return true;
  }
  const recent = ordered.slice(-3);
  if (recent.length === 3 && recent.every((trial) => trial.condition === candidate.condition)) {
    return true;
  }
  return false;
}

function pseudoRandomize(candidates, firstMustBeNeutral = false) {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    const remaining = shuffle(candidates);
    const ordered = [];

    if (firstMustBeNeutral) {
      const neutralIndexes = remaining
        .map((trial, index) => ({ trial, index }))
        .filter((item) => item.trial.condition === "neutral");
      const picked = neutralIndexes[Math.floor(Math.random() * neutralIndexes.length)];
      ordered.push(...remaining.splice(picked.index, 1));
    }

    while (remaining.length) {
      const legal = remaining
        .map((trial, index) => ({ trial, index }))
        .filter((item) => !violatesRun(item.trial, ordered));
      if (!legal.length) break;
      const picked = legal[Math.floor(Math.random() * legal.length)];
      ordered.push(...remaining.splice(picked.index, 1));
    }

    if (ordered.length === candidates.length) {
      return ordered;
    }
  }
  throw new Error("Unable to build constrained Stroop order");
}

function fixationPlan(totalTrials) {
  const base = [];
  while (base.length < totalTrials) {
    base.push(...FIXATION_DURATIONS);
  }
  return pseudoRandomizeFixations(base.slice(0, totalTrials));
}

function pseudoRandomizeFixations(durations) {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    const out = shuffle(durations);
    let ok = true;
    for (let i = 1; i < out.length; i += 1) {
      if (out[i] === out[i - 1]) {
        ok = false;
        break;
      }
    }
    if (ok) return out;
  }
  return shuffle(durations);
}

function buildPracticeTrials() {
  const candidates = pseudoRandomize(buildPracticeCandidates(), false);
  const fixations = fixationPlan(candidates.length);
  return candidates.map((trial, index) =>
    makeTrial({
      ...trial,
      blockType: "practice",
      blockIndex: 0,
      trialInBlock: index + 1,
      fixationMs: fixations[index],
    }),
  );
}

function buildFormalBlock(blockIndex) {
  const candidates = pseudoRandomize(buildFormalCandidates(), true);
  const fixations = fixationPlan(candidates.length);
  return candidates.map((trial, index) =>
    makeTrial({
      ...trial,
      blockType: "formal",
      blockIndex,
      trialInBlock: index + 1,
      fixationMs: fixations[index],
    }),
  );
}

function appendEvent(trial, data) {
  const response = data.response || "";
  const accuracy = response === trial.correct_key;
  const responseWord = responseColor(response);
  const trialIndex = events.length + 1;
  if (trial.block_type === "formal") formalTrialCounter += 1;
  events.push({
    timestamp: nowIso(),
    participant_name: participant.name || "",
    participant_id: participant.studentId || "",
    session_id: participant.sessionId || "",
    trial_index: trialIndex,
    block_type: trial.block_type,
    block_index: trial.block_index,
    trial_in_block: trial.trial_in_block,
    formal_trial_index: trial.block_type === "formal" ? formalTrialCounter : "",
    condition: trial.condition,
    word: trial.word,
    ink_color: trial.ink.word,
    ink_color_en: trial.ink.color,
    correct_key: trial.correct_key.toUpperCase(),
    response_key: response ? response.toUpperCase() : "",
    response_color: responseWord,
    accuracy,
    rt_ms: data.rt == null ? "" : Math.round(data.rt),
    fixation_ms: trial.fixation_ms,
  });
}

function formalEvents() {
  return events.filter((event) => event.block_type === "formal");
}

function mean(values) {
  const clean = values.filter((value) => Number.isFinite(value));
  if (!clean.length) return "";
  return clean.reduce((sum, value) => sum + value, 0) / clean.length;
}

function computeSummary() {
  const formal = formalEvents();
  const correct = formal.filter((event) => event.accuracy === true);
  const byCondition = (condition) => correct.filter((event) => event.condition === condition).map((event) => Number(event.rt_ms));
  const meanCongruent = mean(byCondition("congruent"));
  const meanIncongruent = mean(byCondition("incongruent"));
  const meanNeutral = mean(byCondition("neutral"));
  const finishedAt = timestampCompact();
  return {
    participant_name: participant.name || "",
    participant_id: participant.studentId || "",
    session_id: participant.sessionId || "",
    started_at: startedAt,
    finished_at: finishedAt,
    practice_trial_count: events.filter((event) => event.block_type === "practice").length,
    formal_trial_count: formal.length,
    total_correct: correct.length,
    total_errors: formal.length - correct.length,
    accuracy_percent: formal.length ? Number(((correct.length / formal.length) * 100).toFixed(2)) : "",
    mean_rt_correct_ms: mean(correct.map((event) => Number(event.rt_ms))) === "" ? "" : Number(mean(correct.map((event) => Number(event.rt_ms))).toFixed(2)),
    mean_rt_congruent_ms: meanCongruent === "" ? "" : Number(meanCongruent.toFixed(2)),
    mean_rt_incongruent_ms: meanIncongruent === "" ? "" : Number(meanIncongruent.toFixed(2)),
    mean_rt_neutral_ms: meanNeutral === "" ? "" : Number(meanNeutral.toFixed(2)),
    stroop_interference_ms:
      meanCongruent === "" || meanIncongruent === "" ? "" : Number((meanIncongruent - meanCongruent).toFixed(2)),
    duration_sec: Math.max(0, Math.round((performance.now() - startedPerf) / 1000)),
    trial_count: events.length,
  };
}

function getPayload() {
  return {
    experiment: "stroop_jspsych",
    summary,
    events,
  };
}

function isLocalClassroomMode() {
  return window.location.protocol.startsWith("http") && window.location.hostname !== CONFIG.githubPagesHost;
}

function configuredSubmitUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("submit") || CONFIG.submitUrl || "";
}

async function submitData() {
  summary = computeSummary();
  const payload = getPayload();
  const remoteSubmitUrl = configuredSubmitUrl();

  if (remoteSubmitUrl) {
    try {
      const response = await fetch(remoteSubmitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json;charset=utf-8" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`remote submit failed: ${response.status}`);
      saveState = "remote_success";
      return;
    } catch (error) {
      console.error(error);
      saveState = "remote_failed";
      return;
    }
  }

  if (isLocalClassroomMode()) {
    try {
      const response = await fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json;charset=utf-8" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`local submit failed: ${response.status}`);
      saveState = "local_success";
      return;
    } catch (error) {
      console.error(error);
      saveState = "local_failed";
      return;
    }
  }

  saveState = "no_endpoint";
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const text = typeof value === "object" ? JSON.stringify(value) : String(value);
  if (/[",\n\r]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

function rowsToCsv(rows) {
  if (!rows.length) return "";
  const columns = Object.keys(rows[0]);
  return [columns.join(","), ...rows.map((row) => columns.map((column) => csvEscape(row[column])).join(","))].join("\n");
}

function downloadUrl(content, mime = "text/csv") {
  return URL.createObjectURL(new Blob([content], { type: `${mime};charset=utf-8` }));
}

function finishHtml() {
  const prefix = `stroop_${participant.studentId || "participant"}_${timestampCompact()}`;
  const summaryUrl = downloadUrl(rowsToCsv([summary]));
  const trialsUrl = downloadUrl(rowsToCsv(events));
  const jsonUrl = downloadUrl(JSON.stringify(getPayload(), null, 2), "application/json");
  const stateText = {
    remote_success: "数据已自动提交。",
    local_success: "数据已提交到本地课堂服务器。",
    remote_failed: "自动提交失败，请下载备用数据。",
    local_failed: "本地提交失败，请下载备用数据。",
    no_endpoint: "未配置自动提交地址，请下载备用数据。",
    pending: "正在提交数据...",
  }[saveState];
  const adminLink = isLocalClassroomMode() ? '<p><a href="/admin" target="_blank">老师管理下载入口</a></p>' : "";

  return `
    <div class="screen center">
      <h1>任务完成</h1>
      <p>${stateText}</p>
      <p class="muted">正式成绩不在页面显示。您可以关闭页面。</p>
      <p>
        <a class="download-link" download="${prefix}_summary.csv" href="${summaryUrl}">下载汇总备份</a>
        <a class="download-link secondary-link" download="${prefix}_trials.csv" href="${trialsUrl}">下载明细备份</a>
        <a class="download-link secondary-link" download="${prefix}_all.json" href="${jsonUrl}">下载 JSON 备份</a>
      </p>
      ${adminLink}
    </div>
  `;
}

function introHtml() {
  const keyCards = COLORS.map(
    (color) => `<div class="key-card"><b>${color.keyLabel}</b><span style="color:${color.css};">${color.word}色</span></div>`,
  ).join("");
  return `
    <div class="screen">
      <h1>颜色-文字判断任务</h1>
      <p>本任务用于测量在颜色词干扰下的反应速度与准确性。请根据<strong>字体颜色</strong>按键，不要根据字义按键。</p>
      <div class="notice">
        <p>请在安静环境中完成，双手放在键盘附近，尽量快速且准确地反应。</p>
        <p>每个颜色出现次数严格相等，congruent / incongruent / neutral 比例固定。每位被试的试次顺序会独立随机化。</p>
        <p>练习阶段共 10 个试次；正式实验包含 3 个实验块，每个块 72 个试次。</p>
        <p>数据仅用于研究分析，您可以随时关闭页面退出。</p>
      </div>
      <div class="notice">
        <h2>按键映射</h2>
        <div class="key-grid">${keyCards}</div>
      </div>
    </div>
  `;
}

function participantFormHtml() {
  return `
    <div class="screen">
      <h2>参与信息</h2>
      <div class="form-row">
        <label for="participant_name">姓名</label>
        <input name="participant_name" id="participant_name" required />
      </div>
      <div class="form-row">
        <label for="participant_id">学号/编号</label>
        <input name="participant_id" id="participant_id" required />
      </div>
      <label class="consent">
        <input name="consent" type="checkbox" required />
        <span>我同意将本次匿名作答数据用于研究分析。</span>
      </label>
      <p class="muted">准备好后点击开始。</p>
    </div>
  `;
}

function makeTrialTimeline(trial, jsPsych) {
  return [
    {
      type: jsPsychHtmlKeyboardResponse,
      stimulus: `<div class="fixation">+</div>`,
      choices: "NO_KEYS",
      trial_duration: trial.fixation_ms,
      data: { task: "fixation" },
    },
    {
      type: jsPsychHtmlKeyboardResponse,
      stimulus: () => trialStimulus(trial),
      choices: RESPONSE_KEYS,
      data: { task: "stroop", block_type: trial.block_type },
      on_finish: (data) => appendEvent(trial, data),
    },
  ];
}

function feedbackTrial() {
  return {
    type: jsPsychHtmlKeyboardResponse,
    stimulus: () => {
      const last = events[events.length - 1];
      if (last && last.accuracy === true) return '<div class="feedback-good">正确</div>';
      return '<div class="feedback-bad">错误</div>';
    },
    choices: "NO_KEYS",
    trial_duration: 650,
  };
}

function buildTimeline(jsPsych) {
  const timeline = [];
  const practiceTrials = buildPracticeTrials();
  const formalBlocks = Array.from({ length: FORMAL_BLOCKS }, (_, index) => buildFormalBlock(index + 1));

  timeline.push({
    type: jsPsychHtmlButtonResponse,
    stimulus: introHtml(),
    choices: ["继续"],
    button_html: PRIMARY_BUTTON_HTML,
  });

  timeline.push({
    type: jsPsychSurveyHtmlForm,
    preamble: "",
    html: participantFormHtml(),
    button_label: "点击开始",
    on_finish: (data) => {
      const response = data.response || {};
      participant = {
        name: String(response.participant_name || "").trim(),
        studentId: String(response.participant_id || "").trim(),
        sessionId: `stroop_${timestampCompact()}_${Math.random().toString(36).slice(2, 8)}`,
      };
      startedAt = timestampCompact();
      startedPerf = performance.now();
    },
  });

  timeline.push({
    type: jsPsychHtmlButtonResponse,
    stimulus: `
      <div class="screen center">
        <h2>练习阶段</h2>
        <p>练习阶段共 10 个试次，会显示正确/错误反馈。</p>
        <p>请根据字体颜色按键。</p>
      </div>
    `,
    choices: ["点击开始"],
    button_html: PRIMARY_BUTTON_HTML,
  });

  practiceTrials.forEach((trial) => {
    timeline.push(...makeTrialTimeline(trial, jsPsych));
    timeline.push(feedbackTrial());
  });

  timeline.push({
    type: jsPsychHtmlButtonResponse,
    stimulus: `
      <div class="screen center">
        <h2>正式实验</h2>
        <p>正式实验包含 3 个实验块，每个块 72 个试次。</p>
        <p>正式实验不显示反馈。请快速且准确地反应。</p>
      </div>
    `,
    choices: ["点击开始"],
    button_html: PRIMARY_BUTTON_HTML,
  });

  formalBlocks.forEach((block, index) => {
    if (index > 0) {
      timeline.push({
        type: jsPsychHtmlButtonResponse,
        stimulus: `
          <div class="screen center">
            <h2>休息</h2>
            <p>您已完成第 ${index} 个正式实验块。</p>
            <p>准备好后点击开始下一组测试。</p>
          </div>
        `,
        choices: ["点击开始"],
        button_html: PRIMARY_BUTTON_HTML,
      });
    }
    block.forEach((trial) => timeline.push(...makeTrialTimeline(trial, jsPsych)));
  });

  timeline.push({
    type: jsPsychCallFunction,
    async: true,
    func: async (done) => {
      await submitData();
      done();
    },
  });

  timeline.push({
    type: jsPsychHtmlButtonResponse,
    stimulus: finishHtml,
    choices: [],
  });

  return timeline;
}

const jsPsych = initJsPsych({
  show_progress_bar: false,
  on_finish: () => {},
});

jsPsych.run(buildTimeline(jsPsych));
