---
title: "Lab prep: build the lab and meet Bandit"
date: 2026-11-12
kind: lab
minutes: 30
---

## What the lab practises

This week's lab has two halves. First, **build an isolated lab network** so you can safely practise later in the course. Second, work through **OverTheWire Bandit**, a game for learning the Linux shell and permissions. Each level hides a password for the next level somewhere on the system. Bandit is a practice platform built to be attacked, and that is the only thing it is for.

Why both? Bandit makes the shell feel natural. The lab network gives you a safe place for everything from week 3 onward.

## Setup checklist

Everything below comes from the lab's setup notes. Set aside about 30 minutes today and finish the rest on Saturday.

- [ ] Install a hypervisor, for example [VirtualBox](https://www.virtualbox.org/).
- [ ] Create an attacker VM, for example [Kali Linux](https://www.kali.org/get-kali/).
- [ ] Import the deliberately vulnerable target, Metasploitable 2. Read the [Rapid7 documentation](https://docs.rapid7.com/metasploit/metasploitable-2/) first, especially the network warnings.
- [ ] Put the target on a **host-only network** with no route to the internet or your home network.
- [ ] Check isolation: from inside the target, confirm you cannot reach anything outside, and that your home devices cannot reach it.
- [ ] Open the [Bandit page](https://overthewire.org/wargames/bandit/) and read the level 0 instructions.

## Safety reminder

The only targets this week are the Bandit servers, which exist for this purpose, and your own isolated VMs. Do not point anything you learn at systems you do not own or have permission to test. Never give the vulnerable VM a bridged adapter.

## Predict before you start

Write your answer down first: *What do you expect Bandit's early levels to ask you to find, and which `ls`, `cat` and `find` options do you think you will need?* After Saturday, compare.

## Notes template

Copy this into `me/notes/lab-and-linux.md`:

```markdown
# Lab and Linux: notes

## What I did

## What worked

## What failed

## What a defender would see

## One open question
```
