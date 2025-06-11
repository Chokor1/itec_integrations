import frappe

def execute(filters=None):
	if not filters:
		filters = {}

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	# Step 1: Fetch records ordered by item and creation
	raw_data = frappe.db.sql("""
		SELECT code, stock, creation
		FROM `tabStylus Stock History Item`
		WHERE creation BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY code, creation
	""", {
		"from_date": from_date,
		"to_date": to_date
	}, as_dict=True)

	# Step 2: Process in Python to compute absolute changes
	movement_by_item = {}
	previous_stock = {}

	for row in raw_data:
		code = row["code"]
		stock = row["stock"]

		if code in previous_stock:
			change = abs(stock - previous_stock[code])
			movement_by_item[code] = movement_by_item.get(code, 0) + change

		previous_stock[code] = stock  # Update last known stock

	# Step 3: Format output
	data = []
	for code, total_change in movement_by_item.items():
		data.append({
			"code": code,
			"total_absolute_change": total_change
		})

	columns = [
		{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 200},
		{"label": "Total Stock Movement", "fieldname": "total_absolute_change", "fieldtype": "Float", "width": 200}
	]

	return columns, data


