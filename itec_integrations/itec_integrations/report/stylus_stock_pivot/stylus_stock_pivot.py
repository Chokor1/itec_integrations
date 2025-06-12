import frappe
from datetime import datetime, timedelta

def execute(filters=None):
	if not filters:
		filters = {}

	from_date = datetime.strptime(filters.get("from_date"), "%Y-%m-%d")
	to_date = datetime.strptime(filters.get("to_date"), "%Y-%m-%d")

	# 1. Build list of date strings
	date_list = []
	current_date = from_date
	while current_date <= to_date:
		date_list.append(current_date.strftime("%Y-%m-%d"))
		current_date += timedelta(days=1)

	# 2. Get raw stock data
	raw_data = frappe.db.sql("""
		SELECT code, DATE(creation) AS creation_date, stock
		FROM `tabStylus Stock History Item`
		WHERE creation BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY code, creation
	""", {
		"from_date": from_date.strftime("%Y-%m-%d"),
		"to_date": to_date.strftime("%Y-%m-%d")
	}, as_dict=True)

	# 3. Build nested structure: {item: {date: latest_stock}}
	item_date_stock = {}
	seen = {}

	for row in raw_data:
		code = row["code"]
		date = row["creation_date"]
		stock = row["stock"]

		if code not in item_date_stock:
			item_date_stock[code] = {}
			seen[code] = {}

		# Store only the last stock seen per date
		seen[code][date] = stock
		item_date_stock[code][date] = stock

	# 4. Create rows
	data = []
	for code, stocks_by_date in item_date_stock.items():
		row = {"code": code}
		last_stock = None
		for date in date_list:
			if date in stocks_by_date:
				last_stock = stocks_by_date[date]
			# Carry forward last known stock
			row[date] = last_stock if last_stock is not None else 0
		data.append(row)

	# 5. Create columns dynamically
	columns = [{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 150}]
	for date in date_list:
		columns.append({
			"label": date,
			"fieldname": date,
			"fieldtype": "Float",
			"width": 100
		})

	return columns, data

