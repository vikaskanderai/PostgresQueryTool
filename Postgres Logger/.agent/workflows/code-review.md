---
description: Run code review on the PostgreSQL Query Tool codebase
---

# Code Review Workflow

This workflow runs the automated code review agent to validate the codebase against project standards.

## Steps

1. Navigate to the pg_logger directory
```bash
cd pg_logger
```

// turbo
2. Run the code review agent with terminal output
```bash
python3 code_review.py --root pg_logger
```

3. (Optional) Generate a markdown report
```bash
python3 code_review.py --root pg_logger --format markdown --output code_review_report.md
```

4. (Optional) Generate a JSON report for automation
```bash
python3 code_review.py --root pg_logger --format json --output code_review.json
```

## Understanding Results

- **🔴 CRITICAL**: Must be fixed immediately (security risks, architectural violations)
- **🟡 WARNING**: Should be addressed (potential issues, missing best practices)
- **🔵 INFO**: Informational (suggestions for improvement)

## Documentation

For more information, see [CODE_REVIEW.md](file:///home/vikas-kanderai/Antigravity/PostgresQueryTool/Postgres%20Logger/pg_logger/CODE_REVIEW.md)
