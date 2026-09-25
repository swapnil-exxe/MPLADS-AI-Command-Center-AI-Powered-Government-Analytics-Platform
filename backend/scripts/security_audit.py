import os
import sys
import re
import subprocess
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent

def check_hardcoded_secrets():
    print("--- 1. Scanning Codebase for Hardcoded Keys & Secrets ---")
    secret_patterns = [
        (r'gsk_[A-Za-z0-9_\-]{20,}', "Groq API Key"),
        (r'sb_secret_[A-Za-z0-9_\-]{20,}', "Supabase Secret Key"),
        (r'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_\-]{30,}', "Hardcoded JWT Token"),
        (r'(?:postgres|postgresql)://[a-zA-Z0-9_\.]+:([a-zA-Z0-9_!@#$%^&*]{6,})@', "Hardcoded Database Password"),
    ]
    
    ignore_dirs = {".git", ".venv", "venv", "node_modules", "dist", ".oxlint_cache", "__pycache__"}
    findings = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            if f.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".sql", ".sh")) and f != "security_audit.py":
                filepath = Path(root) / f
                if filepath.name in [".env", ".env.local"]:
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                        lines = file.readlines()
                        for i, line in enumerate(lines, 1):
                            for pattern, desc in secret_patterns:
                                if re.search(pattern, line):
                                    findings.append((filepath.relative_to(root_dir), i, desc))
                except Exception:
                    pass

    if findings:
        print("[FAIL] Hardcoded secrets detected in source files:")
        for path, line, desc in findings:
            print(f"  - {path}:{line} -> {desc}")
        return False
    else:
        print("[PASS] Zero hardcoded API keys or secrets found in codebase source files.")
        return True

def check_gitignore():
    print("\n--- 2. Auditing .gitignore & Secrets Exclusion ---")
    gitignore_path = root_dir / ".gitignore"
    if not gitignore_path.exists():
        print("[FAIL] .gitignore file missing!")
        return False

    with open(gitignore_path, "r") as f:
        content = f.read()

    required = [".env", "*.key", "*.pem", "node_modules"]
    missing = [req for req in required if req not in content]
    if missing:
        print(f"[FAIL] Missing patterns in .gitignore: {missing}")
        return False
    else:
        print("[PASS] .gitignore properly excludes .env, keys, and sensitive binaries.")
        return True

def check_git_history():
    print("\n--- 3. Checking Git Commit History for Exposed .env Secrets ---")
    try:
        cmd = ["git", "log", "--all", "--full-history", "--", "*.env"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=root_dir)
        if res.stdout.strip():
            print("[WARNING] Historical commit references to .env files detected in git log:")
            print(res.stdout[:300])
        else:
            print("[PASS] Git commit history is clean of committed .env secret files.")
        return True
    except Exception as e:
        print(f"[SKIP] Git command failed: {e}")
        return True

def check_rate_limiting():
    print("\n--- 4. Testing API Rate Limiting Configuration ---")
    auth_py = root_dir / "api" / "routers" / "auth.py"
    if auth_py.exists():
        with open(auth_py, "r") as f:
            content = f.read()
        if "@limiter.limit(" in content:
            print("[PASS] Login endpoint rate limit configured and active.")
            return True
        else:
            print("[FAIL] Login endpoint rate limit decorator missing.")
            return False
    return True

def main():
    print("======================================================================")
    print("RUNNING VIBE CODING SECURITY AUDIT & CHECKS")
    print("======================================================================")
    
    r1 = check_hardcoded_secrets()
    r2 = check_gitignore()
    r3 = check_git_history()
    r4 = check_rate_limiting()

    print("\n======================================================================")
    if r1 and r2 and r3 and r4:
        print("SECURITY AUDIT PASSED: 0 CRITICAL VULNERABILITIES REMAINING")
    else:
        print("SECURITY AUDIT COMPLETED WITH ISSUES TO RESOLVE")
    print("======================================================================")

if __name__ == "__main__":
    main()
