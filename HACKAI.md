Use this block at the top of almost every Copilot prompt.

Project: Restaurant Growth Copilot

Goal:  
Build an end-to-end AI platform for local restaurants that helps scale revenue and reduce costs using:  
1\. menu optimization  
2\. inventory management  
3\. social media recommendations

Core product principle:  
The system must not hallucinate strategies. It must use:  
\- analytics \+ rule-based strategy selection  
\- a fixed strategy library  
\- strategy history and feedback memory  
\- LLM only for explanation and report generation

Tech stack:  
\- Frontend: Next.js \+ TypeScript \+ Tailwind  
\- Backend: FastAPI \+ Python  
\- Database: PostgreSQL  
\- ORM: SQLAlchemy  
\- Validation: Pydantic  
\- Analytics: pandas, numpy, scikit-learn, mlxtend  
\- Charts/UI: Recharts or equivalent  
\- Async/background tasks only if lightweight and necessary

Main entities:  
\- Restaurant  
\- MenuItem  
\- SalesRecord  
\- InventoryItem  
\- RecipeMapping  
\- SocialPost  
\- StrategyDefinition  
\- StrategyHistory  
\- Recommendation

Important strategy-memory rules:  
\- maintain strategy history  
\- track active, successful, failed, archived strategies  
\- use cooldown windows  
\- do not repeat recent or active strategies  
\- rank strategies by evidence, confidence, expected impact, and ease of execution

Coding constraints:  
\- produce modular code  
\- use clear file boundaries  
\- include type hints  
\- include docstrings  
\- include error handling  
\- include realistic sample data support  
\- keep the MVP demo-ready in 36 hours

When writing code:  
\- assume this is part of a larger codebase  
\- mention file names  
\- generate production-inspired but hackathon-friendly code  
\- avoid placeholders unless necessary  
\- if adding new files, list them first  
\- preserve compatibility with previous outputs

# **5\. How to preserve strategy history across prompts**

This is the most important part of your request.

Create a file like:

docs/strategy\_memory\_contract.md

and a table in DB:

strategy\_history

Also maintain a prompt-side context snippet like this:

Current strategy history behavior to preserve:  
\- strategies are selected only from a fixed playbook  
\- strategy statuses: suggested, accepted, active, evaluating, successful, failed, archived  
\- cooldown default: 14 days  
\- recently failed strategies should be deprioritized or blocked  
\- active strategies should not be re-suggested  
\- successful strategies can lead to "scale-up" recommendations instead of repetition  
\- each recommendation must include evidence and blocked reasons

Later prompts should also carry this:

Previously implemented modules:  
\- database models for Restaurant, MenuItem, SalesRecord, InventoryItem, RecipeMapping, SocialPost  
\- strategy library and strategy history  
\- recommendation filters based on active/failed/cooldown states

Build the next module without breaking existing architecture.  
Reuse existing models and contracts.

That is how you avoid zero-shot behavior.

## **Subpart 1 — Scaffold the whole codebase**

**Goal:** Create the initial project structure and development roadmap.

### **Prompt 1**

Use the following project context and generate the initial codebase structure.

\[PASTE SHARED PROJECT CONTEXT BLOCK\]

Task:  
Create a modular end-to-end project structure for this application with:  
\- frontend in Next.js \+ TypeScript  
\- backend in FastAPI  
\- PostgreSQL database  
\- analytics and recommendation layers in Python

I want:  
1\. complete folder structure  
2\. purpose of each folder  
3\. recommended file names  
4\. development order  
5\. basic API boundary plan  
6\. a short architecture note explaining how analytics, strategy engine, strategy history, recommendation engine, and LLM explanation layer interact

Important:  
\- this must support menu optimization, inventory management, social media recommendations, strategy history, and a non-hallucinating recommendation system  
\- include docs files for prompt history and strategy memory contract  
\- keep it hackathon-friendly but end-to-end

Output format:  
\- folder tree  
\- file purpose list  
\- implementation roadmap  
\- architecture summary  
---

## **Subpart 2 — Define the database schema**

**Goal:** Create all models needed for the whole product.

### **Prompt 2**

Continue from the existing project architecture.

Already decided:  
\- the codebase has separate frontend and backend folders  
\- backend uses FastAPI, SQLAlchemy, Pydantic, PostgreSQL  
\- recommendation logic must use strategy history and a fixed strategy library

Now generate the backend data model layer.

Requirements:  
Create SQLAlchemy models and matching Pydantic schemas for:  
\- Restaurant  
\- MenuItem  
\- SalesRecord  
\- InventoryItem  
\- RecipeMapping  
\- SocialPost  
\- StrategyDefinition  
\- StrategyHistory  
\- Recommendation

Include important fields such as:  
\- restaurant profile info  
\- item price, ingredient cost, margin-related fields where appropriate  
\- timestamps  
\- statuses for strategy history  
\- strategy outcome metrics  
\- cooldown dates  
\- evidence JSON fields if useful  
\- recommendation confidence and blocked\_reason fields

Important business rules:  
\- StrategyHistory must support statuses: suggested, accepted, active, evaluating, successful, failed, archived  
\- Recommendations must be linked to strategy definitions and restaurant/item context  
\- Social posts should support engagement metrics  
\- Inventory items should support reorder thresholds and expiry dates

Output:  
1\. list of backend files to create  
2\. SQLAlchemy model code  
3\. Pydantic schemas  
4\. notes on relationships  
5\. any enums needed  
---

## **Subpart 3 — Create database setup and migrations**

**Goal:** Make the app runnable.

### **Prompt 3**

Use the previously created SQLAlchemy models and schemas.

Now generate the database setup layer for FastAPI.

Requirements:  
\- create database connection configuration  
\- SQLAlchemy session management  
\- base model setup  
\- environment variable loading  
\- Alembic-ready structure  
\- starter migration guidance  
\- dev-friendly config

Assume existing model files already exist.  
Do not rewrite models unless necessary.

Output:  
1\. file list  
2\. code for db/session/base/config files  
3\. instructions for wiring Alembic  
4\. startup notes

## **Subpart 4 — Build FastAPI app skeleton**

**Goal:** Create a proper API structure.

### **Prompt 4**

Continue from the existing backend models and database setup.

Now generate the FastAPI application skeleton.

Requirements:  
\- main.py  
\- API router registration  
\- health endpoint  
\- versioned API structure  
\- dependency injection for DB sessions  
\- modular route folders for:  
 \- restaurants  
 \- uploads  
 \- analytics  
 \- strategies  
 \- recommendations  
 \- social  
 \- chat

Important:  
\- keep route handlers thin  
\- business logic must live in services/engines  
\- code should be hackathon-ready but clean

Output:  
1\. file list  
2\. code for main app and routers  
3\. notes on how later services will plug in  
---

## **Subpart 5 — Build CSV ingestion pipeline**

**Goal:** Enable realistic restaurant onboarding.

### **Prompt 5**

Continue from the existing FastAPI backend.

Context already implemented:  
\- models for Restaurant, MenuItem, SalesRecord, InventoryItem, RecipeMapping, SocialPost, StrategyDefinition, StrategyHistory, Recommendation  
\- DB session setup  
\- FastAPI skeleton with uploads router

Now build CSV ingestion for the MVP.

Requirements:  
Create endpoints and service code to upload and parse CSV files for:  
\- menu items  
\- sales records  
\- inventory items  
\- recipe mappings  
\- social post history

Requirements:  
\- validate required columns  
\- clean column names  
\- normalize item names  
\- reject malformed rows with useful error messages  
\- support restaurant\_id  
\- store parsed data into PostgreSQL  
\- create reusable parser helpers  
\- return ingestion summary stats

Important:  
\- this is for local restaurants, so CSV import is preferred over external POS integration  
\- keep file-by-file services modular  
\- add sample expected CSV schemas

Output:  
1\. file list  
2\. route code  
3\. parser/service code  
4\. expected CSV formats  
5\. validation logic  
---

## **Subpart 6 — Seed demo data and sample CSVs**

**Goal:** Make the product demo-ready.

### **Prompt 6**

Continue from the existing backend and CSV ingestion layer.

Now generate realistic sample datasets and seed utilities for two restaurants:  
1\. local cafe  
2\. fast-casual burger restaurant

Include:  
\- menu.csv  
\- sales.csv for 90 days  
\- inventory.csv  
\- recipe\_mapping.csv  
\- social\_posts.csv

Requirements:  
\- data should produce meaningful analytics  
\- include good and bad menu items  
\- include examples of low margin/high popularity items  
\- include inventory waste patterns  
\- include social content engagement patterns  
\- include enough order variation for basket analysis

Also create:  
\- a seed script or utility for loading demo data into the DB  
\- notes about where the files should live in the repo

Output:  
1\. sample CSV structures and content generation approach  
2\. seed utility code  
3\. file paths  
4\. any assumptions made  
---

## **Subpart 7 — Build menu analytics engine**

**Goal:** Compute evidence, not strategy.

### **Prompt 7**

Continue from the current backend.

Already implemented:  
\- core data models  
\- CSV ingestion  
\- demo dataset support

Now build the menu analytics engine.

Requirements:  
Create service code that calculates:  
\- top selling items  
\- bottom selling items  
\- revenue by item  
\- estimated profit by item  
\- margin percentage by item  
\- popularity score  
\- menu engineering classification  
\- pair frequency and association analysis using order-level sales data  
\- day/time demand trends  
\- category performance

Important:  
\- keep analytics and recommendations separate  
\- this layer should only compute facts and scores  
\- no free-form strategy generation here  
\- support structured outputs that can be used by later strategy selection logic

Use:  
\- pandas  
\- numpy  
\- mlxtend for basket analysis if helpful

Output:  
1\. file list  
2\. analytics service code  
3\. output schemas or DTOs  
4\. notes on assumptions and formulas  
---

## **Subpart 8 — Build inventory analytics engine**

**Goal:** Connect sales to stock decisions.

### **Prompt 8**

Continue from the existing restaurant analytics backend.

Already implemented:  
\- menu analytics  
\- recipe mapping  
\- inventory and sales models

Now build the inventory analytics engine.

Requirements:  
Create services that compute:  
\- ingredient usage based on recipe mapping and sales history  
\- projected days of stock left  
\- reorder alerts  
\- overstock risk  
\- stockout risk  
\- expiry risk  
\- waste-prone ingredients  
\- menu items causing disproportionate ingredient complexity or waste

Important:  
\- keep this layer purely analytical  
\- no LLM usage  
\- no strategy text generation yet  
\- return structured evidence for later recommendation logic

Output:  
1\. file list  
2\. service code  
3\. helper functions  
4\. output schema suggestions  
5\. notes on forecasting simplifications for MVP  
---

## **Subpart 9 — Build social media analytics engine**

**Goal:** Ground social recommendations in evidence.

### **Prompt 9**

Continue from the existing codebase.

Already implemented:  
\- social post history ingestion  
\- sales data ingestion  
\- menu and inventory analytics

Now build the social media analytics engine.

Requirements:  
Compute:  
\- engagement by post type  
\- engagement by posting time/day  
\- item-linked post performance  
\- trending products worth featuring  
\- campaign opportunity windows based on sales patterns  
\- recommended content category candidates based on top-selling or high-margin items

Important:  
\- keep this evidence-based and structured  
\- no free-form post generation yet  
\- connect social performance to restaurant sales patterns where possible

Output:  
1\. file list  
2\. analytics service code  
3\. return schemas  
4\. assumptions and limitations for MVP  
---

## **Subpart 10 — Create the strategy playbook**

**Goal:** Fixed set of allowed strategies.

### **Prompt 10**

Continue from the existing analytics-driven backend.

Already implemented:  
\- menu analytics  
\- inventory analytics  
\- social analytics

Now create a fixed strategy library for the recommendation system.

Requirements:  
Define approved strategy types for categories such as:  
\- pricing  
\- bundling  
\- upsell  
\- menu simplification  
\- ingredient cost optimization  
\- reorder timing  
\- reduce overstock  
\- reduce waste  
\- promote on reels  
\- promote at specific day/time  
\- highlight high-margin items  
\- scale successful campaign  
\- remove or de-emphasize low-performing items

For each strategy definition include:  
\- unique code  
\- name  
\- category  
\- description  
\- applicability rules  
\- blocked conditions  
\- expected evidence fields  
\- optional cooldown defaults  
\- required confidence thresholds  
\- expected KPI targets

Important:  
\- this library must be machine-readable  
\- recommendations later must only use strategies from this playbook  
\- no open-ended invented strategy types

Output:  
1\. file list  
2\. strategy definition structure  
3\. code or JSON seed for playbook  
4\. examples of strategy applicability rules

## **Subpart 11 — Build strategy history engine**

**Goal:** Prevent repetition and track learning.

### **Prompt 11**

Continue from the existing codebase.

Already implemented:  
\- StrategyDefinition model or equivalent fixed strategy library  
\- StrategyHistory model  
\- analytics engines

Now build the strategy history engine.

Requirements:  
Create service logic that:  
\- records suggested strategies  
\- records acceptance/rejection  
\- marks strategies active  
\- marks strategies evaluating  
\- records outcomes as successful or failed  
\- supports archived strategies  
\- applies cooldown windows  
\- blocks duplicate active strategies  
\- deprioritizes recently failed strategies  
\- allows successful strategies to lead to "scale-up" follow-up recommendations instead of repetition

Important:  
\- this service is critical to preventing repeated or nonsensical recommendations  
\- design it so later recommendation ranking can query it easily

Output:  
1\. file list  
2\. service code  
3\. example DB query helpers  
4\. clear explanation of the lifecycle transitions  
---

## **Subpart 12 — Build rule-based recommendation selector**

**Goal:** Convert evidence into eligible actions.

### **Prompt 12**

Continue from the existing backend.

Already implemented:  
\- menu analytics  
\- inventory analytics  
\- social analytics  
\- strategy playbook  
\- strategy history engine

Now build the recommendation selector.

Requirements:  
Create logic that:  
1\. takes structured analytics outputs  
2\. matches them to eligible strategies from the fixed playbook  
3\. checks strategy history  
4\. filters out blocked or duplicate strategies  
5\. ranks remaining strategies by:  
  \- expected business impact  
  \- confidence  
  \- ease of execution  
  \- novelty relative to recent recommendations  
6\. returns top recommendations as structured JSON

Each recommendation should include:  
\- restaurant\_id  
\- optional item\_id or ingredient\_id  
\- strategy\_code  
\- title seed  
\- evidence  
\- confidence  
\- urgency  
\- expected\_impact  
\- blocked\_reason if not eligible  
\- explanation\_input payload for later LLM formatting

Important:  
\- no free-form LLM generation here  
\- strategy selection must be deterministic and evidence-based

Output:  
1\. file list  
2\. recommendation selection code  
3\. ranking logic  
4\. example structured outputs  
---

## **Subpart 13 — Build simulation and validation helpers**

**Goal:** Estimate whether a strategy is likely to work.

### **Prompt 13**

Continue from the existing recommendation system.

Already implemented:  
\- analytics engines  
\- strategy playbook  
\- strategy history  
\- rule-based recommendation selector

Now build lightweight strategy validation and simulation helpers.

Requirements:  
Add utilities for:  
\- simple price change simulation  
\- basket/bundle opportunity scoring  
\- reorder quantity impact estimation  
\- stockout risk reduction estimation  
\- social timing opportunity scoring

Important:  
\- keep methods lightweight and transparent for hackathon MVP  
\- use historical data where possible  
\- produce evidence values and confidence adjustments  
\- recommendations should be able to cite these outputs

Output:  
1\. file list  
2\. service/helper code  
3\. formulas used  
4\. notes on limitations and where A/B testing would fit later  
---

## **Subpart 14 — Build LLM explanation layer**

**Goal:** LLM writes, but does not decide.

### **Prompt 14**

Continue from the existing recommendation engine.

Already implemented:  
\- deterministic recommendation selection  
\- strategy history filtering  
\- structured recommendation JSON with evidence and confidence

Now build the LLM explanation layer.

Requirements:  
Create prompt templates and service code that:  
\- take structured recommendation JSON as input  
\- generate a concise restaurant-owner-friendly explanation  
\- do not invent metrics  
\- do not change the selected strategy  
\- do not introduce unsupported business claims  
\- can generate:  
 \- recommendation explanation  
 \- weekly summary  
 \- social caption draft  
 \- action checklist

Important:  
\- the LLM is only an explanation and formatting layer  
\- prompt templates must explicitly forbid adding unsupported numbers or strategy types  
\- include fallback non-LLM string formatting option for demo reliability

Output:  
1\. file list  
2\. prompt template files  
3\. service code  
4\. sample structured input and output  
---

## **Subpart 15 — Build recommendations API**

**Goal:** Expose the core value to frontend.

### **Prompt 15**

Continue from the existing backend.

Already implemented:  
\- analytics services  
\- recommendation selector  
\- strategy history engine  
\- LLM explanation layer

Now create the recommendations API.

Requirements:  
Add API endpoints to:  
\- generate recommendations for a restaurant  
\- fetch current recommendations  
\- fetch blocked recommendations and reasons  
\- accept a recommendation  
\- reject a recommendation  
\- update strategy status  
\- record a measured outcome

Important:  
\- keep route handlers thin  
\- use service layer  
\- recommendation generation should be reproducible  
\- endpoints should support frontend dashboard use

Output:  
1\. file list  
2\. router code  
3\. service integration code  
4\. request/response schemas  
---

## **Subpart 16 — Build frontend app structure**

**Goal:** Create a clean demo flow.

### **Prompt 16**

Use the existing backend API contracts and generate the frontend app structure.

Context:  
This is a Next.js \+ TypeScript \+ Tailwind dashboard for Restaurant Growth Copilot.  
The backend already supports:  
\- CSV uploads  
\- analytics  
\- recommendations  
\- strategy history updates

Now create the frontend structure.

Requirements:  
Pages:  
\- dashboard overview  
\- menu insights  
\- inventory insights  
\- social insights  
\- recommendations  
\- strategy history  
\- upload data

Components:  
\- summary cards  
\- charts  
\- recommendation cards  
\- blocked recommendation panel  
\- strategy history timeline  
\- upload forms  
\- action buttons for accept/reject/status update

Important:  
\- clean, modern, judge-friendly  
\- easy to understand in a 2-minute demo  
\- use service clients to connect to backend APIs

Output:  
1\. file tree  
2\. page/component breakdown  
3\. frontend state/data flow plan

## **Subpart 17 — Build upload UI**

**Goal:** Let user onboard data.

### **Prompt 17**

Continue from the existing frontend app structure.

Now build the upload data page and components.

Requirements:  
\- CSV upload forms for menu, sales, inventory, recipe mapping, social posts  
\- success and error states  
\- progress indicators  
\- ingestion summary display  
\- restaurant selector or restaurant creation flow if needed

Important:  
\- align with backend upload endpoints already defined  
\- keep UX simple and hackathon-friendly

Output:  
1\. files to create  
2\. page code  
3\. reusable upload components  
4\. API service helpers  
---

## **Subpart 18 — Build dashboard overview**

**Goal:** Show top value instantly.

### **Prompt 18**

Continue from the existing frontend and backend API contracts.

Now build the main dashboard overview page.

Requirements:  
Display:  
\- revenue trend  
\- top-selling item  
\- lowest-performing item  
\- high-margin opportunities  
\- waste risk alert  
\- stockout alert  
\- best social opportunity  
\- top 3 recommendations

Important:  
\- use reusable chart and card components  
\- data should come from backend services  
\- design must be polished for demo use

Output:  
1\. files to create  
2\. page code  
3\. any shared components  
4\. notes on loading and empty states  
---

## **Subpart 19 — Build menu insights page**

### **Prompt 19**

Continue from the existing frontend.

Now build the menu insights page.

Requirements:  
Display:  
\- top and bottom sellers  
\- margin vs popularity matrix  
\- item pairings  
\- category performance  
\- item-level opportunity cards  
\- recommendation hooks for menu actions

Important:  
\- use data from backend analytics endpoints  
\- keep charts clean and understandable  
\- support clicking an item to view relevant recommendations and strategy history

Output:  
1\. files to create  
2\. page code  
3\. components  
4\. API hooks/service code  
---

## **Subpart 20 — Build inventory insights page**

### **Prompt 20**

Continue from the existing frontend.

Now build the inventory insights page.

Requirements:  
Display:  
\- ingredients at stockout risk  
\- overstock risks  
\- waste-prone ingredients  
\- projected days left  
\- ingredient-to-menu-item impact  
\- inventory-related recommendations

Important:  
\- align with backend inventory analytics and recommendation APIs  
\- design should highlight urgent actions clearly

Output:  
1\. files to create  
2\. page code  
3\. components  
4\. API integration helpers  
---

## **Subpart 21 — Build social insights page**

### **Prompt 21**

Continue from the existing frontend.

Now build the social insights page.

Requirements:  
Display:  
\- engagement by post type  
\- best day/time to post  
\- products worth featuring  
\- top content opportunities  
\- social-related recommendations  
\- draft caption preview panel if available

Important:  
\- use backend social analytics and explanation endpoints  
\- keep visuals simple and business-focused

Output:  
1\. files to create  
2\. page code  
3\. components  
4\. API service integration  
---

## **Subpart 22 — Build recommendations page**

### **Prompt 22**

Continue from the existing frontend and recommendation API.

Now build the recommendations page.

Requirements:  
Display:  
\- top ranked recommendations  
\- confidence  
\- urgency  
\- expected impact  
\- evidence panel  
\- blocked recommendations and blocked reasons  
\- actions: accept, reject, mark active, mark evaluating, mark successful, mark failed

Important:  
\- this is the core value page  
\- design recommendation cards so judges immediately understand that the system is evidence-based and not hallucinating  
\- show the relationship to strategy history where useful

Output:  
1\. files to create  
2\. page code  
3\. recommendation card components  
4\. status update flow  
---

## **Subpart 23 — Build strategy history page**

### **Prompt 23**

Continue from the existing frontend.

Now build the strategy history page.

Requirements:  
Display:  
\- strategy timeline  
\- current active strategies  
\- successful strategies  
\- failed strategies  
\- archived strategies  
\- cooldown information  
\- outcome metrics if available

Important:  
\- this page should make it obvious that the platform learns from past recommendations and avoids repetition  
\- support filtering by item, category, and status

Output:  
1\. files to create  
2\. page code  
3\. timeline/table components  
4\. API integration helpers  
---

## **Subpart 24 — Build AI chat assistant**

**Goal:** Natural interface, but grounded.

### **Prompt 24**

Continue from the full existing codebase.

Already implemented:  
\- analytics engines  
\- recommendation system  
\- strategy history  
\- LLM explanation layer  
\- frontend dashboard pages

Now build the AI chat assistant.

Requirements:  
The assistant should answer questions like:  
\- What menu items should I promote this weekend?  
\- Why is waste increasing?  
\- What has worked so far?  
\- Which strategies failed for fries?  
\- What should we test next?

Important:  
\- the chat assistant must use analytics, recommendations, and strategy history as context  
\- it must not invent unsupported recommendations  
\- it should cite structured evidence from the backend payloads  
\- it should reuse existing explanation logic where possible

Output:  
1\. files to create  
2\. backend chat service code  
3\. API endpoint  
4\. frontend chat component/page  
5\. prompt design showing how history and evidence are injected  
---

## **Subpart 25 — Build end-to-end integration tests**

### **Prompt 25**

Continue from the existing full codebase.

Now create end-to-end integration tests for the MVP.

Cover:  
\- CSV upload and parsing  
\- analytics generation  
\- strategy playbook matching  
\- strategy history filtering  
\- blocked repeated recommendations  
\- recommendation generation  
\- recommendation acceptance and lifecycle updates  
\- successful/failed strategy outcome recording  
\- chat assistant grounding on strategy history  
\- key frontend API integration tests if practical

Important:  
\- focus on the business-critical flows  
\- include at least one test case proving that a recently failed strategy is not recommended again  
\- include one test case proving that a successful strategy creates a scale-up follow-up instead of repetition

Output:  
1\. file list  
2\. backend test code  
3\. any sample fixtures  
4\. explanation of test coverage  
---

## **Subpart 26 — Final polish and demo mode**

### **Prompt 26**

Continue from the existing full-stack application.

Now add final polish for hackathon demo readiness.

Requirements:  
\- create a demo mode with seeded restaurant data  
\- create a one-click "Generate Growth Plan" flow  
\- improve empty states and loading states  
\- add polished labels and copy across the UI  
\- ensure recommendation evidence is readable  
\- add a compact executive summary panel  
\- add a sample weekly growth report page or export option if feasible

Important:  
\- do not break the deterministic recommendation architecture  
\- keep the demo smooth and easy to narrate in under 3 minutes

Output:  
1\. files to update  
2\. final polish code  
3\. demo flow summary  
4\. presenter notes for the product walkthrough

# **7\. How to feed previous strategy history into subsequent prompts**

After Prompt 11 onward, add a block like this to each new prompt:

Existing strategy-memory behavior already implemented:  
\- fixed strategy playbook exists  
\- strategy statuses: suggested, accepted, active, evaluating, successful, failed, archived  
\- cooldown logic exists  
\- active strategies are blocked from repetition  
\- recently failed strategies are blocked or deprioritized  
\- successful strategies may produce scale-up recommendations  
\- recommendations must include evidence and confidence

Preserve and extend this behavior.  
Do not replace it with free-form recommendation generation.

