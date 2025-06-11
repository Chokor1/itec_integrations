import frappe

def execute(filters=None):
	if not filters:
		filters = {}

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	# Step 1: Fetch item stock history
	raw_data = frappe.db.sql("""
		SELECT code, stock, creation, designation, price, main_category, brand
		FROM `tabStylus Stock History Item`
		WHERE creation BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY code, creation
	""", {
		"from_date": from_date,
		"to_date": to_date
	}, as_dict=True)

	# Step 2: Calculate absolute stock movements per item
	movement_by_item = {}
	previous_stock = {}
	item_info = {}

	for row in raw_data:
		code = row["code"]
		stock = row["stock"]

		# Save item metadata once
		if code not in item_info:
			item_info[code] = {
				"designation": row.get("designation"),
				"price": row.get("price"),
				"main_category": row.get("main_category"),
				"brand": row.get("brand")
			}

		# Calculate change if previous stock exists
		if code in previous_stock:
			change = abs(stock - previous_stock[code])
			movement_by_item[code] = movement_by_item.get(code, 0) + change

		previous_stock[code] = stock

	# Step 3: Build final data, excluding 0-change items
	data = []
	for code, total_change in movement_by_item.items():
		if total_change == 0:
			continue  # Skip unchanged items

		info = item_info.get(code, {})
		data.append({
			"code": code,
			"designation": info.get("designation"),
			"price": info.get("price"),
			"main_category": info.get("main_category"),
			"brand": info.get("brand"),
			"total_absolute_change": total_change
		})

	# Step 4: Define report columns
	columns = [
		{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 150},
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 200},
		{"label": "Price", "fieldname": "price", "fieldtype": "Currency", "width": 100},
		{"label": "Category", "fieldname": "main_category", "fieldtype": "Data", "width": 150},
		{"label": "Brand", "fieldname": "brand", "fieldtype": "Data", "width": 150},
		{"label": "Total Stock Movement", "fieldname": "total_absolute_change", "fieldtype": "Float", "width": 180}
	]

	return columns, data



