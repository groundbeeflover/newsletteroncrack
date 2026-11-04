---
title: "How Linux decides: users, permissions, SUID"
date: 2026-11-10
kind: lesson
minutes: 20
---

## The model in one paragraph

Every process runs with a numeric user ID (UID) and group IDs (GIDs). Every file stores an owner, a group and a set of permission bits. When a process opens a file, the kernel compares the process's IDs with the file's and allows or refuses. Names like `alice` are only labels for the numbers. UID 0, `root`, bypasses most of these checks, which is why attackers want it.

## Reading permission bits

```
$ ls -l /etc/shadow /usr/bin/passwd /tmp/notes.txt
-rw-r----- 1 root shadow 1450 Nov  2 09:14 /etc/shadow
-rwsr-xr-x 1 root root  59976 Nov  2 09:14 /usr/bin/passwd
-rw-rw-r-- 1 alice alice  120 Nov  3 18:02 /tmp/notes.txt
```

Each line starts with a type character, then three triples: owner, group, everyone else, each with read (`r`), write (`w`) and execute (`x`). So `/etc/shadow` is readable by root and members of group `shadow`, and by nobody else. Directories use the same bits differently: `x` means "may enter", `r` means "may list".

Numeric form: `r=4, w=2, x=1`, so `640` means owner read+write, group read, others nothing.

## SUID: running as someone else

Look at the `s` in `-rwsr-xr-x`. That is the **SUID bit** (set user ID): when anyone runs this program, the process takes on the *file owner's* identity, not the caller's. It exists because ordinary users must be able to change their own password, which means writing to a root-owned file, but only through a trusted program.

The risk: a SUID-root program is a bridge into root. If it has a bug, or can be tricked into running another program or opening a file you choose, you inherit root. Defenders and attackers both list them:

```
find / -perm -4000 -type f 2>/dev/null
```

The same idea appears for groups (SGID), and in a gentler form as **capabilities**: instead of all-powerful root, a binary receives one narrow privilege, for example `cap_net_bind_service` to bind low ports. `getcap -r / 2>/dev/null` lists them.

## Where mistakes hide

- A world-readable file with secrets (`-rw-r--r--` on a config holding a password).
- A world-writable script run by a root cron job: whoever can edit it runs code as root.
- A SUID binary that calls another program by relative name, so a malicious program placed earlier in `PATH` runs instead.
- Passwords left in shell history or hidden dotfiles (`ls -a` shows them).

None of these are exotic. Bandit, this week's lab, is built around exactly this kind of everyday mistake.

## A worked example: why `cat` fails, then works

Suppose you are logged in as `alice` and run:

```
$ cat /etc/shadow
cat: /etc/shadow: Permission denied
$ id
uid=1000(alice) gid=1000(alice) groups=1000(alice)
```

`id` shows the identity the kernel checks: UID 1000, with no `shadow` group. The file lists only root and group `shadow`, so alice falls into "others" and gets nothing. Nothing about the name `cat` matters. If a SUID-root program opened that file on alice's behalf and printed it, the same read would succeed, because the kernel would see UID 0 at that moment. That is the entire reason SUID programs are audited so closely: they are the places where the answer to "who is asking?" is deliberately changed.

## Your network, again

Last session's lesson was about reachability; today's is about what a process can do once it runs. Together: the network decides *who can talk to the machine*, permissions decide *what they can do once there*.

## Check yourself

1. A file is `-rwxr-x---` owned by `root:ops`. Can `alice`, who is not in `ops`, run it? Can a member of `ops` edit it?
2. Why is a SUID-root program that lets users edit any file they name a bigger problem than an ordinary root-owned file with loose permissions?

<details markdown="1">
<summary>Answers</summary>

1. No: "others" have no bits at all. A member of `ops` can read and run it but not edit it, because the group triple is `r-x`.
2. A loose file exposes one thing. The SUID program lends root's authority to whatever the caller asks, so one flaw can reach everything root can touch, including files you never listed.

</details>
