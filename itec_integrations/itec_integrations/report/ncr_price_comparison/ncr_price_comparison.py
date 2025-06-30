# Copyright (c) 2025, Abbass Chokor and contributors
# For license information, please see license.txt

import frappe
import json

def execute(filters=None):
    columns = [
        {"label": "Product Reference", "fieldname": "product_reference", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": "NCR Product Name", "fieldname": "ncr_name", "fieldtype": "Data", "width": 300},
        {"label": "NCR Price", "fieldname": "ncr_price", "fieldtype": "Currency", "width": 120},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "Internal Price", "fieldname": "internal_price", "fieldtype": "Currency", "width": 120},
        {"label": "Difference", "fieldname": "difference", "fieldtype": "Currency", "width": 100},
        {"label": "Difference (%)", "fieldname": "percent_diff", "fieldtype": "Percent", "width": 120},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100}
    ]

    data = []

    ncr_doc = frappe.get_all("NCR Products", fields=["name"], order_by="creation desc", limit=1)
    if not ncr_doc:
        return columns, data

    ncr_data = frappe.get_doc("NCR Products", ncr_doc[0].name)

    try:
        products = json.loads(ncr_data.data_json)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Invalid JSON in NCR Products")
        return columns, data

    sync_setting = frappe.get_single("NCR Sync Setting")
    tax_category = sync_setting.tax_category

    for p in products:
        product_ref = p.get("productReference")
        ncr_name = p.get("productName")
        ncr_price = p.get("price") or 0

        item = frappe.db.get_value("Item", {"item_code": product_ref, "disabled": 0}, ["item_name"], as_dict=True)
        if item:
            item_price = frappe.db.get_all(
                "Item Price",
                filters={
                    "item_code": product_ref,
                    "price_list": "Standard Selling",
                    "selling": 1
                },
                fields=["price_list_rate"],
                order_by="creation desc",
                limit=1
            )

            item_tax = frappe.db.get_value(
                "Item Tax",
                {
                    "parent": product_ref,
                    "tax_category": tax_category,
                },
                ["item_tax_template"],
                as_dict=True
            )

            tax_rate = 0
            if item_tax:
                tax = frappe.db.get_value(
                    "Item Tax Template Detail",
                    {
                        "parent": item_tax.item_tax_template,
                    },
                    ["tax_rate"],
                    as_dict=True
                )
                if tax:
                    tax_rate = tax.tax_rate or 0

            qty = frappe.db.sql("""SELECT SUM(actual_qty) as qty FROM `tabBin` WHERE item_code = %s""", product_ref, as_dict=True)[0].qty or 0

            if item_price:
                internal_price = item_price[0].price_list_rate + (item_price[0].price_list_rate * tax_rate / 100)
                difference = internal_price - ncr_price
                percent_diff = (difference / internal_price * 100) if internal_price else 0

                data.append({
                    "product_reference": product_ref,
                    "ncr_name": ncr_name,
                    "ncr_price": ncr_price,
                    "item_name": item.item_name,
                    "internal_price": internal_price,
                    "difference": difference,
                    "percent_diff": percent_diff,
                    "qty": qty
                })

    return columns, data
