# Copyright (c) 2025, Abbass Chokor and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import requests
import base64
import frappe
from frappe.utils import now



class StylusSyncStockSetting(Document):
    pass

@frappe.whitelist()
def run_sync():
	setting = frappe.get_single("Stylus Sync Stock Setting")

	if not setting.enabled:
		return
    
	headers = {
            "Authorization": f"Basic {base64.b64encode((setting.access_key + ':').encode()).decode()}",
			"Accept": "application/json",
    		"User-Agent": "MyApp/1.0"
        }
	try:
		response = requests.get(
                "https://www.stylus.co.ao/encomendas/api/stockparceiros",
                headers=headers,
            )
		response.raise_for_status()
		data = response.json()

		if not isinstance(data, list):
			frappe.throw("Unexpected response format from Stylus API")

		history_doc = frappe.get_doc(
                {"doctype": "Stylus Stock History", "items": []}
            )

		for item in data:
			history_doc.append(
                    "items",
                    {
                        "code": item.get("CODE"),
                        "designation": item.get("DESIGNATION"),
                        "price": item.get("PRICE"),
                        "stock": item.get("STOCK"),
                        "main_category": item.get("CATEGORIA_PRINCIPAL"),
                        "brand": item.get("MARCA"),
                        "description_html": item.get("DESCRICAO"),
						"imagens": item.get("IMAGENS"),
						"imagem_capa": item.get("IMAGEM_CAPA")
                    },
                )

		history_doc.insert(ignore_permissions=True)
		setting.last_inventory_sync = now()
		setting.save()
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Stylus Sync Failed")
		frappe.throw(f"Stylus Sync failed: {e}")
