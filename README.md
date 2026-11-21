# Mini-VulnFinBot — Secure CI/CD Pipeline with AI-Specific Security Controls

## 1. Project Description

**Mini-VulnFinBot** is a simplified AI-powered financial assistant REST API built with Python 3.12 and Flask. The project demonstrates a production-style DevSecOps CI/CD pipeline in GitHub Actions that combines traditional application security testing (Unit Tests, SAST, SCA, Container Scanning, DAST) with AI-specific security testing (prompt injection, system prompt disclosure, sensitive data leakage, unauthorized tool usage, and output validation).

> **Note on Mock AI Implementation:** The application uses a mock AI response generator to verify application-level input validation, pattern filtering, authorization boundaries, and output sanitization. True semantic prompt injection resistance requires evaluating a live LLM in a controlled, isolated environment.

## 2. Technologies Used

| Technology / Tool | Category | Purpose |
| :--- | :--- | :--- |
| Python 3.12, Flask, Gunicorn | Backend / WSGI | REST API implementation (`GET /health`, `POST /api/chat`) and production server |
| pytest | Testing | Automated unit tests and AI-specific security test suite |
| GitHub Actions | CI/CD | Automated workflow triggered on `push` and `pull_request` |
| Bandit | SAST | Python static security analysis |
| Semgrep | SAST | Rule-based static analysis with custom rules (`security/semgrep/rules.yml`) |
| pip-audit | SCA | Python dependency vulnerability scanning against known CVEs |
| Docker & Trivy | Container Security | Non-root container image build and OS/library vulnerability scanning |
| OWASP ZAP (Baseline) | DAST | Passive dynamic scanning of the running containerized application |
| GitHub Actions Artifacts | Reporting | Centralized collection and 30-day retention of all security reports |

## 3. Project Architecture

```text
vulnfinbot-secure-pipeline/
├── app/
│   ├── __init__.py          # Flask app factory, security headers, JSON error handlers
│   └── routes.py            # /health & /api/chat endpoints, validation & AI guards
├── tests/
│   ├── __init__.py
│   ├── test_app.py          # 7 unit test scenarios (11 parametrized cases)
│   └── test_ai_security.py  # 5 AI security scenarios + ai-security-report.md generator
├── security/
│   └── semgrep/
│       └── rules.yml        # Custom Semgrep rules (eval, exec, shell=True, debug=True)
├── reports/                 # Output directory for generated reports (gitignored)
├── .github/
│   └── workflows/
│       └── security-pipeline.yml  # Full DevSecOps CI/CD pipeline
├── requirements.txt
├── Dockerfile               # Non-root python:3.12-slim + Gunicorn container
├── .dockerignore
├── .gitignore
├── run.py
└── README.md
```

## 4. Installing Dependencies

```bash
python -m venv .venv
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
# Optional: install local security scanners
pip install bandit semgrep pip-audit
```

## 5. Running the Application

### Locally with Flask

```bash
python run.py
```

The API listens on `http://127.0.0.1:5000`.

- Health check: `GET http://127.0.0.1:5000/health`
- Chat endpoint: `POST http://127.0.0.1:5000/api/chat` with JSON body `{"message": "How can I manage my monthly budget?"}`

### With Docker

```bash
docker build -t vulnfinbot:latest .
docker run --rm -p 5000:5000 vulnfinbot:latest
```

## 6. Executing Tests

```bash
pytest -v
```

Running `pytest` executes both unit tests (`tests/test_app.py`) and AI security tests (`tests/test_ai_security.py`), automatically generating `reports/ai-security-report.md`.

## 7. CI/CD Pipeline Description

The GitHub Actions workflow (`.github/workflows/security-pipeline.yml`) triggers automatically on every push to `main` or `test-*` branches and on pull requests targeting `main`. It runs the following stages sequentially:

1. Checkout repository and set up Python 3.12.
2. Create the `reports/` directory and install dependencies + SAST/SCA scanners.
3. Run unit tests (`pytest tests/test_app.py -v`) and AI security tests (`pytest tests/test_ai_security.py -v`).
4. Run Bandit SAST and export `reports/bandit-report.json`.
5. Run Semgrep SAST with custom rules and export `reports/semgrep-report.json`.
6. Run `pip-audit` and export `reports/dependency-report.json`.
7. Build the Docker image (`vulnfinbot:latest`) and scan it with Trivy (`reports/trivy-report.json`).
8. Start the container and run OWASP ZAP Baseline scan (`reports/zap-report.json`), then stop the container (`if: always()`).
9. Upload all reports in `reports/` as a GitHub Actions Artifact named `vulnfinbot-security-reports` (`if: always()`).

## 8. Integrated Security Tools

- **Bandit:** Detects insecure Python constructs, hardcoded secrets, and weak cryptography.
- **Semgrep:** Enforces custom security rules defined in `security/semgrep/rules.yml` (`python-no-eval`, `python-no-exec`, `python-subprocess-shell-true`, `flask-debug-enabled`).
- **pip-audit:** Checks `requirements.txt` against PyPI/OSV vulnerability databases.
- **Trivy:** Scans OS packages and Python dependencies inside the built Docker image.
- **OWASP ZAP Baseline:** Passively inspects HTTP responses, headers, and potential information disclosure against the running container.
- **AI Security Test Suite:** Evaluates 5 OWASP LLM Top 10 risk categories (LLM01, LLM02, LLM05, LLM06, LLM07) and produces a structured Markdown report.

## 9. Accessing Security Reports

1. Open the **Actions** tab in this GitHub repository.
2. Select a completed run of **Security CI Pipeline**.
3. Scroll to the **Artifacts** section at the bottom of the summary page.
4. Download **`vulnfinbot-security-reports`**, which contains:
   - `bandit-report.json`
   - `semgrep-report.json`
   - `dependency-report.json`
   - `trivy-report.json`
   - `zap-report.json`
   - `ai-security-report.md`

## 10. Identified Vulnerabilities and Remediation Recommendations

| Security Tool | Findings | Severity | Recommended Action |
| :--- | :--- | :--- | :--- |
| **Bandit** | 0 issues on `main` (1 `B307` finding detected on `test-vuln` branch before fix) | None (Medium pre-fix) | Ban `eval()`/`exec()`; use safe parsers such as `json.loads()` or `ast.literal_eval()`. |
| **Semgrep** | 0 findings on `main` (1 `python-no-eval` finding detected on `test-vuln` branch before fix) | None (Error pre-fix) | Keep custom SAST rules enforced in CI on every PR. |
| **pip-audit** | 0 known CVEs in `requirements.txt` | None | Periodically update dependencies and rebuild the image when security patches release. |
| **Trivy** | 0 HIGH/CRITICAL Python vulnerabilities; minor OS-level advisories in base Debian image | Low / Medium | Rebuild regularly with updated `python:3.12-slim` base images and keep running as non-root `appuser`. |
| **OWASP ZAP** | 0 FAIL; informational warnings (`Server` header version leak `[10036]`, missing `Permissions-Policy` `[10063]`) | Low / Info | Strip `Server` header at reverse proxy (e.g. Nginx) and add a `Permissions-Policy` response header. |
| **AI Security Tests** | 5 / 5 application-level scenarios passed | Info | When integrating a live LLM, run adversarial red-teaming in an isolated staging environment. |
