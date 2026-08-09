# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Kestrel.ai, please send an email to [INSERT EMAIL]. All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### What to include

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity, typically 2-4 weeks

### What to expect

- A confirmation email within 48 hours
- An assessment of the vulnerability within 1 week
- A fix timeline based on severity
- Credit in the release notes (unless you prefer anonymity)

## Security Best Practices

### Environment Variables

- Never commit `.env` files to version control
- Use `.env.example` as a template
- Rotate secrets regularly

### Authentication

- Clerk is used for authentication
- JWT tokens are verified on every protected endpoint
- API keys should be stored in environment variables

### Data Protection

- All database connections use SSL
- Sensitive data is encrypted at rest
- PII is handled according to GDPR guidelines

### Dependencies

- Dependencies are audited regularly via `npm audit` and `pip audit`
- Automated security scanning via GitHub Dependabot

## Scope

This security policy applies to:
- The main Kestrel.ai application
- Backend API services
- Frontend application
- Infrastructure configurations

This policy does NOT apply to:
- Third-party services or integrations
- Forks of this repository
