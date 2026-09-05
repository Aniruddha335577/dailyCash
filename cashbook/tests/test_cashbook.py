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

    def test_business_currency_defaults_to_company(self):
        business = self.env["cashbook.business"].create({"name": "Default Currency Co"})
        self.assertTrue(business.currency_id)

    def test_unlimited_books_per_business(self):
        books = self.env["cashbook.book"].create([
            {"business_id": self.business.id, "name": f"Book {i}"}
            for i in range(5)
        ])
        self.assertEqual(len(books), 5)

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
        both = self.env["cashbook.partner"].create({
            "name": "Both Co",
            "partner_type": "both",
        })
        self.assertEqual(vendor.partner_type, "vendor")
        self.assertEqual(both.partner_type, "both")
