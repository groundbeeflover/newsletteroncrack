# Sources

The routine pulls these feeds first, then uses web search to fill gaps. Feed URLs marked "verify" are best guesses; the routine checks them and corrects this file when it finds the right one.

## News

| Source | Feed | Why it's here |
|---|---|---|
| The Record | https://therecord.media/feed/ | Policy, nation-state activity, ransomware |
| BleepingComputer | https://www.bleepingcomputer.com/feed/ | Fast on breaches, ransomware, and patches |
| Krebs on Security | https://krebsonsecurity.com/feed/ | Deep investigations, low volume |
| SecurityWeek | https://www.securityweek.com/feed/ | Broad coverage, regular funding and M&A roundups |
| Dark Reading | https://www.darkreading.com/rss.xml | Enterprise and industry angle |
| Ars Technica security | https://arstechnica.com/security/feed/ | Clear technical explainers |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews | High volume; confirm with a second source |

## Vulnerabilities and advisories

| Source | Feed | Why it's here |
|---|---|---|
| CISA KEV catalog | https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | Vulnerabilities confirmed exploited in the wild (use `dateAdded`) |
| CISA advisories | https://www.cisa.gov/cybersecurity-advisories/all.xml (verify) | Government advisories and joint reports |
| NVD | https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-YYYY-NNNNN | CVE details and scores |
| SANS Internet Storm Center | https://isc.sans.edu/rssfeed_full.xml | Daily handler diaries, hands-on analysis |

## Research and threat intelligence

| Source | Feed | Why it's here |
|---|---|---|
| Google Project Zero | https://googleprojectzero.blogspot.com/feeds/posts/default | Vulnerability research |
| PortSwigger Research | https://portswigger.net/research/rss (verify) | Web security research |
| Cisco Talos | https://blog.talosintelligence.com/rss/ (verify) | Threat intelligence |
| Palo Alto Unit 42 | https://unit42.paloaltonetworks.com/feed/ | Threat intelligence |
| Microsoft Security blog | https://www.microsoft.com/en-us/security/blog/feed/ | Threat actor reports, Windows and identity |
| Securelist | https://securelist.com/feed/ | Malware and APT research |
| Schneier on Security | https://www.schneier.com/feed/atom/ | Commentary and policy |

## Market and industry

| Source | Feed | Why it's here |
|---|---|---|
| Return on Security | https://www.returnonsecurity.com/ (find feed) | Security funding and market analysis |
| Strategy of Security | https://strategyofsecurity.com/ (find feed) | Market structure and company strategy |
| Crunchbase News | https://news.crunchbase.com/ (search "cybersecurity") | Funding rounds |
| Risky Business | https://risky.biz/ (find feed) | News and commentary |
| tl;dr sec | https://tldrsec.com/ (find feed) | Curated weekly technical newsletter |

## EU and policy

| Source | Feed | Why it's here |
|---|---|---|
| ENISA | https://www.enisa.europa.eu/ (find feed) | EU threat landscape, NIS2 guidance |

## Blocked hosts

Hostnames the routine couldn't reach because of the environment's network policy. Add them to the environment's allowed domains if you want them.

## Broken feeds
