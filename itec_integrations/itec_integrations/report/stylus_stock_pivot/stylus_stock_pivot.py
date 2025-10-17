import frappe
from datetime import datetime


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
		distinct=True
	)

	# Ensure dates are formatted and sorted in descending order
	date_list = sorted(
		[
			d.get("date").strftime("%Y-%m-%d")
			if hasattr(d.get("date"), "strftime")
			else str(d.get("date"))
			for d in dates
		],
		reverse=True
	)

	# Step 2: Define columns
	columns = [
		{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 150},
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 200},
		{"label": "Main Category", "fieldname": "main_category", "fieldtype": "Data", "width": 150},
		{"label": "Brand", "fieldname": "brand", "fieldtype": "Data", "width": 150}
	]
 
	for date in date_list:
		columns.append({
			"label": date,
			"fieldname": date,
			"fieldtype": "Float",
			"width": 150
		})

	# Step 3: Get raw stock data
	raw_data = frappe.db.sql("""
		SELECT
			`code`,
			`designation`,
			`main_category`,
			`brand`,
			DATE(`creation`) AS `date`,
			`stock` AS `stock`
		FROM
			`tabStylus Stock History Item`
		WHERE
			DATE(`creation`) BETWEEN %s AND %s
		GROUP BY
			`code`, DATE(`creation`)
	""", (from_date, to_date), as_dict=True)

	# Step 4: Transform data into row-wise format
	item_map = {}
	for row in raw_data:
		key = row.code
		date = row.date.strftime("%Y-%m-%d")
		stock = row.stock

		if key not in item_map:
			item_map[key] = {
				"code": row.code,
				"designation": row.designation,
				"main_category": row.main_category,
				"brand": row.brand
			}

		item_map[key][date] = stock

	# Step 5: Return columns and data
	data = list(item_map.values())
	return columns, data
