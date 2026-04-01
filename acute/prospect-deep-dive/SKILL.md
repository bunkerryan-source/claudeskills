---
name: prospect-deep-dive
description: >
  Conduct a comprehensive intelligence-driven deep dive on a prospective customer for Priority1 Logistics,
  a freight brokerage offering LTL and full truckload services. Use this skill whenever the user mentions
  a prospect deep dive, prospect analysis, customer research for Priority1, sales intelligence brief,
  freight prospect research, or wants to analyze a potential customer's logistics needs, supply chain,
  freight profile, or shipping patterns to identify how Priority1 can win their business. Also trigger
  when the user names a company and asks for a deep dive, prospect brief, customer analysis, or sales
  strategy related to freight or logistics services. Even if the user just says something like "do a
  deep dive on [Company]" or "research [Company] as a prospect" — use this skill.
---

# Prospect Deep-Dive Skill

This skill produces two deliverables for a named prospective customer of Priority1 Logistics:

1. **In-Depth Customer Analysis (.docx)** — A comprehensive internal report covering the prospect's business, freight profile, supply chain, logistics challenges, competitive landscape, and a tailored sales strategy for Priority1 to win their freight business. Includes a one-page internal deal brief at the end.
2. **Structured Presentation Outline (.md)** — A 15–20 slide outline for a customer-facing pitch presentation, saved as markdown for subsequent conversion to .pptx.

---

## Step 1: Identify the Prospect

The user will name a company in their message (e.g., "Do a prospect deep dive on Acme Corp"). Extract the company name — this is your `[Company Name]` for everything that follows. If the user hasn't named a specific company, ask them which company they'd like you to research.

## Step 2: Read the Priority1 Reference Material

Before doing any research or writing, read the Priority1 business reference file:

```
claude-cowork/skills/freight/prospect-deep-dive/reference/Priority1_Logistics and Freight Solutions Company.md
```

This file contains a detailed profile of Priority1's business — its services, unique value proposition, technology (Cabo TMS), independent agent model, competitive landscape, target market, and sales approach. Understanding Priority1 deeply is essential because every section of the analysis must connect the prospect's needs back to specific Priority1 capabilities and differentiators.

Pay particular attention to:
- Priority1's core services: LTL, full truckload (dry van, flatbed, temperature-controlled, drayage), expedited, and freight management
- The Cabo TMS platform and its capabilities
- The independent agent model and what it means for customer service
- Priority1's sweet spot: small and mid-sized businesses
- Key differentiators vs. competitors (WWEX, TQL, C.H. Robinson, Echo, Coyote)
- Priority1's group purchasing power and 47,000+ carrier network

## Step 3: Read the Prospect Deep-Dive Prompt

Before beginning any research, read the full prompt file:

```
claude-cowork/skills/freight/prospect-deep-dive/reference/Priority 1 - Prospect Deep-Dive Prompt.md
```

This file is the authoritative guide for what the analysis must cover. It specifies every category of research and analysis required — from the full prospect intelligence brief and freight profile translation, to supply chain mapping, industry challenges, recent news, competitive landscape, sales strategy, and executive summary. It also defines the two required output deliverables and their formats. Your research in the next step and the final deliverables must address every topic and requirement listed in this prompt. Do not rely solely on the general guidance in this SKILL.md — the prompt file contains the complete, detailed specification.

## Step 4: Research the Prospect

Conduct thorough research on `[Company Name]`. If web search tools are available, use them to find current information. Search for:
- Company overview, products, and services
- Recent news, press releases, acquisitions, expansions, leadership changes
- Supply chain and logistics-related developments
- Financial performance or growth indicators
- Sustainability initiatives (if relevant to the company)
- Industry trends affecting their logistics needs

If web search is not available, use your training knowledge and be transparent about the recency of your information.

## Step 5: Read the DOCX Skill

Before creating the .docx report, read the docx skill to ensure professional formatting:

```
Read the SKILL.md file located at the skills directory for docx
```

Follow the docx skill's guidance for formatting, fonts, and document structure. The report should be clean, modern, and organized with headings. Minimal or no use of color. Consider use of Inter font for a clean, modern look.

## Step 6: Create the In-Depth Customer Analysis (.docx)

Create a comprehensive internal customer analysis report. Name the file using the prospect's company name and the current date in YYYYMMDD format (e.g., `Acme_Corp_Prospect_Deep_Dive_20260320.docx`). Save it to `claude-cowork/output/`. Create the `output` directory if it does not already exist.

### Report Sections

The report must cover all of the following sections. Each section should be substantive — not just surface-level observations, but analysis that connects the prospect's situation to specific Priority1 capabilities and selling opportunities.

#### 1. Full Prospect Intelligence Brief
A comprehensive overview of `[Company Name]` as a prospective customer for Priority1. Include:
- Overview of products and services
- Industries and end markets served
- Geographic footprint (headquarters, facilities, distribution points)
- Freight profile (what they ship, how much, how often)
- Supply chain structure
- Logistics challenges and pain points
- Recent news and developments
- Competitive pressures they face
- Priority1 value opportunities
- Tailored sales angles

#### 2. Products / Freight Profile Translation
Analyze the prospect's products and translate them into a likely freight and shipping profile:
- Product characteristics that affect shipping (weight, dimensions, fragility, temperature sensitivity, hazmat, etc.)
- Likely LTL vs. FTL mix
- Palletization and density risk
- NMFC/class sensitivity
- Accessorial exposure (liftgate, inside delivery, residential, limited access, etc.)
- Where Priority1 can add specific value

#### 3. Supply Chain & Network Mapping
Map the prospect's supply chain:
- Upstream suppliers and raw material sourcing
- Manufacturing and production locations
- Warehousing and distribution strategy
- Downstream customers and delivery requirements
- Domestic vs. international exposure
- Points of transportation risk where Priority1 can reduce cost or complexity
- Sustainability considerations (if important to the prospect)

#### 4. Industry-Specific Logistics Challenges
Based on the prospect's industry, identify common logistics and transportation challenges:
- Capacity volatility and seasonal demand patterns
- Rate pressure and cost management
- Service failures and on-time delivery challenges
- Accessorial exposure and billing complexity
- Claims risk and cargo damage concerns
- Visibility and tracking issues
- Explain specifically how Priority1's LTL and FTL services, technology (Cabo TMS), and carrier network address each challenge

#### 5. Recent News & Trigger Events Analysis
Review recent news and press coverage for the prospect. Identify:
- Acquisitions or mergers
- Facility expansions or relocations
- New product launches or market entries
- Leadership changes
- Growth initiatives or strategic shifts
- Any development that may increase shipping complexity and create opportunities for Priority1

#### 6. Competitive Landscape & Broker Opportunity
Analyze the prospect's likely logistics provider landscape:
- Likely current providers (asset carriers, brokers, 3PLs)
- Assessment of asset vs. broker usage
- Common incumbent shortcomings the prospect may be experiencing
- Where Priority1's service model can outperform
- Positioning statements for sales conversations

#### 7. Sales Strategy & Messaging Framework
Create an actionable sales strategy:
- Likely pain points to lead with
- Discovery questions for initial conversations
- Priority1 value propositions tailored to this prospect
- Proof points and case study angles
- Objection handling guidance (price, size, incumbent loyalty, etc.)
- Recommended outreach sequence

#### 8. Executive-Level Logistics Summary
A concise executive summary covering:
- Strategic shipping risks facing the prospect
- Key cost drivers in their transportation spend
- How logistics impacts their growth trajectory
- Why Priority1 should be viewed as a strategic logistics partner (not just another broker)

#### 9. One-Page Internal Deal Brief
At the end of the report, include a separate one-page internal deal brief for `[Company Name]`. This should be a quick-reference page that a Priority1 sales rep can use at a glance. Include:
- **Company Snapshot**: Industry, size, headquarters, key facts
- **Freight Profile**: Estimated volume, modes, key lanes
- **Risks & Opportunities**: Top 3 of each
- **Recommended Service Focus**: Which Priority1 services to lead with
- **Primary Sales Angle**: The single most compelling reason this prospect should choose Priority1
- **Next Steps**: Recommended actions to advance the opportunity

## Step 7: Create the Structured Presentation Outline (.md)

After completing the .docx report, create a structured markdown outline for a 15–20 slide customer-facing pitch presentation. Name the file using the prospect's company name and the current date in YYYYMMDD format (e.g., `Acme_Corp_Presentation_Outline_20260320.md`). Save it to `claude-cowork/output/` (the same directory as the .docx report).

This outline will be used to subsequently create a .pptx presentation, so it should be clearly structured with slide numbers, titles, and bullet points for each slide's content.

### Expected Slide Structure

The outline should include slides covering:

1. **Title Slide** — Priority1 + prospect company name, meeting context
2. **Agenda / Overview** — What will be covered
3. **Understanding Your Business** (2–3 slides) — Demonstrate that Priority1 has done its homework on the prospect's products, markets, and operations
4. **Understanding Your Supply Chain** (2–3 slides) — Show knowledge of the prospect's supply chain, distribution network, and logistics complexity
5. **Industry Logistics Challenges** (2–3 slides) — Identify the specific freight and logistics challenges facing the prospect's industry, connecting them to real pain points
6. **Introducing Priority1** (2–3 slides) — Priority1's business overview, scale, technology (Cabo TMS), carrier network, and service capabilities
7. **How Priority1 Addresses Your Challenges** (2–3 slides) — Direct mapping of Priority1 capabilities to the prospect's specific challenges and needs
8. **Our Value Proposition for [Company Name]** (1–2 slides) — Tailored value props specific to this prospect
9. **Proposed Engagement Timeline** (1–2 slides) — A realistic timeline and process for how Priority1 can demonstrate its value, including:
   - Request to evaluate some or all of the prospect's freight lanes
   - Priority1's process for analyzing those lanes
   - A proposal on how Priority1 would address those lanes and customer needs
   - Pilot program or trial period structure
   - Success metrics and review cadence
10. **Next Steps & Call to Action** (1 slide) — Clear next steps to advance the relationship
11. **Thank You / Contact** (1 slide)

Each slide in the outline should include:
- Slide number and title
- 3–6 bullet points of content
- Speaker notes or talking points where helpful

---

## Output Checklist

Before finishing, verify:
- [ ] Priority1 reference material was read and understood
- [ ] Web research was conducted on the prospect (if tools available)
- [ ] The .docx report covers all 9 sections with substantive analysis
- [ ] The one-page deal brief is included at the end of the report
- [ ] The .docx formatting is clean, modern, and professional
- [ ] The .md presentation outline covers 15–20 slides
- [ ] The presentation outline includes a proposed engagement timeline with lane evaluation request
- [ ] Both files are named with the prospect's company name and date (YYYYMMDD)
- [ ] Both files are saved to `claude-cowork/output/`
