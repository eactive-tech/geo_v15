# Copyright (c) 2026, eactive and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DealerCategoryCriteriaPaper(Document):
	def validate(self):
		self.validate_single_active()

	def validate_single_active(self):
		"""Only one Criteria Paper may be active at a time."""
		if not self.is_active:
			return

		active = frappe.db.get_value(
			"Dealer Category Criteria Paper",
			{"is_active": 1, "name": ["!=", self.name]},
			"name",
		)
		if active:
			frappe.throw(
				_(
					"Dealer Category Criteria Paper {0} is already active. Deactivate it before activating this document."
				).format(active),
				title=_("Another Document Is Active"),
			)
