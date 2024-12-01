// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Statement of account for supplier', {
	// refresh: function(frm) {

	// }
	view_properties: function(frm) {
		frappe.route_options = {doc_type: 'Customer'};
		frappe.set_route("Form", "Customize Form");
	},
	refresh: function(frm){
		if(!frm.doc.__islocal) {
			frm.add_custom_button(__('Send Emails'), function(){
				if (frm.is_dirty()) frappe.throw(__("Please save before proceeding."))
				frappe.call({
					method: "geo_v15.geo_v15.doctype.process_statement_of_account_for_supplier.process_statement_of_account_for_supplier.send_emails",
					args: {
						"document_name": frm.doc.name,
					},
					callback: function(r) {
						if(r && r.message) {
							frappe.show_alert({message: __('Emails Queued'), indicator: 'blue'});
						}
						else{
							frappe.msgprint(__('No Records for these settings.'))
						}
					}
				});
			});
			frm.add_custom_button(__('Download'), function(){
				if (frm.is_dirty()) frappe.throw(__("Please save before proceeding."))
				let url = frappe.urllib.get_full_url(
					'/api/method/geo_v15.geo_v15.doctype.process_statement_of_account_for_supplier.process_statement_of_account_for_supplier.download_statements?'
					+ 'document_name='+encodeURIComponent(frm.doc.name))
				$.ajax({
					url: url,
					type: 'GET',
					success: function(result) {
						if(jQuery.isEmptyObject(result)){
							frappe.msgprint(__('No Records for these settings.'));
						}
						else{
							window.location = url;
						}
					}
				});
			});
		}
	},
	onload: function(frm) {
		frm.set_query('currency', function(){
			return {
				filters: {
					'enabled': 1
				}
			}
		});
		frm.set_query("account", function() {
			return {
				filters: {
					'company': frm.doc.company
				}
			};
		});
		if(frm.doc.__islocal){
			frm.set_value('from_date', frappe.datetime.add_months(frappe.datetime.get_today(), -1));
			frm.set_value('to_date', frappe.datetime.get_today());
		}
	},

	frequency: function(frm){
		if(frm.doc.frequency != ''){
			frm.set_value('start_date', frappe.datetime.get_today());
		}
		else{
			frm.set_value('start_date', '');
		}
	},

	fetch_suppliers: function(frm){
			frappe.call({
				method: "geo_v15.geo_v15.doctype.process_statement_of_account_for_supplier.process_statement_of_account_for_supplier.fetch_suppliers",
				args: {
					'supplier_group': frm.doc.supplier_group,
					'supplier_name': frm.doc.supplier_name?frm.doc.supplier_name:'' ,
					'primary_mandatory': frm.doc.primary_mandatory
				},
				callback: function(r) {
					console.log(r)
					if(!r.exc) {
						if(r.message.length){
							frm.clear_table('suppliers');
							for (const supplier of r.message){
								var row = frm.add_child('suppliers');
								row.supplier = supplier.name;
								row.primary_email = supplier.primary_email;
								row.billing_email = supplier.billing_email;
							}
							frm.refresh_field('suppliers');
						}
						else{
							frappe.throw(__('No suppliers found with selected options.'));
						}
					}
				}
			});
		
	}

});

