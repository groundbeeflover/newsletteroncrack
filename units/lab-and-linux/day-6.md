---
title: "Review: lab, permissions and Linux"
date: 2026-11-15
kind: review
minutes: 15
---

This is the first unit, so there are no earlier units to revisit yet. All five questions come from this week; later weeks will bring older material back.

## Questions

1. Why should a deliberately vulnerable VM sit on a host-only network, and what could go wrong with a bridged adapter?
2. A process running as `alice` tries to read a file with mode `-rw-r-----` owned by `root:shadow`. What does the kernel decide, and what does it look at?
3. What does the `s` in `-rwsr-xr-x` do, and why is it risky on a root-owned program?
4. Name two Linux log sources or tools for noticing misuse of privileges, and what each one shows.
5. Pick one Bandit level and describe the mistake it teaches and the fix.

<details markdown="1">
<summary>Answers</summary>

1. Host-only means the VM reaches only the host and other lab VMs, with no route to the internet or home network. Bridging puts a weak machine on the home network, where scanners and other devices can reach it.
2. It compares the process's UID and GIDs with the file's owner, group and bits. Alice is not root, and unless she is in group `shadow` she falls under "others", which has no bits, so access is denied.
3. SUID makes the program run with the file owner's identity, so root-owned means root. Any flaw in the program is therefore a route to root.
4. For example the authentication log (logins, failures, `sudo` use) and `auditd` (file access and program execution rules you define). File integrity monitoring is another valid answer.
5. Any honest answer works. For example: a password in a world-readable file, fixed by tightening the mode and owner, and keeping secrets out of plain files.

</details>

## Log the unit

When the lab is done, add this under `progress:` in `me/progress.yaml`:

```yaml
  - unit: lab-and-linux
    lab_done: YYYY-MM-DD
    confidence: 3
    note: "one line on what stuck and what didn't"
```

Then write a five-sentence explanation of the week, in your own words, in `me/notes/lab-and-linux.md`. It will get a real debrief next week.
