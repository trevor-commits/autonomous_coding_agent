# Codex App Marketplace Evaluations

This document records the 2026-04-17 marketplace-app sweep from the Codex app
screenshots and the repo-local judgment for each app's likely value.

These are operator-fit judgments for Trevor's current Codex-heavy software
workflow, not universal product rankings. The question here is "would this add
real leverage to this repo and surrounding operator flow?" rather than "is this
company good?"

Already-enabled core apps such as `GitHub`, `Linear`, `Gmail`,
`Google Calendar`, `Figma`, `Vercel`, `Hugging Face`, `Superpowers`,
`Cloudflare`, `Build Web Apps`, `CodeRabbit`, and `plugin-eval` are treated as
the current baseline and are only mentioned below when they create a
redundancy call for another app.

## Recommendation key

- `Add now` — likely immediate leverage if Trevor wants to widen the app
  surface soon.
- `Strong conditional` — valuable when the matching workflow becomes real.
- `Conditional` — useful in a narrower operating mode; otherwise noise.
- `Redundant` — overlaps a tool or stack already chosen.
- `Skip` — low expected value for this repo and current workflow.
- `Choose one` — useful category, but multiple apps in the same lane would
  create tool sprawl.

## Quick take

- Highest-leverage general adds: `Slack`, `Notion`, `Google Drive`, `Sentry`,
  `Jam`, `Stripe`, `Amplitude`, `Neon Postgres`, `Help Scout`, `Readwise`.
- Strong research add if Trevor wants evidence-sensitive literature support:
  `Scite`.
- Strong lightweight CRM add if relationship tracking becomes messy: `Attio`.
- Strong "only if needed" infra add: `Render` or `Netlify`, but not as casual
  extras if `Vercel` and `Cloudflare` already cover the real deployment paths.
- Biggest redundancy traps: Microsoft collaboration apps while already using
  Google; `Atlassian Rovo`, `ClickUp`, `Monday.com`, and `Teamwork.com` while
  already using `Linear`; multiple meeting-summary tools at once; multiple CRMs
  at once; multiple finance-research products without an actual investing or
  corp-dev workflow.

## Choose-one warnings

- Meeting memory / transcript lane: `Granola`, `Fireflies`, `Otter.ai`,
  `Read AI`, `Circleback`, `Fyxer`.
- CRM lane: `Attio`, `HubSpot`, `Pipedrive`, `Streak`, `HighLevel`,
  `Carta CRM`.
- Project-management lane: `Linear` is already chosen, so `Atlassian Rovo`,
  `ClickUp`, `Monday.com`, and `Teamwork.com` should only be added if the real
  work moves there.
- Deploy lane: `Vercel` and `Cloudflare` are already enabled, so `Render`,
  `Netlify`, and `Hostinger` should be added only for a specific hosting gap.
- Finance / market-intelligence lane: `PitchBook`, `CB Insights`, `Factiva`,
  `Morningstar`, `Moody's`, `Quartr`, `Daloopa`, `MT Newswires`, and
  `Third Bridge` are powerful only if market/investment research is actually a
  standing job.

## Collaboration, Docs, And General Workspace

| App | Recommendation | Thoughts |
|---|---|---|
| `Slack` | Add now | Highest-value collaboration add if real decisions, bug reports, or handoffs happen there. |
| `Notion` | Add now | Strong if specs, research, or roadmaps live there and need to be referenced without copy-paste. |
| `Statsig` | Strong conditional | Worth it for feature flags, experiments, and product metrics; otherwise it is extra surface area. |
| `Google Drive` | Add now | High leverage if Docs, Sheets, or Slides are part of the real workflow. |
| `Teams` | Redundant | Only makes sense if the real org communication surface is Microsoft, not Google plus Slack. |
| `SharePoint` | Redundant | Useful only when the source-of-truth file estate already lives there. |
| `Outlook Email` | Redundant | Not worth adding if Gmail is the actual email system. |
| `Outlook Calendar` | Redundant | Same story as Outlook Email; adds value only in a Microsoft-native environment. |

## Coding, Infra, And Shipping

| App | Recommendation | Thoughts |
|---|---|---|
| `Netlify` | Conditional | Good only if Trevor actually deploys there; otherwise redundant with `Vercel` and `Cloudflare`. |
| `Game Studio` | Conditional | Useful only if browser-game prototyping becomes a real workstream. |
| `CircleCI` | Redundant | Only worth adding if Trevor wants CircleCI specifically instead of current CI/GitHub workflows. |
| `Sentry` | Add now | One of the clearest adds. Error monitoring plus tracing is real leverage once software is shipped. |
| `Build iOS Apps` | Conditional | Useful only when native iOS work exists. |
| `Build macOS Apps` | Conditional | Useful only when a macOS app becomes an actual target. |
| `Test Android Apps` | Conditional | Only relevant if Android app work exists. |
| `Expo` | Conditional | Strong only for React Native / Expo mobile work. |
| `Neon Postgres` | Add now | Strong fit if Trevor wants hosted Postgres with branching and easier preview/dev workflows. |
| `Cloudinary` | Strong conditional | Worth it when image/video upload, transformation, and delivery are real product concerns. |
| `Hostinger` | Skip | Low leverage unless hosting already lives there. |
| `MarcoPolo` | Conditional | Only if a secure workspace / isolated data-room style workflow becomes necessary. |
| `Quicknode` | Skip | Specific to web3 / blockchain infrastructure. |
| `SendGrid` | Conditional | Useful if email sending becomes a real system concern and Trevor chooses SendGrid as the provider. |
| `Vantage` | Conditional | Only useful if cloud-cost visibility becomes enough of a problem to justify a dedicated tool. |
| `YepCode` | Conditional | Potentially useful for lightweight automations, but not obviously higher leverage than the current stack. |
| `Render` | Strong conditional | Good backend/deploy surface if Trevor wants long-lived services or preview environments outside the current hosting stack. |

## Design, Media, And Consumer / Lifestyle

| App | Recommendation | Thoughts |
|---|---|---|
| `Canva` | Conditional | Handy for launch assets, docs visuals, decks, and quick brand-safe collateral. |
| `Remotion` | Strong conditional | Genuinely strong if code-generated video, product demos, or tutorial clips become part of the workflow. |
| `BioRender` | Skip | Excellent for life-science figures; low value outside that domain. |
| `Cogedim` | Skip | Unrelated to this repo and Trevor's current software workflow. |
| `FINN` | Skip | Consumer car-subscription surface, not a workflow tool for this repo. |
| `MyRegistry.com` | Skip | Consumer registry tool; not relevant here. |
| `Setu Bharat Connect BillPay` | Skip | Region- and payment-rail-specific utility, not a fit for current work. |
| `WeatherPromise` | Skip | Consumer/travel-style protection surface rather than repo/workflow leverage. |
| `United Rentals` | Skip | Jobsite equipment rental is unrelated to this repo's software workflow. |

## Product, Support, CRM, Analytics, And Search

| App | Recommendation | Thoughts |
|---|---|---|
| `Atlassian Rovo` | Redundant | Useful if Trevor moves into Jira/Confluence; otherwise it overlaps the already-chosen `Linear` path. |
| `Jam` | Add now | Very strong add for frontend QA and bug reports because it carries replay, console, network, and environment context. |
| `Stripe` | Add now | Near-top priority if monetization, billing, or subscriptions are current or imminent. |
| `Box` | Conditional | Useful only if files already live in Box. |
| `Amplitude` | Add now | Strong if product analytics, funnels, activation, retention, or experiments matter. |
| `Attio` | Strong conditional | Best lightweight CRM candidate on this list if relationship tracking becomes messy. |
| `Brand24` | Conditional | Useful only if brand/social monitoring becomes an actual growth or support channel. |
| `Brex` | Conditional | Only if Trevor wants finance-ops workflows connected to Brex. |
| `Carta CRM` | Skip | Narrower investor-relations / venture-specific CRM, not a general need here. |
| `Channel99` | Conditional | Only if B2B go-to-market measurement becomes serious. |
| `Circleback` | Choose one | Viable meeting-summary/action-item tool, but should not coexist with several near-duplicates. |
| `ClickUp` | Redundant | Only add if Trevor actually wants to leave `Linear`; otherwise it is extra project-management noise. |
| `Common Room` | Conditional | Good for community-led growth or signal aggregation, but not a general-purpose must-have. |
| `Conductor` | Conditional | Primarily useful for mature SEO operations. |
| `Coupler.io` | Conditional | Useful if lots of spreadsheet/data-source syncing becomes operationally painful. |
| `Coveo` | Conditional | Enterprise search platform; only worth it for a much larger content/search estate. |
| `Demandbase` | Conditional | Strong only in a serious B2B ABM motion. |
| `Docket` | Conditional | Sales-meeting / prep surface; useful only in a real sales workflow. |
| `Domotz (Preview)` | Skip | Network-operations niche. |
| `Dovetail` | Strong conditional | Good if customer interviews, user research, and feedback synthesis become a real discipline. |
| `Egnyte` | Conditional | Useful only if the file estate already lives there. |
| `Fireflies` | Choose one | Good team transcript/search surface, but should compete with the other meeting tools rather than join them. |
| `Fyxer` | Choose one | More assistant-style inbox/meeting support; only worth it if that exact lane matters. |
| `Granola` | Choose one | Strong personal meeting-memory candidate if Trevor wants polished note enhancement. |
| `Happenstance` | Conditional | Potentially useful for relationship discovery/networking, but not a current priority. |
| `Help Scout` | Add now | Strong support add once real customer volume exists; cleaner support value than most tools on this page. |
| `HighLevel` | Conditional | Makes sense for agency-style marketing ops, not for every software workflow. |
| `HubSpot` | Strong conditional | Powerful all-in-one CRM/marketing stack, but heavy compared with `Attio`. |
| `KeyBid Puls` | Skip | Niche short-term-rental / profitability surface, not relevant here. |
| `Mem` | Strong conditional | Interesting if Trevor wants an AI-searchable second-brain layer, but should be a deliberate choice. |
| `Monday.com` | Redundant | Only worth it if the team actually moves there. |
| `MotherDuck` | Conditional | Strong if DuckDB/cloud analytics becomes part of the real data workflow. |
| `Network Solutions` | Skip | Only useful if domains or hosting are already managed there. |
| `Omni Analytics` | Conditional | Useful for governed analytics and dashboards, but only if analytics maturity justifies it. |
| `Otter.ai` | Choose one | Mainstream meeting transcript tool; should not be installed alongside several similar tools. |
| `Pipedrive` | Conditional | Viable sales CRM, but only if Trevor wants a simpler sales-specific CRM lane. |
| `Pylon` | Conditional | Support-specific; only useful if the support workflow matches it better than `Help Scout`. |
| `Ranked AI` | Skip | Too niche / unclear for current repo needs. |
| `Razorpay` | Conditional | Only useful if India-specific payment rails are relevant. |
| `Read AI` | Choose one | Another meeting-intelligence candidate; useful only if it becomes the chosen transcript lane. |
| `Responsive` | Conditional | RFP / questionnaire automation niche. |
| `Semrush` | Strong conditional | Worth it if SEO becomes a serious acquisition channel. |
| `SignNow` | Conditional | Useful if e-signature friction becomes real operational pain. |
| `SkyWatch` | Skip | Satellite-imagery-specific niche. |
| `Streak` | Conditional | Good only if Trevor explicitly wants a Gmail-native CRM instead of a broader CRM tool. |
| `Teamwork.com` | Redundant | Better fit for agency/client-delivery shops than for a `Linear`-centric product workflow. |
| `Waldo` | Skip | Too niche / unclear from current workflow needs to justify adding now. |
| `Windsor.ai` | Conditional | Useful only if paid-marketing attribution and connector sprawl become real problems. |

## Research, Finance, And Market Intelligence

| App | Recommendation | Thoughts |
|---|---|---|
| `Life Science Research` | Skip | Valuable only for life-sciences research work. |
| `Alpaca` | Conditional | Good only if Trevor builds or researches trading/fintech workflows. |
| `Binance` | Skip | Crypto/trading-specific. |
| `CB Insights` | Conditional | Strong market/private-company research tool if strategy or investing becomes real work. |
| `Cube` | Conditional | Useful if Trevor needs a semantic layer or governed analytics platform. |
| `Daloopa` | Skip | Finance-data niche. |
| `Dow Jones Factiva` | Conditional | Powerful for enterprise news and due diligence, but not a default add. |
| `GovTribe` | Conditional | Useful only for government-contracting research. |
| `Moody's` | Skip | Credit/risk intelligence is not a current repo need. |
| `Morningstar` | Skip | Investment/fund research niche. |
| `MT Newswires` | Skip | Real-time market-news niche. |
| `Particl Market Research` | Conditional | Useful if ecommerce/retail market intelligence becomes part of the workflow. |
| `PitchBook` | Conditional | Strong only for venture/private-market research, corp-dev, or investing. |
| `PolicyNote` | Skip | Policy/regulatory research niche. |
| `Quartr` | Conditional | Good if public-company transcripts and IR material become recurring source inputs. |
| `Readwise` | Add now | Best broad-use research add on this page if Trevor saves and revisits lots of reading. |
| `Scite` | Strong conditional | Great when literature review and evidence quality matter; overkill otherwise. |
| `Taxdown` | Skip | Tax workflow niche and region-specific. |
| `Third Bridge` | Skip | Institutional research niche. |
| `Tinman AI` | Skip | Mortgage / loan-officer niche. |

## Lowest-value adds for this repo

If Trevor wants the shortest "do not bother unless something changes" list,
these are the easiest skips right now:

- `Cogedim`
- `FINN`
- `MyRegistry.com`
- `Setu Bharat Connect BillPay`
- `WeatherPromise`
- `United Rentals`
- `Quicknode`
- `Domotz (Preview)`
- `KeyBid Puls`
- `Network Solutions`
- `SkyWatch`
- `Binance`
- `Moody's`
- `Morningstar`
- `MT Newswires`
- `Third Bridge`
- `Taxdown`
- `Tinman AI`

## Future update rule

If a later chat actually enables, trials, or rejects one of these apps in a
real workflow, update this file directly and then record any consequential
follow-up in `todo.md` rather than leaving the reasoning stranded in chat.
