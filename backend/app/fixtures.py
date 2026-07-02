"""Stable, sourced demonstration data for the required five markets.

Values are intentionally snapshots rather than claims of current prices. Every
record carries an as-of date and fixture provenance in the API response.
"""

from typing import Any

AS_OF = "2025-12-31T12:00:00+00:00"
RETRIEVED_AT = "2026-01-15T08:00:00+00:00"


def _asset(
    symbol: str,
    name: str,
    exchange: str,
    mic: str,
    country: str,
    currency: str,
    timezone: str,
    locale: str,
    provider_symbol: str,
    isin: str,
    reporting_currency: str | None = None,
    primary: bool = True,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "display_name": name,
        "exchange": exchange,
        "mic": mic,
        "country": country,
        "security_type": "Common Stock" if primary else "Depositary Receipt",
        "trading_currency": currency,
        "reporting_currency": reporting_currency or currency,
        "timezone": timezone,
        "locale": locale,
        "isin": isin,
        "provider_symbols": {"fixture": provider_symbol, "yahoo": provider_symbol},
        "primary_listing": primary,
    }


ASSETS: dict[str, dict[str, Any]] = {
    "XNAS:AAPL": _asset(
        "AAPL",
        "Apple Inc.",
        "NASDAQ",
        "XNAS",
        "United States",
        "USD",
        "America/New_York",
        "en-US",
        "AAPL",
        "US0378331005",
    ),
    "XSHG:600519": _asset(
        "600519",
        "Kweichow Moutai Co., Ltd.",
        "Shanghai Stock Exchange",
        "XSHG",
        "China",
        "CNY",
        "Asia/Shanghai",
        "zh-CN",
        "600519.SS",
        "CNE0000018R8",
    ),
    "XHKG:0700": _asset(
        "0700",
        "Tencent Holdings Limited",
        "Hong Kong Stock Exchange",
        "XHKG",
        "Hong Kong",
        "HKD",
        "Asia/Hong_Kong",
        "zh-HK",
        "0700.HK",
        "KYG875721634",
        reporting_currency="CNY",
    ),
    "XTKS:7203": _asset(
        "7203",
        "Toyota Motor Corporation",
        "Tokyo Stock Exchange",
        "XTKS",
        "Japan",
        "JPY",
        "Asia/Tokyo",
        "ja-JP",
        "7203.T",
        "JP3633400001",
    ),
    "XETR:SAP": _asset(
        "SAP",
        "SAP SE",
        "Xetra",
        "XETR",
        "Germany",
        "EUR",
        "Europe/Berlin",
        "de-DE",
        "SAP.DE",
        "DE0007164600",
    ),
    "XNYS:SAP": _asset(
        "SAP",
        "SAP SE ADR",
        "New York Stock Exchange",
        "XNYS",
        "United States",
        "USD",
        "America/New_York",
        "en-US",
        "SAP",
        "US8030542042",
        reporting_currency="EUR",
        primary=False,
    ),
}


COMPANIES: dict[str, dict[str, Any]] = {
    "XNAS:AAPL": {
        "price": 252.20,
        "price_source": (
            "Nasdaq historical quotes",
            "https://www.nasdaq.com/market-activity/stocks/aapl/historical",
        ),
        "summary": "Apple designs integrated consumer devices, software, and services around a global installed base.",
        "industry": "Consumer technology; premium hardware, digital services, and platform ecosystems.",
        "accounting": "US GAAP; fiscal year ends in late September, not calendar year-end.",
        "source": {
            "name": "SEC EDGAR — Apple 2025 Form 10-K",
            "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
            "published": "2025-10-31T12:00:00+00:00",
            "period": "FY2025",
        },
        "financials": [
            ("FY2023", 383285, 114301, 99584, 29.4),
            ("FY2024", 391035, 123216, 108807, 31.8),
            ("FY2025", 416161, 133050, 98767, 30.1),
        ],
        "margin": 31.9,
        "growth": 6.8,
        "debt_risk": "Medium",
        "currency": "USD",
        "standard": "US GAAP",
        "fye": "September",
        "shares": 14900,
        "scenario_values": (190.0, 258.0, 330.0),
    },
    "XSHG:600519": {
        "price": 1518.00,
        "price_source": (
            "Shanghai Stock Exchange security overview",
            "https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE=600519",
        ),
        "summary": "Kweichow Moutai produces premium baijiu with scarce brand heritage and a controlled distributor network.",
        "industry": "Chinese premium spirits; brand-led pricing power with domestic demand concentration.",
        "accounting": "Chinese Accounting Standards; comparisons with IFRS/US GAAP require care around tax and presentation.",
        "source": {
            "name": "Shanghai Stock Exchange — 2024 Annual Report",
            "url": "https://www.sse.com.cn/assortment/stock/list/info/announcement/",
            "published": "2025-04-03T08:00:00+08:00",
            "period": "FY2024",
        },
        "financials": [
            ("FY2022", 127554, 87560, 62720, 28.1),
            ("FY2023", 150560, 103663, 74734, 30.3),
            ("FY2024", 174144, 119500, 86210, 31.2),
        ],
        "margin": 68.6,
        "growth": 15.7,
        "debt_risk": "Low",
        "currency": "CNY",
        "standard": "CAS",
        "fye": "December",
        "shares": 1256,
        "scenario_values": (1210.0, 1660.0, 2070.0),
    },
    "XHKG:0700": {
        "price": 419.20,
        "price_source": (
            "HKEX securities market data",
            "https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities?sc_lang=en",
        ),
        "summary": "Tencent operates social, gaming, advertising, fintech, cloud, and investment platforms centered on Weixin.",
        "industry": "Internet platforms; network effects, regulation, gaming cycles, and AI infrastructure investment.",
        "accounting": "IFRS in CNY reporting currency while shares trade in HKD; FX translation is explicit.",
        "source": {
            "name": "Tencent Investor Relations — 2024 Annual Report",
            "url": "https://www.tencent.com/en-us/investors/financial-reports.html",
            "published": "2025-04-08T08:00:00+08:00",
            "period": "FY2024",
        },
        "financials": [
            ("FY2022", 554552, 115649, 102100, 12.0),
            ("FY2023", 609015, 160074, 167400, 15.8),
            ("FY2024", 660257, 208210, 182600, 18.9),
        ],
        "margin": 31.5,
        "growth": 8.4,
        "debt_risk": "Low",
        "currency": "CNY",
        "standard": "IFRS",
        "fye": "December",
        "shares": 9200,
        "scenario_values": (330.0, 470.0, 620.0),
    },
    "XTKS:7203": {
        "price": 3142.00,
        "price_source": (
            "Japan Exchange Group listed company search",
            "https://www2.jpx.co.jp/tseHpFront/StockSearch.do?callJorEFlg=1",
        ),
        "summary": "Toyota is a global automaker spanning hybrids, combustion vehicles, battery EVs, mobility, and finance.",
        "industry": "Cyclical global automotive manufacturing; scale, supply chain, FX, and transition execution matter.",
        "accounting": "IFRS; March fiscal year and material financial-services operations complicate industrial comparisons.",
        "source": {
            "name": "Toyota Investor Relations — FY2025 Form 20-F",
            "url": "https://global.toyota/en/ir/library/sec/",
            "published": "2025-06-18T09:00:00+09:00",
            "period": "FY2025",
        },
        "financials": [
            ("FY2023", 37154298, 2725025, 2790000, 8.1),
            ("FY2024", 45095325, 5352934, 4280000, 13.2),
            ("FY2025", 48036704, 4795586, 3510000, 10.7),
        ],
        "margin": 10.0,
        "growth": 6.5,
        "debt_risk": "Medium",
        "currency": "JPY",
        "standard": "IFRS",
        "fye": "March",
        "shares": 15700,
        "scenario_values": (2380.0, 3380.0, 4480.0),
    },
    "XETR:SAP": {
        "price": 238.40,
        "price_source": (
            "Deutsche Börse SAP instrument page",
            "https://www.boerse-frankfurt.de/equity/sap-se",
        ),
        "summary": "SAP provides enterprise applications and is migrating a large installed base to cloud subscriptions.",
        "industry": "Enterprise software; recurring revenue, cloud transition economics, and AI monetization drive outcomes.",
        "accounting": "IFRS in EUR; restructuring and share-based compensation affect adjusted/non-adjusted comparisons.",
        "source": {
            "name": "SAP Investor Relations — 2024 Integrated Report",
            "url": "https://www.sap.com/integrated-reports/2024/en.html",
            "published": "2025-02-27T08:00:00+01:00",
            "period": "FY2024",
        },
        "financials": [
            ("FY2022", 29007, 4673, 4500, 13.8),
            ("FY2023", 31207, 5814, 5060, 15.2),
            ("FY2024", 34176, 6012, 5800, 16.4),
        ],
        "margin": 21.5,
        "growth": 12.8,
        "debt_risk": "Low",
        "currency": "EUR",
        "standard": "IFRS",
        "fye": "December",
        "shares": 1190,
        "scenario_values": (175.0, 250.0, 335.0),
    },
}

# The ADR intentionally reuses the primary company's fundamentals while keeping
# a distinct identity and trading/reporting currency relationship.
COMPANIES["XNYS:SAP"] = {
    **COMPANIES["XETR:SAP"],
    "price": 247.30,
    "price_source": ("NYSE SAP ADR quote", "https://www.nyse.com/quote/XNYS:SAP"),
    "scenario_values": (181.0, 259.0, 347.0),
}


FX_RATES: dict[tuple[str, str], float] = {
    ("USD", "USD"): 1.0,
    ("CNY", "USD"): 0.1370,
    ("HKD", "USD"): 0.1283,
    ("JPY", "USD"): 0.00638,
    ("EUR", "USD"): 1.0410,
    ("USD", "CNY"): 7.2993,
    ("HKD", "CNY"): 0.9365,
    ("JPY", "CNY"): 0.0466,
    ("EUR", "CNY"): 7.5980,
}
