# 中文 Stroop 测试

这是一个可部署到 Streamlit 的中文 Stroop 测试页面，按照方案实现：

- 刺激词：红、蓝、绿
- 条件：一致 / 不一致
- 练习：30 trials，15 一致、15 不一致
- 正式测试：3 blocks × 96 trials，共 288 trials
- 每个正式 block：48 一致、48 不一致
- 按键：红 = F，蓝 = J，绿 = K
- 刺激呈现：直到被试按键
- 试次间：750 ms ISI + 500 ms 空屏
- block 间：固定 60 秒休息，自动继续
- 结束后不显示成绩，只提供结果下载

## 本地运行

```bash
streamlit run app.py
```

## 学生需要提交的文件

测试结束页面会提供四个下载：

- `*_raw_trials.csv`：trial-level 原始数据，必须提交
- `*_session_summary.csv`：session-level 指标，必须提交
- `*_block_summary.csv`：block-level 汇总，推荐提交
- `*_all_results.json`：完整备份，推荐保留

如果在 Streamlit Secrets 中配置了 `COLLECTOR_URL`，测试结束后会自动把结果提交到老师的 Google Sheet。下载按钮仍会保留，用作备份。

自动汇总设置见 `GOOGLE_SHEETS_SETUP.md`。

## 数据清洗规则

正式分析仅使用正式测试 trials。练习阶段不进入分析。

1. 仅分析正确反应 trials。
2. trial-level 先剔除 `RT < 200 ms` 与 `RT > 3000 ms`。
3. subject-level `IC_score` 基于剩余 valid trials 计算。
4. `IC_score = mean RT(incongruent correct valid) - mean RT(congruent correct valid)`。
