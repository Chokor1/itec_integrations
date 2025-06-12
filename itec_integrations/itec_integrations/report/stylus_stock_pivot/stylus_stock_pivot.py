# Copyright (c) 2025, Abbass Chokor and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if not filters:
		filters = {}

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	if not from_date or not to_date:
		frappe.throw("Please set both From Date and To Date")

    # Step 1: Get distinct dates
	dates = frappe.db.get_all(
        "Stylus Stock History Item",
        fields=["DATE(creation) as date"],
        filters={"creation": ["between", [from_date, to_date]]},
        distinct=True,
        order_by="date"
    )
	date_list = [d.date.strftime("%Y-%m-%d") for d in dates]

    # Step 2: Define columns
	columns = [{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 150},{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 200}]
	for date in date_list:
		columns.append({
            "label": date,
            "fieldname": date,
            "fieldtype": "Float",
            "width": 100
        })

    # Step 3: Get raw stock data
	raw_data = frappe.db.sql("""
        SELECT
            `code`,
			`designation`,		  
            DATE(`creation`) AS `date`,
            SUM(`stock`) AS `stock`
        FROM
            `tabStylus Stock History Item`
        WHERE
            DATE(`creation`) BETWEEN %s AND %s
        GROUP BY
            `code`, DATE(`creation`)
    """, (from_date, to_date), as_dict=True)


	item_map = {}
	for row in raw_data:
		key = row.code
		date = row.date.strftime("%Y-%m-%d")
		stock = row.stock

		if key not in item_map:
			item_map[key] = {
				"code": row.code,
				"designation": row.designation
			}

		item_map[key][date] = stock

	data = list(item_map.values())
	return columns, data
