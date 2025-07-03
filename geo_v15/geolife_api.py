from datetime import datetime
import json
import random
import frappe
from frappe import auth
import base64
import os
from frappe.utils.data import escape_html
# from frappe.website.utils import is_signup_enabled
from redis import DataError
import requests
from erpnext.selling.doctype.customer.customer import get_credit_limit, get_customer_outstanding
from frappe.utils import flt
from frappe.utils import generate_hash, get_files_path, get_site_name, now
# import filetype



@frappe.whitelist(allow_guest=True)
def gm_write_file(data, filename, docname, doctype):
    try:
        filename_ext = f'/home/frappe/frappe-bench/sites/geolife.erpgeolife.com/private/files/{filename}.png'
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
    


def any_file_write_file(base64data, filename, docname, doctype, file_type="private"):
    try:
        site_path = frappe.get_site_path()
        folder = "public/files" if file_type == "public" else "private/files"
        full_path = f"{site_path}/{folder}/{filename}"
        frappe.log_error(f"any_file_write_file full_path: {full_path}", "any_file_write_file")

        if "base64," in base64data:
            base64data = base64data.split("base64,", 1)[1]

        filedata = base64.b64decode(base64data)

        with open(full_path, 'wb') as f:
            f.write(filedata)

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"{filename}",
            "is_private": 0 if file_type == "public" else 1,
            "file_url": f"/{folder}/{filename}",
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
        })
        file_doc.flags.ignore_permissions = True
        file_doc.insert()
        frappe.db.commit()
        return file_doc.file_url

    except Exception as e:
        frappe.log_error("any_file_write_file error", str(e))
        return None


@frappe.whitelist(allow_guest=True)
def update_agreementfrom_proposed_dealer():
    try:
        data = frappe.form_dict
        frappe.log_error(f"update_agreementfrom_proposed_dealer data",  data)

        if not data.get("customer"):
            frappe.throw("Customer name is required.")

        dealer = frappe.get_doc("Customer", data.get("customer"))
        if not dealer:
            frappe.throw("customer not found.")

        if data.get("custom_geolife_dealership_agreement"):
            base64_string = data["custom_geolife_dealership_agreement"]
            if "," in base64_string:
                base64_string = base64_string.split(",", 1)[1]

            file_url = any_file_write_file(base64_string, f"{dealer.name}geolife_dealership_agreement.pdf", dealer.name, "Customer", "private")
            if file_url:
                dealer.custom_geolife_dealership_agreement = file_url

        dealer.save()
        return {"status": "Success", "message": "Agreement updated successfully."}

    except Exception as e:
        frappe.log_error(f"Error in update_agreementfrom_proposed_dealer", str(e))
        return {"status": "Error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def create_customer_from_proposed():
    try:
        data = frappe.form_dict
        frappe.log_error(f"create_customer_from_proposed data",  data)

        customer_pre_text_mapping = {
            "Gujarat": "GJ", "Bihar": "BIH", "Punjab": "PB", "Haryana": "HA", "Rajasthan": "RJ",
            "Tamil Nadu": "TN", "Telangana": "TL", "Andhra Pradesh": "AP", "Maharashtra": "MH",
            "Madhya Pradesh": "MP", "Uttar Pradesh": "UP", "Karnataka": "KRT", "Head Office": "HO"
        }

        branch_name = data.get("branch")
        if not branch_name:
            frappe.throw("Branch is required.")

        
        branch = frappe.get_doc("Branch", branch_name)
       
        customer_pre_text_mapping = {
            "Gujarat": "GJ",
            "Bihar": "BIH",
            "Punjab": "PB",
            "Haryana": "HA",
            "Rajasthan": "RJ",
            "Tamil Nadu": "TN",
            "Telangana": "TL",
            "Andhra Pradesh": "AP",
            "Maharashtra": "MH",
            "Madhya Pradesh": "MP",
            "Uttar Pradesh": "UP",
            "Karnataka": "KRT",
            "Head Office": "HO",
            "Delhi": "DEL",
            "West Bengal": "WB",
            "Odisha": "OD",
            "Assam": "AS",
            "Kerala": "KL",
            "Uttarakhand": "UK",
            "Chhattisgarh": "CG",
            "Jharkhand": "JH",
            "Goa": "GOA",
            "Himachal Pradesh": "HP",
            "Jammu and Kashmir": "JK",
            "Arunachal Pradesh": "AR",
            "Sikkim": "SK",
            "Tripura": "TR",
            "Meghalaya": "MG",
            "Nagaland": "NG",
            "Mizoram": "MZ",
            "Puducherry": "PY",
            "Chandigarh": "CH",
            "Dadra and Nagar Haveli": "DNH",
            "Daman and Diu": "DD",
            "Andaman and Nicobar Islands": "ANI",
            "Lakshadweep": "LKD",
            "Sikkim": "SKM",
            "Arunachal Pradesh": "ARP"
        }
        pre_text = customer_pre_text_mapping.get(data.get("branch"))


        account = frappe.get_doc({
        "doctype": "Account",
        "account_name": f"{pre_text or 'CUST'}-{data.get('customer_name')}-{data.get('market_place_or_tehsil') or ''}",
        "parent_account":data.get("customer_parent_account"),
        "account_type": "Receivable",
        "account_currency":"INR",
        "is_group":0,
        "root_type":"Liability",
        "branch": data.get("branch")
        })
        account.insert(ignore_permissions=True)

        if not frappe.db.exists("Sales Person", {'employee':data.get("sales_person")}):
            return {"status": "Error", "message": "Sales Person not found."}
        sp = frappe.get_doc("Sales Person", {'employee':data.get("sales_person")}) if data.get("sales_person") else None

        customer = frappe.get_doc({
            "doctype": "Customer",
            # "customer_name": f'{pre_text or "CUST"}-{data.get("customer_name")}-{data.get("market_place_or_tehsil") or ""}',
            "customer_name": f'{account.get("name")}',
            "branch": data.get("branch"),
            "custom_dealer_type": data.get("dealer_type"),
            "customer_type": data.get("customer_type") or "Company",
            "customer_group": data.get("customer_group") or "All Customer Groups",
            "territory": data.get("territory") or "All Territories",
            "market_place_or_tehsil": data.get("market_place_or_tehsil") or "",
            "zone": data.get("zone") or "",
            "region": data.get("region") or "",
            "email_id": data.get("email_id"),
            "mobile_no": data.get("mobile_no"),
            "mobile_number": data.get("contact_person_mobile_no"),
            "default_price_list": branch.price_list,
            "accounts" : [{'account':account.name}],
            "sales_person":data.get("sales_person") or "",
            "default_currency":"INR",
            "sales_team": [{
                "sales_person": sp.name if sp else "",
                "allocated_percentage": 100
            }],
            "credit_limits": [{
                "credit_limit": 1,
                "bypass_credit_limit_check": 1
            }],
            "payment_terms":"100 % Advance",
            "geo_date_of_marriage_anniversary": data.get("marriage_anniversary") or "",
            "geo_date_of_incorporation_or_start_of_business": data.get("date_of_incorporation") or "",
            "geo_date_of_birth_of_dealer": data.get("date_of_birth") or "",
            "tax_id": data.get("gst_no") or "",
            "gstin": data.get("gst_no") or "",
            "aadhar_no": data.get("aadhar_no") or "",
            "udyog_aadhar_no": data.get("udyog_aadhar_no") or "",
            "pan": data.get("pan") or "",
            "cin": data.get("cin") or "",

        })
        customer.insert(ignore_mandatory=True)

        if data.get("contact_person_name"):
            contact = frappe.get_doc({
                "doctype": "Contact",
                "first_name": data.get("contact_person_name"),
                "phone": data.get("contact_person_mobile_no"),
                "mobile_no": data.get("mobile_no"),
                "email_id": data.get("email_id"),
                "links": [{
                    "link_doctype": "Customer",
                    "link_name": customer.name
                }]
            })
            contact.insert()

        file_fields = [
            "custom_gst_certificate", "custom_upload_pan_card", "custom_aadhar_card", "custom_security_blank_cheque_no_1",
            "custom_security_blank_cheque_no_2", "custom_geo_pesticides_license", "custom_geo_fertiliser_license",
            "custom_geo_address_proof", "custom_blank_letter_head", "custom_geo_bank_statement", "custom_geolife_dealership_agreement",
            "custom_dealer_location_image","custom_dealer_shop_image"
        ]

        updated = False
        # for fieldname in file_fields:
        #     if data.get(fieldname):
        #         try:
        #             filedata = base64.b64decode(data[fieldname])
        #             filename = f"{fieldname}_{customer.name}.file"
        #             file_doc = save_file(filename, filedata, "Customer", customer.name, is_private=1)
        #             # Set file URL to respective field
        #             customer.set(fieldname, file_doc.file_url)
        #             updated = True
        #         except Exception as e:
        #             frappe.log_error(f"File Upload Failed: {fieldname}", str(e))
        for fieldname in file_fields:
            if data.get(fieldname):
                try:
                    base64_string = data[fieldname]['base64']
                    if "," in base64_string:
                        base64_string = base64_string.split(",", 1)[1]

                    filedata = base64.b64decode(base64_string)

                    # Detect extension
                    # kind = filetype.guess(filedata)
                    # ext = f".{kind.extension}" if kind else ".bin"
                    # frappe.log_error(f"Detected {fieldname}: {ext}",f"{fieldname}")

                    # Generate filename
                    # unique_name = generate_hash(length=12)
                    # filename = f"{unique_name}{ext}"
                    filename = data[fieldname]['file_name']
                    file_url = any_file_write_file(base64_string, filename, customer.name, "Customer", "private")

                    if file_url:
                        customer.set(fieldname, file_url)
                        updated = True

                except Exception as e:
                    frappe.log_error(f"Custom File Upload Failed: {fieldname}", str(e))
                    return {"status": "Error", "message": str(e)}

        if updated:
            customer.save()


        return {"status": "Approved", "customer": customer.name}
    except Exception as err:
        frappe.log_error(f"Error in create_customer_from_proposed", f"{str(e)}")
        return {"status": "Error", "message": str(err)}
