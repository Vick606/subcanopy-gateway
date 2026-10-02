# Security policy

## Supported versions

Only the latest release on the `main` branch receives security fixes.

## Reporting a vulnerability

Report privately by email to vickoch20@gmail.com, or use GitHub's
private vulnerability reporting at
https://github.com/Vick606/subcanopy-gateway/security/advisories/new

Do not open a public issue for security problems.

## What to include

- Affected version or commit
- Steps to reproduce
- Impact assessment
- Any suggested fix

## What is in scope

- The gateway API surface (`/scan`, `/scan/batch`, `/scans`)
- Database handling and SQL injection
- Authentication and authorization (once Stage 4 lands)
- Denial of service through the scan endpoints

Out of scope: vulnerabilities in the underlying `subcanopy-guard`
library. Report those against that project.

## Response

Acknowledgment within 72 hours. A fix or mitigation timeline follows
once the report is triaged.