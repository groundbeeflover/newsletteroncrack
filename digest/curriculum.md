# Learning track

One concept per issue, top to bottom. The routine ticks items off as `- [x] Title — YYYY-MM-DD`. Reorder, add, or delete lines freely; keep the `- [ ] ` format and the `## ` module headings so the site can draw the track.

## Foundations

- [ ] Thinking like an attacker: threat modeling with STRIDE
- [ ] Risk, the CIA triad, and how security decisions actually get made
- [ ] The security industry map: who sells what (endpoint, identity, cloud, SIEM, MDR, services)
- [ ] Networking from an attacker's view: ports, services, and what's exposed
- [ ] DNS: how it works and how it's abused (hijacking, tunneling, subdomain takeover)
- [ ] TLS and certificates: what they protect and what they don't
- [ ] Cryptographic building blocks: hashing, encryption, signatures, MACs
- [ ] Password storage: salting, bcrypt and Argon2, and why fast hashes fail
- [ ] Authentication, sessions, and how MFA gets bypassed
- [ ] OAuth 2.0 and OpenID Connect: what they're for and common misconfigurations
- [ ] The Linux permission model: users, groups, SUID, capabilities
- [ ] The Windows security model: accounts, tokens, privileges, UAC

## Penetration testing methodology

- [ ] What a penetration test is: scope, rules of engagement, written authorization
- [ ] Pentests, red teams, vulnerability assessments, and bug bounties compared
- [ ] Careers in security: offensive, defensive, and governance roles, and which certifications matter
- [ ] Passive reconnaissance and OSINT
- [ ] Active scanning with nmap: host discovery, port scans, service detection
- [ ] Enumerating common services: SMB, FTP, SSH, HTTP
- [ ] Prioritizing vulnerabilities: CVSS, EPSS, and the KEV catalog
- [ ] Getting started with CTFs and building a home lab
- [ ] Writing findings that get fixed: the pentest report

## Web application security

- [ ] How browsers enforce security: same-origin policy, CORS, cookies
- [ ] The OWASP Top 10 as a map
- [ ] Broken access control and IDOR
- [ ] SQL injection
- [ ] Cross-site scripting: reflected, stored, DOM-based
- [ ] Content Security Policy as a defense against XSS
- [ ] CSRF and SameSite cookies
- [ ] Authentication and session management flaws
- [ ] Path traversal and unsafe file uploads
- [ ] OS command injection
- [ ] Server-side request forgery and cloud metadata endpoints
- [ ] Server-side template injection
- [ ] XML external entities
- [ ] Insecure deserialization
- [ ] JSON Web Token pitfalls
- [ ] API security: broken object-level authorization and mass assignment
- [ ] Business logic flaws and race conditions
- [ ] HTTP request smuggling
- [ ] Bug bounty programs and coordinated vulnerability disclosure

## Systems and networks

- [ ] Password attacks: cracking, spraying, credential stuffing
- [ ] From advisory to proof of concept: reproducing a known CVE safely
- [ ] Memory corruption basics and modern mitigations (ASLR, DEP, stack canaries)
- [ ] Linux privilege escalation
- [ ] Windows privilege escalation
- [ ] LLMNR and NBT-NS poisoning and NTLM relay
- [ ] Lateral movement: how attackers move between machines
- [ ] Pivoting and tunneling
- [ ] Command and control: how implants talk home
- [ ] Persistence techniques on Windows and Linux

## Active Directory

- [ ] Active Directory fundamentals: domains, forests, trusts, Group Policy
- [ ] Kerberos and NTLM explained
- [ ] Enumerating AD and finding attack paths with BloodHound
- [ ] Kerberoasting and AS-REP roasting
- [ ] Pass-the-hash and pass-the-ticket
- [ ] Active Directory Certificate Services abuse
- [ ] DCSync, golden tickets, and silver tickets
- [ ] Hardening AD: tiering, LAPS, Protected Users

## Defense and detection

- [ ] Defense in depth and zero trust
- [ ] Hardening baselines: CIS Benchmarks and attack surface reduction
- [ ] Logging that matters: Windows event IDs, Sysmon, auditd
- [ ] SIEM fundamentals: collect, normalize, correlate
- [ ] MITRE ATT&CK as a shared language
- [ ] Detection engineering and Sigma rules
- [ ] How EDR works and how attackers try to evade it
- [ ] Network security monitoring with Zeek and Suricata
- [ ] Email security: SPF, DKIM, DMARC, and phishing defense
- [ ] Threat hunting: forming and testing hypotheses
- [ ] Incident response: the NIST lifecycle in practice
- [ ] Digital forensics basics: disk, memory, and timelines
- [ ] Vulnerability management as a program, not a scan
- [ ] Deception: honeypots and canary tokens
- [ ] Security regulation in the EU: NIS2, GDPR breach notification, DORA, the Cyber Resilience Act

## Cloud and supply chain

- [ ] The shared responsibility model
- [ ] Cloud IAM and the misconfigurations behind most cloud breaches
- [ ] Container security: images, runtime, and escapes
- [ ] The Kubernetes attack surface
- [ ] Secrets management
- [ ] CI/CD security and software supply chain attacks
- [ ] SBOMs, dependency confusion, and typosquatting

## Threats and intelligence

- [ ] Malware families and what they're built to do
- [ ] The ransomware economy: affiliates, access brokers, extortion
- [ ] Social engineering and adversary-in-the-middle phishing kits
- [ ] Threat intelligence: indicators versus behaviors, and the Pyramid of Pain
- [ ] Malware analysis basics: static, dynamic, and sandboxes
- [ ] Nation-state actors and how threat groups get named
- [ ] How security companies get funded, acquired, and consolidated
