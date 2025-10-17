// Copyright (c) 2025, Abbass Chokor and contributors
// For license information, please see license.txt

frappe.ui.form.on('HP Amplify', {
	refresh: function(frm) {
		// Add beautiful primary Export to Excel button
		frm.page.set_primary_action(__('Export to Excel'), function() {
			// Validate dates before export
			if (!frm.doc.from_date || !frm.doc.to_date) {
				frappe.msgprint(__('Please select From Date and To Date before exporting.'));
				return;
			}
			
			// Validate reporter_id
			if (!frm.doc.reporter_id) {
				frappe.msgprint(__('Please enter Reporter ID before exporting.'));
				return;
			}
			
			// Show custom loading message
			frappe.show_alert({
				message: __('⚡ ISOFT - Powering Your Business Intelligence | Generating HP Amplify Report...'),
				indicator: 'blue'
			});
			
			// Call server method to generate Excel
			frappe.call({
				method: 'itec_integrations.hp_partnership.doctype.hp_amplify.hp_amplify.export_hp_amplify_report',
				args: {
					from_date: frm.doc.from_date,
					to_date: frm.doc.to_date,
					warehouses: frm.doc.warehouses,
					suppliers: frm.doc.suppliers,
					brands: frm.doc.brands,
					item_groups: frm.doc.item_groups,
					reporter_id: frm.doc.reporter_id,
					items_force_add: frm.doc.items_force_add,
					items_force_remove: frm.doc.items_force_remove
				},
				freeze: true,
				callback: function(r) {
					if (r.message) {
						// Show success message
						frappe.show_alert({
							message: __('✅ ISOFT Report Generated Successfully!'),
							indicator: 'green'
						});
						
						// Open the file in a new window
						window.open(frappe.urllib.get_full_url(
							"/api/method/frappe.core.doctype.file.file.download_file?"
							+ "file_url=" + encodeURIComponent(r.message)
						));
					}
				},
				error: function(r) {
					frappe.show_alert({
						message: __('❌ ISOFT Report Generation Failed'),
						indicator: 'red'
					});
				}
			});
		});
		
		// Change the button icon to Excel icon
		frm.page.btn_primary.addClass('btn-primary');
		frm.page.btn_primary.find('.btn-label').prepend('<i class="fa fa-file-excel-o" style="margin-right: 5px;"></i>');
	}
});
