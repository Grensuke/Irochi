import argparse
import json
import subprocess
import sys
import time
import urllib.request


def check_prerequisites(skip_docker: bool = False):
    print("Checking prerequisites...")
    try:
        response = urllib.request.urlopen("http://localhost:8000/health")
        if response.getcode() != 200:
            print("Error: Backend is running but /health returned non-200")
            sys.exit(1)
    except urllib.error.URLError:
        print("Error: Cannot connect to http://localhost:8000/health")
        print("Please start the backend with: uvicorn app.main:app --port 8000 --reload")
        sys.exit(1)

    if not skip_docker:
        try:
            # Check docker compose ps --format json
            result = subprocess.run(
                ["docker", "compose", "-f", "../infrastructure/docker-compose.yml", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            # Docker compose JSON output might be a single array or JSON per line
            output = result.stdout.strip()
            services = []
            if output:
                try:
                    # Try parsing as a single array
                    services = json.loads(output)
                    if isinstance(services, dict): # Sometimes it returns a single dict if only one service
                        services = [services]
                except json.JSONDecodeError:
                    # Try parsing JSON lines
                    services = [json.loads(line) for line in output.split('\n') if line.strip()]
            
            for service in services:
                # depending on docker compose version, keys might vary
                state = service.get("State", service.get("state", ""))
                status = service.get("Status", service.get("status", ""))
                if "running" not in state.lower() and "up" not in status.lower():
                    print(f"Warning: Service {service.get('Name', service.get('Service', 'unknown'))} does not seem fully running (Status: {status})")
                    
        except FileNotFoundError:
            print("Warning: docker compose command not found, skipping docker check.")
        except subprocess.CalledProcessError as e:
            print("Warning: Could not check docker compose status. Are you in the right directory?")
            
    print("Prerequisites OK.\n")


def run_phase(cmd: list[str], label: str) -> tuple[bool, float]:
    print(f"--- Running {label} ---")
    start_time = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - start_time
    success = (result.returncode == 0)
    print(f"{'PASS' if success else 'FAIL'} ({elapsed:.1f}s)\n")
    return success, elapsed


def main():
    parser = argparse.ArgumentParser(description="Run all tests for SIH26145")
    parser.add_argument("--skip-load", action="store_true", help="Skip the slow load tests")
    parser.add_argument("--unit-only", action="store_true", help="Skip all e2e tests")
    args = parser.parse_args()

    check_prerequisites(skip_docker=args.unit_only)

    phases = []
    
    # PHASE 1
    phases.append({
        "cmd": [sys.executable, "-m", "pytest", "tests/", "-v", "--ignore=tests/e2e", "--tb=short", "-q"],
        "label": "Phase 1  Unit & Integration Tests (63)"
    })
    
    # PHASE 2
    phases.append({
        "cmd": [sys.executable, "scripts/validate_api.py", "--url", "http://localhost:8000"],
        "label": "Phase 2  API Validator (15 checks)"
    })

    if not args.unit_only:
        # PHASE 3
        phases.append({
            "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_pipeline_e2e.py", "-v", "--tb=short"],
            "label": "Phase 3  E2E Pipeline Tests (7)"
        })
        
        # PHASE 4
        phases.append({
            "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_api_contracts_e2e.py", "-v", "--tb=short"],
            "label": "Phase 4  E2E API Contract Tests (8)"
        })
        
        # PHASE 5
        phases.append({
            "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_security_e2e.py", "-v", "--tb=short"],
            "label": "Phase 5  E2E Security Tests (9)"
        })
        
        # PHASE 6
        phases.append({
            "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_database_integrity_e2e.py", "-v", "--tb=short"],
            "label": "Phase 6  E2E Database Integrity Tests (6)"
        })
        
        # PHASE 7
        phases.append({
            "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_redis_state_e2e.py", "-v", "--tb=short"],
            "label": "Phase 7  E2E Redis State Tests (5)"
        })
        
        if not args.skip_load:
            # PHASE 8
            phases.append({
                "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_load_e2e.py", "-v", "--tb=short", "-m", "slow"],
                "label": "Phase 8  Load & Stress Tests (4)"
            })

    total_time = 0.0
    results = []
    
    for phase in phases:
        success, elapsed = run_phase(phase["cmd"], phase["label"])
        results.append((phase["label"], success, elapsed))
        total_time += elapsed

    # Final Report
    print("===========================================================")
    print(" SIH26145 - COMPLETE TEST REPORT")
    print("===========================================================")
    
    failed_phases = []
    for label, success, elapsed in results:
        status = "PASS" if success else "FAIL"
        if not success:
            failed_phases.append(label.split("  ")[0]) # e.g. "Phase 5"
        print(f" {label:<45} {status} {elapsed:>5.1f}s")
        
    print("-----------------------------------------------------------")
    if not failed_phases:
        print(" RESULT: ALL PHASES PASSED")
        print(f" Total time: {total_time:.1f}s")
        print(" Backend is READY FOR FRONTEND INTEGRATION")
        print("===========================================================")
        sys.exit(0)
    else:
        print(f" RESULT: {len(failed_phases)} PHASES FAILED")
        print(f" Failed: {', '.join(failed_phases)}")
        print(" See output above for details.")
        print("===========================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
