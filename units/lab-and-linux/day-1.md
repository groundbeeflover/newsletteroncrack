---
title: "A hypothetical: the practice box that wasn't isolated"
date: 2026-11-09
kind: lesson
minutes: 20
---

## Before you read

Answer in one sentence each, from your own intuition: if you run a deliberately vulnerable virtual machine on your laptop, what could go wrong *for you*? Who could reach that machine, and what could it reach?

## A scenario (hypothetical, not a real event)

This course has no verified real incident to anchor this week yet, so today uses an invented story. Nothing below happened to anyone. It is built from a very common mistake.

Dana, a master's student, wants to practise security. She installs a hypervisor (software that runs virtual machines), imports a deliberately vulnerable Linux VM, and starts it. To make downloads easy she gives the VM a *bridged* network adapter, which puts it on her home Wi-Fi as if it were a separate laptop.

What happens next, step by step:

1. The vulnerable VM gets an IP address from her router, like every other device at home.
2. The VM runs old services with default passwords. That is its purpose: it is meant to be attacked.
3. Her router forwards a port for a game server she set up last year. The forwarding rule points at "the device with this address". After a reboot the VM receives that address.
4. The vulnerable service is now reachable from the internet. Automated scanners, which constantly try every public address, find it within hours.
5. A scanner logs in with a default password. Because the VM shares the home network, it can also talk to her family's printer, NAS and phones.

Dana never did anything "wrong" in the sense of attacking someone. She simply gave a machine built to be compromised a path to the real world.

## Why it worked

Three ordinary facts combined:

- **Default trust on a flat network.** Devices on one home network can usually reach each other freely.
- **Automation.** Attackers do not pick targets by hand. They scan everything, so being obscure is not protection.
- **A deliberately weak machine** has no defences to fall back on.

The vocabulary for this: the VM's reachable surface is its **attack surface** (everything an attacker can interact with), and the home network lacked a **trust boundary** (a line where you decide what may cross). You will meet both again in the threat-modeling unit.

## What a good setup looks like instead

Compare with a safer version of the same evening. Dana creates a host-only network in the hypervisor, attaches only the vulnerable VM and her attacker VM to it, and leaves the VM's internet access off. When she needs a package, she downloads it on her normal machine and copies it in. It is slightly less convenient. In exchange, the worst thing a compromised practice box can do is attack another practice box.

A second habit helps: snapshots. A snapshot saves the VM's state, so after you break something, or something breaks you, you roll back in seconds. Snapshot before every experiment.

## What to notice

The fix is not a smarter VM. It is a **network design** decision: a *host-only* network (VMs can talk to your computer and each other, and to nothing else) means no route to the internet and no route to the rest of your home, whatever services run inside it.

## Carry into tomorrow

On Linux, a service runs as some user. If an attacker gets a foothold in a service, what decides whether they can read `/etc/shadow` (the file that stores password hashes) or become root?
