frappe.ui.form.on("Process Statement Of Accounts", {

    refresh(frm) {
        frm.add_custom_button(__('Multi Download'), function(){
            if (frm.is_dirty()) frappe.throw(__("Please save before proceeding."))
                let customers= frm.doc.customers
                customers.forEach(a => {
                    setTimeout(() => {
                        
                        let customer = []
                        customer.push(a)
                        console.log(customer)

                        let url = frappe.urllib.get_full_url(
                            '/api/method/erpnext.accounts.doctype.process_statement_of_accounts.process_statement_of_accounts.download_statements?'
                            + 'document_name='+encodeURIComponent(frm.doc.name)+ '&mcustomer='+encodeURIComponent(JSON.stringify(customer)))
                        $.ajax({
                            url: url,
                            type: 'GET',
                            freeze: true,
                            freeze_message: "Downloading PDF please wait",
                            success: function(result) {
                                if(jQuery.isEmptyObject(result)){
                                    frappe.msgprint(__('No Records for these settings.'));
                                }
                                else{
                                    window.open(url, '_blank')
                                }
                            }
                        });
                        
               
                    }, 1000);
            });
        });
    }

})