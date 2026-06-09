# Copyright (c) 2025, Abbass Chokor and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import requests
import base64
import io
import frappe
from frappe import _
from frappe.utils import now, getdate, flt, add_days



class StylusSyncStockSetting(Document):
    pass

@frappe.whitelist()
def run_sync():
	setting = frappe.get_single("Stylus Sync Stock Setting")

	if not setting.enabled:
		return
    
	headers = {
            "Authorization": f"Basic {base64.b64encode((setting.access_key + ':').encode()).decode()}",
			"Accept": "application/json",
    		"User-Agent": "MyApp/1.0"
        }
	try:
		response = requests.get(
                "https://www.stylus.co.ao/encomendas/api/stockparceiros",
                headers=headers,
            )
		response.raise_for_status()
		data = response.json()

		if not isinstance(data, list):
			frappe.throw("Unexpected response format from Stylus API")

		history_doc = frappe.get_doc(
                {"doctype": "Stylus Stock History", "items": []}
            )

		for item in data:
			history_doc.append(
                    "items",
                    {
                        "code": item.get("CODE"),
                        "designation": item.get("DESIGNATION"),
                        "price": item.get("PRICE"),
                        "stock": item.get("STOCK"),
                        "main_category": item.get("CATEGORIA_PRINCIPAL"),
                        "brand": item.get("MARCA"),
                        "description_html": item.get("DESCRICAO"),
						"imagens": item.get("IMAGENS"),
						"imagem_capa": item.get("IMAGEM_CAPA")
                    },
                )

		history_doc.insert(ignore_permissions=True)
		_record_price_changes(history_doc)
		_record_new_items(history_doc)
		_cleanup_stylus_stock_history_duplicates(getdate(history_doc.creation))
		setting.last_inventory_sync = now()
		setting.save()
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Stylus Sync Failed")
		frappe.throw(f"Stylus Sync failed: {e}")


# Status (column D) value that marks an item as available/in stock.
_DISPONIVEL = "disponível"

# Values that the Excel export uses for "no data"; treated as blank.
_NA_VALUES = {"#N/A", "N/A", "#REF!", "#VALUE!", "-"}


def _cell(value):
	"""Trim a cell to a clean string, or None when empty."""
	if value is None:
		return None
	text = str(value).strip()
	return text or None


def _no_na(value):
	"""Collapse Excel error/placeholder markers to None."""
	if value is None:
		return None
	return None if value.strip().upper() in _NA_VALUES else value


@frappe.whitelist()
def import_manual_stock_excel(file_url=None):
	"""Build a Stylus Stock History from the manually-exported 'MAPA DE STOCKS'
	Excel file. Use this when the Stylus API is unavailable.

	Only rows whose Status (column D) is 'Disponível' are imported, and each is
	recorded with stock = 1. Column mapping:
		A -> code, C -> designation, F -> price (PVP AKZ),
		O -> main_category (Família), Q -> brand (Marca).
	Mirrors run_sync()'s post-insert steps (price-change / new-item logs and
	duplicate cleanup) so manual imports behave like API syncs."""
	import openpyxl

	setting = frappe.get_single("Stylus Sync Stock Setting")
	file_url = file_url or setting.manual_stock_import_file
	if not file_url:
		frappe.throw(_("Please attach the stock map Excel file first."))

	file_doc = frappe.get_doc("File", {"file_url": file_url})
	try:
		workbook = openpyxl.load_workbook(
			io.BytesIO(file_doc.get_content()), read_only=True, data_only=True
		)
	except Exception as e:
		frappe.throw(_("Could not read the attached file as an Excel workbook: {0}").format(e))

	worksheet = workbook.active
	rows = worksheet.iter_rows(values_only=True)

	# Locate the header row (the one carrying 'Código' and 'Status') so the
	# import survives extra banner rows at the top of the export.
	header_found = False
	for row in rows:
		labels = {(_cell(cell) or "").lower() for cell in row}
		if "status" in labels and ("código" in labels or "codigo" in labels):
			header_found = True
			break
	if not header_found:
		frappe.throw(_("Could not find the header row (expected columns 'Código' and 'Status')."))

	history_doc = frappe.get_doc({"doctype": "Stylus Stock History", "items": []})
	imported = 0
	skipped = 0
	# `rows` is now positioned just after the header, so this continues over data.
	for row in rows:
		code = _cell(row[0]) if len(row) > 0 else None
		status = _cell(row[3]) if len(row) > 3 else None
		if not code and not status:
			continue
		if (status or "").lower() != _DISPONIVEL:
			skipped += 1
			continue

		history_doc.append(
			"items",
			{
				"code": code,
				"designation": _cell(row[2]) if len(row) > 2 else None,
				"price": flt(row[5]) if len(row) > 5 else 0,
				"stock": 1,
				"main_category": _no_na(_cell(row[14])) if len(row) > 14 else None,
				"brand": _no_na(_cell(row[16])) if len(row) > 16 else None,
			},
		)
		imported += 1

	if not imported:
		frappe.throw(_("No rows with status 'Disponível' were found in the file."))

	history_doc.insert(ignore_permissions=True)
	_record_price_changes(history_doc)
	_record_new_items(history_doc)
	_cleanup_stylus_stock_history_duplicates(getdate(history_doc.creation))
	setting.last_inventory_sync = now()
	setting.save()
	frappe.db.commit()

	return {"history": history_doc.name, "imported": imported, "skipped": skipped}


def _record_price_changes(history_doc):
	"""Compare prices in the just-inserted Stylus Stock History against the most
	recent prior history and persist a Stylus Price Change Log row per item
	whose price changed."""
	previous = frappe.get_all(
		"Stylus Stock History",
		filters={"name": ["!=", history_doc.name]},
		order_by="creation desc",
		limit=1,
		pluck="name",
	)
	if not previous:
		return

	previous_name = previous[0]
	prev_rows = frappe.get_all(
		"Stylus Stock History Item",
		filters={"parent": previous_name},
		fields=["code", "price"],
	)
	prev_price_by_code = {row.code: flt(row.price) for row in prev_rows if row.code}

	sync_dt = history_doc.creation or now()

	for item in history_doc.items:
		code = item.code
		if not code or code not in prev_price_by_code:
			continue

		old_price = flt(prev_price_by_code[code])
		new_price = flt(item.price)
		if old_price == new_price:
			continue

		change_amount = new_price - old_price
		change_pct = (change_amount / old_price * 100.0) if old_price else 0.0

		log = frappe.get_doc(
			{
				"doctype": "Stylus Price Change Log",
				"code": code,
				"designation": item.designation,
				"main_category": item.main_category,
				"brand": item.brand,
				"stock_history": history_doc.name,
				"previous_stock_history": previous_name,
				"sync_datetime": sync_dt,
				"old_price": old_price,
				"new_price": new_price,
				"change_amount": change_amount,
				"change_pct": change_pct,
				"direction": "Increase" if change_amount > 0 else "Decrease",
			}
		)
		log.insert(ignore_permissions=True)


def _record_new_items(history_doc):
	"""Compare item codes in the just-inserted Stylus Stock History against the
	cumulative set of codes seen across every prior history and persist a
	Stylus New Item Log row per item whose code has never appeared before."""
	previous = frappe.get_all(
		"Stylus Stock History",
		filters={"name": ["!=", history_doc.name]},
		order_by="creation desc",
		limit=1,
		pluck="name",
	)
	if not previous:
		return

	previous_name = previous[0]
	seen_codes = _seen_codes_excluding(history_doc.name)

	sync_dt = history_doc.creation or now()

	for item in history_doc.items:
		code = item.code
		if not code or code in seen_codes:
			continue

		log = frappe.get_doc(
			{
				"doctype": "Stylus New Item Log",
				"code": code,
				"designation": item.designation,
				"main_category": item.main_category,
				"brand": item.brand,
				"stock_history": history_doc.name,
				"previous_stock_history": previous_name,
				"sync_datetime": sync_dt,
				"price": flt(item.price),
				"stock": flt(item.stock),
			}
		)
		log.insert(ignore_permissions=True)


def _seen_codes_excluding(history_name):
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT shi.code
		FROM `tabStylus Stock History Item` shi
		INNER JOIN `tabStylus Stock History` sh ON sh.name = shi.parent
		WHERE sh.name != %s AND shi.code IS NOT NULL AND shi.code != ''
		""",
		(history_name,),
	)
	return {row[0] for row in rows}


def _seen_codes_before(creation_dt):
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT shi.code
		FROM `tabStylus Stock History Item` shi
		INNER JOIN `tabStylus Stock History` sh ON sh.name = shi.parent
		WHERE sh.creation < %s AND shi.code IS NOT NULL AND shi.code != ''
		""",
		(creation_dt,),
	)
	return {row[0] for row in rows}


@frappe.whitelist()
def backfill_price_changes(from_date=None, to_date=None, run_in_background=True):
	"""Walk every Stylus Stock History record in [from_date, to_date] in
	chronological order and create Stylus Price Change Log rows for each
	consecutive pair whose price differs. Idempotent: skips a (history, code)
	pair if a log already exists for it."""
	setting = frappe.get_single("Stylus Sync Stock Setting")
	from_date = getdate(from_date or setting.backfill_from_date)
	to_date = getdate(to_date or setting.backfill_to_date)

	if not from_date or not to_date:
		frappe.throw("Please set both From Date and To Date for the backfill.")
	if from_date > to_date:
		frappe.throw("From Date must be on or before To Date.")

	if run_in_background and str(run_in_background).lower() not in ("0", "false"):
		frappe.enqueue(
			"itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting._run_backfill_price_changes",
			queue="long",
			timeout=3600,
			from_date=from_date.isoformat(),
			to_date=to_date.isoformat(),
		)
		return {"queued": True, "from_date": from_date.isoformat(), "to_date": to_date.isoformat()}

	return _run_backfill_price_changes(from_date.isoformat(), to_date.isoformat())


def _run_backfill_price_changes(from_date, to_date):
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	range_start = f"{from_date.isoformat()} 00:00:00"
	range_end = f"{to_date.isoformat()} 23:59:59"

	histories = frappe.get_all(
		"Stylus Stock History",
		filters={"creation": ["between", (range_start, range_end)]},
		order_by="creation asc",
		fields=["name", "creation"],
	)
	if len(histories) < 2:
		frappe.logger().info(
			f"Stylus backfill: nothing to do, found {len(histories)} history rows in range"
		)
		return {"queued": False, "histories": len(histories), "logs_created": 0}

	# Seed with the most recent history strictly before the range so the first
	# in-range history can also produce a log if its price differs from the
	# preceding day's snapshot.
	prior = frappe.get_all(
		"Stylus Stock History",
		filters={"creation": ["<", range_start]},
		order_by="creation desc",
		limit=1,
		fields=["name"],
	)
	prev_name = prior[0].name if prior else None
	prev_price_by_code = _price_map_for_history(prev_name) if prev_name else None

	logs_created = 0
	for hist in histories:
		current_name = hist.name
		current_rows = frappe.get_all(
			"Stylus Stock History Item",
			filters={"parent": current_name},
			fields=["code", "designation", "price", "main_category", "brand"],
		)

		if prev_price_by_code is not None:
			existing_log_codes = set(
				frappe.get_all(
					"Stylus Price Change Log",
					filters={"stock_history": current_name},
					pluck="code",
				)
			)

			for row in current_rows:
				code = row.code
				if not code or code not in prev_price_by_code:
					continue
				if code in existing_log_codes:
					continue

				old_price = flt(prev_price_by_code[code])
				new_price = flt(row.price)
				if old_price == new_price:
					continue

				change_amount = new_price - old_price
				change_pct = (change_amount / old_price * 100.0) if old_price else 0.0

				log = frappe.get_doc(
					{
						"doctype": "Stylus Price Change Log",
						"code": code,
						"designation": row.designation,
						"main_category": row.main_category,
						"brand": row.brand,
						"stock_history": current_name,
						"previous_stock_history": prev_name,
						"sync_datetime": hist.creation,
						"old_price": old_price,
						"new_price": new_price,
						"change_amount": change_amount,
						"change_pct": change_pct,
						"direction": "Increase" if change_amount > 0 else "Decrease",
					}
				)
				log.insert(ignore_permissions=True)
				logs_created += 1

		prev_name = current_name
		prev_price_by_code = {r.code: flt(r.price) for r in current_rows if r.code}

	frappe.db.commit()
	frappe.logger().info(
		f"Stylus backfill done: {len(histories)} histories scanned, {logs_created} price logs created"
	)
	return {"queued": False, "histories": len(histories), "logs_created": logs_created}


def _price_map_for_history(history_name):
	rows = frappe.get_all(
		"Stylus Stock History Item",
		filters={"parent": history_name},
		fields=["code", "price"],
	)
	return {r.code: flt(r.price) for r in rows if r.code}


@frappe.whitelist()
def backfill_new_items(from_date=None, to_date=None, run_in_background=True):
	"""Walk every Stylus Stock History record in [from_date, to_date] in
	chronological order and create Stylus New Item Log rows for each item code
	that appears for the first time across all prior history (not just the
	immediately preceding snapshot). Idempotent: skips a (history, code) pair
	if a log already exists for it."""
	setting = frappe.get_single("Stylus Sync Stock Setting")
	from_date = getdate(from_date or setting.new_items_backfill_from_date)
	to_date = getdate(to_date or setting.new_items_backfill_to_date)

	if not from_date or not to_date:
		frappe.throw("Please set both From Date and To Date for the new-items backfill.")
	if from_date > to_date:
		frappe.throw("From Date must be on or before To Date.")

	if run_in_background and str(run_in_background).lower() not in ("0", "false"):
		frappe.enqueue(
			"itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting._run_backfill_new_items",
			queue="long",
			timeout=3600,
			from_date=from_date.isoformat(),
			to_date=to_date.isoformat(),
		)
		return {"queued": True, "from_date": from_date.isoformat(), "to_date": to_date.isoformat()}

	return _run_backfill_new_items(from_date.isoformat(), to_date.isoformat())


def _run_backfill_new_items(from_date, to_date):
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	range_start = f"{from_date.isoformat()} 00:00:00"
	range_end = f"{to_date.isoformat()} 23:59:59"

	histories = frappe.get_all(
		"Stylus Stock History",
		filters={"creation": ["between", (range_start, range_end)]},
		order_by="creation asc",
		fields=["name", "creation"],
	)
	if not histories:
		frappe.logger().info("Stylus new-item backfill: nothing to do, no history rows in range")
		return {"queued": False, "histories": 0, "logs_created": 0}

	prior = frappe.get_all(
		"Stylus Stock History",
		filters={"creation": ["<", range_start]},
		order_by="creation desc",
		limit=1,
		fields=["name"],
	)
	prev_name = prior[0].name if prior else None
	# Cumulative set of every code ever seen strictly before the range. An item
	# only counts as "new" if its code has never appeared in any earlier
	# snapshot — not just the immediately previous one.
	seen_codes = _seen_codes_before(range_start)
	has_prior = bool(prev_name)

	logs_created = 0
	for hist in histories:
		current_name = hist.name
		current_rows = frappe.get_all(
			"Stylus Stock History Item",
			filters={"parent": current_name},
			fields=["code", "designation", "price", "stock", "main_category", "brand"],
		)

		if has_prior:
			existing_log_codes = set(
				frappe.get_all(
					"Stylus New Item Log",
					filters={"stock_history": current_name},
					pluck="code",
				)
			)

			for row in current_rows:
				code = row.code
				if not code or code in seen_codes:
					continue
				if code in existing_log_codes:
					continue

				log = frappe.get_doc(
					{
						"doctype": "Stylus New Item Log",
						"code": code,
						"designation": row.designation,
						"main_category": row.main_category,
						"brand": row.brand,
						"stock_history": current_name,
						"previous_stock_history": prev_name,
						"sync_datetime": hist.creation,
						"price": flt(row.price),
						"stock": flt(row.stock),
					}
				)
				log.insert(ignore_permissions=True)
				logs_created += 1

		seen_codes.update(r.code for r in current_rows if r.code)
		prev_name = current_name
		has_prior = True

	frappe.db.commit()
	frappe.logger().info(
		f"Stylus new-item backfill done: {len(histories)} histories scanned, {logs_created} new-item logs created"
	)
	return {"queued": False, "histories": len(histories), "logs_created": logs_created}


def _cleanup_stylus_stock_history_duplicates(target_date=None):
	if not target_date:
		target_date = getdate()

	target_date = getdate(target_date)
	date_str = target_date.isoformat()
	histories = frappe.get_all(
		"Stylus Stock History",
		filters={
			"creation": [
				"between",
				(f"{date_str} 00:00:00", f"{date_str} 23:59:59"),
			]
		},
		order_by="creation desc",
		fields=["name"],
	)

	if len(histories) <= 1:
		return

	names_to_remove = [row.get("name") for row in histories[1:] if row.get("name")]
	if not names_to_remove:
		return

	frappe.db.delete(
		"Stylus Stock History Item",
		{"parent": ["in", names_to_remove]},
	)
	# Null out link fields on price change logs so they don't point at rows
	# we're about to delete.
	if frappe.db.exists("DocType", "Stylus Price Change Log"):
		frappe.db.set_value(
			"Stylus Price Change Log",
			{"stock_history": ["in", names_to_remove]},
			"stock_history",
			None,
			update_modified=False,
		)
		frappe.db.set_value(
			"Stylus Price Change Log",
			{"previous_stock_history": ["in", names_to_remove]},
			"previous_stock_history",
			None,
			update_modified=False,
		)
	if frappe.db.exists("DocType", "Stylus New Item Log"):
		frappe.db.set_value(
			"Stylus New Item Log",
			{"stock_history": ["in", names_to_remove]},
			"stock_history",
			None,
			update_modified=False,
		)
		frappe.db.set_value(
			"Stylus New Item Log",
			{"previous_stock_history": ["in", names_to_remove]},
			"previous_stock_history",
			None,
			update_modified=False,
		)
	frappe.db.delete(
		"Stylus Stock History",
		{"name": ["in", names_to_remove]},
	)
