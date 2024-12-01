from datetime import datetime
import json
import random
import frappe
from frappe import auth
import base64
import os
from frappe.utils import get_files_path, get_site_name, now
from frappe.utils.data import escape_html
# from frappe.website.utils import is_signup_enabled
from redis import DataError
import requests
from erpnext.selling.doctype.customer.customer import get_credit_limit, get_customer_outstanding
from frappe.utils import flt


@frappe.whitelist(allow_guest=True)
def gm_write_file(data, filename, docname, doctype):
    try:
        filename_ext = f'/home/geolife/frappe-bench/sites/geolife.erpgeolife.com/private/files/{filename}.png'
        base64data = data.replace('data:image/jpeg;base64,', '')
        imgdata = base64.b64decode(base64data)
        with open(filename_ext, 'wb') as file:
            file.write(imgdata)

        doc = frappe.get_doc(
            {
                "file_name": f'{filename}.png',
                "is_private": 1,
                "file_url": f'/private/files/{filename}.png',
                "attached_to_doctype": doctype if doctype else "Geo Mitra Ledger Report",
                "attached_to_name": docname,
                "doctype": "File",
            }
        )
        doc.flags.ignore_permissions = True
        doc.insert()
        frappe.db.commit()
        return doc.file_url

    except Exception as e:
        frappe.log_error('ng_write_file', str(e))
        return e


@frappe.whitelist(allow_guest=True)
def get_doctype_images(doctype, docname, is_private):
    attachments = frappe.db.get_all("File",
        fields=["attached_to_name", "file_name", "file_url", "is_private"],
        filters={"attached_to_name": docname, "attached_to_doctype": doctype}
    )
    resp = []
    for attachment in attachments:
        # file_path = site_path + attachment["file_url"]
        x = get_files_path(attachment['file_name'], is_private=is_private)
        with open(x, "rb") as f:
            # encoded_string = base64.b64encode(image_file.read())
            img_content = f.read()
            img_base64 = base64.b64encode(img_content).decode()
            img_base64 = 'data:image/jpeg;base64,' + img_base64
        resp.append({"image": img_base64})

    return resp
    
@frappe.whitelist()
def customer_credit_limit_outstanding_bl():
    dealers=json.loads(frappe.request.data)
    try:
        dealers_details=[]

        for dealer in dealers['dealers']:
            if frappe.db.exists('Customer', dealer):
                d=frappe.get_doc('Customer',dealer)
                outstanding_amt = get_customer_outstanding(d.name, "Geolife Agritech India Private Limited", ignore_outstanding_sales_order=d.credit_limits[0].bypass_credit_limit_check if d.credit_limits else 0)
                credit_limit = get_credit_limit(d.name, "Geolife Agritech India Private Limited")
                bal = flt(credit_limit) - flt(outstanding_amt)

                biilling_amt = frappe.db.get_list('Sales Invoice', filters={'customer':dealer, 'docstatus':1, 'is_return':0}, fields=["sum(grand_total) as total"])
            dealers_details.append({'dealer':dealer,'outstanding_amt':outstanding_amt,'credit_limit':credit_limit,'bal':bal,"biilling_amt":biilling_amt[0].total if biilling_amt else 0})
        return dealers_details
    except Exception as e:
        frappe.log_error(e,'demoer')

        return e