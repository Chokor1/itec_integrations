// Copyright (c) 2025, Abbass Chokor and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stylus Sync Stock Setting', {
	refresh: function (frm) {
		frm.add_custom_button(__('Import Manual Stock'), function () {
			if (!frm.doc.manual_stock_import_file) {
				frappe.msgprint(__('Please attach the stock map Excel file in the Manual Stock Import section first.'));
				return;
			}

			frappe.confirm(
				__('Import a new Stylus Stock History from the attached Excel? Only rows with Status "Disponível" are imported (each with stock = 1), using column F as the price.'),
				function () {
					frappe.call({
						method: 'itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting.import_manual_stock_excel',
						args: {
							file_url: frm.doc.manual_stock_import_file,
						},
						freeze: true,
						freeze_message: __('Importing stock from Excel...'),
						callback: function (r) {
							if (r.message) {
								frappe.msgprint(__('Manual import complete. History: {0}. Rows imported (Disponível): {1}. Rows skipped: {2}.',
									[r.message.history, r.message.imported, r.message.skipped]));
								frm.reload_doc();
							}
						},
					});
				}
			);
		}, __('Manual Stock Import'));

		frm.add_custom_button(__('Run Backfill'), function () {
			if (!frm.doc.backfill_from_date || !frm.doc.backfill_to_date) {
				frappe.msgprint(__('Please set both From Date and To Date before running the backfill.'));
				return;
			}
			if (frm.doc.backfill_from_date > frm.doc.backfill_to_date) {
				frappe.msgprint(__('From Date must be on or before To Date.'));
				return;
			}

			frappe.confirm(
				__('Backfill price changes from {0} to {1}? This walks existing Stylus Stock History records and creates Stylus Price Change Log rows for any price differences. Existing logs will be preserved.',
					[frappe.datetime.str_to_user(frm.doc.backfill_from_date),
					 frappe.datetime.str_to_user(frm.doc.backfill_to_date)]),
				function () {
					frappe.call({
						method: 'itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting.backfill_price_changes',
						args: {
							from_date: frm.doc.backfill_from_date,
							to_date: frm.doc.backfill_to_date,
							run_in_background: 1,
						},
						freeze: true,
						freeze_message: __('Queueing backfill...'),
						callback: function (r) {
							if (r.message && r.message.queued) {
								frappe.show_alert({
									message: __('Backfill queued in the background. Check the Stylus Price Change Log list once it finishes.'),
									indicator: 'green',
								}, 7);
							} else if (r.message) {
								frappe.msgprint(__('Backfill complete. Histories scanned: {0}. Logs created: {1}.',
									[r.message.histories, r.message.logs_created]));
							}
						},
					});
				}
			);
		}, __('Backfill Price Changes'));

		frm.add_custom_button(__('Run Backfill'), function () {
			if (!frm.doc.new_items_backfill_from_date || !frm.doc.new_items_backfill_to_date) {
				frappe.msgprint(__('Please set both From Date and To Date in the Backfill New Items section before running the backfill.'));
				return;
			}
			if (frm.doc.new_items_backfill_from_date > frm.doc.new_items_backfill_to_date) {
				frappe.msgprint(__('From Date must be on or before To Date.'));
				return;
			}

			frappe.confirm(
				__('Backfill new items from {0} to {1}? This walks existing Stylus Stock History records and creates Stylus New Item Log rows for any item codes that appear for the first time across all prior history. Existing logs will be preserved.',
					[frappe.datetime.str_to_user(frm.doc.new_items_backfill_from_date),
					 frappe.datetime.str_to_user(frm.doc.new_items_backfill_to_date)]),
				function () {
					frappe.call({
						method: 'itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting.backfill_new_items',
						args: {
							from_date: frm.doc.new_items_backfill_from_date,
							to_date: frm.doc.new_items_backfill_to_date,
							run_in_background: 1,
						},
						freeze: true,
						freeze_message: __('Queueing backfill...'),
						callback: function (r) {
							if (r.message && r.message.queued) {
								frappe.show_alert({
									message: __('Backfill queued in the background. Check the Stylus New Item Log list once it finishes.'),
									indicator: 'green',
								}, 7);
							} else if (r.message) {
								frappe.msgprint(__('Backfill complete. Histories scanned: {0}. Logs created: {1}.',
									[r.message.histories, r.message.logs_created]));
							}
						},
					});
				}
			);
		}, __('Backfill New Items'));
	},
});
