---
title: "Prevent and detect: hardening and watching permissions"
date: 2026-11-11
kind: lesson
minutes: 20
---

## Controls, most effective first

1. **Remove the exposure.** A service that is not installed or not reachable cannot be attacked. For your lab: host-only networking, no bridged adapters, no port forwards to the lab.
2. **Least privilege.** Run each service as its own unprivileged user. Give files the narrowest mode that works: `600` for secrets, `640` with a dedicated group when two accounts need them.
3. **Shrink the privileged set.** Audit SUID/SGID binaries and remove the bit from anything not needed. Prefer a narrow capability to SUID root. Mount data partitions with `nosuid,noexec` where possible.
4. **Contain failure.** Separate users, containers or VMs, so a compromised service cannot read other services' data.
5. **Patch.** Bugs in SUID programs and the kernel are fixed upstream; updates close them. This matters, but it is last here because it only helps after a flaw is known.

## Detecting trouble

Prevention fails, so you also watch. What to collect on Linux:

- **Authentication log** (`/var/log/auth.log` on Debian-style systems, or `journalctl -u ssh`): lines such as `Failed password for root from 203.0.113.9` show password guessing. `sudo` records who ran what as root.
- **auditd** (the Linux audit framework) can log file access and program execution. An illustrative rule that records any change to the password file:

```
-w /etc/shadow -p wa -k shadow_change
```

- **File integrity monitoring**: hash important files and alert when a hash or mode changes, or a new SUID file appears.
- **Process and network telemetry**: a web server process spawning a shell is unusual and worth an alert.

This unit has no assigned MITRE ATT&CK techniques, but for orientation, ATT&CK is the public catalogue of attacker behaviour, and the Linux privilege-escalation material falls under its Privilege Escalation tactic. Later units assign specific IDs.

## Two practical habits for the lab

- **Make a list before you hunt.** After each Bandit level, write down what permission or setting made it possible. Defence is mostly pattern recognition, and a written list builds the patterns.
- **Check your own box.** Run `find / -perm -4000 -type f 2>/dev/null` on your Kali VM and look up one result you do not recognise. Ask what it needs the bit for, and what would break if you removed it.

Also remember the review mindset: a control that you cannot see working is a control you cannot trust. Try to read your own authentication log after a deliberately wrong SSH login, and find the line that records it.

## Back to Monday's hypothetical

Walking Dana's story, the control that breaks each step:

| Step | What broke it |
|---|---|
| VM joins the home network | Host-only network: it never gets a route out |
| Router forwards a port to its address | No route means forwarding has nothing to reach |
| Scanner finds the VM | Not reachable from the internet |
| Default password works | In a lab this is fine; the isolation is the control |
| VM reaches the printer and NAS | Isolated segment: nothing else is on it |

Notice that the strongest control is the first one on the list, and it is a design choice rather than a product.

## Check yourself

1. Why is `chmod 600` on a file full of API keys better than a note saying "do not share this"?
2. You see an `auditd` event: `/usr/bin/vim.basic` was run by a web-server user and then `/bin/sh` was started from it. Name two things that make this worth investigating.

<details markdown="1">
<summary>Answers</summary>

1. The kernel enforces permissions on every access. A note relies on people behaving; the mode applies even when a process is compromised or someone makes a mistake.
2. A service account has no normal reason to run an interactive editor, and a shell launched from an editor suggests an escape to command execution. The web-server identity also suggests an intruder already controls the service.

</details>
