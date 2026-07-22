# Serenity Bottleneck Tracker

每日自動更新的 Serenity（[@aleabitoreddit](https://x.com/aleabitoreddit)）卡點股追蹤儀表板。

**Live 頁面：** https://iamafu.github.io/serenity-bottleneck-tracker/

## 架構

- **資料層**：每日 clone [yan-labs/serenity-aleabitoreddit](https://github.com/yan-labs/serenity-aleabitoreddit) 的公開推文提及統計（`data/ticker_stats.txt`）
- **價格層**：`scripts/price.py`（vendored from [Mrjie7205/serenity-bottleneck-hunter](https://github.com/Mrjie7205/serenity-bottleneck-hunter), MIT）— EODHD 優先、無 key 則回退 yfinance
- **管線**：`scripts/build.py` 合併兩者，輸出 `docs/data/tickers.json`
- **前端**：`docs/index.html` 純靜態頁面讀取 JSON 渲染表格，無框架依賴
- **自動化**：`.github/workflows/update.yml` 每日排程（`workflow_dispatch` 亦可手動觸發）跑管線並 commit 回 `docs/data/`，GitHub Pages 從 `main` 分支 `/docs` 目錄發布

架構設計參考 [iamafu/tw-us-elliott-wave](https://github.com/iamafu/tw-us-elliott-wave)（GitHub Actions cron + `docs/` 靜態發布模式）。

## 本地執行

```bash
pip install -r requirements.txt
python scripts/build.py
```

（可選）設定 `EODHD_API_KEY` 環境變數以取得更完整的海外股價數據，未設定則自動回退 yfinance（美股覆蓋佳）。

## 免責聲明

僅供研究教育用途，非投資建議、非自動交易工具。與 Serenity / @aleabitoreddit 本人無官方關聯，其自報績效未經驗證，存在明顯倖存者偏差。所有數據延遲且可能有誤，請自行查證再做任何決策。
