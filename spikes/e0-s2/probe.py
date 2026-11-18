"""E0-S2 spike: check which public funding-rate endpoints answer from the current machine.

Throwaway script (stdlib only). Run locally and on a GitHub Actions runner, then compare.
Usage: python3 probe.py [--markdown]
"""

import json
import sys
import time
import urllib.error
import urllib.request

HL_INFO = "https://api.hyperliquid.xyz/info"
UA = {"User-Agent": "perpmeter-spike/0.1"}


def hl(body: dict) -> urllib.request.Request:
    return urllib.request.Request(
        HL_INFO,
        data=json.dumps(body).encode(),
        headers={**UA, "Content-Type": "application/json"},
        method="POST",
    )


def get(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers=UA, method="GET")


def probes() -> list[tuple[str, urllib.request.Request]]:
    start_ms = int((time.time() - 6 * 3600) * 1000)
    return [
        ("Hyperliquid metaAndAssetCtxs", hl({"type": "metaAndAssetCtxs"})),
        ("Hyperliquid fundingHistory BTC", hl({"type": "fundingHistory", "coin": "BTC", "startTime": start_ms})),
        ("Hyperliquid predictedFundings", hl({"type": "predictedFundings"})),
        ("Binance data.binance.vision (monthly zip)",
         get("https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-09.zip")),
        ("Binance fapi fundingRate (live)", get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1")),
        ("Bybit v5 funding history", get("https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=1")),
        ("OKX funding-rate", get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP")),
    ]


def run(req: urllib.request.Request) -> tuple[str, str, str]:
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(300)
            status = str(resp.status)
            note = body[:120].decode("utf-8", "replace").replace("\n", " ").replace("|", "/")
    except urllib.error.HTTPError as e:
        status = str(e.code)
        note = e.read(120).decode("utf-8", "replace").replace("\n", " ").replace("|", "/")
    except Exception as e:  # network errors, timeouts
        status = "ERR"
        note = f"{type(e).__name__}: {e}"[:120]
    return status, f"{time.monotonic() - t0:.2f}s", note


def main() -> int:
    markdown = "--markdown" in sys.argv
    rows = [(name, *run(req)) for name, req in probes()]
    if markdown:
        print("| Endpoint | HTTP | Time | Body (first 120 chars) |")
        print("|---|---|---|---|")
        for name, status, took, note in rows:
            print(f"| {name} | {status} | {took} | `{note}` |")
    else:
        for name, status, took, note in rows:
            print(f"{status:>4}  {took:>6}  {name}  ::  {note[:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
