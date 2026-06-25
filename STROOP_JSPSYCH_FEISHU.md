# Stroop jsPsych + 飞书收数

## 学生实验网页

GitHub Pages 发布后，学生打开：

```text
https://ipanxin-dev.github.io/wang-stroop-test/
```

注意：GitHub Pages 是纯静态网页，不能安全保存飞书 `App Secret`。如果要自动保存到飞书，需要同时运行 `stroop_server.py` 后端，并让学生打开后端打印出来的课堂 URL，例如：

```text
http://老师电脑局域网IP:8766
```

如果以后把 `stroop_server.py` 部署到公网后端，学生也可以打开 GitHub Pages 链接并带 `submit` 参数：

```text
https://ipanxin-dev.github.io/wang-stroop-test/?submit=https%3A%2F%2F你的后端域名%2Fsubmit
```

## 实验设置

- 任务名称：颜色-文字判断任务
- 颜色：红、蓝、绿、黄
- 按键：D=红，F=蓝，J=绿，K=黄
- 练习：10 个试次，提供正确/错误反馈
- 正式：3 个实验块，每块 72 个试次
- 每块条件：24 congruent、24 incongruent、24 neutral
- 每块颜色：每种字体颜色 18 次
- 伪随机约束：
  - 同一条件连续出现不超过 3 次
  - 同一单词不得立即重复
  - 同一字体颜色不得立即重复
  - 每个正式 block 的第一个刺激为 neutral
- 注视十字：500、625、750、875、1000 ms 伪随机呈现

## 本地后端运行

```bash
python3 stroop_server.py
```

默认地址：

```text
http://127.0.0.1:8766
```

老师管理页：

```text
http://127.0.0.1:8766/admin
```

默认老师密码：

```text
stroop-admin
```

可用环境变量修改：

```bash
STROOP_ADMIN_PASSWORD=你的密码 STROOP_PORT=8766 python3 stroop_server.py
```

## 飞书环境变量

飞书密钥不要写入前端、README 或 GitHub。后端读取：

```bash
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
STROOP_FEISHU_APP_TOKEN=xxx
STROOP_FEISHU_SUMMARY_TABLE_ID=tblxxx
STROOP_FEISHU_TRIALS_TABLE_ID=tblxxx
python3 stroop_server.py
```

`FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 可以继续使用已审核通过的飞书自建应用；但 Stroop 需要另建一个飞书多维表格文档，并把该应用添加为可编辑文档应用。

当前 Stroop 独立飞书多维表格配置：

```bash
FEISHU_APP_ID=cli_aab14ddcf1b45cc8
FEISHU_APP_SECRET=这里填飞书应用密钥
STROOP_FEISHU_APP_TOKEN=OUuebaW7Ia8jnEsLcIcc4dumnTf
STROOP_FEISHU_SUMMARY_TABLE_ID=tblRCnmIT4heV3pe
STROOP_FEISHU_TRIALS_TABLE_ID=tblKMgDZEeN8TtCT
python3 stroop_server.py
```

已完成一次测试写入，返回：

```text
{"enabled": true, "summary_rows": 1, "trial_rows": 1}
```

## summary 表字段

```text
participant_name
participant_id
session_id
started_at
finished_at
practice_trial_count
formal_trial_count
total_correct
total_errors
accuracy_percent
mean_rt_correct_ms
mean_rt_congruent_ms
mean_rt_incongruent_ms
mean_rt_neutral_ms
stroop_interference_ms
duration_sec
trial_count
```

## trials 表字段

```text
timestamp
participant_name
participant_id
session_id
trial_index
block_type
block_index
trial_in_block
formal_trial_index
condition
word
ink_color
ink_color_en
correct_key
response_key
response_color
accuracy
rt_ms
fixation_ms
```
