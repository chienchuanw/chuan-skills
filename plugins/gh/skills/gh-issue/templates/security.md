## Summary

{One sentence describing the security concern. Do not include exploit details in the title.}

## Severity Assessment

- **Severity**: {Critical / High / Medium / Low}
- **Attack vector**: {Network, Local, Physical, Adjacent}
- **Impact**: {What an attacker could achieve: data exposure, privilege escalation, denial of service, etc.}
- **Exploitability**: {How easy it is to exploit: requires authentication, requires specific conditions, publicly known, etc.}

## Vulnerability Details

{Describe the vulnerability. Include the type (e.g., SQL injection, XSS, CSRF, insecure deserialization, path traversal) and the mechanism.}

## Affected Code

{Specific file paths, functions, and line numbers where the vulnerability exists.}

- `{file_path}:{line}` -- {brief description of the vulnerable code}

## Reproduction Steps

{How to demonstrate the vulnerability in a controlled environment. Be specific enough for a developer to verify the fix, but do not provide weaponized exploit code.}

1. {Step 1}
2. {Step 2}
3. {Step 3}

## Proposed Fix

{Describe the remediation strategy. Reference security best practices or framework-specific guidance.}

- **Immediate mitigation**: {short-term workaround if the fix requires significant work}
- **Permanent fix**: {the proper solution}

## Acceptance Criteria

- [ ] Vulnerability is no longer reproducible using the steps above
- [ ] Fix does not introduce new security issues
- [ ] {Specific security control is in place, e.g., "Input is sanitized before query execution"}
- [ ] Security test added to prevent regression
