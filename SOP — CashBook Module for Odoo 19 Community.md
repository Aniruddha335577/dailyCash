# SOP — CashBook Module for Odoo 19 Community

## 1. Objective

Build a lightweight standalone **CashBook / Business Ledger** module for **Odoo 19 Community**.

The module is intended for a SaaS environment where one Odoo database/tenant may contain multiple businesses.

The purpose of the module is to provide simple business bookkeeping:

- Businesses
- Books
- Entries
- Entry lines
- Customers/vendors
- Entry types
- Payments
- Payment methods
- Basic totals and due amounts

This is **not** an accounting replacement and must not depend on Odoo Accounting.

The implementation should prioritize:

- Simplicity
- Low database/server overhead
- Minimal dependencies
- Clean Odoo architecture
- Maintainability
- Standard Odoo CRUD
- Standard Odoo search/filter/group-by
- Clear separation from the SaaS subscription/package system

Do not introduce functionality that is not explicitly required by this SOP.

---

# 2. Target Environment

Target:

- Odoo 19 Community
- Python compatible with Odoo 19
- PostgreSQL
- SaaS multi-tenant deployment

The module must work as an independent Odoo addon.

---

# 3. Module Dependency

The CashBook module should depend only on:

```text
base
```

Do NOT add dependencies on:

```text
account
sale
purchase
stock
product
hr
contacts
```

The module must not require Odoo Accounting.

Do not use:

```text
account.move
account.move.line
account.payment
account.journal
stock.move
product.product
uom.uom
```

unless a future requirement explicitly introduces such functionality.

---

# 4. SaaS Package Architecture — IMPORTANT

The CashBook module exists inside a larger SaaS architecture.

There is a **separate SaaS Package / Subscription module** responsible for package configuration and restrictions.

The architecture is:

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
                        │ exposes restriction/value
                        ▼
             ┌─────────────────────┐
             │      CashBook       │
             │                     │
             │ Business creation   │
             │ checks applicable   │
             │ business limit      │
             └─────────────────────┘
```

## 4.1 Responsibilities

### cPanel

cPanel is the external source of package configuration.

It sends package update information to the SaaS Package / Subscription module.

CashBook must know nothing about cPanel.

### SaaS Package / Subscription Module

This module is responsible for:

- Receiving package updates
- Storing package details
- Storing restrictions
- Maintaining the current package configuration
- Exposing package restrictions to other modules

### CashBook

CashBook is only responsible for enforcing the restriction relevant to CashBook.

For example:

```text
Maximum number of businesses
```

CashBook should ask the SaaS Package module for the applicable restriction before creating a new business.

Conceptually:

```python
allowed = self.env['saas.package'].check_limit(
    feature='cashbook.business',
    current_count=current_count,
)
```

However:

**DO NOT blindly implement the above exact model or method name.**

Inspect the existing SaaS Package / Subscription module and use its actual existing interface.

If the SaaS Package module already provides a service/helper/API for checking restrictions, use that.

Do not create a duplicate package system inside CashBook.

---

# 5. What CashBook MUST NOT Do

CashBook must NOT:

- Receive webhooks from cPanel
- Call cPanel APIs
- Store package records
- Store subscription records
- Store package codes
- Store subscription IDs
- Store plan names
- Store package versions
- Duplicate `max_businesses` as CashBook configuration
- Implement package lifecycle
- Implement package upgrades/downgrades
- Implement billing
- Implement payment for SaaS subscriptions
- Maintain a second source of truth for package restrictions

Do not add fields such as:

```text
package_code
subscription_id
plan_name
max_businesses
package_version
subscription_status
```

to the CashBook Business model.

The package system owns those concerns.

---

# 6. Business Creation and Package Restriction

When creating:

```text
cashbook.business
```

CashBook must determine whether creation is allowed according to the applicable SaaS package restriction.

Conceptually:

```text
User creates Business
        │
        ▼
CashBook checks current business count
        │
        ▼
CashBook asks SaaS Package module
for applicable business limit
        │
        ├── Allowed
        │      │
        │      ▼
        │   Create Business
        │
        └── Limit exceeded
               │
               ▼
          ValidationError
```

The actual implementation must use the existing SaaS Package module interface.

Do not duplicate the restriction value inside CashBook.

If the SaaS Package module is not currently available in the development environment, isolate the integration cleanly rather than inventing a fake package system.

---

# 7. Functional Hierarchy

The data hierarchy is:

```text
Odoo Database / SaaS Tenant
│
├── Business 1
│   ├── Book A
│   │   ├── Entry
│   │   │   ├── Entry Lines
│   │   │   └── Payments
│   │   └── Entry
│   │
│   └── Book B
│
├── Business 2
│
└── Business N
```

Relationships:

```text
Business
  └── 1:N Books
        └── 1:N Entries
              ├── N:1 Entry Type
              ├── N:1 Partner
              ├── 1:N Entry Lines
              └── 1:N Payments
                        └── N:1 Payment Method
```

---

# 8. Models

Create these models:

```text
cashbook.business
cashbook.book
cashbook.entry.type
cashbook.partner
cashbook.entry
cashbook.entry.line
cashbook.payment.method
cashbook.payment
```

---

# 9. Business Model

Technical name:

```text
cashbook.business
```

Purpose:

Represents one business within the Odoo tenant.

Fields:

```python
name = fields.Char(required=True)

currency_id = fields.Many2one(
    'res.currency',
    required=True,
)

active = fields.Boolean(default=True)
```

Business does NOT contain:

- Users
- Members
- Roles
- Permissions
- Package information
- Subscription information

There is no custom business membership system in V1.

Use standard Odoo model access rules.

---

# 10. Business Currency

Each Business has exactly one currency.

All child records inherit the Business currency.

Therefore:

```text
Business
   ↓
Book
   ↓
Entry
   ↓
Entry Line / Payment
```

must use the same currency.

Users must not manually select a different currency on individual entries, lines, or payments.

Use related currency fields where appropriate.

Do not implement:

- Currency conversion
- Exchange rates
- Multi-currency entries
- Currency conversion reports

in V1.

---

# 11. Book Model

Technical name:

```text
cashbook.book
```

Fields:

```python
business_id = fields.Many2one(
    'cashbook.business',
    required=True,
    ondelete='cascade',
)

name = fields.Char(required=True)

description = fields.Text()

active = fields.Boolean(default=True)
```

Requirements:

- A business can have unlimited books.
- There is no package restriction on number of books.
- Books belong to exactly one Business.
- Deleting a Business cascades to its Books.

Do not implement book limits.

---

# 12. Entry Type Model

Technical name:

```text
cashbook.entry.type
```

Entry Type must be a normal database model.

Do NOT implement it as a hardcoded selection field.

Fields:

```python
name = fields.Char(required=True)

description = fields.Text()

active = fields.Boolean(default=True)
```

Examples:

```text
Sale
Purchase
Expense
Income
Salary
Transport
Other
```

These are examples only.

Users must be able to:

- Create
- Edit
- Archive
- View

Entry Types.

If an Entry Type is already used by existing entries, do not allow destructive deletion that would break those records.

Prefer archiving.

---

# 13. Partner Model

Technical name:

```text
cashbook.partner
```

This is a lightweight CashBook-specific partner/customer/vendor model.

Do NOT use:

```text
res.partner
```

in V1.

Fields:

```python
name = fields.Char(required=True)

partner_type = fields.Selection(
    [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('both', 'Both'),
    ],
    required=True,
    default='customer',
)

phone = fields.Char()

notes = fields.Text()

active = fields.Boolean(default=True)
```

One partner may be both:

```text
Customer
Vendor
```

Do not create separate Customer and Vendor models.

Do not add unnecessary CRM/contact/accounting functionality.

---

# 14. Entry Model

Technical name:

```text
cashbook.entry
```

Fields:

```python
book_id = fields.Many2one(
    'cashbook.book',
    required=True,
    ondelete='cascade',
)

business_id = fields.Many2one(
    'cashbook.business',
    related='book_id.business_id',
    store=True,
    index=True,
)

entry_type_id = fields.Many2one(
    'cashbook.entry.type',
    required=True,
)

partner_id = fields.Many2one(
    'cashbook.partner',
)

entry_datetime = fields.Datetime(
    required=True,
    default=fields.Datetime.now,
)

line_ids = fields.One2many(
    'cashbook.entry.line',
    'entry_id',
)

payment_ids = fields.One2many(
    'cashbook.payment',
    'entry_id',
)

total_amount = fields.Monetary(
    compute='_compute_amounts',
    store=True,
)

paid = fields.Monetary(
    compute='_compute_amounts',
    store=True,
)

due = fields.Monetary(
    compute='_compute_amounts',
    store=True,
)

currency_id = fields.Many2one(
    'res.currency',
    related='business_id.currency_id',
    store=True,
)

remarks = fields.Text()
```

---

# 15. Entry Workflow

Entries use simple CRUD.

There is NO:

```text
Draft
Posted
Cancelled
Approved
```

workflow.

An entry can be:

- Created
- Edited
- Deleted

according to normal Odoo access rights.

Do not implement accounting posting.

---

# 16. Entry Date

Entries can be backdated freely.

There should be:

- No date lock
- No warning
- No approval
- No restriction against old dates

Users may enter any valid date/time.

---

# 17. Entry Lines

Technical name:

```text
cashbook.entry.line
```

Fields:

```python
entry_id = fields.Many2one(
    'cashbook.entry',
    required=True,
    ondelete='cascade',
)

product_name = fields.Char(
    required=True,
)

product_price = fields.Monetary(
    required=True,
)

quantity = fields.Float(
    required=True,
    default=1.0,
)

total_price = fields.Monetary(
    compute='_compute_total_price',
    store=True,
)

uom = fields.Char()

description = fields.Text()

currency_id = fields.Many2one(
    'res.currency',
    related='entry_id.currency_id',
    store=True,
)
```

---

# 18. Product / Item Design

`product_name` must be free text.

Do NOT use:

```text
product.product
```

Do not depend on the Inventory or Product modules.

The CashBook module is a simple ledger and does not manage inventory.

Example:

```text
product_name = "Office Chair"
product_price = 5000
quantity = 2
```

---

# 19. Entry Line Calculation

Formula:

```text
total_price = product_price × quantity
```

Example:

```text
Product price = 500
Quantity = 3

Total = 1500
```

Validation:

```text
quantity > 0
product_price >= 0
```

Do not allow negative quantities in V1.

Do not implement refunds through negative quantities.

---

# 20. Entry Total

Entry total is calculated from its lines:

```text
Entry Total =
SUM(all entry line total_price)
```

Users must not manually enter or override:

```text
total_amount
```

It must be computed.

---

# 21. Payment Method Model

Technical name:

```text
cashbook.payment.method
```

Payment methods are **global/common to the Odoo database**.

They are NOT per Business.

Fields:

```python
name = fields.Char(required=True)

description = fields.Text()

active = fields.Boolean(default=True)
```

The module should provide default payment methods:

```text
Cash
Bank
bKash
Nagad
Card
Other
```

These are default records only.

Users can:

- Create payment methods
- Edit payment methods
- Archive payment methods
- Delete unused payment methods

If a payment method is already used by payments, destructive deletion should be prevented.

Use:

```text
ondelete='restrict'
```

where appropriate.

---

# 22. Payment Model

Technical name:

```text
cashbook.payment
```

Fields:

```python
entry_id = fields.Many2one(
    'cashbook.entry',
    required=True,
    ondelete='cascade',
)

payment_method_id = fields.Many2one(
    'cashbook.payment.method',
    required=True,
    ondelete='restrict',
)

amount = fields.Monetary(
    required=True,
)

payment_datetime = fields.Datetime(
    required=True,
    default=fields.Datetime.now,
)

currency_id = fields.Many2one(
    'res.currency',
    related='entry_id.currency_id',
    store=True,
)

remarks = fields.Text()
```

---

# 23. Payment Design

Payments are separate records.

Do NOT store a single payment amount directly on the Entry.

Reason:

One Entry may have:

```text
Cash       3000
bKash      2000
Bank       5000
```

for a total of:

```text
10000
```

Payments can also be added later.

Example:

```text
September 1
Entry Total = 10000

Payment:
Cash = 3000

Paid = 3000
Due = 7000
```

Later:

```text
September 10
Payment:
bKash = 4000

Paid = 7000
Due = 3000
```

Later:

```text
September 20
Payment:
Bank = 3000

Paid = 10000
Due = 0
```

---

# 24. Payment Date

Payment has its own datetime:

```text
payment_datetime
```

This must be independent from:

```text
entry_datetime
```

Payments may also be backdated freely.

No payment date locks or warnings.

---

# 25. Payment Calculation

Entry paid amount:

```text
paid =
SUM(all payment.amount)
```

Entry due:

```text
due =
total_amount - paid
```

Example:

```text
Total = 10000
Paid = 7000
Due = 3000
```

---

# 26. Payment Validation

V1 should enforce:

```text
amount > 0
```

and:

```text
total payments <= entry total
```

Therefore, an entry with:

```text
Total = 10000
```

cannot have payments totaling:

```text
11000
```

The system should raise an appropriate `ValidationError`.

Do not implement overpayment/credit-balance behavior in V1.

---

# 27. Minimum Entry Requirements

An Entry should contain at least one Entry Line before it can be saved.

Therefore:

```text
Entry
  └── At least 1 Entry Line
```

is required.

Payments are optional.

This allows:

```text
Total = 10000
Paid = 0
Due = 10000
```

---

# 28. Core Calculation Summary

The complete calculation model is:

```text
Entry Line Total
    = quantity × product_price

Entry Total
    = SUM(entry line totals)

Entry Paid
    = SUM(payment amounts)

Entry Due
    = Entry Total - Entry Paid
```

These values should be computed automatically.

Store computed totals where appropriate so that they can be efficiently searched, grouped and reported.

Do not create unnecessary custom calculation infrastructure.

---

# 29. Data Integrity

Enforce the following:

### Business

```text
name required
currency required
```

### Book

```text
business required
name required
```

### Entry

```text
book required
entry type required
entry datetime required
at least one line required
```

### Entry Line

```text
product_name required
product_price >= 0
quantity > 0
```

### Payment

```text
entry required
payment method required
amount > 0
total payments <= entry total
```

### Relationships

Ensure:

```text
Book → Business
Entry → Book
Entry Line → Entry
Payment → Entry
Payment → Payment Method
```

remain logically consistent.

---

# 30. Deletion Behavior

Deleting a Business:

```text
Business
 └── Books
      └── Entries
           ├── Lines
           └── Payments
```

should cascade where explicitly appropriate.

Deleting an Entry:

```text
Entry
 ├── Lines
 └── Payments
```

should cascade to its lines and payments.

Payment Method deletion:

- Allowed if unused
- Blocked if referenced by existing payments
- Archiving remains available

Entry Type deletion:

- Do not break existing entries
- Prefer archive/block deletion if already referenced

---

# 31. No Audit / Approval System in V1

Do not implement:

- Approval workflow
- Audit log
- Immutable ledger
- Change history
- Reconciliation
- Journal posting
- Accounting locks

unless explicitly requested later.

V1 is intentionally a simple CRUD-based ledger.

---

# 32. Security

Create standard Odoo model access rules.

There is no custom Business membership/role system in V1.

Do not create:

```text
cashbook.business.member
cashbook.business.role
cashbook.business.user
```

or similar models.

Use standard Odoo model-level access control.

If future requirements introduce business-specific users and permissions, that should be designed separately.

---

# 33. Views

Create standard Odoo views.

Each major model should have appropriate:

- List view
- Form view
- Search view

where useful.

Use standard Odoo UI patterns.

---

# 34. Entry List View

Recommended columns:

```text
Date/Time
Book
Entry Type
Partner
Total
Paid
Due
Currency
```

The list should make it easy to understand the financial status of each entry.

---

# 35. Entry Form View

The Entry form should allow the user to manage:

### Header

```text
Book
Entry Type
Partner
Date/Time
```

### Entry Lines

Inline editable One2many list:

```text
Item
Price
Quantity
UOM
Total
Description
```

### Payments

Inline editable One2many list:

```text
Payment Method
Amount
Payment Date/Time
Remarks
```

### Totals

Display:

```text
Total
Paid
Due
```

These must be read-only computed values.

---

# 36. Search / Filters / Group By

Use standard Odoo search functionality.

Entries should support searching/filtering/grouping by:

```text
Business
Book
Entry Type
Partner
Date
Create User
```

Useful date filters:

```text
Today
This Week
This Month
Previous Month
```

Use standard Odoo mechanisms instead of custom reporting infrastructure.

---

# 37. Menus

Suggested menu structure:

```text
CashBook
│
├── Businesses
├── Books
├── Entries
├── Partners
│
└── Configuration
    ├── Entry Types
    └── Payment Methods
```

Keep the menu structure simple.

Do not add unnecessary dashboards or reporting menus in V1.

---

# 38. Suggested Module Structure

Use:

```text
cashbook/
├── __init__.py
├── __manifest__.py
│
├── models/
│   ├── __init__.py
│   ├── business.py
│   ├── book.py
│   ├── entry_type.py
│   ├── partner.py
│   ├── entry.py
│   ├── entry_line.py
│   ├── payment_method.py
│   └── payment.py
│
├── views/
│   ├── business_views.xml
│   ├── book_views.xml
│   ├── entry_type_views.xml
│   ├── partner_views.xml
│   ├── entry_views.xml
│   ├── payment_method_views.xml
│   └── menus.xml
│
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
│
└── data/
    └── payment_method_data.xml
```

You may adjust the exact file organization if Odoo 19 best practices or the existing project structure justify it, but do not unnecessarily increase the module complexity.

---

# 39. Naming

Use the module prefix:

```text
cashbook
```

Examples:

```text
cashbook.business
cashbook.book
cashbook.entry
cashbook.entry.line
cashbook.payment
```

Use clear Python field names.

Avoid abbreviations unless they are standard Odoo conventions.

---

# 40. ORM Design

Use normal Odoo ORM:

```python
models.Model
fields.Many2one
fields.One2many
fields.Char
fields.Text
fields.Selection
fields.Float
fields.Monetary
fields.Boolean
fields.Datetime
```

Use:

```python
@api.depends(...)
```

for computed fields.

Prefer normal ORM constraints:

```python
@api.constrains(...)
```

where appropriate.

Do not implement raw SQL unless there is a demonstrated performance requirement.

---

# 41. Computed Fields

Use stored computed fields for:

```text
total_amount
paid
due
total_price
```

where this improves search/group-by/reporting performance.

Ensure dependency declarations correctly include the relevant One2many fields.

For example, changes to Entry Lines must recompute Entry totals.

Changes to Payments must recompute Entry paid/due.

---

# 42. Package Restriction Integration

The package restriction check should be isolated from the core CashBook business model logic as much as practical.

The CashBook module should have a clean dependency/interface boundary:

```text
CashBook
    ↓
SaaS Package restriction interface
```

not:

```text
CashBook
    ↓
cPanel
```

and not:

```text
CashBook
    ↓
duplicated package fields
```

If an integration adapter/helper is necessary, keep it small and clearly named.

Do not embed assumptions about the cPanel API.

---

# 43. Package Restriction Failure Behavior

If the SaaS Package module determines that the Business limit has been reached:

```text
raise ValidationError
```

with a clear user-facing message.

Do not silently create the Business.

Do not modify package data.

Do not attempt to upgrade the package.

Do not contact cPanel.

CashBook only enforces the result supplied by the package system.

---

# 44. Avoid Overengineering

Do NOT add the following in V1:

```text
Accounting integration
Inventory integration
Invoices
Sales Orders
Purchase Orders
Stock
Product catalog
Multi-currency
Currency conversion
Tax engine
Fiscal positions
Payment gateways
Bank reconciliation
Accounting journals
Approval workflow
Business membership
Business-specific roles
Subscription management
Package management
cPanel integration
Complex dashboards
Complex reporting engine
Audit framework
```

The goal is a small, maintainable CashBook.

---

# 45. Expected Example

Example Business:

```text
Business:
    ABC Trading

Currency:
    BDT
```

Books:

```text
Main Book
Office Book
```

Entry:

```text
Book:
    Main Book

Entry Type:
    Sale

Partner:
    Rahim

Date:
    2026-09-01
```

Lines:

```text
Item             Price     Qty     Total
------------------------------------------------
Office Chair     5000      2       10000
```

Entry total:

```text
10000 BDT
```

Payments:

```text
Cash       3000 BDT
bKash      2000 BDT
```

Therefore:

```text
Total = 10000
Paid  = 5000
Due   = 5000
```

Later:

```text
Bank = 5000 BDT
```

Then:

```text
Total = 10000
Paid  = 10000
Due   = 0
```

---

# 46. Implementation Order

Implement in this order:

### Phase 1 — Module foundation

Create:

```text
__manifest__.py
__init__.py
models/
security/
views/
data/
```

Confirm the module installs successfully.

### Phase 2 — Core master data

Implement:

```text
Business
Book
Entry Type
Partner
Payment Method
```

### Phase 3 — Transactions

Implement:

```text
Entry
Entry Line
Payment
```

### Phase 4 — Calculations

Implement:

```text
line total
entry total
paid
due
```

### Phase 5 — Validation

Implement:

```text
positive quantity
non-negative price
positive payment
payment <= total
minimum one entry line
```

### Phase 6 — UI

Implement:

```text
menus
list views
form views
search views
inline entry lines
inline payments
```

### Phase 7 — SaaS restriction integration

Connect Business creation to the existing SaaS Package / Subscription module.

Do not implement a second package system.

### Phase 8 — Testing

Test the complete CRUD and calculation behavior.

---

# 47. Required Test Scenarios

Test at minimum:

## Business

```text
Create Business
Edit Business
Archive Business
Delete Business
```

Verify currency is required.

Verify package restriction is checked during creation.

---

## Books

```text
Create unlimited Books under one Business
Edit Book
Archive Book
Delete Book
```

---

## Entry Types

```text
Create
Edit
Archive
Delete unused
Prevent destructive deletion when referenced
```

---

## Partners

Test:

```text
Customer
Vendor
Both
```

---

## Entry

Create an entry with:

```text
1 line
Multiple lines
No payment
```

Verify totals.

---

## Payments

Test:

```text
One payment
Multiple payments
Different payment methods
Payment added later
Backdated payment
```

Verify:

```text
Paid
Due
```

---

## Overpayment

Attempt:

```text
Entry Total = 10000
Payments = 11000
```

Expected:

```text
ValidationError
```

---

## Backdating

Create:

```text
Entry dated in the past
Payment dated in the past
```

Expected:

```text
Allowed
```

No warning.

---

## Currency

Verify:

```text
Business currency = BDT
Entry currency = BDT
Line currency = BDT
Payment currency = BDT
```

Users must not be able to select another currency.

---

## Package Limit

Test:

```text
Current business count < package limit
```

Expected:

```text
Business creation succeeds
```

Then:

```text
Current business count = package limit
```

Expected:

```text
Business creation blocked
```

Verify CashBook itself does not store duplicate package information.

---

# 48. Code Quality Requirements

Code should follow normal Odoo conventions.

Requirements:

- Clear model names
- Clear field names
- Small methods
- No duplicated business logic
- No unnecessary abstraction
- No raw SQL without justification
- No unnecessary dependencies
- No unused imports
- No dead code
- No hardcoded package limits
- No hardcoded business limits
- No cPanel logic

Add comments only where they clarify non-obvious architecture or behavior.

Do not fill the code with unnecessary comments.

---

# 49. Important Architectural Rule

The most important separation is:

```text
cPanel
   ↓
SaaS Package Module
   ↓
CashBook
```

NOT:

```text
cPanel
   ↓
CashBook
```

and NOT:

```text
cPanel
   ↓
CashBook package fields
```

The SaaS Package module is the owner of package configuration.

CashBook is only a consumer of the applicable restriction.

---

# 50. Final Acceptance Criteria

The implementation is complete when:

1. CashBook installs on Odoo 19 Community.
2. The module has only the necessary dependency on `base`.
3. Business → Book → Entry hierarchy works.
4. Business has exactly one currency.
5. Businesses can contain unlimited Books.
6. Entry Types are user-manageable records.
7. Partners are lightweight CashBook records.
8. Entries support multiple lines.
9. Entry line totals calculate correctly.
10. Entries calculate total, paid and due correctly.
11. Entries support multiple payments.
12. Payments can be added later.
13. Payments can use different payment methods.
14. Payment methods are global.
15. Backdated entries are allowed.
16. Backdated payments are allowed.
17. Overpayment is rejected.
18. An Entry requires at least one line.
19. Standard Odoo CRUD works.
20. Standard Odoo search/filter/group-by works.
21. No Accounting dependency exists.
22. No Inventory dependency exists.
23. No Product dependency exists.
24. No custom Business membership system exists.
25. No package/subscription data is duplicated in CashBook.
26. CashBook does not communicate directly with cPanel.
27. Business creation obtains its applicable restriction from the existing SaaS Package module.
28. Package restrictions are enforced without CashBook becoming responsible for package management.
29. The implementation remains lightweight and maintainable.

---

# 51. Instruction to Cursor

Before writing code:

1. Inspect the existing Odoo 19 project structure.
2. Inspect the existing SaaS Package / Subscription module and identify its actual model/service/interface for package restrictions.
3. Do not assume the model or method names shown in this SOP are already present.
4. Identify the cleanest integration point for checking the Business limit.
5. Confirm that CashBook will not duplicate package information.
6. Then implement the CashBook module according to this SOP.
7. Do not add features outside this specification.
8. If an architectural conflict is discovered, stop and explain the conflict before introducing a workaround.

The final implementation should be a **small standalone CashBook module with a clean one-way dependency on the SaaS Package restriction interface**, while keeping cPanel/package-management concerns completely outside CashBook.