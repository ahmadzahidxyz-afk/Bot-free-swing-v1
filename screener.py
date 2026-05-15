import yfinance as yf
import pandas as pd

# =====================================================
# RSI Function
# =====================================================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# =====================================================
# Fibonacci (Hanya dipakai di /scan)
# =====================================================
def get_fib_levels(symbol, timeframe="1d"):
    interval_map = {"30m": "30m", "1h": "60m", "1d": "1d"}
    limit_map = {"30m": 1000, "1h": 500, "1d": 90}

    interval = interval_map.get(timeframe, "1d")
    limit = limit_map.get(timeframe, 90)

    df = yf.download(symbol, period="6mo", interval=interval, progress=False)
    if df.empty:
        return None

    df = df.tail(limit)

    high = float(df['High'].max())
    low = float(df['Low'].min())

    fib_786 = round(high - (high - low) * 0.786, 2)
    fib_618 = round(high - (high - low) * 0.618, 2)
    fib_50 = round(high - (high - low) * 0.50, 2)
    tp_21 = round(high + (high - low) * 0.21, 2)

    return {
        "fib_786": fib_786,
        "fib_618": fib_618,
        "fib_50": fib_50,
        "tp_21": tp_21
    }


# =====================================================
# Scan 1 symbol (dipakai /scan)
# =====================================================
def scan_symbol(symbol, timeframe="1h"):
    try:
        df = yf.download(
            symbol,
            period="6mo",
            interval={"30m": "30m", "1h": "60m", "1d": "1d"}[timeframe],
            progress=False
        )
        if df.empty:
            return None

        close = df["Close"]
        last_close = float(close.iloc[-1])
        ma60 = float(close.rolling(60).mean().iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])

        ma_status = "Above MA60" if last_close > ma60 else "Below MA60"

        vol_last = float(df['Volume'].iloc[-1])
        vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])

        vol_status = "Normal ⚪"
        if vol_last > 1.5 * vol_ma20:
            vol_status = "High 🔵"
        elif vol_last < 0.5 * vol_ma20:
            vol_status = "Low 🔴"

        value_last = round(last_close * vol_last)
        value_ma20 = float((df['Close'] * df['Volume']).rolling(20).mean().iloc[-1])

        value_status = "Normal ⚪"
        if value_last > 1.5 * value_ma20:
            value_status = "High 🔵"
        elif value_last < 0.5 * value_ma20:
            value_status = "Low 🔴"

        fib = get_fib_levels(symbol, timeframe)
        if fib is None:
            return None

        data = {
            "symbol": symbol,
            "price": round(last_close, 2),
            "ma60": round(ma60, 2),
            "rsi": round(rsi_val, 2),
            "ma_status": ma_status,
            "vol_last": round(vol_last),
            "vol_status": vol_status,
            "value_last": value_last,
            "value_status": value_status,
            "fib_786": fib["fib_786"],
            "fib_618": fib["fib_618"],
            "fib_50": fib["fib_50"],
            "tp_21": fib["tp_21"],
            "timeframe": timeframe,
        }

        return data

    except:
        return None


# =====================================================
# Helper filter untuk /rekomendasi & /swing
# =====================================================
def simple_scan(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="60m", progress=False)
        if df.empty:
            return None

        close = df["Close"]
        last_close = float(close.iloc[-1])
        ma60 = float(close.rolling(60).mean().iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])

        ma_status = "Above MA60" if last_close > ma60 else "Below MA60"

        return {
            "symbol": symbol.replace(".JK", ""),
            "price": round(last_close, 2),
            "ma60": round(ma60, 2),
            "rsi": round(rsi_val, 2),
            "ma_status": ma_status
        }
    except:
        return None


# =====================================================
# Batch screening
# =====================================================
try:
    from issi_symbols import ISSI_BATCHES
except ImportError:
    ISSI_BATCHES = []


def screen_all():
    results = []
    for batch in ISSI_BATCHES:
        for sym in batch:
            d = simple_scan(sym)
            if d:
                results.append(d)
    return results

# =====================================================
# Hitung Harga Wajar Saham
# =====================================================
def calculate_harga_wajar(symbol, per_wajar_range=(10, 15), pbv_wajar_range=(1.0, 1.5)):
    """
    Hitung harga wajar saham berdasarkan EPS dan PBV
    """
    try:
        stock = yf.Ticker(symbol + ".JK")
        info = stock.info

        harga_saham = info.get('regularMarketPrice')
        eps_ttm = info.get('trailingEps')
        pbv = info.get('bookValue')
        per_ttm = info.get('trailingPE')

        if None in (harga_saham, eps_ttm, pbv, per_ttm):
            return None  # gagal ambil data

        # Hitung harga wajar
        harga_per_min = eps_ttm * per_wajar_range[0]
        harga_per_max = eps_ttm * per_wajar_range[1]

        harga_pbv_min = pbv * pbv_wajar_range[0]
        harga_pbv_max = pbv * pbv_wajar_range[1]

        gabungan_min = (harga_per_min + harga_pbv_min) / 2
        gabungan_max = (harga_per_max + harga_pbv_max) / 2

        # Status over/under/fair
        if harga_saham < gabungan_min:
            status = "Undervalue ✅"
        elif harga_saham > gabungan_max:
            status = "Overvalue ❌"
        else:
            status = "Fair Value ⚖️"

        result = {
            "symbol": symbol,
            "harga_saham": harga_saham,
            "eps": eps_ttm,
            "pbv": pbv,
            "per": per_ttm,
            "wajar": {
                "PER": (harga_per_min, harga_per_max),
                "PBV": (harga_pbv_min, harga_pbv_max),
                "Gabungan": (gabungan_min, gabungan_max),
            },
            "status": status
        }
        return result

    except:
        return None
