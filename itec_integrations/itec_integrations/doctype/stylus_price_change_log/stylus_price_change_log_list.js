// Copyright (c) 2026, Abbass Chokor and contributors
// For license information, please see license.txt

frappe.listview_settings['Stylus Price Change Log'] = {
	get_indicator: function (doc) {
		if (doc.direction === 'Increase') {
			return [__('Increase'), 'green', 'direction,=,Increase'];
		}
		if (doc.direction === 'Decrease') {
			return [__('Decrease'), 'red', 'direction,=,Decrease'];
		}
		return [doc.direction || '', 'gray', 'direction,=,' + (doc.direction || '')];
	},
};
