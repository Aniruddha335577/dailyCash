# 01 — SaaS Architecture & Module Boundaries

## 1. Purpose

This document defines the non-negotiable architecture and responsibility boundaries for the SaaS system.

It is specifically intended to be read **before implementing the CashBook module**.

The goal is to ensure that CashBook remains a lightweight business ledger and does not become responsible for SaaS subscription/package management or cPanel integration.

---

## 2. High-Level Architecture

The system follows this responsibility flow:

```text
                    cPanel
                      │
                      │ package update request
                      ▼
             ┌─────────────────────┐
             │ SaaS Package /      │
             │ Subscription Module │
             │                     │
             │ package_code        │
             │ restrictions        │
             │ feature values      │
             │ package metadata    │
             └──────────┬──────────┘
                        │
                        │ exposes applicable
                        │ restriction/value
                        ▼
             ┌─────────────────────┐
             │      CashBook       │
             │                     │
             │ Business creation   │
             │ checks applicable   │
             │ business limit      │
             └─────────────────────┘
```

The direction of responsibility is:

```text
cPanel
   ↓
SaaS Package / Subscription Module
   ↓
CashBook
```

CashBook must **not** communicate directly with cPanel.

---

## 3. Source of Truth

### cPanel

cPanel is the external source of truth for package configuration.

It may send package update information to the SaaS Package / Subscription module.

cPanel is outside the CashBook module.

### SaaS Package / Subscription Module

The SaaS Package / Subscription module is the Odoo-side owner of package information.

It is responsible for:

- Receiving package updates from cPanel
- Storing the current package configuration
- Storing package restrictions
- Storing feature values
- Maintaining package/subscription-related state
- Exposing applicable restrictions to other Odoo modules

### CashBook

CashBook is a consumer of package restrictions.

It does not own package information.

---

## 4. Strict Module Boundaries

### CashBook owns

CashBook owns:

- Businesses
- Books
- Entries
- Entry lines
- CashBook partners
- Entry types
- Payments
- Payment methods
- CashBook calculations
- CashBook-specific validation
- Enforcement of CashBook-related package restrictions

### SaaS Package / Subscription module owns

The SaaS Package / Subscription module owns:

- Package configuration
- Subscription information
- Package codes
- Package versions
- Package restrictions
- Feature values
- Package lifecycle
- Package updates received from cPanel

### cPanel integration belongs to

The SaaS Package / Subscription layer.

It does **not** belong to CashBook.

---

## 5. What CashBook Must NOT Implement

CashBook must NOT:

- Receive cPanel webhooks
- Call cPanel APIs
- Authenticate with cPanel
- Store cPanel credentials
- Store package records
- Store subscription records
- Store package codes
- Store subscription IDs
- Store plan names
- Store package versions
- Implement package upgrades
- Implement package downgrades
- Implement package billing
- Implement subscription lifecycle
- Maintain its own package limits
- Maintain a second source of truth for package restrictions

Do not add package-related fields to CashBook models merely to make the integration easier.

For example, CashBook Business should NOT contain fields such as:

```text
package_code
subscription_id
plan_name
max_businesses
package_version
subscription_status
```

The package module owns these values.

---

## 6. Restriction Consumption

CashBook may need to enforce restrictions supplied by the SaaS Package / Subscription module.

For example:

```text
Maximum number of CashBook businesses
```

The correct flow is:

```text
User
 │
 │ creates Business
 ▼
CashBook
 │
 │ asks package layer for applicable restriction
 ▼
SaaS Package / Subscription Module
 │
 │ returns applicable value/result
 ▼
CashBook
 │
 ├── allowed ──────► create Business
 │
 └── not allowed ──► ValidationError
```

CashBook should consume the restriction through the **existing interface provided by the SaaS Package / Subscription module**.

Do not assume a model or method name.

Before implementation, inspect the existing SaaS Package / Subscription module and identify its actual interface.

For example, a conceptual interface could look like:

```python
allowed = self.env['saas.package'].check_limit(
    feature='cashbook.business',
    current_count=current_count,
)
```

This is only an architectural example.

**Do not create this exact API unless it matches the existing system.**

---

## 7. No Duplicated Restriction Data

The restriction value must remain owned by the SaaS Package / Subscription module.

For example, if the package says:

```text
Maximum CashBook businesses = 5
```

CashBook should not store:

```python
max_businesses = 5
```

on `cashbook.business` or another CashBook configuration model.

Instead:

```text
SaaS Package Module
        │
        │ current restriction = 5
        ▼
CashBook
        │
        │ checks current business count
        ▼
Allow / Reject
```

This prevents two sources of truth.

---

## 8. Business Creation Rule

Business creation is the primary CashBook operation affected by the package architecture.

The expected flow is:

```text
1. User requests creation of a Business.
2. CashBook determines the current number of applicable businesses.
3. CashBook asks the SaaS Package / Subscription module for the applicable limit.
4. The SaaS Package module provides the current restriction/result.
5. CashBook compares the current usage with the restriction according to the package module's interface.
6. If allowed, Business is created.
7. If the limit is exceeded, Business creation is rejected.
```

CashBook must not:

- Modify the package
- Change the restriction
- Request a package upgrade
- Contact cPanel
- Create a subscription
- Bypass the package module

---

## 9. Dependency Direction

The architectural dependency should be:

```text
CashBook
    ↓
SaaS Package restriction interface
```

and:

```text
cPanel
    ↓
SaaS Package / Subscription Module
```

Avoid this:

```text
CashBook
    ↓
cPanel
```

Also avoid:

```text
cPanel
    ↓
CashBook
```

The CashBook module should remain isolated from the external provisioning/package infrastructure.

---

## 10. Existing SaaS Module Must Be Inspected First

Before implementing CashBook's package restriction integration:

1. Locate the existing SaaS Package / Subscription module.
2. Inspect its models.
3. Identify how package restrictions are stored.
4. Identify how feature/restriction values are exposed.
5. Identify whether an existing helper/service/API already exists.
6. Reuse the existing interface where possible.
7. Do not invent duplicate package models or fields.
8. Do not modify the package architecture unnecessarily.

If the existing module does not yet expose a clean restriction-checking interface, implement the **smallest appropriate interface in the SaaS Package module**, rather than moving package logic into CashBook.

---

## 11. Failure and Edge Cases

If the package module says the limit is exceeded:

```text
CashBook → ValidationError
```

with a clear user-facing message.

CashBook should not silently bypass the restriction.

If the package restriction interface is temporarily unavailable or incorrectly configured, do not silently assume an unlimited package unless that behavior is explicitly defined by the SaaS Package architecture.

The fallback/error behavior should be determined by the SaaS Package module's existing contract.

---

## 12. CashBook Independence

CashBook should remain conceptually understandable and maintainable without knowing how cPanel works.

A CashBook developer should only need to understand:

```text
"Ask the SaaS Package module whether this operation is allowed."
```

They should not need to understand:

```text
cPanel API
webhook authentication
HMAC
package synchronization
subscription billing
provisioning
```

Those concerns belong elsewhere.

---

## 13. Example

Suppose cPanel sends:

```text
package_code = BUSINESS_PRO
max_cashbook_businesses = 10
```

The SaaS Package / Subscription module stores this information.

CashBook should NOT receive the cPanel payload directly.

Instead:

```text
cPanel
   │
   │ package update
   ▼
SaaS Package Module
   │
   │ stores restriction
   │
   ▼
CashBook
   │
   │ "Can I create another Business?"
   ▼
SaaS Package Module
   │
   │ allowed / rejected
   ▼
CashBook
```

If 10 businesses already exist, the 11th creation should be rejected according to the package module's restriction.

CashBook does not need to know:

- Where the package came from
- How cPanel authenticated the request
- How the package was updated
- How the package is billed
- How the subscription is renewed

---

## 14. Non-Negotiable Rules

The following rules are architectural constraints:

### Rule 1

**cPanel is not a CashBook dependency.**

### Rule 2

**CashBook does not receive package updates directly from cPanel.**

### Rule 3

**The SaaS Package / Subscription module owns package data.**

### Rule 4

**CashBook must not duplicate package restriction values.**

### Rule 5

**CashBook consumes restrictions through the SaaS Package module's interface.**

### Rule 6

**Do not invent a package API without first inspecting the existing SaaS Package module.**

### Rule 7

**If a new restriction interface is required, add it to the SaaS Package layer rather than putting package logic into CashBook.**

### Rule 8

**CashBook must remain a lightweight standalone ledger module.**

### Rule 9

**Business limits are package restrictions, not CashBook configuration.**

### Rule 10

**Do not introduce unrelated SaaS, billing, provisioning, or cPanel functionality into CashBook.**

---

## 15. Relationship to the CashBook SOP

This file defines the **architecture and responsibility boundaries**.

The separate:

```text
02_CASHBOOK_SOP.md
```

defines the actual CashBook implementation requirements.

Cursor must read this file first.

Then it should read:

```text
02_CASHBOOK_SOP.md
```

and implement CashBook without violating the architecture defined here.

If the two documents appear to conflict, this architecture document takes precedence for:

- Module boundaries
- Package ownership
- Subscription ownership
- cPanel integration
- Restriction storage
- Restriction consumption
- Dependency direction

---

## 16. Cursor Implementation Instruction

Before writing CashBook code:

1. Read this document completely.
2. Inspect the existing SaaS Package / Subscription module.
3. Identify its actual restriction interface.
4. Confirm where the CashBook business-count restriction is stored.
5. Determine the cleanest way for CashBook to consume that restriction.
6. Do not duplicate package data in CashBook.
7. Do not create direct cPanel integration.
8. Then read `02_CASHBOOK_SOP.md`.
9. Implement CashBook according to the SOP.
10. Keep the implementation minimal and avoid unrelated features.

If the existing SaaS Package module does not provide the required interface, explain what is missing and propose the smallest architectural change before implementing a workaround inside CashBook.
