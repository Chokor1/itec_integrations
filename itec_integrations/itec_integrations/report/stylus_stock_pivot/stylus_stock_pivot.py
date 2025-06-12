import frappe
from datetime import datetime, timedelta

def execute(filters=None):
	if not filters:
		filters = {}

	from_date = datetime.strptime(filters.get("from_date"), "%Y-%m-%d")
	to_date = datetime.strptime(filters.get("to_date"), "%Y-%m-%d")

	date_list = []
	current_date = from_date
	while current_date <= to_date:
		date_list.append(current_date.strftime("%Y-%m-%d"))
		current_date += timedelta(days=1)

	raw_data = frappe.db.sql("""
		SELECT code, DATE(creation) AS creation_date, stock
		FROM `tabStylus Stock History Item`
		WHERE creation BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY code, creation
	""", {
		"from_date": from_date.strftime("%Y-%m-%d"),
		"to_date": to_date.strftime("%Y-%m-%d")
	}, as_dict=True)

	item_date_stock = {}
	for row in raw_data:
		code = row["code"]
		date = row["creation_date"]
		stock = row["stock"]

		if code not in item_date_stock:
			item_date_stock[code] = {}
		item_date_stock[code][date] = stock

	data = []
	for code, stock_by_date in item_date_stock.items():
		row = {"code": code}
		last_stock = None
		seen_any = False

		for date in date_list:
			if date in stock_by_date:
				last_stock = stock_by_date[date]
				seen_any = True
			row[date] = last_stock if last_stock is not None else 0

		if seen_any:
			data.append(row)

	columns = [{"label": "Item Code", "fieldname": "code", "fieldtype": "Data", "width": 150}]
	for date in date_list:
		columns.append({
			"label": date,
			"fieldname": date,
			"fieldtype": "Float",
			"width": 100
		})

	return columns, data
