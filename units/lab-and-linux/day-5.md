---
title: "The lab: Bandit levels 0 to 15"
date: 2026-11-14
kind: lab
minutes: 120
---

Today's target is [OverTheWire Bandit](https://overthewire.org/wargames/bandit/), a platform built to be practised on. Read each level's page, and use the hints only after you have tried for a while.

## The steps

**Step 1. Connect and read (levels 0 to 3).** Log in over SSH with the details on the level 0 page, then find each next password in a file.

<details markdown="1">
<summary>Hint 1</summary>

Start with `ls -la` and `cat`. The level pages say where to look.

</details>

<details markdown="1">
<summary>Hint 2</summary>

Some filenames confuse the shell: ones that start with `-` or contain spaces. Think about how to tell a command "this is a path, not an option", and how quoting works.

</details>

<details markdown="1">
<summary>Hint 3</summary>

Prefix a path with `./` for dash names, and quote or escape names with spaces. Hidden files start with a dot, and `ls -a` shows them.

</details>

**Step 2. Find files by property (levels 4 to 6).** Identify the right file by type, size or owner instead of reading everything.

<details markdown="1">
<summary>Hint 1</summary>

`file` tells you what a file contains. `find` can filter by many properties.

</details>

<details markdown="1">
<summary>Hint 2</summary>

Check `man find` for `-size`, `-user`, `-group`, and `-type`. Redirect errors with `2>/dev/null` to quiet permission denials.

</details>

<details markdown="1">
<summary>Hint 3</summary>

Combine tests: for example type, owner, group and exact size in bytes in one `find` command, starting at the directory the level names.

</details>

**Step 3. Filter text (levels 7 to 9).** The password sits in a large file; work out how to isolate one line.

<details markdown="1">
<summary>Hint 1</summary>

`grep` finds lines; `sort` and `uniq` group them.

</details>

<details markdown="1">
<summary>Hint 2</summary>

If a line is unique, `sort | uniq -u` isolates it. For binary files, `strings` prints the readable parts.

</details>

<details markdown="1">
<summary>Hint 3</summary>

Pipe commands: `strings file | grep <pattern>`. Use `-u` with `uniq` only after `sort`, since it compares neighbouring lines.

</details>

**Step 4. Decode and unpack (levels 10 to 12).** Passwords arrive encoded or compressed repeatedly.

<details markdown="1">
<summary>Hint 1</summary>

`base64 -d` decodes base64. Character rotation can be done with `tr`.

</details>

<details markdown="1">
<summary>Hint 2</summary>

Work in a scratch directory under `/tmp` you create yourself (use `mktemp -d`). A hex dump can be turned back into bytes with `xxd -r`, and `file` tells you which compression format you have.

</details>

<details markdown="1">
<summary>Hint 3</summary>

Repeat: identify with `file`, decompress with the matching tool (`gzip -d`, `bzip2 -d`, `tar -x`), and rename the file with the right extension if the tool requires one.

</details>

**Step 5. Keys and network services (levels 13 to 15).** Use an SSH private key, then send a password to a local port.

<details markdown="1">
<summary>Hint 1</summary>

`ssh -i <keyfile>` logs in with a key. Keys need strict permissions or SSH refuses them.

</details>

<details markdown="1">
<summary>Hint 2</summary>

For talking to a port, `nc` (netcat) opens a plain TCP connection; for an encrypted one, `openssl s_client -connect host:port`.

</details>

<details markdown="1">
<summary>Hint 3</summary>

Connect to `localhost` on the port the level names, paste the previous password, and read what comes back. The level text says which of the two tools fits.

</details>

## Defender's view

For each level, write one line: **which file permission or setting let you read something you should not have, and how you would fix it.** For example, "password file readable by all users: change the mode to `600` and the owner to the intended user". By level 15 you should have a list of recurring mistakes. Group them: loose modes, secrets in files, hidden files, trust in obscurity.

## Stretch goal (optional)

Carry on past level 15 and do one more. Or write a one-line `find` that lists every SUID file on your own Kali VM, then explain why each one needs the bit.

## Finish up

Write your notes in `me/notes/lab-and-linux.md`, and log the lab (Sunday's page shows how).
