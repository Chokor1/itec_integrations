frappe.ui.form.on('Stylus Sync Stock Setting', {
    refresh: function(frm) {
        if (frm.doc.enabled) {
            frm.add_custom_button('Run Stock Sync Now', function() {
                frappe.call({
                    method: 'itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting.run_sync',
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint('Stock sync completed!');
                        }
                    }
                });
            });
        }
    }
});
