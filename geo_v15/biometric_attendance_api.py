import datetime
import frappe
from frappe.utils import now, add_to_date, get_datetime
from frappe.integrations.utils import make_get_request
from datetime import datetime ,time



@frappe.whitelist()
def get_biometric_data():
    try:
        from_date = frappe.utils.today()
        to_date = frappe.utils.today()
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
        to_date = to_date_obj.strftime('%d%m%Y')
        from_date = from_date_obj.strftime('%d%m%Y')
        mindex = frappe.db.get_value("Biometric Attendance Log", filters={'device_location':'Factory'}, fieldname="max(indexno)") or 0
        response = make_get_request(f"http://157.20.160.34:80/COSEC/api.svc/v2/template-data?action=get;id=3;date-range={from_date}-{to_date};format=json;index={int(mindex)+1}", auth=("sa", "admin"))
        frappe.log_error("get_biometric_data backend", response)
        if response['template-data']:
            for b in response['template-data']:
                try:
                    date_str = b.get('eventdatetime')
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
                    eventdatetime = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    mdoc = frappe.get_doc({
                        'doctype':'Biometric Attendance Log',
                        'employee': b.get('userid'),
                        'employee_code': (frappe.db.exists('Employee', {'name':b.get('userid')}) or '') if b.get('userid') else '',
                        'employee_name': b.get('username'),
                        'indexno': b.get('indexno'),
                        'eventdatetime': eventdatetime,
                        'device_location':'Factory'
                        }).insert()
                    if frappe.db.exists('Employee', mdoc.get('employee_code')):
                        emp = frappe.get_doc("Employee", mdoc.get('employee_code'))

                        now = datetime.now()
                        # Define the cutoff time (11 AM)
                        cutoff_time = time(11, 0)
                        if now.time() < cutoff_time:
                            log_type = "IN"
                        else:
                            log_type = "OUT"
                            
                        checkin =frappe.get_doc({
                            'doctype':'Employee Checkin',
                            'employee':emp.get('name'),
                            'time':eventdatetime,
                            "device_id": "Factory Biometric Machine",
                            "log_type":log_type,
                            "custom_biometric_log":mdoc.get('name'),
                        }).insert()
                except Exception as err:
                    frappe.log_error("get_biometric_data error for log", err)
                    
                frappe.db.commit()


        frappe.response.message={
                'status':True,
                'message':f"Data Inserted"
        }
    except Exception as e:
        frappe.log_error("get_biometric_data error", e)
        frappe.response.message={
            'status':False,
            'message':f"{e}"
        }