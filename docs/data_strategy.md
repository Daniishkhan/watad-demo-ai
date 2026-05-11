# AridOS RFQ Copilot — Mock Data & Ingestion Strategy

## 1. Goal

The pilot needs reliable data for a smooth demo, but it should also show that the system can handle real procurement messiness.

The strategy is to use four layers:

1. Clean seeded tables for deterministic workflow behavior.
2. Messy CSV/spreadsheet data for normalization.
3. Public construction PDFs/pages for document ingestion and retrieval.
4. Synthetic supplier offers generated from deterministic rules.

## 2. Why Not Only Seeded Data?

Seeded demo data is useful, but by itself it can look artificial. The interview should show that the architecture can handle real-world inputs: inconsistent material names, mixed units, Arabic/English terms, missing fields, PDFs, pricing references, and unreliable source quality.

## 3. Data Layers

### Layer A — Clean Seed Data

Use for stable demo execution.

Files:

```text
data/seed/suppliers.csv
data/seed/supplier_materials.csv
data/seed/buyer_profiles.csv
data/seed/credit_policies.csv
data/seed/material_taxonomy.csv
data/seed/historical_orders.csv
```

### Layer B — Messy Operational Data

Use to demonstrate ingestion and normalization.

Files:

```text
data/messy/messy_supplier_catalog.csv
data/messy/messy_historical_orders.csv
data/messy/messy_material_aliases.csv
```

Include messy examples:

- `16mm steel bars`, `rebar`, `reinforcement steel`, `حديد تسليح`
- `MT`, `tons`, `طن`
- `Riyadh`, `Riyad`, `الرياض`
- `SAR 2,410`, `2410 SAR/MT`, `2.41k`
- duplicated supplier names
- missing delivery terms
- ambiguous payment terms like `later`, `credit`, `60d`

### Layer C — Public Reference Documents

Use to demonstrate PDF ingestion and RAG. Do not claim these are Watad supplier records.

Good source categories:

- Saudi construction material price statistics
- construction material specifications
- building material regulations
- cement and ready-mix product catalogs
- public tender/specification documents

Store a manifest:

```text
data/docs/public_source_manifest.csv
```

Fields:

```csv
source_id,title,url,source_type,usage,license_notes,downloaded_at
```

Usage labels:

- terminology
- specification_reference
- price_context
- demo_document_ingestion

### Layer D — Synthetic Supplier Offers

Generate from rules, not arbitrary LLM output.

Offer generation inputs:

- material base price
- city
- delivery distance
- supplier capacity
- delivery window
- payment-term premium
- reliability score
- split-delivery constraints

Outputs:

```text
data/generated/synthetic_offers.json
```

## 4. Production Migration Story

In real Watad production, replace mock sources with:

- supplier database
- RFQ history
- PO history
- invoices
- delivery records
- buyer credit profiles
- payment history
- approved vendor lists
- supplier catalogs
- contract terms
- user-uploaded documents

Production controls needed:

- RBAC and tenant isolation
- source-level permissions
- data freshness checks
- deduplication
- source attribution
- PII/commercial-data handling
- prompt-injection handling for uploaded docs
- human review for low-confidence normalization

## 5. Interview Line

Use this exact explanation:

> "For demo reliability, supplier availability and offers are seeded and deterministic. To show production readiness, I also include messy supplier/catalog data and public construction PDFs to exercise ingestion, normalization, and retrieval. In a real Watad deployment, those connectors would point to Watad's supplier, RFQ, PO, invoice, delivery, and credit systems."
