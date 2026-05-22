// Copyright (c) 2026, Abbass Chokor and contributors
// For license information, please see license.txt

frappe.listview_settings['Stylus New Item Log'] = {
	add_fields: ['price', 'stock'],
	get_indicator: function (doc) {
		return [__('New'), 'blue', 'name,is,set'];
	},
	formatters: {
		code: function (value) {
			return value
				? `<span style="color: var(--blue-600, #2490ef); font-weight: 600;">${value}</span>`
				: '';
		},
	},
};
