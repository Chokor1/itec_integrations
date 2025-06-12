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
	date_results = frappe.db.get_all(
		"Stylus Stock History Item",
		fields=["DATE(creation) as date"],
		filters={"creation": ["between", [from_date, to_date]]},
		distinct=True,
		order_by="date"
	)
	date_list = sorted([d.date.strftime("%Y-%m-%d") for d in date_results])

	# Step 2: Define columns
	columns = [
		{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 120},
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 180}
	]
	for date in date_list:
		columns.append({
			"label": date,
			"fieldname": date,
			"fieldtype": "Float",
			"width": 100
		})
	columns.append({"label": "Total Change (Δ)", "fieldname": "total_change", "fieldtype": "Float", "width": 120})
	columns.append({"label": "Absolute Change (|Δ|)", "fieldname": "total_change_abs", "fieldtype": "Float", "width": 140})

	# Step 3: Fetch stock data
	raw_data = frappe.db.sql("""
		SELECT
			code,
			designation,
			DATE(creation) AS date,
			SUM(stock) AS stock
		FROM `tabStylus Stock History Item`
		WHERE DATE(creation) BETWEEN %s AND %s
		GROUP BY code, designation, DATE(creation)
	""", (from_date, to_date), as_dict=True)

	# Step 4: Group by item and pivot data
	item_map = {}
	for row in raw_data:
		key = row.code
		date = row.date.strftime("%Y-%m-%d")
		if key not in item_map:
			item_map[key] = {
				"code": row.code,
				"designation": row.designation
			}
		item_map[key][date] = row.stock

	# Step 5: Calculate changes
	for item in item_map.values():
		qty_by_date = [item.get(date, 0) for date in date_list]
		if qty_by_date:
			start_qty = qty_by_date[0]
			end_qty = qty_by_date[-1]
			item["total_change"] = end_qty - start_qty
			item["total_change_abs"] = abs(end_qty - start_qty)
		else:
			item["total_change"] = 0
			item["total_change_abs"] = 0

	# Step 6: Return
	data = list(item_map.values())
	return columns, data
