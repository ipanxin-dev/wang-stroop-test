# 自动汇总到 Google Sheets

这个版本支持学生完成后自动把数据提交到老师的 Google Sheet。

## 1. 创建 Google Sheet

新建一个 Google Sheet，例如命名为 `Stroop 数据汇总`。

## 2. 添加 Apps Script

在 Google Sheet 顶部菜单选择：

`Extensions` -> `Apps Script`

删除默认内容，粘贴下面代码：

```javascript
function ensureSheet(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
    return sheet;
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }
  return sheet;
}

function appendObjects(sheetName, rows) {
  if (!rows || rows.length === 0) return;
  const headers = Object.keys(rows[0]);
  const sheet = ensureSheet(sheetName, headers);
  const values = rows.map(row => headers.map(header => row[header] ?? ""));
  sheet.getRange(sheet.getLastRow() + 1, 1, values.length, headers.length).setValues(values);
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);

  try {
    const payload = JSON.parse(e.postData.contents);
    appendObjects("session_summary", payload.session_summary || []);
    appendObjects("block_summary", payload.block_summary || []);
    appendObjects("raw_trials", payload.raw_data || []);

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(error) }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return ContentService.createTextOutput("Stroop collector is running.");
}
```

## 3. 部署为 Web App

在 Apps Script 右上角点击 `Deploy` -> `New deployment`。

设置：

- Type: `Web app`
- Execute as: `Me`
- Who has access: `Anyone`

点击 `Deploy`，授权后复制 Web app URL。

## 4. 配置 Streamlit Secrets

在 Streamlit App 页面进入：

`Manage app` -> `Settings` -> `Secrets`

填入：

```toml
COLLECTOR_URL = "把第 3 步复制的 Web app URL 粘贴到这里"
```

保存后重启 App。

## 5. 使用方式

学生完成测试后，页面会自动提交到 Google Sheet，并显示下载按钮作为备份。

建议仍要求学生保留 `raw_trials.csv` 和 `session_summary.csv`，以防个别设备网络异常。
