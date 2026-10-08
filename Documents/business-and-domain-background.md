# Business and Domain Background

## 1. Purpose, Who This Is For, and Scope

**Purpose.** This document gives you the business and domain knowledge you need to understand why Layer 0 exists. It explains who Flex and SpinCo are, what they sell, how engineered products are quoted today, what CPQ (Configure, Price, Quote) software does and does not do, how a bid opportunity is handled, and how to read a real request for proposal (RFP). It assumes no electrical-engineering or Flex background. Each technical term is explained where it first appears.

**The starting point in one paragraph.** The spin-off does not start from nothing. SpinCo starts as an existing business with existing products, existing customers, existing engineers and existing business units. Each unit can already sell its own products to its own customers. For larger opportunities, such as an AI data-centre build, several units can combine their offerings into one bid. Layer 0 is intended to help manage that kind of incoming opportunity, from the moment an RFP arrives until the final bid response is assembled (the business direction described in the review meetings; see sections 7 to 9).

**Who this is for.** Developers newly joined to the Layer 0 proof of concept (PoC: a small build that tests whether an idea works; it is not a product). Layer 0 is the project and system name. For what the project is and how far it has got, read [project-overview.md](project-overview.md). For the problems it addresses, see [problem-mapping.md](problem-mapping.md). For how the code is built, see [architecture-overview.md](architecture-overview.md).

**Scope.** The customer's business and domain only. It does not describe the code, the build status or the roadmap. Electrical detail is limited to what is needed to read the worked example in section 10.

**How statements are labelled.**

- **Company and market facts** come from the written portfolio and market sources and are labelled where they are inferred or unverified.
- **Review-meeting statements** (the review meetings of 22 Sep, 5 Oct and 8 Oct 2026) are the working baseline for Layer 0's purpose and workflow. Statements from the 8 Oct 2026 meeting are marked "(8 Oct 2026)" where the date matters, and written client direction given before it is marked as such. They are not verified corporate facts, and the workflow has not been formally signed off. Where a meeting statement is used for a business fact, it is marked **Needs confirmation** or "from the review meetings; needs confirmation".
- A statement that is an argument made by a source, not a verified fact, is marked as such.
- Where sources disagree, the conflict is named and left open.
- Illustrative examples are labelled **illustrative**. They are not recorded SpinCo bids.

## 2. Flex and SpinCo (Axiom Solutions)

- **Flex** (Flextronics) is a large contract manufacturer and the ultimate customer of this PoC. Its **Cloud & Power Infrastructure (CPI)** segment (a reporting division) is being separated into its own company.
- **SpinCo** is the working name for that business. A spin-off is when a parent company makes one of its businesses an independent company with its own shares. SpinCo will list as **Axiom Solutions International**, ticker AXM, and is expected to be led by Revathi Advaithi, currently Flex's chief executive officer (CEO). This document uses "SpinCo (to become Axiom Solutions)" and then "SpinCo".
- **An existing business, not a blank start.** SpinCo begins with products that are already designed and sold, customers that already buy, engineers who already quote and build, and business units that already run. The spin-off changes the ownership and the need to work together. It does not create the products, customers or teams from scratch.
- **Individual and combined selling.** Each unit can sell individually: a single product to a single customer, such as switchgear to a utility. Units can also combine offerings for larger opportunities, such as a data-centre campus that needs power, cooling and compute. The review meetings described the units as previously able to bid for products themselves and now coming together for the first time (from the review meetings; needs confirmation).
- **Timing.** The spin-off is targeted to close in the first quarter of calendar 2027. Flex will keep a stake of at most 19.9%. The review meetings described SpinCo as already a separate company called Axiom Solutions, with a start date of "January 4" and no year given. Only the name and the 2027 target are used as facts. The exact start date is **Needs confirmation** and is not a verified corporate fact.
- **Zensar** is the company building the PoC for Flex. The Zensar team is taking it forward.
- **What SpinCo is not.** It is not a holding company of many consumer brands. It is organised around four product pillars, led day to day by two businesses, Embedded Power and Critical Power. The "companies" people mention are acquired brands that fill those pillars.
- **How sure the facts are.** The portfolio source separates facts taken directly from Flex's investor deck, press releases and filings from facts that are inferred. The business identity, pillars, finances and leadership are confirmed. The assignment of each brand to SpinCo is inferred until Flex files a **Form 10** (the registration statement with the US securities regulator, the SEC, that lists the legal entities moving to SpinCo). As of 10 Sep 2026 it was not filed.
- **How many companies, and what are the business units?** The earlier review meetings described SpinCo as a subset of "six companies" that previously could bid for products themselves. The written sources describe four pillars and seven named brands, one still pending. The review of 8 Oct 2026 settled the working picture: **six business units**, with EP² (Electrical Power Products) named as one. The working list is Anord Mardix, Crown Technical Systems, EP², Flex Power Modules, JetCool and Cloud (in-house); EPC Power stays pending acquisition and is not active. The exact list is **Needs confirmation**. Business units are data in the system, so the list can change without code changes. Each business unit has a **product manager** and a **design engineer**. One **bid manager**, who has a general idea of all the units, receives the RFP and owns the opportunity (8 Oct 2026). The six business units are not the six grid-to-chip layers (see section 3.6).

## 3. What SpinCo Sells

### 3.1 Positioning: "grid to chip"

Flex describes the portfolio as "grid to chip": everything from the electricity-grid connection down to the computer chip. The thesis is that, as the power drawn per server cabinet (rack) rises with AI workloads, power, cooling and computing must be designed together and delivered as one system. A quoted positioning statement: "A leader in critical digital infrastructure, delivering end-to-end power and thermal management technologies for AI data centers and mission-critical applications". The review meetings gave the same picture: power from the grid through medium voltage into the data centre, into the racks and from the power supply to the chip itself, plus liquid cooling because AI data centres cannot be cooled using air (from the review meetings; needs confirmation).

### 3.2 The four pillars

| Pillar | What it covers | Example products | Led by |
|---|---|---|---|
| Critical Power Products | Electrical equipment for the utility connection and the building | Medium- and low-voltage switchgear, power distribution units, busway, prefabricated modular pods, substation control buildings, relay panels, remote power panels | Todd Hoover, President, Critical Power |
| Embedded Power Products | Power inside the rack and on the circuit board | Chip-level power, power shelves, power modules, an "800VDC sidecar" | Mattias Jansson, President, Embedded Power |
| Thermal Management Products | Liquid cooling for high-density racks | Cold plates, coolant distribution units, direct-to-die cooling modules | Part of CPI |
| Cloud | Integrated compute systems | Compute trays, rack integration, servers, storage | Part of CPI |

One source calls these "pillars" and another calls them "segments". They are the same four groups. The name "Critical Power Products" is recommended for the first one.

Terms in the table, explained:

- **Switchgear**: cabinets of switches and circuit breakers that switch, protect and isolate electrical circuits. **Medium voltage (MV)** is roughly 1 to 35 kV (kilovolts; a kilovolt is a thousand volts) and needs much more engineering than **low voltage (LV)**, under about 1,000 V.
- **Busway**: enclosed metal bars that carry large currents across a room instead of cables.
- **PDU (power distribution unit)** and **RPP (remote power panel)**: units that hand out branch-level power to racks.
- **Prefabricated modular pod or skid**: a factory-built power module delivered ready to install, for fast, repeatable deployment.
- **Relay panel** and **utility control building**: a relay detects a fault and tells breakers to open; these hold the control and protection equipment of a substation, the site where voltage is changed and circuits are switched between the grid and the user.
- **Power shelf, power module, DC-DC converter**: units that convert electricity to the voltages servers and chips need; a DC-DC converter changes one direct current (DC) voltage to another.
- **800 VDC**: an 800-volt direct-current power design for AI racks. The "sidecar" is not explained in the sources, so it is **Needs confirmation**; it is presumably a power cabinet beside the rack.
- **Cold plate, direct-to-chip cooling, CDU (coolant distribution unit)**: a cold plate sits on the chip; direct-to-chip means liquid flows right to the processor; a CDU pumps and manages the coolant loop.
- **Compute tray**: the slide-in unit of a rack that holds processors and memory.
- MCMS (listed in one source as "modular circuit monitoring systems") is not explained by the sources. **Needs confirmation.**

**Lifecycle services** wrap around all four pillars: component sourcing, logistics and fulfilment, repair and refurbishment, and install, monitor and maintain services for uptime over the equipment's life.

### 3.3 The brands

Brand-to-SpinCo assignments are inferred until the Form 10 is filed, with one exception: written client direction (before the 8 Oct 2026 review) is that EP² is already part of SpinCo / Axiom Solutions. The Layer 0 design assumes this and includes solution components coming from EP²; the working code must include EP² products.

| Brand | Pillar | What it does |
|---|---|---|
| Anord Mardix | Critical Power | Switchgear, busway, power distribution, modular power, monitoring and services. Mostly configure-to-order |
| Crown Technical Systems | Critical Power | Control panels, medium-voltage switchgear (arc-resistant and standard), E-Houses |
| Electrical Power Products (EP²) | Critical Power | Substation control buildings, relay and protection panels, auxiliary power. Labelled "engineered-to-order" on Flex's website. Part of SpinCo by written client direction; the architecture includes EP² components |
| Flex Power Modules | Embedded Power | Board-level DC-DC converters, power modules, rack power shelves |
| JetCool | Thermal Management | Chip-level liquid cooling, cold plates, coolant distribution units |
| EPC Power | Critical or Embedded Power (sources give both) | 800 V DC and grid-forming power conversion, some designs first-of-kind. **Pending acquisition**: $4.4 billion, announced 3 Sep 2026, close expected in Q4 2026 |
| Cloud (built in-house) | Cloud | Compute-tray build and rack-scale integration; no separate brand name |

An **E-House** is a pre-built, transportable building that contains electrical equipment. **Arc-resistant** switchgear is built to contain an internal electrical explosion (an arc flash) and direct it away from people. **Grid-forming** power electronics can create and stabilise an electrical grid by themselves rather than only following the utility.

**Needs confirmation (new conflict).** One source describes the EPC Power acquisition as closed; another, which cites the dated filing, says it is pending. This document uses pending.

Brands that appear likely to stay with Flex are Coreworks (it might feed power products), Farm, Irumold, Sønderborg Værktøjsfabrik and MCi. The brand list, other than EP², is **Needs confirmation** until the Form 10 is filed.

### 3.4 The six-layer grid-to-chip stack

"Layer" in this document always means one of these six product families. "Layer 0" is not one of them: it is the name of the system that sits in front of all six. Another list of six layers (grid, high voltage, medium voltage, low voltage, distribution, load) appears in some earlier project documents; which list is intended is **Needs confirmation**.

| Layer | Covers | Brand(s) | Team that handles it |
|---|---|---|---|
| L1 Grid Interface | Grid-forming conversion, 800 V DC, on-site storage and microgrid support (a small local grid that can run separately from the utility) | EPC Power (pending) | Critical Power |
| L2 Utility / Facility Electrical | Medium- and low-voltage switchgear, substation control, protection, E-Houses | Crown, EP², Anord Mardix | Critical Power |
| L3 Power Distribution (room, row, rack) | Busway, PDUs, RPPs, modular power pods | Anord Mardix | Critical Power |
| L4 Rack and Board Power | Power shelves, rack power, DC-DC modules | Flex Power Modules, EPC Power | Embedded Power |
| L5 Thermal Management | Cold plates, direct-to-chip cooling, CDUs | JetCool | Thermal (JetCool) |
| L6 Compute and Integration | Compute trays, rack-scale integration | Cloud | Cloud |

In the project's knowledge base, the L2 brand choice follows a rule: arc-resistant requirements go to Crown, substation control and protection panels go to EP², utility-level 2N redundancy goes to EP² or Crown, and everything else goes to Anord Mardix. **Redundancy** means spare capacity so one failure does not cause an outage. **N+1** means one spare unit; **2N** means a complete second copy.

### 3.5 Single products and combinations

SpinCo sells both single-brand products and named multi-brand systems.

- **Confirmed** combination: Flex's AI Infrastructure Platform, launched with NVIDIA Omniverse DSX reference designs (a reference design is a published blueprint others can build from; press release of 16 Mar 2026). It joins an 800 VDC power rack, liquid-cooled IT racks, liquid cooling and critical power infrastructure into one factory-built system, so at least a three- to four-way combination of layers. The "1MW rack" (Flex Power Modules plus JetCool) is also named in Flex's own materials.
- **Single-unit sales continue.** A standalone product, such as medium-voltage switchgear for a utility, is sold by one unit without combining anything.
- **Current state**: matching an incoming RFP to the right brand or combination of brands is, as the source describes it, "a manual, engineer-driven process". No measurement is given.

### 3.6 Keeping the terms distinct: companies, units, pillars, layers and teams

Several different groupings are used when people talk about SpinCo. They overlap in places but they are different kinds of thing. None of them maps one-to-one to another, and this document never treats them as interchangeable.

| Term | What it is | Count in the sources | Status |
|---|---|---|---|
| Company or brand | An acquired company name, such as Anord Mardix, Crown, EP², Flex Power Modules, JetCool, EPC Power (pending) or Cloud | Seven named brands, one pending | Written count; Form 10 not filed |
| Business unit | An organisational unit of SpinCo that sells and delivers; each has a product manager and a design engineer | Six (8 Oct 2026): Anord Mardix, Crown Technical Systems, EP², Flex Power Modules, JetCool, Cloud (in-house). EP² is confirmed as one | The exact list is **Needs confirmation**, including how units map to pillars, layers and teams. EPC Power is pending and not active |
| Product pillar | A product grouping: Critical Power, Embedded Power, Thermal Management, Cloud | Four | Confirmed |
| Product layer | One of the six grid-to-chip product families, L1 to L6 | Six | Project knowledge-base list; an alternative list exists |
| Delivery or engineering team | The group that owns and answers requirements for a bid | The v0.3.0 knowledge base uses four: Critical Power, Embedded Power, Thermal (JetCool), Cloud | Project working assumption |

The six business units must not be equated with the six grid-to-chip layers. The two numbers match only by coincidence of count. One layer can involve several brands (L2 involves three), one brand can sit in more than one layer (EPC Power is listed in L1 and L4), and one team can cover several layers (Critical Power covers L1 to L3). The working list of business units follows the brand names, but the exact list is not confirmed, and no one-to-one mapping to pillars, layers or teams should be assumed.

## 4. Who Buys and How Big the Business Is

**Customer types** (confirmed): silicon providers (chip companies), hyperscalers, neoclouds, colocation providers and utilities.

- A **hyperscaler** is a very large cloud company that builds its own data centres.
- A **neocloud** is a newer cloud provider focused on renting AI computing power (GPUs: graphics processing units, the chips used for AI).
- A **colocation provider** owns data-centre buildings and rents space, power and cooling to others.
- A **utility** is an electricity company.

The grounded product-alignment research maps Power Products (Critical and Embedded Power) to utilities, and Thermal Management and Cloud to silicon providers, colocation providers, hyperscalers and neoclouds. Later project demo scenarios put hyperscalers and neoclouds into 15 kV switchgear purchases, which does not match that mapping; whether those scenarios are realistic is **Needs confirmation**. Customer type matters for how a bid is handled; see section 8.

**Concentration.** The two largest customers account for about 64% of revenue (34% plus 30%). They are not named. One source infers they are hyperscale or cloud-adjacent, which it says is not confirmed.

**Size**:

- Revenue for FY26 (fiscal year 2026) was about $6.6 billion, up from $3.24 billion in FY24 and $4.80 billion in FY25. The review meetings gave "$7 billion"; this is not a verified figure, and the written figure is used.
- The split is 31% Power Products and 69% Thermal Management plus Cloud.
- Adjusted operating margin for FY26 was about 8.9%.
- Flex guides growth of about 38% in FY26, 65 to 75% in FY27 and more than 80% in FY28. The review meetings mentioned 3x to 4x; that is not used as fact.
- The total addressable market (all spending SpinCo could sell into) is about $1.1 trillion for compute and power infrastructure (Omdia, as quoted by Flex).

**Leadership** (Flex press release, 29 Jul 2026): Revathi Advaithi (CEO), Bill Watkins (Non-Executive Chairman), Kevin Krumm (chief financial officer, CFO), Rob Campbell (Chief Commercial Officer), Mattias Jansson (President, Embedded Power), Todd Hoover (President, Critical Power), Hooi Tan (chief operating officer, COO) and Chris Butler (Chief Technology Strategy Officer). Other documents give Butler a different title and role; this is **Needs confirmation**.

**Is Syracuse a customer type?** No. The Syracuse airport RFP used as the worked example in section 10 is a public-sector aviation buyer, which is not a listed customer type. Its product category matches SpinCo's Critical Power list, so it is a technical illustration, not "a customer just like yours".

## 5. How Engineered Products Are Sold: From Make-to-Stock to Engineer-to-Order

Manufacturers differ in how much is decided before the customer orders and how much after.

| Model | Meaning | Example |
|---|---|---|
| **MTS** (make-to-stock) | Built before any order exists | An off-the-shelf breaker |
| **ATO** (assemble-to-order) | Built from stocked modular parts, assembled after the order | A standard server rack |
| **CTO** (configure-to-order) | Built from a fixed set of options chosen by rules | A power pod chosen from a menu |
| **ETO** (engineer-to-order) | The design itself is created after the order | A bespoke power skid or substation |

The scale runs from low customisation and fast delivery (MTS) to high customisation and slow delivery (ETO).

**The ETO quoting flow without software help**:

1. The client, or the general contractor who manages the construction project, sends a request with the load specification, voltage design and redundancy requirement (the **basis of design**).
2. A design engineer draws a single-line diagram (a simplified drawing of how power flows) and sizes the switchgear, busway and transformers. This takes days to weeks.
3. The engineer generates an **EBOM** (engineering bill of materials: the full parts list from the design).
4. An engineer or estimator manually costs the bill of materials (BOM): parts, labour, testing, logistics.
5. If the order is won, a **MBOM** (manufacturing bill of materials) is produced, then the factory builds and tests.

Steps 2 to 4 need an engineer even for quotes that may never win. The source gives an illustration, not SpinCo data: a company that issues 20 requests and wins 4 spent real design time on the 16 never built. This is called **quote churn**.

**SpinCo mixes the models.** The review meetings described three kinds of offering: configurable, custom (designed for a specific data-centre rack, completely custom), and semi-custom (standard components, then something made exclusively for the customer) (from the review meetings; needs confirmation). The review of 8 Oct 2026 named the three offering types in the client's vocabulary (below). The sources use the MTS/ATO/CTO/ETO vocabulary. Comparing the two (configurable with CTO, custom with ETO) is this document's comparison, not a stated source claim. The written evidence:

- EP² is labelled engineered-to-order on Flex's site, so part of the portfolio is purely ETO. The review of 8 Oct 2026 also said EP² is in the engineered-to-order business.
- Anord Mardix sells switchboards and packaged substations "configured to project requirements" and also "bespoke end-to-end solutions".
- EPC Power has high-complexity designs, some first-of-kind.

The sources argue that a fully CTO company buys CPQ off the shelf, a fully ETO company does not, and SpinCo is neither. This is an argument, not a measurement.

**Three offering types (8 Oct 2026, client vocabulary).** Layer 0 shows one offering type per requirement:

- **Configure-to-order (CTO):** a base model with options chosen, handled by CPQ. Think of configuring a laptop's memory and disk.
- **Semi-custom:** a configured product plus extra workshop work for the customer. Think of a car from the showroom sent to a workshop for tinted windows.
- **Engineered-to-order (ETO):** no existing product; the whole thing is designed to the customer's requirements. Example: a custom 8-foot rack with its own dimensions, wiring and power. EP² is in this business.

The project's earlier tiers map to these: `CTO_AUTOMATE` is CTO; `ETO_GUIDED` (the system drafts a basis of design and an engineer approves) is semi-custom, or guided ETO; `ETO_EXCEPTION` (engineers design manually) is ETO.

**Four tiers used by the project (earlier vocabulary).** Layer 0 labels each part of a bid with one of these (an older document spells the last tier ETO_ESCALATE):

- `CTO_AUTOMATE`: standard; can be configured and priced automatically and sent to the CPQ tool.
- `ETO_GUIDED`: mostly bespoke; standard sub-parts can be priced from the catalogue, and the rest is written up as a basis of design for a design engineer. The system does not design.
- `ETO_EXCEPTION`: fully bespoke or new; no design is attempted. The requirement is captured, the price left as a margin-protected placeholder (a price field marked "to be decided by an engineer"), and the work routed to a specialist.
- `OUT_OF_SCOPE`: the layer is not asked for.

When parts disagree, the most conservative tier wins, so a bid never looks more automatable than it is. These tiers are a supporting input to the opportunity workflow (which items can go to standard tools and which need engineering), not the workflow itself.

## 6. What CPQ Is and Where It Stops

**CPQ (Configure, Price, Quote)** is "a rules-based software layer that lets a sales or applications engineer, or even a customer, generate a valid configuration, an accurate price, and a quote, without a design engineer doing bespoke work for every" request. It was built for configure-to-order businesses such as cars and IT hardware, where the options are finite and can be written as rules, for example "if 400 A busway, then this breaker family". An ampere (A) is the unit of electrical current. The review meetings used an analogy: buying a Dell laptop online, where you change memory or disk and the price updates.

**How CPQ works, step by step**:

1. A salesperson or the customer enters load, voltage and redundancy.
2. A rules engine checks constraints, such as "an 800 A busway needs this enclosure class". This takes minutes.
3. The system builds a bill of materials from pre-mapped parts.
4. Cost, margin and discount rules produce a price and quote, within hours.
5. If the deal is won, detailed engineering produces the final manufacturing design.

CPQ gives a **quote-grade BOM** and price: accurate enough to sell, not the final design. A figure of "about 90 to 95%" accuracy appears in the sources without a basis (unverified).

**CPQ sits before detailed engineering.** One early assumption was that ETO design comes first and CPQ second. The explainer corrects this: CPQ goes in front of detailed engineering, at the quoting stage, so a full design pass is not needed just to produce a price. If the deal is lost, no further engineering time is spent. If won, detailed engineering follows, for weeks, only for what rules could not pre-validate.

**Where CPQ stops.** CPQ cannot replace engineering for the most novel work: a first-of-its-kind substation, a new grid-forming design from EPC Power, or an unusual busway run. An engineer would not sign a quote where thermal headroom (spare cooling capacity), busbar sizing (a busbar is a thick metal bar that carries large current inside switchgear) or short-circuit rating (the fault current equipment can survive) went unchecked (argument). Anything non-standard goes to engineering by hand, often through spreadsheets and email.

**Flex already has CPQ software.** Early project documents stated that Flex had none. That was an incomplete read of the market-data source. Later documents correct it: **Logik.io**, a commercial configuration and solving engine normally used with Salesforce, is in Flex's stack, along with Salesforce CRM (customer-relationship management: the system that tracks customers and sales). The rest of the known stack, per the same source:

| Tool | What it is |
|---|---|
| Logik.io | CPQ configuration engine |
| Salesforce CRM | Customer system that hosts CPQ |
| QuoteWin | Quoting tool (handles requests for quotation) |
| aPriori | Should-cost (calculated estimate of what a part should cost to make) and design-for-manufacture simulation |
| Product life-cycle management (PLM) tools: Oracle PLM, Autodesk Vault, Solidpdm | Store designs, engineering data and CAD (computer-aided design) drawing files |
| Enterprise resource planning (ERP) systems: SAP and Infor LN | Core business system for orders, inventory, purchasing and finance; two run in parallel |

Layer 0 must feed Logik.io, not compete with it. Which brands Logik.io is configured for, whether QuoteWin is used for this business, and whether SpinCo keeps these systems after separation are all **Needs confirmation**. The boundary between Layer 0 and these systems (what is handed off, what is read back, and whether opportunities are created in a CRM) is open. An earlier document did not find Logik.io and argued from public research that no quoting capability spans the brands. That research shows only that none is publicly visible, not that none exists.

## 7. How a Bid Works Today

**Bid vocabulary**:

- **RFI** (Request for Information): an early, informal inquiry about capability, usually before an RFP.
- **RFP** (Request for Proposal): a formal request; vendors reply with a proposal that gives method and cost. A hyperscaler building something new would normally issue an RFP, because it is evaluating how SpinCo would design the solution.
- **RFQ** (Request for Quotation): mainly asks the price of something already clearly defined.
- An **opportunity** is an incoming bid (from an RFP, RFQ or RFI) that the business considers pursuing.
- A **bid** (or bid response) is the vendor's reply. The **bid/no-bid** (go/no-go) decision is whether to respond at all.
- A **quote** is a formal price offer. A **preliminary quote** is a first estimate made without detailed estimation. The review meetings put it at close to 90% accurate (Needs confirmation).
- A **proposal** has an introduction, approach, scope tables, effort estimates and a pricing section.
- An **addendum** is an official change to the RFP issued after publication. **Clarifications (Q&A)** are vendor questions and customer answers during the bid. Both can change or add requirements.
- A **requirement** is one thing the solution must do or be, such as "switchgear rated 15 kV". A **requirement ID** is a unique label for it. A **sub-requirement** is a part of a requirement. A **work package** is a group of requirements assigned to a team, and a **team response** is that team's answer to its assigned requirements.
- **Traceability** is following a requirement from the RFP to the response and back. **Triage** here means deciding for each part of a bid whether it is standard or needs an engineer.
- A **win rate** is the share of bids that become contracts. The example given in the review meetings is one in three.
- A **deal desk** is the internal team that approves prices, discounts and terms.

A real RFP is "a real, often-messy document (PDF, spec tables, sometimes CAD/BOQ attachments), not a structured web form". CAD means engineering drawing files; a BOQ (bill of quantities) is a list of items and quantities to price.

**The process, per the project documents**:

1. A customer sends an RFP. Customers include hyperscalers, data-centre developers, utilities and public bodies such as airports. An RFP can run past 100 pages.
2. An **application engineer** (an engineer who matches customer needs to products) reads it. The documents estimate 5 to 10 days for a complex bid. This is an expert estimate, not measured SpinCo data.
3. For each line, the engineer decides whether it is standard or configurable, or needs custom engineering.
4. Standard items go to Logik.io and pricing. Custom items go to **design engineers**, who design enough to give a preliminary quote.
5. The responses from each team are gathered into one proposal and sent.

**The review-meeting version**, stated as an assumption: the salesperson receives the RFP and studies it for a few days, sends the same document to everybody, each group somehow produces its own response, and there is no workflow or system (Needs confirmation). For a data-centre bid, someone must decide whether one company or several of the brands can handle it and then whether to bid at all. This was contrasted with a single power unit sold to a factory, which can be quoted in the CPQ way (Needs confirmation).

**Roles and the bid flow (Expected (review meetings), 8 Oct 2026).** One **bid manager** has a general idea of all the business units, receives the RFP and owns the opportunity. **Each business unit has a product manager and a design engineer.** The tool reads the RFP and maps each requirement against the product offerings each business unit carries, creating one **line item** per requirement. An RFP may involve one or more business units. The bid manager then sends each participating unit its part in one simple step: the main RFP plus the line items assigned to it. The unit's product manager and design engineer complete their part. The response works as a checklist per requirement: the design engineer states that the requirement is met, and with what. Someone then validates the responses. Responses flow back to the bid manager, who assembles the comprehensive response. The analogy is different groups writing different chapters of one proposal. The system tracks which units have responded. The product is built from a bill of materials (BOM) held in a separate system; the response itself may not include the BOM.

**Concurrency, identifiers and retention (8 Oct 2026).** Several RFPs run at once, and people work on several at once. Requirement IDs must be unique across all opportunities; part numbers need not be. Each engagement has its own workspace and workflow. All data for an opportunity (RFP, requirements, responses, communication) must be captured and protected for the life of the project and beyond, because warranty clauses apply. The record is append-only.

**The intended opportunity workflow (Expected, review meetings).** The business direction described in the review meetings is to manage each opportunity from the arrival of the RFP until the final bid response is assembled. In order, it is:

1. **Read and understand** the incoming RFP. Every extracted item keeps an exact source reference: document, page and quoted text.
2. **Determine participation**: whether one, several or all relevant business units need to take part. Not every data-centre bid needs every unit.
3. **Support a human go/no-go decision.** The system assembles the evidence (scope fit, deviations, capacity or portfolio conflicts, open questions). A named person decides, and the decision is recorded. The working baseline is that Layer 0 supports the decision and does not make it.
4. **If go, establish the workflow** for that opportunity. Different customers and product combinations need different workflows: some steps are mandatory, some configurable.
5. **Break the RFP into requirements and work packages** assigned to the appropriate teams. One requirement may involve several teams.
6. **Track each team's response** against its assigned requirements.
7. **Bring the responses together** into the final bid response with complete traceability, and check that every requirement is answered or explicitly excluded.

Cross-cutting, at every step: human approval and accountability; an audit history of decisions and changes; and handling of clarifications, addenda and change requests against the affected requirements. The review meetings described change requests being handled incrementally, with a drastically changed RFP treated as a new opportunity (how this works in detail is open).

**What a bid response contains and what must be tracked** (description from the review meetings, using how Zensar answers RFPs) (from the review meetings; needs confirmation):

1. The response has narrative text, tables and a pricing section.
2. Each customer requirement gets an ID, grouped by discipline and routed to the right people.
3. Plain configuration options (the example given is one quality-assurance (QA) resource, meaning one tester) can be picked and priced directly. Everything else goes to program managers or, at Flex, to design engineers.
4. Each team fills an **estimation sheet** (a table listing, per requirement ID, the work, people, hours or weeks and cost). Whether estimation sheets, or any price or margin figure, belong inside Layer 0 is an open scope question.
5. Non-technical requirements, such as working from a given geography or night-time support, also become IDs and must trace back to the response.
6. Clarification answers and addenda become new or updated requirement IDs, so all information for the bid is in one place.
7. Before the final proposal, a **QC (quality-control) check** confirms every customer requirement (the example given is 25) has been answered.
8. For a bid split across teams, three connected views must meet in the final response: the original RFP, how its requirements were broken up and assigned, and how each team responded. The chain to preserve is: **Original RFP requirement → breakdown and team assignment → team response → final bid response.**

**What goes wrong today**:

- Decisions are unrecorded. The judgment of which parts are standard lives in a few experienced heads.
- There is no systematic way to decide which units take part, and go/no-go decisions lack structured evidence and clear accountability.
- No opportunity-specific workflow is set up when a bid goes ahead, and team responses are not coordinated or tracked against assigned requirements.
- Under load, some bids are skimmed, priced conservatively or declined, which shows up later as a lower win rate that is never recorded.
- A missed clause becomes a costly field modification, and no one can trace who decided. None of this appears in the financial reports ("not on a profit-and-loss line").
- Clarifications and addenda have no single place that updates the requirements.
- Nothing checks at the end that every requirement was answered.
- **Why this persists**: CPQ assumes structured input after a human has read the RFP, and before language models, software could not reliably extract engineering requirements from messy documents.

## 8. Why Customer Type, Product Mix and Participating Units Change the Bid

A bid is not one fixed process. Who takes part, which steps are needed, who makes the decisions and how long it takes all depend on the customer, the products asked for, and which business units must be involved. The two ends of the range are a standalone product sale and a multi-unit data-centre opportunity.

| Aspect | Standalone product sale | Multi-unit data-centre opportunity |
|---|---|---|
| Who participates | Usually one unit and one engineering team | Several units and teams, possibly with outside suppliers or integrators |
| Workflow | Light: review of requirements, commercial and compliance items, a quote | Heavier: split the RFP across units, coordinate responses, resolve overlaps, consolidate |
| Decision-making | Go/no-go turns mainly on scope fit and deviations | Go/no-go also weighs which units take part, capacity across units, and whether the combined offering is credible |
| Time | Shorter; closer to a CPQ-style quote where items are standard | Longer; more people to coordinate, and more places for a requirement to be missed or answered twice |
| Requirement ownership | One requirement, one team | One requirement may involve two or more teams |

The review meetings drew the same contrast: a single power unit sold to a factory can be handled in the CPQ way, while a data-centre bid needs someone to decide which companies respond and whether to bid at all (from the review meetings; needs confirmation). Customer type matters too. A utility buying switchgear, a hyperscaler asking for a campus design and a colocation provider asking for a pod have different requirements, different approval needs and different participants (see section 4).

**Participation is a decision, not an assumption.** A data-centre bid does not automatically need every unit. Which units take part follows from what the RFP actually asks for. The workflow for the opportunity is set up after that decision and after a go decision.

**Illustrative examples** (illustrative; not recorded SpinCo bids):

*Single-unit opportunity.* A standalone medium-voltage switchgear RFP, like the public Syracuse airport RFP used in section 10.

- Likely Crown Technical Systems takes part (arc-resistant medium-voltage switchgear), and possibly EP² (relay and protection panels). The matcher proposes this and a person confirms it.
- The workflow is light: engineering review of requirements such as arc-resistant Type 2B, plus commercial and compliance items.
- Go/no-go turns on scope fit and deviations.
- Every requirement still traces to its owning team and to its answer in the final response.

*Multi-unit opportunity.* An AI data-centre campus RFP, like the synthetic 48 MW hyperscale-campus sample.

- It may need Anord Mardix (facility power and switchgear), Flex Power Modules (rack and board power), JetCool (liquid cooling), Cloud (compute integration), and possibly EP² for substation control.
- That means several business units. One requirement, such as rack power plus cooling at a given density, may involve two teams.
- The workflow is heavier and must coordinate responses across units before they are consolidated.
- Not every data-centre bid needs every unit. The synthetic modular inference-pod sample may need fewer.

Which templates apply to which customer type and product mix, and which workflow steps are mandatory and which configurable, are not yet decided.

## 9. Quote-to-Cash and Where Layer 0 Sits

**Quote-to-cash** is the whole business process from a customer request to being paid. The sources break it into 12 steps:

1. Demand capture: the RFP or RFQ arrives, often unstructured. **Layer 0.** No vendor covers it.
2. Qualify and triage: bid/no-bid, scope, complexity, standard or bespoke. **Layer 0.** No vendor covers it.
3. Configure: CPQ (Logik.io).
4. Cost: aPriori or CPQ.
5. Price: CPQ.
6. Approve: CPQ and people, including the deal desk.
7. Quote document: CPQ.
8. Negotiate: sales.
9. Order: ERP.
10. Engineering release (EBOM to MBOM): PLM or ERP.
11. Manufacture: factory.
12. Deliver and service: field services.

**Layer 0's role: opportunity management.** Layer 0 is intended to be the workflow that manages a bid opportunity from the arrival of the RFP until the final bid response is assembled. It should help understand the RFP, determine which business units need to take part, support a human go/no-go decision, set up the workflow for that opportunity, break the RFP into requirements and work packages owned by the right teams, track each team's response, and bring the responses together into a final response that traces back to every original requirement. In the 12 steps above, this spans steps 1 and 2 and then continues through the team-response and consolidation work that feeds the quote document (step 7), so it is wider than intake alone. This workflow is the business direction described in the review meetings and is used as the working baseline. It has not been formally signed off, and no existing build implements it end to end.

**Supporting capabilities.** The following serve the workflow. They are not the definition of Layer 0:

- reading RFPs and extracting requirements with exact source references (intake);
- scope detection across the six product layers, and mapping of layers and brands to teams;
- triage into the four automation tiers (section 5), which shows which items can go to standard tools and which need engineering;
- specification and engineering checks, and deviation checks against past bids;
- bid, execution and portfolio checks for capacity, specification and timeline conflicts across customers;
- a coverage or completeness check at the end;
- human review gates and an audit log;
- pointer links to artefacts held in other systems (drawings, vendor specs, test reports) (Proposed).

**Why this matters beside CPQ.** One source argues that "every CPQ platform on the market begins at the moment a human has already read the RFP and decided what kind of job it is. ... that moment is the bottleneck, and it is the only part of the stack nobody sells" (argument). Traditional CPQ works at steps 3 to 8, so the overlap with Layer 0 is small. Layer 0 is not a CPQ system. It sits upstream of CPQ, and it also coordinates the human and team work around an opportunity, which CPQ does not do. Non-standard requests also matter here: in complex manufacturing they carry a large share of real revenue and escape into spreadsheets and email, and for EP² and EPC Power they "could be the majority path" (unverified).

**Scope boundaries.**

- Tracking team work is part of Layer 0. It does not require Layer 0 to be a general-purpose collaboration platform.
- Linking and consolidating team responses is not autonomous proposal writing. People write the responses.
- Supporting go/no-go does not give a model decision authority. A person decides and is recorded.
- CPQ (Logik.io with Salesforce), costing (aPriori), quoting (QuoteWin), ERP (SAP, Infor LN), product-data systems and engineering teams may support downstream work. The integration boundaries are open (section 6).
- Whether per-team estimation sheets or any price or margin figures belong inside Layer 0 is an open scope question. Earlier documents say Layer 0 never produces a price, the review meetings mention estimation tables, and one earlier demo produced margin estimates on synthetic data.

For the project's status and how the different framings relate, see [project-overview.md](project-overview.md).

**Hypothesised value (to be measured; no figures).** The expected benefits are fewer coordination delays between units and teams, fewer missed hand-offs, fewer unanswered requirements at submission, less rework from late-discovered requirements or changes, faster, more consistent and more accountable go/no-go decisions, clearer ownership, and less time spent reading RFPs. None of these has been measured. Earlier catch-rate and ROI claims are superseded. Measuring them needs SpinCo historical bids.

**The business case rests on unmeasured assumptions.** For the reading part alone: if reading and triage take about 10% of the bid cycle (2 of 20 days), that part is not worth much. If they take 40% or more (5 to 10 days), it is a worthwhile investment. Nobody has measured the share; the documents propose checking 20 to 30 past SpinCo RFQs. The sources therefore avoid claiming "quotes in hours instead of weeks". They claim only that reading is inconsistent, undocumented and unauditable.

## 10. Reading an RFP: A Worked Example (Syracuse Switchgear)

### 10.1 What the example is and is not

The project's main example is **RFP 2023-20** from Syracuse Regional Airport (also called Syracuse Hancock International): replacing or upgrading switchgear. It was issued in August 2023 with a deadline of 29 September 2023. The RFP is **real and public**. The repository holds a genuine 101-page copy.

It is **not a record of a SpinCo bid**. The "past bid" that quoted standard switchgear, the missed requirement and any loss figure are constructed illustrations. Whether SpinCo or any brand ever bid on it is **Needs confirmation**. Real validation would need a pilot on SpinCo's own historical RFPs with known outcomes (Proposed). It is a single-unit opportunity in the sense of section 8.

### 10.2 What the RFP asks for

- **Equipment**: free-standing, dead-front, metal-clad medium-voltage distribution switchgear.
- **Key sentence**, quoted and repeated in the RFP: "The switchgear lineup shall be Arc-Resistant Type 2B per ANSI/IEEE C37.20.7."
- **Electrical parameters**: 15 kV (medium voltage); 630 A continuous; several sections; an NEMA 1 enclosure; installed in a switchgear building. The sample set counts 18 vacuum circuit-breaker positions.

The terms, in plain words:

- **Metal-clad**: major parts (the breaker, the bus bars that carry power, the instrument compartment) sit in separate grounded metal compartments, usually with breakers that can be pulled out.
- **Dead-front**: no live parts are exposed on the side the operator faces.
- **Free-standing**: a floor-mounted, self-supporting lineup, not wall-mounted.
- **Lineup and sections**: cabinets bolted side by side. The incoming main receives the supply, distribution sections feed outgoing circuits, and monitoring and control sections hold meters and controls.
- **Continuous current rating (630 A)**: the current the equipment can carry indefinitely without overheating.
- **Vacuum circuit breaker**: a breaker that interrupts current inside a vacuum bottle; "breaker positions" are the slots for them.
- **NEMA 1**: an enclosure rating for indoor use (the source's "weathertight" wording is odd for this rating).
- **Arc flash**: an explosive electrical fault inside equipment. **Arc-resistant** equipment is tested and certified to contain and redirect that energy so it does not burst out where people stand.
- **Type 2B, ANSI/IEEE C37.20.7**: the source explains Type 2B as a rating where arcing must not burn through the freely accessible front, sides or rear, and where the instrument compartment is isolated. It calls this "the highest practical arc-containment rating for this class of equipment" (unverified). C37.20.7 is the US guide for testing metal-enclosed switchgear for internal arcing faults.

### 10.3 Why a missed requirement hurts

1. Type 2B "is not a baseline requirement; it's an upgrade". It needs specific engineering, testing and certification.
2. Lead time and cost differ materially from standard switchgear.
3. A bid that omits it looks cheaper and faster. The customer then finds out after award, or at design review, that the equipment quoted does not meet the requirement. A post-award design or price change like this is called a **change order**.
4. The cause the source implies is a hidden assumption such as "bid standard now, upgrade after award". No other root cause is stated.

**The clarification (RFI) answer.** Bidder RFI #3 asked: "Does the incoming switch need to be arc resistant too?" The answer: "Ideally, the full switchgear lineup including the switches should be Arc Resistant. If this is not feasible in the manufacturer's design, please identify what components/compartments will not be Arc Resistant as a deviation." A **deviation** is a component or compartment that will not meet the specification, which bidders must name explicitly. The source reads this as the customer being serious and accepting deviations only if clearly identified and justified. This is an example of a clarification that changes how a requirement must be answered, and so must be recorded against that requirement.

**Availability.** ABB, Eaton, Schneider and Siemens, among others, offer Type 2B switchgear in this 15 kV, 630 A configuration. The source calls it "a standard product, not exotic": the risk is whether the bid included it, not whether it exists.

### 10.4 What the PoC does with it

The sample PDF used for development now lives in Layer0-Flex/data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf. The description below is of the v0.3.0 bid-triage pipeline, the demo built on this RFP. It is **current state** for one code line, not the target workflow. It covers only part of the early steps of the intended workflow (section 7) and does not produce a go/no-go output, set up a workflow, or track team responses.

1. The reading stage extracts values such as 15 kV, Arc-resistant Type 2B and 18 breaker positions. Counting keywords (for example, "switchgear" about 163 times) shows the RFP asks for layer L2 and not for cooling.
2. L2 is mapped to Crown and tiered `ETO_GUIDED`.
3. The solving stage refuses to calculate: medium-voltage switchgear needs engineering judgment. The documents say that "knowing what not to answer is what earns an engineer's trust".
4. A coverage map lists each clause, its tier and a link that opens the source page with the sentence highlighted.

Three cautions apply:

- The demo marked L1 and L3 to L6 out of scope. That is a result for this RFP only, since it asks only for switchgear. It is not a statement that rack, board or thermal products are outside SpinCo's offering. The 22 Sep review meeting described these as not part of this Flex offering; the written sources show otherwise.
- Commercial clauses (pricing basis, lump sum) were not extracted, and clause splitting on the full 101-page PDF is unreliable.
- The 22 Sep review meeting stated that an LLM is used (a large language model: AI software that reads and writes text), while the demo ran in a default mode that uses pattern matching, not a language model.

### 10.5 Other sample documents

The project also uses a synthetic hyperscale campus RFP (2N redundancy, 800 VDC; the multi-unit example in section 8), a synthetic modular inference pod RFP (N+1, 415 VAC), a real US District Court RFQ in southern Florida for a 45 kVA (kilovolt-ampere, explained below) **UPS** (uninterruptible power supply: a battery-backed unit that keeps power on during an outage), and a real US Air Force request for an AI data centre at Davis-Monthan, which is a land lease SpinCo would not bid on. The "real" text files in the repository are short author-written summaries, not the full documents.

The UPS example is the one an engineer can check by hand. **kVA** (kilovolt-amperes) rates "apparent" power. Starting from 45 kVA, apply an 80% limit for continuous loads under the US electrical code (NEC 210.20(A)), giving 36.0 kVA. Multiplying by an assumed **power factor** of 0.9 (the share of apparent power that is usable; the code assumes 0.9 when unstated and flags it) gives 32.4 kW. Dividing across 10 racks gives 3.24 kW per rack. A **rack** is a standard cabinet that holds servers; racks above about 100 kW need liquid cooling in the project's rules.

## 11. Why Timing Matters

- **Growth versus headcount.** Flex guides growth of 65 to 75% in FY27 and more than 80% in FY28. Quote volume must grow with revenue, but engineering headcount cannot grow 65 to 80% a year. This is an inference in the sources (argument).
- **The "structural squeeze".** Demand grows; capacity is limited by design engineers who must do bespoke quoting; and systems are fragmented. Quote capacity then limits how much of the AI-infrastructure market SpinCo can bid for (argument).
- **The cost is hidden.** Engineering hours spent on RFPs that were lost show up only as declined, slow or conservatively priced bids.
- **Fragmentation by acquisition.** The portfolio was assembled by buying companies, and each has its own quoting practice. SAP and Infor LN both run. Anord Mardix has its own head of IT and a separately procured stack. Two ERPs plus brand autonomy suggest no single quoting path across the portfolio. This is an inference from market-data sources, not a measurement. Because units that previously sold on their own must now combine offerings, the coordination burden falls on opportunities that span units.
- **Future (not in scope).** If the design works well, the review of 8 Oct 2026 noted many similar use cases in the semiconductor industry.
- **The window.** The sources argue that a separation is the one moment a company rebuilds its commercial systems by choice. Before separation the change is part of standing up the company; afterwards it becomes a migration project competing for budget (Proposed argument).
- **Expectation in the review meetings.** Volume is expected to grow 3x to 4x; with about a one-in-three conversion rate, a business three times larger means answering far more RFPs, and the teams cannot be multiplied to match (from the review meetings; needs confirmation).

Two domain constraints also apply. RFPs contain commercially sensitive information such as capacity, location and timeline. Engineered electrical systems typically need a licensed engineer's sign-off in most jurisdictions, so AI can draft but cannot be the final validator. That second statement is not verified against any regulation and is **Needs confirmation** for the jurisdictions SpinCo works in.
