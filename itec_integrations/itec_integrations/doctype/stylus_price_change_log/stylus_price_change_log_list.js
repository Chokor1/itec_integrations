// Copyright (c) 2026, Abbass Chokor and contributors
// For license information, please see license.txt

frappe.listview_settings['Stylus Price Change Log'] = {
	add_fields: ['direction', 'change_amount', 'change_pct'],
	get_indicator: function (doc) {
		if (doc.direction === 'Increase') {
			return [__('Increase'), 'green', 'direction,=,Increase'];
		}
		if (doc.direction === 'Decrease') {
			return [__('Decrease'), 'red', 'direction,=,Decrease'];
		}
		return [__(doc.direction || '-'), 'gray', 'direction,=,' + (doc.direction || '')];
	},
	formatters: {
		direction: function (value) {
			if (value === 'Increase') {
				return `<span style="color: var(--green-600, #1f9d55); font-weight: 600;">${__('Increase')}</span>`;
			}
			if (value === 'Decrease') {
				return `<span style="color: var(--red-600, #cf3c4f); font-weight: 600;">${__('Decrease')}</span>`;
			}
			return value || '';
		},
		change_amount: function (value, df, doc) {
			const color = doc.direction === 'Increase'
				? 'var(--green-600, #1f9d55)'
				: doc.direction === 'Decrease'
					? 'var(--red-600, #cf3c4f)'
					: '';
			const formatted = format_currency(value, doc.currency);
			return color
				? `<span style="color: ${color}; font-weight: 600;">${formatted}</span>`
				: formatted;
		},
		change_pct: function (value, df, doc) {
			const color = doc.direction === 'Increase'
				? 'var(--green-600, #1f9d55)'
				: doc.direction === 'Decrease'
					? 'var(--red-600, #cf3c4f)'
					: '';
			const formatted = (flt(value, 2)) + '%';
			return color
				? `<span style="color: ${color}; font-weight: 600;">${formatted}</span>`
				: formatted;
		},
	},
};
