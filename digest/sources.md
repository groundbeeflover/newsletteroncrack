# Sources

The routine reads these feeds for the weekly news page, then uses web search to fill gaps. Feed URLs marked "verify" are best guesses; the routine checks them and corrects this file when it finds the right one.

## News

| Source | Feed | Why it's here |
|---|---|---|
| The Record | https://therecord.media/feed | Policy, nation-state activity, ransomware |
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
| CISA advisories | https://www.cisa.gov/cybersecurity-advisories/all.xml (403, see "Broken feeds") | Government advisories and joint reports |
| NVD | https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-YYYY-NNNNN | CVE details and scores |
| SANS Internet Storm Center | https://isc.sans.edu/rssfeed_full.xml | Daily handler diaries, hands-on analysis |

## Research and threat intelligence

| Source | Feed | Why it's here |
|---|---|---|
| Google Project Zero | https://projectzero.google/feed.xml | Vulnerability research (the old blogspot feed redirects here) |
| PortSwigger Research | https://portswigger.net/research/rss | Web security research |
| Cisco Talos | https://blog.talosintelligence.com/rss/ | Threat intelligence |
| Palo Alto Unit 42 | https://unit42.paloaltonetworks.com/feed/ | Threat intelligence |
| Microsoft Security blog | https://www.microsoft.com/en-us/security/blog/feed/ | Threat actor reports, Windows and identity |
| Securelist | https://securelist.com/feed/ | Malware and APT research |
| Schneier on Security | https://www.schneier.com/feed/atom/ | Commentary and policy |

## Market and industry

| Source | Feed | Why it's here |
|---|---|---|
| Return on Security | https://rss.hiivinternal.com/feeds/tLSvUYOBwf.xml | Security funding and market analysis |
| Strategy of Security | https://strategyofsecurity.com/rss/ | Market structure and company strategy |
| Crunchbase News | https://news.crunchbase.com/feed/ (filter for "cybersecurity") | Funding rounds |
| Risky Business | https://risky.biz/feeds/risky-business-news/ | News and commentary |
| tl;dr sec | https://rss.hiivinternal.com/feeds/xgTKUmMmUm.xml | Curated weekly technical newsletter |

## Blocked hosts

Hostnames the routine couldn't reach because of the environment's network policy. Add them to the environment's allowed domains if you want them.

- `projectzero.google`: the network policy refuses it (403 on connect), checked 2026-11-15. Google Project Zero's old blogspot feed now redirects here. The host isn't in `course/link-hosts.txt` either.
- `rss.hiivinternal.com`: the network policy refuses it, checked 2026-11-15. It serves the RSS feeds of Return on Security and tl;dr sec. (`rss.beehiiv.com` is refused too.)
- `www.cisa.gov`: partly. The site itself (its CDN, not the network policy) answers 403 "Access Denied" to the advisories feed and the KEV catalog web page; the KEV JSON feed loads fine. Checked 2026-11-15.
- `www.darkreading.com`: partly. The RSS feed loads, but article pages answer 403 with a bot challenge from the site, not the network policy. Checked 2026-11-15.

## Broken feeds

- ENISA (https://www.enisa.europa.eu/): the homepage advertises no RSS feed, and `/rss.xml` and `/news/rss` return 404 (checked 2026-11-15). Used for EU threat landscape and NIS2 guidance; search the site directly until a feed turns up.
- CISA advisories (https://www.cisa.gov/cybersecurity-advisories/all.xml): returns 403 from CISA's CDN (checked 2026-11-15); see "Blocked hosts". Search for CISA advisories through the news outlets instead.
