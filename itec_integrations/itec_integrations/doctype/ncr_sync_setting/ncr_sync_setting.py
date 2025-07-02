# Copyright (c) 2025, Abbass Chokor and contributors
# For license information, please see license.txt

# from frappe.model.document import Document
# import frappe
# import requests
# import json
# from playwright.sync_api import sync_playwright

# class NCRSyncSetting(Document):
# 	pass

# @frappe.whitelist()
# def run_sync():
# 	try:
# 		url = "https://www.ncrangola.com/_v/segment/graphql/v1"
# 		headers = {
# 			"Content-Type": "application/json",
# 			"Accept": "application/json",
# 			"User-Agent": "Mozilla/5.0"
# 		}

# 		all_products = []
# 		sync_doc = frappe.get_doc("NCR Sync Setting")
# 		for row in sync_doc.ncr_sync_categories:
# 			hash = get_sha256_hash(row.category)
# 			if not hash:
# 				frappe.throw("Hash Sync Error")
# 			else: 
# 				frappe.msgprint(hash)
	# 		start = 0
	# 		step = 15
	# 		if row.include:
	# 			while True:
	
	# 				payload = {
	# 			"operationName": "productSearchV3",
	# 			"variables": {
	# 				"query": row.category,
	# 				"selectedFacets": [
   	# 				{
    #   				"key": "c",
    #   				"value": row.category
    # 				}
 	# 				 ],
	# 				"from": start,
	# 				"to": start + step,
	# 				"orderBy": "OrderByScoreDESC",
	# 				"map": "c"
	# 			},
	# 			"extensions": {
	# 				"persistedQuery": {
	# 					"version": 1,
	# 					"sha256Hash": "e48b7999b5713c9ed7d378bea1bd1cf64c81080be71d91e0f0b427f41e858451",
	# 					"sender": "vtex.store-resources@0.x",
	# 					"provider": "vtex.search-graphql@0.x"
	# 				}
	# 			}
	# 		}

	# 				response = requests.post(url, json=payload, headers=headers)

	# 				if response.status_code != 200:
	# 					frappe.log_error(response.text, "VTEX API Error")
	# 					break
	# 				data = response.json()

	# 				if data.get("data", {}).get("productSearch", {}):
	# 					products = data.get("data", {}).get("productSearch", {}).get("products", [])
	# 				else:
	# 					break

	# 				if not products:
	# 					break  

	# 				for p in products:
	# 					all_products.append({
	# 				"productReference": p.get("productReference"),
	# 				"productName": p.get("productName"),
	# 				"brand": p.get("brand"),
	# 				"price": p.get("priceRange", {}).get("sellingPrice", {}).get("lowPrice")
	# 					})


	# 				start += step

	# 	doc_name = frappe.get_all("NCR Products", fields=["name"], limit=1)
	# 	if doc_name:
	# 		doc = frappe.get_doc("NCR Products", doc_name[0].name)
	# 		doc.data_json = json.dumps(all_products, indent=2)
	# 		doc.save(ignore_permissions=True)
	# 	else:
	# 		doc = frappe.get_doc({
	# 			"doctype": "NCR Products",
	# 			"data_json": json.dumps(all_products, indent=2)
	# 		})
	# 		doc.insert(ignore_permissions=True)
	# 	frappe.db.set_value("NCR Sync Setting", None, "last_sync_at", frappe.utils.now_datetime())
	# 	frappe.db.commit()
	# 	return "success"

	# except Exception as e:
	# 	frappe.log_error(frappe.get_traceback(), "NCR VTEX Sync Error")
	# 	return "error"





# def get_sha256_hash(search_term):
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page()

#         sha256_hash = None

#         def intercept_request(route, request):
#             nonlocal sha256_hash
#             if "/graphql/v1" in request.url and request.method == "POST":
#                 post_data = request.post_data
#                 if "sha256Hash" in post_data:
#                     payload = json.loads(post_data)
#                     sha256_hash = payload.get("extensions", {}).get("persistedQuery", {}).get("sha256Hash")
#             route.continue_()

#         page.route("**/*", intercept_request)
#         page.goto("https://www.ncrangola.com")
#         page.fill("input[type='search']", search_term)
#         page.keyboard.press("Enter")
#         page.wait_for_timeout(6000)  # wait for requests to fire

#         browser.close()
#         return sha256_hash


