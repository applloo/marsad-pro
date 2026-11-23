# Marsad News — Source Catalog Audit & Paid-Article Radar

## Scope of this audit

This is a structural audit of the source registries in the project, followed by additions to the registry and a new discovery workflow. It is **not** a claim that every publisher's website, RSS feed, or Google News indexing was live-tested individually. Publisher coverage and access rules change frequently. French-language source search was enabled in the search connector as part of this release; the app already had French translation support.

## Existing coverage found in the project

Before this release, the project already had substantial coverage across:

- Israeli Hebrew/English press, broadcasters, business press, and security publications.
- US national media, political press, policy journals, defense reporting, think tanks, and congressional research.
- UK press, broadcasters, policy institutes, defense research, and Middle East-focused outlets.
- Turkey, Iran, and Ethiopia, including native-language sources where supported by the search engine. Phase 8.18 also expands Sudan, Somalia, Yemen, Iraq, Lebanon, Syria, Jordan, Gulf agencies, Eritrea, and Djibouti.
- Egyptian, Arabic, and regional press.
- An OSINT/intelligence registry covering military analysis, conflict data, official documents, humanitarian reporting, energy, and economic institutions.

## Additions in Phase 8.18

### Israel
- IDF public information, Israel Ministry of Defense, National Security Council, Israel Democracy Institute, and Israel Policy Forum.
- Official statements are labelled as the issuing party's account, not independent verification.

### United States
- Pentagon, State Department, White House, ODNI, CIA, DIA, NSA, NGA, and the public US Intelligence Community portal.
- USNI News, Jamestown, Hudson, Carnegie, New Lines, DefenseScoop, C4ISRNET, Air & Space Forces Magazine, Army Times, and Stars and Stripes.

### United Kingdom
- Ministry of Defence, FCDO, NCSC, SIS/MI6, MI5, GCHQ, Parliament Commons Library, UK Defence Journal, Forces News, and Jane's.

### International and regional
- Germany, France, EU policy reporting, China, Japan, South Korea, Russia/Eurasia, Southern and Eastern Africa.
- UN News, IAEA, IMO, OPCW, and OHCHR.
- Sudan: Sudan Tribune, Radio Dabanga, Radio Tamazuj, Sudan War Monitor, and Sudan Post.
- Somalia: Garowe Online, Hiiraan Online, Somali Guardian, and SONNA.
- Yemen: Yemen Monitor, Sana’a Center, and South24.
- Iraq: Rudaw, Shafaq News, Iraqi News, NINA, and Kurdistan24.
- Lebanon/Syria/Jordan: Naharnet, L’Orient Today, The Syrian Observer, Enab Baladi, SANA, The Jordan Times, and Ammon News.
- Gulf official agencies and press: QNA, ONA, KUNA, SPA, WAM, BNA, The Peninsula, and Gulf Times.

## Registry size after additions

Counts below are based on the current code registries, with domain aliases split and deduplicated:

| Registry | Entries | Unique domains |
|---|---:|---:|
| Israel | 31 | 31 |
| United States | 63 | 63 |
| United Kingdom | 28 | 30 |
| Regional / international | 107 | 106 |
| Arabic press | 19 | 19 |
| Egypt | 27 | 27 |
| **All main search groups** | — | **263 unique domains** |
| Intelligence office registry | **119 organizations/sources** | — |
| Paid / limited-access watchlist | **33 publishers/services** | — |
| Open-coverage discovery allowlist | — | **64 domains** |

Some publishers appear in more than one registry because they serve different search workflows. A source being listed does not mean all its articles are free, that it publishes an RSS feed, or that every search engine indexes it.

## New tab: Paid & Subscription Intelligence Radar

The new tab supports:

1. Monitoring public headlines from a configurable list of subscription, metered, registration-gated, or otherwise limited-access publishers.
2. A special public-index pass for Tactical Report's public Reports and Newsletters pages, in addition to Google News RSS discovery.
3. Arabic translation of every discovered headline while retaining the original headline, publisher, date when available, and source link.
4. A one-click search for the same headline or related coverage across an allowlist of open publishers, agencies, and research institutes using Google News RSS and GDELT.
5. A match label and approximate headline-token similarity score. This is a discovery hint, not proof that two articles are identical or that one republishes the other.
6. Direct reading and Arabic translation of an alternative article only when its text is publicly served from an allowlisted open domain. The original text is retained alongside the Arabic translation.
7. A manual headline search for a title copied from a newsletter, email, or subscription portal.
8. Direct publisher links and search links for reprints, syndication, public summaries, newsletters, and legal subscription routes.

### Tactical Report

The radar checks the public reports index and newsletters page for visible headlines. It does not open locked report bodies. The public product information and newsletters can be consulted here:

- https://www.tacticalreport.com/reports
- https://www.tacticalreport.com/newsletters
- https://www.tacticalreport.com/products

Public newsletter headlines and short public descriptions can be useful leads, but they are not substitutes for the full subscriber report.

## Paywall and copyright boundary

- The radar does not bypass subscriptions, login walls, or metered access.
- It does not request the paid publisher's full article body through third-party proxy or archival services.
- The existing generic article fallback now refuses proxy/archive fallback for known paywalled domains.
- It searches for independent reporting, syndicated copies made available by an authorized publisher, public summaries, newsletters, official releases, and research from open sources.
- An alternative headline may describe the same event without being the same article. The UI explicitly labels it as a likely related coverage unless the headline similarity is strong.
- A site can change its access policy at any time. A candidate labelled as an open source is still checked for direct access at read time.

## Known limitations

- Google News indexing is incomplete and varies by country, language, publisher, and query. An empty result is not evidence that no coverage exists.
- Tactical Report public-index parsing depends on its public page markup; Google News RSS is a second discovery path.
- Some reports show no publication date in the public index. In that case the UI leaves the date unavailable rather than guessing.
- Full Arabic article text is available only when an alternative publisher serves the article text directly and publicly. Paywalled originals remain title/metadata/link only.
- The source catalog has not been live-probed end-to-end against all 226 domains.
- No Streamlit browser session, real publisher feed scan, live deployment, or GitHub push was performed in this build.

## Phase 8.19 operational health coverage
The runtime health-check catalog merges the press-source registries (`ISRAEL`, `USA`, `UK`, `REGION`, `ARABIC`, `EGYPT`), the intelligence-office registry, and the paid/limited-access watchlist. At Phase 8.19 this yields 299 unique domains. A domain may have a source name and perspective tag for comparison, but source membership is not a claim of editorial independence or reliability. Health status is a point-in-time HTTPS/RSS probe; blocked, timed-out, or unreachable sources are not automatically considered permanently offline.
