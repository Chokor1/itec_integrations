// Copyright (c) 2025, Abbass Chokor and contributors
// For license information, please see license.txt

frappe.ui.form.on('NCR Sync Setting', {
	sync_now: function (frm) {
		frappe.call({
			method: 'itec_integrations.itec_integrations.doctype.ncr_sync_setting.ncr_sync_setting.run_sync',
			freeze: true,
			freeze_message: __('Syncing with NCR Website, please wait...'),
			callback: function (r) {
				console.log(r);
				if (r.message === "success") {
					frappe.alert({
						message: __('Sync completed successfully!'),
						indicator: 'green'
					});
					frm.reload_doc();
				} else {
					frappe.msgprint(__('Sync failed. Check error logs.'));
				}
			}
		});
	}
});

