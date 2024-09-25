import frappe
from frappe import _

def get_invoice_data(self):
    
    self.invoices = frappe._dict()
    conditions = self.get_conditions()

    if self.filters.get("branch"):
        conditions = f"{conditions} and branch = '{self.filters.get('branch')}'"

    invoice_data = frappe.db.sql(
        """
        select
            branch,
            {select_columns}
        from `tab{doctype}` si
        where docstatus = 1 {where_conditions}
        and is_opening = 'No'
        order by posting_date desc
        """.format(
            select_columns=self.select_columns,
            doctype=self.doctype,
            where_conditions=conditions,
        ),
        self.filters,
        as_dict=1,
    )

    for d in invoice_data:
        d.is_reverse_charge = "Y" if d.is_reverse_charge else "N"
        self.invoices.setdefault(d.invoice_number, d)


def get_columns(self):
    self.other_columns = []
    self.tax_columns = []
    self.invoice_columns = []

    self.company_currency = frappe.get_cached_value(
        "Company", self.filters.get("company"), "default_currency"
    )

    if (
        self.filters.get("type_of_business") != "NIL Rated"
        and self.filters.get("type_of_business") != "Document Issued Summary"
    ):
        self.tax_columns = [
            {
                "fieldname": "rate",
                "label": _("Rate"),
                "fieldtype": "Int",
                "width": 60,
            },
            {
                "fieldname": "taxable_value",
                "label": _("Taxable Value"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 150,
            },
        ]

    if self.filters.get("type_of_business") == "B2B":
        self.invoice_columns = [
            {
                "fieldname": "billing_address_gstin",
                "label": _("GSTIN/UIN of Recipient"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "branch",
                "label": _("Branch"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "customer_name",
                "label": _("Receiver Name"),
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "fieldname": "invoice_number",
                "label": _("Invoice Number"),
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "width": 100,
            },
            {
                "fieldname": "posting_date",
                "label": _("Invoice date"),
                "fieldtype": "Data",
                "width": 80,
            },
            {
                "fieldname": "invoice_value",
                "label": _("Invoice Value"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            },
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "fieldname": "is_reverse_charge",
                "label": _("Reverse Charge"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "invoice_type",
                "label": _("Invoice Type"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "ecommerce_gstin",
                "label": _("E-Commerce GSTIN"),
                "fieldtype": "Data",
                "width": 120,
            },
        ]
        self.other_columns = [
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            }
        ]

    elif self.filters.get("type_of_business") == "B2C Large":
        self.invoice_columns = [
            {
                "fieldname": "invoice_number",
                "label": _("Invoice Number"),
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "width": 120,
            },
            {
                "fieldname": "posting_date",
                "label": _("Invoice date"),
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "fieldname": "invoice_value",
                "label": _("Invoice Value"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            },
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
        ]
        self.other_columns = [
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            },
            {
                "fieldname": "ecommerce_gstin",
                "label": _("E-Commerce GSTIN"),
                "fieldtype": "Data",
                "width": 130,
            },
        ]
    elif self.filters.get("type_of_business") == "CDNR-REG":
        self.invoice_columns = [
            {
                "fieldname": "billing_address_gstin",
                "label": _("GSTIN/UIN of Recipient"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "customer_name",
                "label": _("Receiver Name"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "invoice_number",
                "label": _("Note Number"),
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "width": 120,
            },
            {
                "fieldname": "posting_date",
                "label": _("Note Date"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "document_type",
                "label": _("Note Type"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "is_reverse_charge",
                "label": _("Reverse Charge"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "invoice_type",
                "label": _("Note Supply Type"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "invoice_value",
                "label": _("Note Value"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 120,
            },
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
        ]
        self.other_columns = [
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            },
        ]
    elif self.filters.get("type_of_business") == "CDNR-UNREG":
        self.invoice_columns = [
            {
                "fieldname": "invoice_type",
                "label": _("UR Type"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "invoice_number",
                "label": _("Note Number"),
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "width": 120,
            },
            {
                "fieldname": "posting_date",
                "label": _("Note Date"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "document_type",
                "label": _("Note Type"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "invoice_value",
                "label": _("Note Value"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 120,
            },
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
        ]
        self.other_columns = [
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            },
        ]
    elif self.filters.get("type_of_business") == "B2C Small":
        self.invoice_columns = [
            {
                "fieldname": "type",
                "label": _("Type"),
                "fieldtype": "Data",
                "width": 50,
            },
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 120,
            },
        ]
        self.other_columns = [
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 100,
            },
            {
                "fieldname": "ecommerce_gstin",
                "label": _("E-Commerce GSTIN"),
                "fieldtype": "Data",
                "width": 130,
            },
        ]
        self.tax_columns.insert(
            1,
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
        )
    elif self.filters.get("type_of_business") == "EXPORT":
        self.invoice_columns = [
            {
                "fieldname": "export_type",
                "label": _("Export Type"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "invoice_number",
                "label": _("Invoice Number"),
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "width": 120,
            },
            {
                "fieldname": "posting_date",
                "label": _("Invoice date"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "invoice_value",
                "label": _("Invoice Value"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 120,
            },
            {
                "fieldname": "port_code",
                "label": _("Port Code"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "shipping_bill_number",
                "label": _("Shipping Bill Number"),
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "fieldname": "shipping_bill_date",
                "label": _("Shipping Bill Date"),
                "fieldtype": "Data",
                "width": 120,
            },
        ]
        self.other_columns = [
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 130,
            }
        ]
    elif self.filters.get("type_of_business") == "Advances":
        self.columns = [
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 180,
            },
            {
                "fieldname": "rate",
                "label": _("Rate"),
                "fieldtype": "Int",
                "width": 60,
            },
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "taxable_value",
                "label": _("Gross Advance Recieved"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 150,
            },
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 130,
            },
        ]
        return
    elif self.filters.get("type_of_business") == "Adjustment":
        self.columns = [
            {
                "fieldname": "place_of_supply",
                "label": _("Place Of Supply"),
                "fieldtype": "Data",
                "width": 180,
            },
            {
                "fieldname": "rate",
                "label": _("Rate"),
                "fieldtype": "Int",
                "width": 60,
            },
            {
                "fieldname": "applicable_tax_rate",
                "label": _("Applicable % of Tax Rate"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "taxable_value",
                "label": _("Gross Advance Adjusted"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 150,
            },
            {
                "fieldname": "cess_amount",
                "label": _("Cess Amount"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 130,
            },
        ]
        return
    elif self.filters.get("type_of_business") == "NIL Rated":
        self.invoice_columns = [
            {
                "fieldname": "description",
                "label": _("Description"),
                "fieldtype": "Data",
                "width": 420,
            },
            {
                "fieldname": "nil_rated",
                "label": _("Nil Rated Supplies"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 200,
            },
            {
                "fieldname": "exempted",
                "label": _("Exempted(other than nil rated/non GST supply)"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 350,
            },
            {
                "fieldname": "non_gst",
                "label": _("Non-GST Supplies"),
                "fieldtype": "Currency",
                "options": self.company_currency,
                "width": 200,
            },
        ]
    elif self.filters.get("type_of_business") == "Document Issued Summary":
        self.other_columns = [
            {
                "fieldname": "nature_of_document",
                "label": _("Nature of Document"),
                "fieldtype": "Data",
                "width": 300,
            },
            {
                "fieldname": "from_serial_no",
                "label": _("Sr. No. From"),
                "fieldtype": "Data",
                "width": 160,
            },
            {
                "fieldname": "to_serial_no",
                "label": _("Sr. No. To"),
                "fieldtype": "Data",
                "width": 160,
            },
            {
                "fieldname": "total_issued",
                "label": _("Total Number"),
                "fieldtype": "Int",
                "width": 150,
            },
            {
                "fieldname": "total_draft",
                "label": _("Draft"),
                "fieldtype": "Int",
                "width": 160,
            },
            {
                "fieldname": "cancelled",
                "label": _("Cancelled"),
                "fieldtype": "Int",
                "width": 160,
            },
        ]
    elif self.filters.get("type_of_business") == "HSN":
        self.columns = get_hsn_columns(self.filters)
        return
    elif self.filters.get("type_of_business") == "Section 14":
        self.columns = self.get_section_14_columns()
        return

    self.columns = self.invoice_columns + self.tax_columns + self.other_columns
