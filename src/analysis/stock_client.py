"""DART (Korea) and SEC EDGAR (US) stock data clients.

Environment variables:
    OPEN_DART_API_KEY   — OpenDART API key (https://opendart.fss.or.kr, free)
    SEC_EDGAR_USER_AGENT — SEC EDGAR user-agent string (required by SEC policy)
                           e.g. "FinanceFlowLabs research@example.com"
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# DART (Korea FSS OpenDART)
# ---------------------------------------------------------------------------

_DART_BASE = "https://opendart.fss.or.kr/api"


class DartStockClient:
    """OpenDART REST API client for Korean listed companies."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key or os.getenv("OPEN_DART_API_KEY", "")

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        if not self._api_key:
            raise ValueError(
                "OPEN_DART_API_KEY is not set. "
                "Register at https://opendart.fss.or.kr to get a free API key."
            )
        params["crtfc_key"] = self._api_key
        qs = urllib.parse.urlencode(params)
        url = f"{_DART_BASE}/{path}?{qs}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "FinanceFlowLabs/1.0 (stock-analysis research bot)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]

    def search_company(self, query: str) -> list[dict[str, Any]]:
        """Search companies by name or ticker on DART.

        Args:
            query: Company name or stock ticker (e.g. "삼성전자", "005930").

        Returns:
            List of dicts with keys: corp_code, corp_name, stock_code, modify_date.
        """
        data = self._get("corpCode.json", {})
        # DART returns a zip of XML; the JSON endpoint is only for corp list download.
        # Use the company search endpoint instead.
        data = self._get(
            "company.json",
            {"corp_name": query},
        )
        status = data.get("status", "")
        if status not in ("000", "013"):
            raise ValueError(
                f"DART API error: status={status!r}, message={data.get('message')!r}"
            )
        items = data.get("results", [])
        if not items:
            # Fallback: try by stock_code
            data2 = self._get("company.json", {"stock_code": query})
            items = data2.get("results", []) if data2.get("status") == "000" else []
        return [
            {
                "corp_code": item.get("corp_code", ""),
                "corp_name": item.get("corp_name", ""),
                "stock_code": item.get("stock_code", ""),
                "modify_date": item.get("modify_date", ""),
            }
            for item in items
        ]

    def fetch_financials(self, corp_code: str, year: int) -> dict[str, Any]:
        """Fetch financial statements for a given corp_code and fiscal year.

        Retrieves consolidated financial statements (연결재무제표).
        Falls back to standalone (개별재무제표) if consolidated is unavailable.

        Args:
            corp_code: DART corp_code (8-digit string, e.g. "00126380").
            year: Fiscal year (e.g. 2024).

        Returns:
            Dict with keys: corp_code, year, income_statement, balance_sheet,
            cash_flow. Each is a list of dicts with account/value pairs.
        """
        results: dict[str, Any] = {
            "corp_code": corp_code,
            "year": year,
            "income_statement": [],
            "balance_sheet": [],
            "cash_flow": [],
        }

        # fs_div: CFS = consolidated, OFS = standalone
        for fs_div in ("CFS", "OFS"):
            common_params = {
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": "11011",  # 사업보고서 (annual)
                "fs_div": fs_div,
            }

            # Income statement (IS)
            if not results["income_statement"]:
                data = self._get("fnlttSinglAcnt.json", {**common_params, "sj_div": "IS"})
                if data.get("status") == "000":
                    results["income_statement"] = _parse_dart_accounts(data.get("list", []))

            # Balance sheet (BS)
            if not results["balance_sheet"]:
                data = self._get("fnlttSinglAcnt.json", {**common_params, "sj_div": "BS"})
                if data.get("status") == "000":
                    results["balance_sheet"] = _parse_dart_accounts(data.get("list", []))

            # Cash flow (CF)
            if not results["cash_flow"]:
                data = self._get("fnlttSinglAcnt.json", {**common_params, "sj_div": "CF"})
                if data.get("status") == "000":
                    results["cash_flow"] = _parse_dart_accounts(data.get("list", []))

            # If all three are populated, no need to try OFS
            if results["income_statement"] and results["balance_sheet"] and results["cash_flow"]:
                break

        return results

    def fetch_disclosures(self, corp_code: str, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch recent disclosure filings for a corp_code.

        Args:
            corp_code: DART corp_code.
            limit: Maximum number of disclosures to return.

        Returns:
            List of dicts with keys: rcept_no, corp_name, report_nm,
            rcept_dt, flr_nm, rm.
        """
        data = self._get(
            "list.json",
            {
                "corp_code": corp_code,
                "page_count": str(limit),
                "sort": "date",
                "sort_mth": "desc",
            },
        )
        status = data.get("status", "")
        if status not in ("000", "013"):
            raise ValueError(
                f"DART API error: status={status!r}, message={data.get('message')!r}"
            )
        items = data.get("list", [])[:limit]
        return [
            {
                "rcept_no": item.get("rcept_no", ""),
                "corp_name": item.get("corp_name", ""),
                "report_nm": item.get("report_nm", ""),
                "rcept_dt": item.get("rcept_dt", ""),
                "flr_nm": item.get("flr_nm", ""),
                "rm": item.get("rm", ""),
            }
            for item in items
        ]


def _parse_dart_accounts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize DART financial account rows to a compact list."""
    result = []
    for row in rows:
        result.append(
            {
                "account_nm": row.get("account_nm", ""),
                "thstrm_amount": row.get("thstrm_amount", ""),  # current year
                "frmtrm_amount": row.get("frmtrm_amount", ""),  # prior year
                "bfefrmtrm_amount": row.get("bfefrmtrm_amount", ""),  # 2 years ago
                "currency": row.get("currency", "KRW"),
            }
        )
    return result


# ---------------------------------------------------------------------------
# SEC EDGAR (US)
# ---------------------------------------------------------------------------

_EDGAR_BASE = "https://data.sec.gov"
_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
_EDGAR_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index?q=%22{query}%22&dateRange=custom&startdt=2020-01-01&forms=10-K"


class EdgarStockClient:
    """SEC EDGAR REST API client for US listed companies."""

    def __init__(self, user_agent: str = "") -> None:
        self._user_agent = (
            user_agent
            or os.getenv("SEC_EDGAR_USER_AGENT", "FinanceFlowLabs research@example.com")
        )

    def _get(self, url: str) -> Any:
        req = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def search_company(self, query: str) -> list[dict[str, Any]]:
        """Search companies by name or ticker on SEC EDGAR.

        Args:
            query: Company name or ticker symbol (e.g. "Apple", "AAPL").

        Returns:
            List of dicts with keys: cik, name, ticker, sic, sic_description.
        """
        # Try ticker lookup first (exact match)
        ticker_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?company={urllib.parse.quote(query)}"
            f"&CIK=&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany"
            f"&output=atom"
        )
        # Use the full-text search company search endpoint
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index"
            f"?q=%22{urllib.parse.quote(query)}%22&forms=10-K"
        )

        # Use the company_tickers.json which maps tickers to CIK
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        try:
            tickers_data: dict[str, dict[str, Any]] = self._get(tickers_url)
            query_lower = query.lower()
            matches = []
            for _idx, entry in tickers_data.items():
                ticker = str(entry.get("ticker", "")).lower()
                title = str(entry.get("title", "")).lower()
                if query_lower == ticker or query_lower in title or query_lower in ticker:
                    cik_str = str(entry.get("cik_str", "")).zfill(10)
                    matches.append(
                        {
                            "cik": cik_str,
                            "name": entry.get("title", ""),
                            "ticker": entry.get("ticker", ""),
                        }
                    )
                    if len(matches) >= 10:
                        break
            return matches
        except Exception:
            return []

    def fetch_company_facts(self, cik: str) -> dict[str, Any]:
        """Fetch XBRL company facts for a CIK.

        Args:
            cik: SEC CIK number (padded to 10 digits, e.g. "0000320193").

        Returns:
            Dict with keys: cik, entity_name, facts_summary.
            facts_summary contains key financial metrics extracted from XBRL tags.
        """
        cik_padded = cik.zfill(10)
        url = f"{_EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik_padded}.json"
        try:
            data: dict[str, Any] = self._get(url)
        except Exception as exc:
            raise ValueError(f"Failed to fetch EDGAR company facts for CIK {cik}: {exc}") from exc

        entity_name = data.get("entityName", "")
        facts = data.get("facts", {})

        # Extract key financial metrics from US-GAAP facts
        us_gaap = facts.get("us-gaap", {})
        summary = _extract_edgar_metrics(us_gaap)

        return {
            "cik": cik_padded,
            "entity_name": entity_name,
            "facts_summary": summary,
        }

    def fetch_recent_filings(self, cik: str, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch recent 10-K and 10-Q filing metadata for a CIK.

        Args:
            cik: SEC CIK number.
            limit: Maximum number of filings to return.

        Returns:
            List of dicts with keys: form, filing_date, report_date,
            accession_number, primary_document.
        """
        cik_padded = cik.zfill(10)
        url = f"{_EDGAR_BASE}/submissions/CIK{cik_padded}.json"
        try:
            data: dict[str, Any] = self._get(url)
        except Exception as exc:
            raise ValueError(f"Failed to fetch EDGAR submissions for CIK {cik}: {exc}") from exc

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])

        results = []
        for i, form in enumerate(forms):
            if form in ("10-K", "10-Q", "20-F"):
                results.append(
                    {
                        "form": form,
                        "filing_date": filing_dates[i] if i < len(filing_dates) else "",
                        "report_date": report_dates[i] if i < len(report_dates) else "",
                        "accession_number": (
                            accession_numbers[i] if i < len(accession_numbers) else ""
                        ),
                        "primary_document": (
                            primary_documents[i] if i < len(primary_documents) else ""
                        ),
                    }
                )
            if len(results) >= limit:
                break

        return results


_KEY_GAAP_METRICS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "GrossProfit",
    "OperatingIncomeLoss",
    "NetIncomeLoss",
    "EarningsPerShareBasic",
    "EarningsPerShareDiluted",
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "CashAndCashEquivalentsAtCarryingValue",
    "LongTermDebt",
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInInvestingActivities",
    "NetCashProvidedByUsedInFinancingActivities",
    "CapitalExpendituresIncurringObligation",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "CommonStockSharesOutstanding",
]


def _extract_edgar_metrics(us_gaap: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract key financial metrics from EDGAR US-GAAP facts dict."""
    result = []
    for tag in _KEY_GAAP_METRICS:
        if tag not in us_gaap:
            continue
        units = us_gaap[tag].get("units", {})
        # Prefer USD values; fallback to shares
        unit_data = units.get("USD", units.get("shares", []))
        # Filter to annual 10-K filings only
        annual = [
            r for r in unit_data if r.get("form") in ("10-K", "20-F") and r.get("val") is not None
        ]
        if not annual:
            continue
        # Sort by end date descending, take last 4 periods
        annual_sorted = sorted(annual, key=lambda r: r.get("end", ""), reverse=True)[:4]
        result.append(
            {
                "metric": tag,
                "unit": "USD" if "USD" in units else list(units.keys())[0] if units else "",
                "periods": [
                    {
                        "end": r.get("end", ""),
                        "val": r.get("val"),
                        "accn": r.get("accn", ""),
                    }
                    for r in annual_sorted
                ],
            }
        )
    return result
