from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCashbook(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency = cls.env.ref("base.USD")
        cls.business = cls.env["cashbook.business"].create({
            "name": "ABC Trading",
            "currency_id": cls.currency.id,
        })
        cls.book = cls.env["cashbook.book"].create({
            "business_id": cls.business.id,
            "name": "Main Book",
        })
        cls.entry_type = cls.env["cashbook.entry.type"].create({"name": "Sale"})
        cls.partner = cls.env["cashbook.partner"].create({
            "name": "Rahim",
            "partner_type": "customer",
        })
        cls.payment_method_cash = cls.env["cashbook.payment.method"].search(
            [("name", "=", "Cash")], limit=1
        )

    def _create_entry(self, lines=None, payments=None):
        line_commands = lines or [(0, 0, {
            "product_name": "Office Chair",
            "product_price": 5000,
            "quantity": 2,
        })]
        vals = {
            "book_id": self.book.id,
            "entry_type_id": self.entry_type.id,
            "partner_id": self.partner.id,
            "line_ids": line_commands,
        }
        if payments:
            vals["payment_ids"] = payments
        return self.env["cashbook.entry"].create(vals)

    def test_bdt_currency_is_active(self):
        bdt = self.env.ref("base.BDT")
        self.assertTrue(bdt.active)

    def test_business_can_use_bdt(self):
        bdt = self.env.ref("base.BDT")
        business = self.env["cashbook.business"].create({
            "name": "BDT Business",
            "currency_id": bdt.id,
        })
        self.assertEqual(business.currency_id, bdt)

    def test_business_currency_defaults_to_company(self):
        business = self.env["cashbook.business"].create({"name": "Default Currency Co"})
        self.assertTrue(business.currency_id)

    def test_business_profile_fields(self):
        business = self.env["cashbook.business"].create({
            "name": "Acme Trading",
            "legal_name": "Acme Trading Ltd.",
            "address_line_1": "12 Market Street",
            "address_line_2": "Floor 3",
            "city": "Dhaka",
            "zip": "1207",
            "phone_1": "+8801712345678",
            "phone_2": "+8801812345678",
            "email": "hello@acme.test",
            "website": "https://acme.test",
            "tax_id": "VAT-123456",
            "registration_number": "TRAD/2020/001",
            "invoice_footer": "Thank you for your business.",
        })
        self.assertEqual(business.legal_name, "Acme Trading Ltd.")
        self.assertEqual(business.email, "hello@acme.test")
        self.assertEqual(business.tax_id, "VAT-123456")

    def test_business_email_validation(self):
        with self.assertRaises(ValidationError):
            self.env["cashbook.business"].create({
                "name": "Bad Email Co",
                "email": "not-an-email",
            })

    def test_unlimited_books_per_business(self):
        books = self.env["cashbook.book"].create([
            {"business_id": self.business.id, "name": f"Book {i}"}
            for i in range(5)
        ])
        self.assertEqual(len(books), 5)

    def test_book_contact_fields(self):
        book = self.env["cashbook.book"].create({
            "business_id": self.business.id,
            "name": "Branch Book",
            "phone_1": "+8801712345678",
            "phone_2": "+8801812345678",
            "email": "branch@acme.test",
        })
        self.assertEqual(book.email, "branch@acme.test")
        self.assertEqual(book.phone_1, "+8801712345678")

    def test_book_email_validation(self):
        with self.assertRaises(ValidationError):
            self.env["cashbook.book"].create({
                "business_id": self.business.id,
                "name": "Bad Email Book",
                "email": "not-an-email",
            })

    def test_entry_line_total(self):
        entry = self._create_entry()
        self.assertEqual(entry.total_amount, 10000)
        self.assertEqual(entry.paid, 0)
        self.assertEqual(entry.due, 10000)

    def test_entry_requires_at_least_one_line(self):
        with self.assertRaises(ValidationError):
            self.env["cashbook.entry"].create({
                "book_id": self.book.id,
                "entry_type_id": self.entry_type.id,
            })

    def test_multiple_payments(self):
        entry = self._create_entry(payments=[
            (0, 0, {
                "payment_method_id": self.payment_method_cash.id,
                "amount": 3000,
            }),
            (0, 0, {
                "payment_method_id": self.payment_method_cash.id,
                "amount": 2000,
            }),
        ])
        self.assertEqual(entry.paid, 5000)
        self.assertEqual(entry.due, 5000)

        self.env["cashbook.payment"].create({
            "entry_id": entry.id,
            "payment_method_id": self.payment_method_cash.id,
            "amount": 5000,
        })
        entry.invalidate_recordset()
        self.assertEqual(entry.paid, 10000)
        self.assertEqual(entry.due, 0)

    def test_overpayment_rejected(self):
        entry = self._create_entry()
        with self.assertRaises(ValidationError):
            self.env["cashbook.payment"].create({
                "entry_id": entry.id,
                "payment_method_id": self.payment_method_cash.id,
                "amount": 11000,
            })

    def test_backdated_entry_and_payment(self):
        past = datetime.now() - timedelta(days=30)
        entry = self._create_entry()
        entry.write({"entry_datetime": past})
        payment = self.env["cashbook.payment"].create({
            "entry_id": entry.id,
            "payment_method_id": self.payment_method_cash.id,
            "amount": 1000,
            "payment_datetime": past,
        })
        self.assertEqual(entry.entry_datetime.date(), past.date())
        self.assertEqual(payment.payment_datetime.date(), past.date())

    def test_currency_inherited_from_business(self):
        entry = self._create_entry()
        line = entry.line_ids[0]
        payment = self.env["cashbook.payment"].create({
            "entry_id": entry.id,
            "payment_method_id": self.payment_method_cash.id,
            "amount": 1000,
        })
        self.assertEqual(entry.currency_id, self.business.currency_id)
        self.assertEqual(line.currency_id, self.business.currency_id)
        self.assertEqual(payment.currency_id, self.business.currency_id)

    def test_entry_type_deletion_blocked_when_used(self):
        entry = self._create_entry()
        self.assertTrue(entry.entry_type_id)
        with self.assertRaises(Exception):
            self.entry_type.unlink()

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValidationError):
            self._create_entry(lines=[(0, 0, {
                "product_name": "Item",
                "product_price": 100,
                "quantity": -1,
            })])

    def test_partner_types(self):
        vendor = self.env["cashbook.partner"].create({
            "name": "Vendor Co",
            "partner_type": "vendor",
        })
        customer = self.env["cashbook.partner"].create({
            "name": "Customer Co",
            "partner_type": "customer",
        })
        self.assertEqual(vendor.partner_type, "vendor")
        self.assertEqual(customer.partner_type, "customer")

    def test_entry_direction_defaults_to_cash_in(self):
        entry = self._create_entry()
        self.assertEqual(entry.direction, "in")

    def test_cash_out_entry(self):
        entry = self._create_entry()
        entry.write({"direction": "out"})
        self.assertEqual(entry.direction, "out")
        self.assertEqual(entry.due, entry.total_amount)

    def test_entry_reference_auto_generated(self):
        entry = self._create_entry()
        self.assertTrue(entry.name)
        self.assertNotIn(entry.name, ("New", "/"))
        self.assertRegex(entry.name, r"^CB/\d{4}/\d+$")

    def test_entry_references_are_unique(self):
        first = self._create_entry()
        second = self._create_entry()
        self.assertNotEqual(first.name, second.name)

    def test_backdated_entry_gets_reference(self):
        past = datetime.now() - timedelta(days=45)
        entry = self.env["cashbook.entry"].create({
            "book_id": self.book.id,
            "entry_type_id": self.entry_type.id,
            "partner_id": self.partner.id,
            "entry_datetime": past,
            "line_ids": [(0, 0, {
                "product_name": "Backdated item",
                "product_price": 100,
                "quantity": 1,
            })],
        })
        self.assertTrue(entry.name)
        self.assertRegex(entry.name, r"^CB/\d{4}/\d+$")
        self.assertEqual(entry.entry_datetime.date(), past.date())

    def test_entry_reference_cannot_be_changed(self):
        entry = self._create_entry()
        original = entry.name
        entry.write({"name": "CB/2099/99999"})
        self.assertEqual(entry.name, original)

    def test_assign_missing_references_backfills_placeholders(self):
        entry = self._create_entry()
        entry.with_context(allow_entry_name_update=True).write({"name": "New"})
        self.env["cashbook.entry"]._assign_missing_references()
        entry.invalidate_recordset(["name"])
        self.assertNotEqual(entry.name, "New")
        self.assertRegex(entry.name, r"^CB/\d{4}/\d+$")

    def test_report_template_default_is_unique(self):
        default = self.env.ref("cashbook.report_template_default")
        with self.assertRaises(ValidationError):
            self.env["cashbook.report.template"].create({
                "name": "Another Default",
                "is_default": True,
            })
        self.assertTrue(default.is_default)

    def test_entry_gets_default_report_template(self):
        entry = self._create_entry()
        default = self.env["cashbook.report.template"]._get_default_template()
        self.assertTrue(default)
        self.assertEqual(entry.report_template_id, default)

    def test_report_business_branding_from_related_business(self):
        self.business.write({
            "logo": False,
            "address_line_1": "12 Market Street",
            "city": "Dhaka",
            "phone_1": "+8801712345678",
            "email": "hello@acme.test",
        })
        entry = self._create_entry()
        business = entry.get_report_business()
        self.assertEqual(business, self.business)
        lines = business._get_report_address_lines()
        self.assertIn("12 Market Street", lines)
        self.assertIn("Dhaka", lines[1])

    def test_effective_report_template_fallback(self):
        entry = self._create_entry()
        entry.report_template_id = False
        default = self.env["cashbook.report.template"]._get_default_template()
        self.assertEqual(entry.get_effective_report_template(), default)

    def test_report_template_color_validation(self):
        with self.assertRaises(ValidationError):
            self.env["cashbook.report.template"].create({
                "name": "Bad Color",
                "primary_color": "not-a-color",
            })

    def test_format_report_amount_uses_currency_code(self):
        bdt = self.env.ref("base.BDT")
        self.business.write({"currency_id": bdt.id})
        entry = self._create_entry()
        formatted = entry.format_report_amount(900)
        self.assertIn("BDT", formatted)
        self.assertNotIn("৳", formatted)
        self.assertRegex(formatted, r"900(\.00)? BDT")

    def test_format_report_amount_value_omits_currency_code(self):
        bdt = self.env.ref("base.BDT")
        self.business.write({"currency_id": bdt.id})
        entry = self._create_entry()
        formatted = entry.format_report_amount_value(90)
        self.assertNotIn("BDT", formatted)
        self.assertRegex(formatted, r"90(\.00)?")

    def test_business_report_branding_helpers(self):
        self.business.write({
            "name": "Pixel Mart",
            "legal_name": "Creative design house",
            "address_line_1": "Jatrabari",
            "city": "Dhaka",
        })
        self.assertEqual(self.business.get_report_initials(), "PM")
        self.assertEqual(self.business.get_report_tagline(), "Creative design house")
        self.assertEqual(self.business.get_report_address_oneline(), "Jatrabari, Dhaka")

    def test_report_payment_status_label(self):
        entry = self._create_entry()
        self.assertEqual(entry.get_report_payment_status_label(), "Unreceived")
        entry.write({
            "payment_ids": [(0, 0, {
                "payment_method_id": self.payment_method_cash.id,
                "amount": 10000,
            })],
        })
        self.assertEqual(entry.get_report_payment_status_label(), "Received")

    def test_list_report_currency_totals(self):
        entry_a = self._create_entry()
        entry_b = self._create_entry()
        totals = self.env["cashbook.entry"].get_list_report_currency_totals(entry_a | entry_b)
        self.assertEqual(len(totals), 1)
        self.assertEqual(totals[0]["count"], 2)
        self.assertEqual(totals[0]["total"], entry_a.total_amount + entry_b.total_amount)
