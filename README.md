<p align="center"><img src="docs/assets/dailycash-banner.svg" alt="DailyCash — clarity for everyday business" width="100%"></p>

<p align="center"><strong>A lightweight business ledger built on Odoo 19 Community.</strong><br>Organize day-to-day cash activity across businesses, books, and partners.</p>

<p align="center"><img alt="Odoo 19" src="https://img.shields.io/badge/Odoo-19.0-714B67?style=flat-square"> <img alt="Python" src="https://img.shields.io/badge/Python-Odoo%20addons-3776AB?style=flat-square"> <img alt="Frontend" src="https://img.shields.io/badge/UI-Owl%20%2B%20SCSS-24836B?style=flat-square"></p>

## The idea

DailyCash makes everyday bookkeeping approachable for small teams. It brings cash-in and cash-out entries, payments, and outstanding amounts together in a focused interface, without requiring Odoo Accounting. It also includes an optional companion addon for SaaS deployments.

## What it does

- **Structure the work:** organize records into businesses and books, with customer and vendor profiles.
- **Record activity:** create cash-in and cash-out entries with line items, entry types, remarks, and payment methods.
- **Follow the numbers:** calculate entry totals, amounts paid, and balances due; browse entries through a custom dashboard and list views.
- **Share records:** generate entry and list reports with configurable report templates.
- **Work in a tailored interface:** use quick entry, global search, mobile navigation, and a branded sign-in experience.
- **Support a SaaS setup:** an optional companion addon handles subscription entitlements, user limits, and provisioner endpoints.

## Built with

| Layer | Technology |
| --- | --- |
| Application | Odoo 19 Community, Python, PostgreSQL |
| Interface | Odoo Owl components, JavaScript, XML, SCSS |
| Reports | Odoo QWeb |
| Addons | `cashbook` and `softobro_saas_subscription` |

The cashbook addon depends on Odoo's `web`, `mail`, and `auth_signup` modules; it does not depend on Accounting. The companion subscription addon retains its technical module name for compatibility and is separate from the ledger.

## Getting started

1. Set up Odoo 19 Community and PostgreSQL using your usual Odoo development environment.
2. Add this repository's `addons` directory to Odoo's `addons_path`, alongside Odoo's own addon directories.
3. Start Odoo, create a database, update the Apps list, and install **DailyCash** (`cashbook`).
4. Create a business and a book, then add entry types, partners, and entries.

For example, with paths and a database appropriate to your installation:

```bash
./odoo-bin -c /path/to/odoo.conf -d dailycash_dev -i cashbook --stop-after-init
```

The configuration must include this project's `addons` directory in `addons_path`. The subscription addon is optional and requires separate provisioning infrastructure; it is not a complete hosted SaaS deployment on its own. Review its configuration, domain, email defaults, and provisioner credentials before using it. The included placeholder master key must be replaced before any deployment.

## Project layout

```text
addons/
  cashbook/                       Ledger models, UI, reports, and tests
  softobro_saas_subscription/     Optional SaaS entitlement and provisioning addon
docs/assets/                      Project artwork
```

The [architecture notes](01_ARCHITECTURE.md) and [original specification](SOP%20%E2%80%94%20CashBook%20Module%20for%20Odoo%2019%20Community.md) provide design context; they are historical planning documents and may differ from the implementation.

## Testing

With a configured Odoo 19 development database, run the addon tests using Odoo's test runner:

```bash
./odoo-bin -c /path/to/odoo.conf -d dailycash_test -i cashbook --test-enable --stop-after-init
```

Use a disposable test database.

## License

Both addon manifests declare LGPL-3. Review the applicable license and ownership of all material before redistributing this project.
