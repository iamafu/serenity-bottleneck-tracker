#!/usr/bin/env python3
"""
Provider-agnostic price/momentum helper for the Serenity bottleneck-hunter skill.

Vendored from Mrjie7205/serenity-bottleneck-hunter (MIT License) so this
tracker has no runtime dependency on that repo's layout.

按优先级回退抓历史价,严禁靠网页猜价格:
  1) EODHD            (若环境变量 EODHD_API_KEY 已设;全球覆盖最广,海外股优先)
  2) yfinance         (无需 key,美股覆盖好,海外股常有 gap)
  3) 失败 -> 报错退出 (do NOT silently guess)

返回每只票的 JSON:last、6 月区间位置、距高点、1/3 月动量、stage 标签。
"""
import json, os, sys, urllib.request, datetime

EODHD_KEY = os.environ.get("EODHD_API_KEY", "").strip()


def _fetch_eodhd(symbol, days=400):
    end = datetime.date.today().isoformat()
    start = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    url = f"https://eodhd.com/api/eod/{symbol}?api_token={EODHD_KEY}&from={start}&to={end}&period=d&fmt=json"
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                d = json.load(r)
                if isinstance(d, list) and d:
                    return [{"date": x["date"], "open": x["open"], "high": x["high"],
                             "low": x["low"], "close": x["close"]} for x in d]
        except Exception:
            pass
    return None


def _fetch_yf(symbol, days=400):
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        t = yf.Ticker(symbol)
        h = t.history(period=f"{max(days, 400)}d", auto_adjust=False)
        if h is None or len(h) == 0:
            return None
        return [{"date": idx.strftime("%Y-%m-%d"),
                 "open": float(row["Open"]), "high": float(row["High"]),
                 "low": float(row["Low"]),   "close": float(row["Close"])}
                for idx, row in h.iterrows()]
    except Exception:
        return None


def fetch_history(symbol, days=400):
    """按 EODHD -> yfinance 顺序抓;返回 (data, provider) 或 (None, None)。"""
    if EODHD_KEY:
        data = _fetch_eodhd(symbol, days)
        if data:
            return data, "eodhd"
    data = _fetch_yf(symbol, days)
    if data:
        return data, "yfinance"
    return None, None


def analyze(symbol, days=400):
    data, prov = fetch_history(symbol, days)
    if data is None:
        return {"ticker": symbol,
                "error": "no data from EODHD or yfinance (delisted, renamed, or wrong ticker/exchange suffix; set EODHD_API_KEY for non-US names)"}
    closes = [x["close"] for x in data]
    last = closes[-1]
    last_date = data[-1]["date"]
    w6 = data[-126:] if len(data) >= 126 else data
    lo6 = min(x["low"] for x in w6)
    hi6 = max(x["high"] for x in w6)
    rng_pos = round((last - lo6) / (hi6 - lo6) * 100) if hi6 > lo6 else 50
    off_high = round((last / hi6 - 1) * 100, 1)
    sma50 = sum(closes[-50:]) / min(50, len(closes))
    r1m = round((last / closes[-21] - 1) * 100, 1) if len(closes) > 21 else None
    r3m = round((last / closes[-63] - 1) * 100, 1) if len(closes) > 63 else None
    up = last > sma50
    hot_1m = (r1m is not None and r1m > 40)
    at_top = (rng_pos >= 95 and (r3m or 0) > 30)
    if (r3m is not None and r3m > 120) or hot_1m or at_top:
        stage = "extended/parabolic"
    elif up and r3m is not None and 5 < r3m <= 120 and not hot_1m:
        stage = "early-uptrend"
    elif not up and r3m is not None and r3m < -10:
        stage = "downtrend/basing"
    else:
        stage = "range/neutral"
    return {
        "ticker": symbol,
        "provider": prov,
        "last": round(last, 2),
        "last_date": last_date,
        "range_pos_6mo_pct": rng_pos,
        "pct_off_6mo_high": off_high,
        "ret_1m_pct": r1m,
        "ret_3m_pct": r3m,
        "above_sma50": up,
        "stage": stage,
    }


if __name__ == "__main__":
    syms = sys.argv[1:]
    if not syms:
        print("usage: python scripts/price.py TICKER [TICKER ...]", file=sys.stderr)
        sys.exit(1)
    for s in syms:
        print(json.dumps(analyze(s), ensure_ascii=False))
