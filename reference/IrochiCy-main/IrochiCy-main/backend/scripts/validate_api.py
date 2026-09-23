"""
SIH26145 API Validator — verifies all endpoints against a running server.

Usage: python scripts/validate_api.py --url http://localhost:8000

Outputs results with ANSI color codes:
  GREEN [PASS] for pass, RED [FAIL] for fail, with latency in ms.
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

# ── ANSI colors (no third-party libs) ────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


class APIValidator:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.passed = 0
        self.failed = 0
        self.results: list[tuple[str, bool, float, str]] = []
        self.token: str | None = None

    def _print_result(self, name: str, ok: bool, ms: float, detail: str = ""):
        if ok:
            icon = f"{GREEN}[PASS]{RESET}"
            self.passed += 1
        else:
            icon = f"{RED}[FAIL]{RESET}"
            self.failed += 1
        self.results.append((name, ok, ms, detail))
        latency = f"{DIM}{ms:.0f}ms{RESET}"
        extra = f"  {DIM}{detail}{RESET}" if detail else ""
        print(f"  {icon} {name}  {latency}{extra}")

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def run(self) -> int:
        print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
        print(f"{BOLD}  SIH26145 API Validator{RESET}")
        print(f"{BOLD}  Target: {self.base_url}{RESET}")
        print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")

        with httpx.Client(base_url=self.base_url, timeout=10.0) as c:
            # 1. Health check
            self._check(c, "GET /health", "GET", "/health",
                        lambda r: r.status_code == 200 and r.json().get("status") == "ok")

            # 2. Login bad creds → 401
            self._check(c, "POST /auth/login (bad creds)", "POST", "/auth/login",
                        lambda r: r.status_code == 401,
                        json={"username": "bad", "password": "bad"})

            # 3. Login good creds
            start = time.perf_counter()
            r = c.post("/auth/login", json={"username": "admin", "password": "12345678"})
            ms = (time.perf_counter() - start) * 1000
            ok = r.status_code == 200 and "access_token" in r.json()
            if ok:
                self.token = r.json()["access_token"]
            self._print_result("POST /auth/login (good creds)", ok, ms)

            # 4. List alerts
            self._check(c, "GET /alerts/", "GET", "/alerts/",
                        lambda r: r.status_code == 200 and "items" in r.json(),
                        headers=self._headers())

            # 5. Filter alerts by severity
            self._check(c, "GET /alerts/?severity=critical", "GET",
                        "/alerts/?severity=critical",
                        lambda r: r.status_code == 200,
                        headers=self._headers())

            # 6. CSV export
            self._check(c, "GET /alerts/export/csv", "GET", "/alerts/export/csv",
                        lambda r: r.status_code == 200 and "text/csv" in r.headers.get("content-type", ""),
                        headers=self._headers())

            # 7. Dashboard summary
            self._check(c, "GET /dashboard/summary", "GET", "/dashboard/summary",
                        lambda r: r.status_code == 200 and "kpi" in r.json(),
                        headers=self._headers())

            # 8. Dashboard timeline
            self._check(c, "GET /dashboard/timeline", "GET", "/dashboard/timeline",
                        lambda r: r.status_code == 200 and len(r.json().get("buckets", [])) == 24,
                        headers=self._headers(),
                        detail="24 buckets")

            # 9. Dashboard KPI
            self._check(c, "GET /dashboard/kpi", "GET", "/dashboard/kpi",
                        lambda r: r.status_code == 200,
                        headers=self._headers())

            # 10. List threats
            self._check(c, "GET /threats/", "GET", "/threats/",
                        lambda r: r.status_code == 200 and len(r.json()) == 5,
                        headers=self._headers(),
                        detail="5 threat types")

            # 11. DDoS detail
            self._check(c, "GET /threats/ddos", "GET", "/threats/ddos",
                        lambda r: r.status_code == 200 and "signals" in r.json().get("stat", {}),
                        headers=self._headers())

            # 12. Invalid threat type → 404
            self._check(c, "GET /threats/invalid_type", "GET", "/threats/invalid_type",
                        lambda r: r.status_code == 404,
                        headers=self._headers())

            # 13. Get current user
            self._check(c, "GET /users/me", "GET", "/users/me",
                        lambda r: r.status_code == 200 and r.json().get("username") == "admin",
                        headers=self._headers())

            # 14. WebSocket (test connection via HTTP upgrade attempt)
            start = time.perf_counter()
            try:
                r = c.get(f"/ws/alerts?token={self.token}")
                ms = (time.perf_counter() - start) * 1000
                # WebSocket endpoints return 403/404/426 on normal HTTP GET
                # Any response means the endpoint is reachable
                ws_ok = r.status_code in (403, 404, 426, 400)
                self._print_result("WS /ws/alerts (reachability)", ws_ok, ms,
                                   f"status={r.status_code} (expected non-200 for HTTP)")
            except Exception as exc:
                ms = (time.perf_counter() - start) * 1000
                self._print_result("WS /ws/alerts (reachability)", False, ms, str(exc))

            # 15. Logout
            self._check(c, "POST /auth/logout", "POST", "/auth/logout",
                        lambda r: r.status_code == 200,
                        headers=self._headers())

        # Summary
        total = self.passed + self.failed
        print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
        if self.failed == 0:
            print(f"  {GREEN}{BOLD}{total}/{total} checks passed [OK]{RESET}")
        else:
            print(f"  {RED}{BOLD}{self.passed}/{total} checks passed "
                  f"({self.failed} failed){RESET}")
        print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")

        return 0 if self.failed == 0 else 1

    def _check(
        self,
        client: httpx.Client,
        name: str,
        method: str,
        path: str,
        assertion,
        json=None,
        headers=None,
        detail: str = "",
    ):
        start = time.perf_counter()
        try:
            r = client.request(method, path, json=json, headers=headers)
            ms = (time.perf_counter() - start) * 1000
            ok = assertion(r)
            info = detail or f"status={r.status_code}"
            self._print_result(name, ok, ms, info)
        except Exception as exc:
            ms = (time.perf_counter() - start) * 1000
            self._print_result(name, False, ms, str(exc))


def main():
    parser = argparse.ArgumentParser(description="SIH26145 API Validator")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the running FastAPI server",
    )
    args = parser.parse_args()
    validator = APIValidator(args.url)
    sys.exit(validator.run())


if __name__ == "__main__":
    main()
