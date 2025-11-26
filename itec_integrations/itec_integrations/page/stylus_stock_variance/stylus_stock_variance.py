import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import cstr, flt, format_datetime, getdate


MAX_ITEMS = 25
DIFF_PRECISION = 3


@frappe.whitelist()
def fetch_stock_variance(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	filters = frappe.parse_json(filters) if filters else {}

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	start_date, end_date = _validate_dates(from_date, to_date)
	params = {
		"start": f"{start_date} 00:00:00",
		"end": f"{end_date} 23:59:59",
		"before_start": f"{start_date} 00:00:00",
	}

	conditions = [
		"`creation` BETWEEN %(start)s AND %(end)s",
		"`code` IS NOT NULL",
		"`code` != ''",
	]

	_append_text_filter("code", filters.get("code"), conditions, params)
	_append_text_filter("designation", filters.get("designation"), conditions, params)
	_append_text_filter("main_category", filters.get("main_category"), conditions, params)
	_append_text_filter("brand", filters.get("brand"), conditions, params)

	where_clause = f"WHERE {' AND '.join(conditions)}"
	distinct_codes = frappe.db.sql(
		f"SELECT DISTINCT `code` FROM `tabStylus Stock History Item` {where_clause}",
		params,
		as_dict=True,
	)

	if not distinct_codes:
		return {"items": []}

	if len(distinct_codes) > MAX_ITEMS:
		frappe.throw(
			_("Your filters match {0} different items. Please narrow them down to {1} or fewer items to keep the page responsive.").format(
				len(distinct_codes), MAX_ITEMS
			)
		)

	rows = frappe.db.sql(
		f"""
			SELECT
				`code`,
				`designation`,
				`main_category`,
				`brand`,
				`price`,
				`stock`,
				`creation`
			FROM `tabStylus Stock History Item`
			{where_clause}
			ORDER BY `code` ASC, `creation` ASC
		""",
		params,
		as_dict=True,
	)

	# Get opening balances (stock before the from_date for each code)
	code_list = [c['code'] for c in distinct_codes]
	opening_balances = _get_opening_balances(code_list, start_date)

	items = _build_items(rows, opening_balances)
	return {"items": items}


def _validate_dates(from_date: Optional[str], to_date: Optional[str]):
	if not from_date or not to_date:
		frappe.throw(_("Both From Date and To Date are required."))

	start = getdate(from_date)
	end = getdate(to_date)

	if start > end:
		frappe.throw(_("From Date cannot be later than To Date."))

	return start, end


def _get_opening_balances(codes: List[str], start_date) -> Dict[str, float]:
	"""Get the last stock value before the start_date for each code (opening balance)."""
	if not codes:
		return {}
	
	# For each code, get the most recent stock entry before start_date
	opening_balances = {}
	
	for code in codes:
		result = frappe.db.sql(
			"""
				SELECT `stock`
				FROM `tabStylus Stock History Item`
				WHERE `code` = %(code)s
					AND `creation` < %(before_start)s
				ORDER BY `creation` DESC
				LIMIT 1
			""",
			{
				"code": code,
				"before_start": f"{start_date} 00:00:00"
			},
			as_dict=True
		)
		
		if result:
			opening_balances[code] = flt(result[0].get("stock"))
		else:
			# No history before start_date, set opening balance to 0
			opening_balances[code] = 0.0
	
	return opening_balances


def _build_items(rows: List[Dict[str, Any]], opening_balances: Dict[str, float]) -> List[Dict[str, Any]]:
	result = OrderedDict()

	for row in rows:
		code = row.get("code")
		if not code:
			continue

		item = result.get(code)
		if not item:
			item = {
				"code": code,
				"designation": row.get("designation") or "",
				"main_category": row.get("main_category") or "",
				"brand": row.get("brand") or "",
				"price": flt(row.get("price")),
				"history": [],
				"differences": [],
				"totals": {"positive": 0.0, "negative": 0.0},
				"last_updated": None,
				"opening_balance": opening_balances.get(code),  # Store opening balance
			}
			result[code] = item
		else:
			if not item.get("designation") and row.get("designation"):
				item["designation"] = row.get("designation")
			if not item.get("main_category") and row.get("main_category"):
				item["main_category"] = row.get("main_category")
			if not item.get("brand") and row.get("brand"):
				item["brand"] = row.get("brand")
			if not item.get("price") and row.get("price"):
				item["price"] = flt(row.get("price"))

		history_entry = {
			"label": format_datetime(row.get("creation"), "yyyy-MM-dd HH:mm"),
			"timestamp": row.get("creation"),
			"stock": flt(row.get("stock")),
			"price": flt(row.get("price")),
		}
		item["history"].append(history_entry)
		item["last_updated"] = history_entry["label"]

		_append_difference(item, history_entry)

	return [
		{
			**item,
			"history": _compress_history(item["history"], item.get("opening_balance")),
			"differences": item["differences"],
			"totals": {
				"positive": _round(item["totals"]["positive"]),
				"negative": _round(item["totals"]["negative"]),
			},
		}
		for item in result.values()
	]


def _append_difference(item: Dict[str, Any], current_entry: Dict[str, Any]) -> None:
	history = item.get("history") or []
	
	# Handle first entry within the date range
	if len(history) == 1:
		# Opening balance is always set now (either from history or 0)
		opening_balance = item.get("opening_balance", 0.0)
		
		# Calculate variance from opening balance
		diff = _round(current_entry["stock"] - opening_balance)
		if diff != 0:
			date_label = format_datetime(current_entry.get("timestamp"), "dd-MM-yyyy") if current_entry.get("timestamp") else current_entry["label"]
			
			diff_record = {
				"period": f"Opening → {current_entry['label']}",
				"date": date_label,
				"difference": diff,
				"stock": _round(current_entry["stock"]),
				"price": flt(current_entry.get("price")),
			}
			
			item["differences"].append(diff_record)
			
			if diff > 0:
				item["totals"]["positive"] = _round(item["totals"]["positive"] + diff)
			else:
				item["totals"]["negative"] = _round(item["totals"]["negative"] + diff)
		return
	
	if len(history) < 2:
		return

	prev_entry = history[-2]
	diff = _round(current_entry["stock"] - prev_entry["stock"])
	if not diff:
		return

	date_label = format_datetime(current_entry.get("timestamp"), "dd-MM-yyyy") if current_entry.get("timestamp") else current_entry["label"]

	diff_record = {
		"period": f"{prev_entry['label']} → {current_entry['label']}",
		"date": date_label,
		"difference": diff,
		"stock": _round(current_entry["stock"]),
		"price": flt(current_entry.get("price")),
	}

	item["differences"].append(diff_record)

	if diff > 0:
		item["totals"]["positive"] = _round(item["totals"]["positive"] + diff)
	else:
		item["totals"]["negative"] = _round(item["totals"]["negative"] + diff)


def _append_text_filter(fieldname: str, value: Any, conditions: List[str], params: Dict[str, Any]) -> None:
	values = _normalize_values(value)
	if not values:
		return

	if len(values) == 1:
		param_key = f"{fieldname}_like"
		conditions.append(f"`{fieldname}` LIKE %({param_key})s")
		params[param_key] = f"%{values[0]}%"
	else:
		sub_conditions = []
		for idx, val in enumerate(values):
			param_key = f"{fieldname}_like_{idx}"
			sub_conditions.append(f"`{fieldname}` LIKE %({param_key})s")
			params[param_key] = f"%{val}%"

		conditions.append("(" + " OR ".join(sub_conditions) + ")")


def _normalize_values(value: Any) -> List[str]:
	if value is None:
		return []

	if isinstance(value, (list, tuple, set)):
		raw_values = list(value)
	else:
		raw_values = re.split(r"[\n,;]+", cstr(value))

	return [cstr(v).strip() for v in raw_values if cstr(v).strip()]


def _round(value: float) -> float:
	return flt(value, DIFF_PRECISION)


def _compress_history(entries: List[Dict[str, Any]], opening_balance: Optional[float] = None) -> List[Dict[str, Any]]:
	if not entries:
		return []
	
	compressed = []
	last_stock = None
	last_price = None
	first_entry_added = False

	# Always add opening balance as the first entry (even if 0)
	if opening_balance is not None:
		compressed.append({
			"label": "Opening",
			"date": "Opening",
			"stock": _round(opening_balance),
			"price": None,
		})
		last_stock = _round(opening_balance)
		first_entry_added = True

	for entry in entries:
		stock_value = _round(entry.get("stock") or 0)
		price_value = entry.get("price")
		if price_value is None:
			price_value = last_price
		else:
			price_value = flt(price_value)

		# Always include the first entry to ensure opening balance is shown
		if last_stock is None or stock_value != last_stock or price_value != last_price:
			compressed.append(
				{
					"label": entry.get("label"),
					"date": format_datetime(entry.get("timestamp"), "dd-MM-yyyy") if entry.get("timestamp") else entry.get("label"),
					"stock": stock_value,
					"price": price_value,
				}
			)
			# Track if first entry was added
			if last_stock is None:
				first_entry_added = True
			last_stock = stock_value
			last_price = price_value
		else:
			if compressed:
				compressed[-1]["price"] = price_value

	# Ensure first entry is always included as opening balance
	if not first_entry_added and entries:
		first_entry = entries[0]
		first_stock = _round(first_entry.get("stock") or 0)
		first_price = first_entry.get("price")
		if first_price is not None:
			first_price = flt(first_price)
		
		compressed.insert(0, {
			"label": first_entry.get("label"),
			"date": format_datetime(first_entry.get("timestamp"), "dd-MM-yyyy") if first_entry.get("timestamp") else first_entry.get("label"),
			"stock": first_stock,
			"price": first_price,
		})

	return compressed

