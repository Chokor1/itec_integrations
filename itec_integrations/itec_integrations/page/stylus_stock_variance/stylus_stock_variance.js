frappe.provide('itec_integrations.pages');

frappe.pages['stylus-stock-variance'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Stylus Historical Stock Activity'),
		single_column: true,
	});

	new itec_integrations.pages.StylusStockVariance(wrapper);
};

itec_integrations.pages.StylusStockVariance = class StylusStockVariance {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.filter_controls = {};
		this.request_id = 0;
		this.charts = [];

		this.wrapper.addClass('stylus-stock-variance-wrapper');

		this.inject_styles();
		this.make_filters();
		this.make_layout();
		this.make_chart_filter();
		this.set_default_filters();
		this.show_state('info', __('Select the filters above and click Run to generate the tables and charts.'));
	}

	inject_styles() {
		if (window.__stylusStockVarianceStyles) return;
		const styles = `
			.stylus-stock-variance-wrapper .stylus-sv-main {
				margin-top: 16px;
			}

			.stylus-stock-variance-wrapper .stylus-sv-state {
				padding: 12px 16px;
				border: 1px dashed var(--gray-400);
				border-radius: 6px;
				background: #fff;
				margin-bottom: 16px;

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.65);
					border-color: rgba(148, 163, 184, 0.4);
					color: #cbd5f5;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-state[data-state="loading"] {
				border-color: var(--blue-400);
				color: var(--blue-600);
			}

			.stylus-stock-variance-wrapper .stylus-sv-state[data-state="error"] {
				border-color: var(--red-400);
				color: var(--red-600);

				@media (prefers-color-scheme: dark) {
					color: #fecaca;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-card {
				background: #fff;
				border-radius: 10px;
				box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
				padding: 20px;
				margin-bottom: 24px;
				border: 1px solid var(--gray-300);
				transition: transform 0.25s ease, opacity 0.25s ease;

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.75);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.55);
					border-color: rgba(148, 163, 184, 0.2);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-card-header {
				display: flex;
				flex-direction: column;
				gap: 6px;
				margin-bottom: 16px;
			}

			.stylus-stock-variance-wrapper .stylus-sv-item-title {
				font-size: 1.05rem;
				font-weight: 600;
				color: var(--gray-900);

				@media (prefers-color-scheme: dark) {
					color: #e2e8f0;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-item-title .code {
				font-family: 'Space Mono', monospace;
				font-size: 0.9rem;
				background: var(--gray-100);
				padding: 2px 6px;
				border-radius: 4px;
				margin-right: 8px;

				@media (prefers-color-scheme: dark) {
					background: rgba(148, 163, 184, 0.2);
					color: #cbd5f5;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-meta {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
				gap: 10px 16px;
				margin-top: 8px;
			}

			.stylus-stock-variance-wrapper .stylus-sv-meta-line {
				display: flex;
				flex-direction: column;
				gap: 4px;
				background: var(--gray-50);
				border-radius: 8px;
				padding: 8px 12px;
				border: 1px solid var(--gray-100);

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.5);
					border-color: rgba(148, 163, 184, 0.25);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-meta-line .meta-label {
				font-size: 0.7rem;
				text-transform: uppercase;
				letter-spacing: 0.08em;
				color: var(--gray-600);

				@media (prefers-color-scheme: dark) {
					color: #94a3b8;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-meta-line .meta-value {
				font-size: 0.95rem;
				font-weight: 600;
				color: var(--gray-900);
				white-space: pre-line;

				@media (prefers-color-scheme: dark) {
					color: #e2e8f0;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-chart-filter {
				display: flex;
				align-items: center;
				gap: 10px;
				margin: 10px 0 18px;
			}

			.stylus-stock-variance-wrapper .stylus-sv-chart-filter.hidden {
				display: none;
			}

			.stylus-stock-variance-wrapper .stylus-sv-chart-filter label {
				font-size: 0.85rem;
				color: var(--gray-700);
				white-space: nowrap;
				font-weight: 600;

				@media (prefers-color-scheme: dark) {
					color: #94a3b8;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-chart-filter input {
				flex: 1;
				border: 1px solid var(--gray-300);
				border-radius: 999px;
				padding: 4px 14px;
				height: 32px;

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.7);
					color: #e2e8f0;
					border-color: rgba(148, 163, 184, 0.35);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-card-body {
				display: flex;
				flex-direction: column;
				gap: 22px;
			}

			.stylus-stock-variance-wrapper .stylus-sv-section {
				width: 100%;
				background: #fff;
				border-radius: 16px;
				padding: 18px;
				box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
				transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, border 0.2s ease;
			}

			.stylus-stock-variance-wrapper .stylus-sv-section table {
				color: inherit;
			}

			.stylus-stock-variance-wrapper .stylus-sv-section table th,
			.stylus-stock-variance-wrapper .stylus-sv-section table td {
				color: inherit;
			}

			@media (prefers-color-scheme: dark) {
				.stylus-stock-variance-wrapper .stylus-sv-card-body {
					background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(8, 13, 23, 0.75));
					border-radius: 24px;
					padding: 20px;
					gap: 22px;
					box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
				}

				.stylus-stock-variance-wrapper .stylus-sv-section {
					background: rgba(15, 23, 42, 0.98);
					border: 1px solid rgba(148, 163, 184, 0.35);
					box-shadow: 0 25px 55px rgba(0, 0, 0, 0.75);
					color: #f8fafc;
				}

				.stylus-stock-variance-wrapper .stylus-sv-section .stylus-sv-section-title {
					color: #cffafe;
				}
			}

			.stylus-stock-variance-wrapper .scrollable-x {
				overflow-x: auto;
			}

			.stylus-stock-variance-wrapper .stylus-sv-section-title {
				text-transform: uppercase;
				font-size: 0.75rem;
				letter-spacing: 0.08em;
				color: var(--gray-600);
				margin-bottom: 6px;

				@media (prefers-color-scheme: dark) {
					color: #94a3b8;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table {
				width: 100%;
				border-collapse: collapse;
				margin-bottom: 12px;
				font-size: 0.9rem;
				background: #fff;
				border-radius: 8px;
				overflow: hidden;

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.65);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table th,
			.stylus-stock-variance-wrapper .stylus-sv-table td {
				padding: 8px;
				border: 1px solid var(--gray-200);
				vertical-align: middle;
				background: #fff;

				@media (prefers-color-scheme: dark) {
					background: transparent;
					border-color: rgba(148, 163, 184, 0.18);
					color: inherit;
				}
			}
			@media (prefers-color-scheme: dark) {
				.stylus-stock-variance-wrapper .stylus-sv-table th.opening-header,
				.stylus-stock-variance-wrapper .stylus-sv-table td.opening-cell {
					color: #fef9c3;
				}

				.stylus-stock-variance-wrapper .stylus-sv-table th.current-balance-header,
				.stylus-stock-variance-wrapper .stylus-sv-table td.current-balance-cell {
					color: #bae6fd;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table thead {
				background: linear-gradient(90deg, rgba(36,144,239,0.08), rgba(36,144,239,0.02));
				color: var(--gray-900);

				@media (prefers-color-scheme: dark) {
					background: linear-gradient(90deg, rgba(36,144,239,0.25), rgba(36,144,239,0.05));
					color: #f8fafc;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .metric-label {
				font-size: 0.8rem;
				text-transform: uppercase;
				letter-spacing: 0.08em;
				font-weight: 600;
				color: var(--gray-700);
				white-space: nowrap;

				@media (prefers-color-scheme: dark) {
					color: #cbd5f5;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .total-negative {
				background: rgba(220, 38, 38, 0.08);
				color: #991b1b;

				@media (prefers-color-scheme: dark) {
					background: rgba(239, 68, 68, 0.15);
					color: #fecaca;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .total-positive {
				background: rgba(34, 197, 94, 0.08);
				color: #166534;

				@media (prefers-color-scheme: dark) {
					background: rgba(34, 197, 94, 0.15);
					color: #bbf7d0;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .positive {
				color: var(--green-600);
				font-weight: 600;

				@media (prefers-color-scheme: dark) {
					color: #86efac;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .negative {
				color: var(--red-600);
				font-weight: 600;

				@media (prefers-color-scheme: dark) {
					color: #f87171;
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table tbody tr:nth-child(even) td {
				background: #f8fafc;

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.45);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .totals-row td {
				font-weight: 600;
				background: var(--gray-50);
				border-top: 2px solid var(--gray-200);

				@media (prefers-color-scheme: dark) {
					background: rgba(15, 23, 42, 0.65);
					border-color: rgba(148, 163, 184, 0.25);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .totals-label {
				display: block;
				font-size: 0.75rem;
				margin-bottom: 2px;
				color: var(--gray-700);
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .totals-row td:first-child {
				text-align: right;
				font-size: 0.85rem;
				letter-spacing: 0.02em;
			}

			.stylus-stock-variance-wrapper .stylus-sv-table td.number-cell {
				text-align: right;
				font-variant-numeric: tabular-nums;
				font-weight: 600;
			}

			.stylus-stock-variance-wrapper .stylus-sv-table td.text-center {
				text-align: center;
			}

			.stylus-stock-variance-wrapper .stylus-sv-table .placeholder-cell {
				color: var(--gray-400);
			}

			@media (prefers-color-scheme: dark) {
				.stylus-stock-variance-wrapper .stylus-sv-table .placeholder-cell {
					color: rgba(148, 163, 184, 0.75);
				}
			}

			.stylus-stock-variance-wrapper .stylus-sv-chart-wrapper {
				min-height: 240px;
			}

			.stylus-stock-variance-wrapper .stylus-sv-chart-wrapper canvas {
				max-width: 100%;
			}

			@media (max-width: 992px) {
				.stylus-stock-variance-wrapper .stylus-sv-chart-wrapper {
					margin-top: 8px;
				}
			}
		`;

		frappe.dom.set_style(styles);
		window.__stylusStockVarianceStyles = true;
	}

	make_filters() {
		const field_definitions = [
			{
				fieldname: 'from_date',
				fieldtype: 'Date',
				label: __('From Date'),
				reqd: 1,
			},
			{
				fieldname: 'to_date',
				fieldtype: 'Date',
				label: __('To Date'),
				reqd: 1,
			},
			{
				fieldname: 'code',
				fieldtype: 'Data',
				label: __('Code'),
				placeholder: __('Comma separated codes'),
			},
			{
				fieldname: 'designation',
				fieldtype: 'Data',
				label: __('Designation'),
				placeholder: __('Comma separated values'),
			},
			{
				fieldname: 'main_category',
				fieldtype: 'Data',
				label: __('Categoria Principal'),
				placeholder: __('Comma separated values'),
			},
			{
				fieldname: 'brand',
				fieldtype: 'Data',
				label: __('Marca'),
				placeholder: __('Comma separated values'),
			},
		];

		field_definitions.forEach((df) => {
			this.filter_controls[df.fieldname] = this.page.add_field(df);
		});

		this.page.set_primary_action(__('Run'), () => this.fetch_data());
		this.page.set_secondary_action(__('Reset Filters'), () => this.reset_filters());
	}

	make_layout() {
		this.$main = $('<div class="stylus-sv-main"></div>').appendTo(this.page.main);
		this.$state = $('<div class="stylus-sv-state small text-muted"></div>').appendTo(this.$main);
		this.$chartFilter = $('<div class="stylus-sv-chart-filter hidden"></div>').appendTo(this.$main);
		this.$chartFilterLabel = $('<label></label>')
			.text(__('Filter charts'))
			.appendTo(this.$chartFilter);
		const chartFilterInput = $('<input type="text" placeholder="' +
			__('Type to filter by code, designation, brand...') +
			'"/>').appendTo(this.$chartFilter);
		this.$chartFilterInput = chartFilterInput;
		this.$results = $('<div class="stylus-sv-results"></div>').appendTo(this.$main);

		const applyFilter = (value) => {
			this.apply_card_filter(value);
		};

		const handler = frappe.utils && frappe.utils.debounce
			? frappe.utils.debounce((e) => applyFilter(e.target.value), 200)
			: (e) => applyFilter(e.target.value);

		chartFilterInput.on('input', handler);
	}

	make_chart_filter() {
		this.chart_filter_value = '';
	}

	set_default_filters() {
		const today = frappe.datetime.get_today();
		const year = today.split('-')[0];
		const year_start = `${year}-01-01`;

		this.filter_controls.from_date.set_value(year_start);
		this.filter_controls.to_date.set_value(today);
		['code', 'designation', 'main_category', 'brand'].forEach((field) => {
			if (this.filter_controls[field]) {
				this.filter_controls[field].set_value('');
			}
		});
	}

	reset_filters() {
		this.set_default_filters();
		this.reset_charts();
		this.$results.empty();
		this.show_state('info', __('Filters reset. Click Run to refresh the dashboard.'));
	}

	get_filter_values() {
		const from_date = this.filter_controls.from_date.get_value();
		const to_date = this.filter_controls.to_date.get_value();

		if (!from_date || !to_date) {
			frappe.msgprint(__('Please select both From Date and To Date.'));
			return null;
		}

		const filters = { from_date, to_date };

		['code', 'designation', 'main_category', 'brand'].forEach((field) => {
			const control = this.filter_controls[field];
			if (!control) return;

			const value = control.get_value();
			const parsed = this.parse_multi_value(value);

			if (parsed.length) {
				filters[field] = parsed;
			}
		});

		return filters;
	}

	parse_multi_value(value) {
		if (!value) {
			return [];
		}

		if (Array.isArray(value)) {
			return value.map((val) => val && val.trim()).filter(Boolean);
		}

		return value
			.split(/[\n,;]+/)
			.map((val) => val && val.trim())
			.filter(Boolean);
	}

	fetch_data() {
		const filters = this.get_filter_values();
		if (!filters) return;

		this.request_id += 1;
		const current_request = this.request_id;

		this.reset_charts();
		this.$results.empty();
		this.show_state('loading', __('Fetching Stylus stock history...'));

		frappe.call({
			method: 'itec_integrations.itec_integrations.page.stylus_stock_variance.stylus_stock_variance.fetch_stock_variance',
			args: { filters },
			freeze: false,
			callback: (response) => {
				if (current_request !== this.request_id) {
					return;
				}

				const items = response?.message?.items || [];
				if (!items.length) {
					this.show_state('info', __('No stock records found for the selected filters.'));
					return;
				}

				this.hide_state();
				this.render_items(items);
			},
			error: (error) => {
				if (current_request !== this.request_id) {
					return;
				}
				const message =
					(error && (error.message || error._server_messages)) ||
					__('Unable to load the Stylus stock history. Please try again.');
				this.show_state('error', message);
				frappe.show_alert({ message, indicator: 'red' }, 7);
			},
		});
	}

	show_state(state, message) {
		this.$state
			.attr('data-state', state)
			.text(message)
			.show();
	}

	hide_state() {
		this.$state.hide();
	}

	reset_charts() {
		if (this.charts?.length) {
			this.charts.forEach((chart) => {
				if (chart && chart.destroy) {
					chart.destroy();
				}
			});
		}
		this.charts = [];
	}

	render_items(items) {
		this.$results.empty();
		let rendered_count = 0;

		items.forEach((item) => {
			const has_differences = (item.differences || []).length > 0;
			if (!has_differences) {
				return;
			}

			const card = $('<div class="stylus-sv-card"></div>').appendTo(this.$results);
			const searchText = [
				item.code || '',
				item.designation || '',
				item.brand || '',
				item.main_category || '',
			]
				.join(' ')
				.toLowerCase();
			card.data('searchText', searchText);

			this.render_header(item, card);

			const body = $('<div class="stylus-sv-card-body"></div>').appendTo(card);
			const tableSection = $('<div class="stylus-sv-section stylus-sv-table-section scrollable-x"></div>').appendTo(body);
			const chartSection = $('<div class="stylus-sv-section stylus-sv-chart-wrapper"></div>').appendTo(body);

			tableSection.append(`<div class="stylus-sv-section-title">${__('Variance Timeline')}</div>`);
			chartSection.append(`<div class="stylus-sv-section-title">${__('Stock Balance')}</div>`);

			this.render_table(item, tableSection);
			const chart = this.render_chart(item, chartSection);
			if (chart) {
				this.charts.push(chart);
			}

			rendered_count += 1;
		});

		if (!rendered_count) {
			this.show_state('info', __('No stock deviations found for the selected filters.'));
			this.$chartFilter.addClass('hidden');
			this.chart_filter_value = '';
			this.$chartFilterInput && this.$chartFilterInput.val('');
		} else {
			this.hide_state();
			this.$chartFilter.removeClass('hidden');
			this.apply_card_filter(this.chart_filter_value || '');
		}
	}

	apply_card_filter(raw_value) {
		const query = (raw_value || '').trim().toLowerCase();
		this.chart_filter_value = query;

		if (this.$chartFilterInput && this.$chartFilterInput.val() !== raw_value) {
			this.$chartFilterInput.val(raw_value);
		}

		const cards = this.$results.find('.stylus-sv-card');
		if (!cards.length) return;

		cards.each((_, el) => {
			const card = $(el);
			const searchable = card.data('searchText') || '';
			const matches = !query || searchable.includes(query);
			const isHidden = card.data('isHidden') === true;

			if (matches && isHidden) {
				card.data('isHidden', false);
				card.stop(true, true).slideDown(200);
			} else if (!matches && !isHidden) {
				card.data('isHidden', true);
				card.stop(true, true).slideUp(200);
			} else if (matches && !isHidden && !card.is(':visible')) {
				card.show();
			}
		});
	}

	render_header(item, parent) {
		const header = $('<div class="stylus-sv-card-header"></div>').appendTo(parent);
		const title = $(`
			<div class="stylus-sv-item-title">
				<span class="code">${frappe.utils.escape_html(item.code || '')}</span>
				<span>${frappe.utils.escape_html(item.designation || '')}</span>
			</div>
		`).appendTo(header);

		if (!item.designation) {
			title.find('span').eq(1).addClass('text-muted').text(__('No designation'));
		}

		const meta = $('<div class="stylus-sv-meta"></div>').appendTo(header);
		this.append_meta_line(meta, __('Categoria'), item.main_category);
		this.append_meta_line(meta, __('Marca'), item.brand);

		const price_display =
			item.price || item.price === 0 ? this.format_currency(item.price) : null;
		this.append_meta_line(meta, __('Price'), price_display);
		this.append_meta_line(meta, __('Last entry'), item.last_updated);

		if (!meta.children().length) {
			meta.remove();
		}
	}

	render_table(item, parent) {
		const snapshots = (item.history || []).map((entry) => {
			const priceValue =
				entry.price !== undefined && entry.price !== null ? Number(entry.price) : null;
			return {
				label: entry.label,
				date: entry.date || this.extract_date_from_label(entry.label),
				stock: Number(entry.stock) || 0,
				price: priceValue,
			};
		});

		if (!snapshots.length) {
			$(
				`<div class="text-muted small">${__(
					'No stock deviations detected in this period.'
				)}</div>`
			).appendTo(parent);
			return;
		}

		const differences = item.differences || [];
		const varianceByDate = {};
		differences.forEach((diff) => {
			const key = diff.date || this.extract_date_from_label(diff.period);
			varianceByDate[key] = Number(diff.difference) || 0;
		});

		const table = $(
			'<table class="stylus-sv-table table table-bordered table-sm"></table>'
		).appendTo(parent);

		const thead = $('<thead></thead>').appendTo(table);
		const header_row = $('<tr></tr>').appendTo(thead);
		header_row.append(`<th>${__('Metric')}</th>`);

		const dates = snapshots.map((snapshot) => snapshot.date || snapshot.label);
		dates.forEach((date_label) => {
			header_row.append(`<th>${frappe.utils.escape_html(date_label)}</th>`);
		});
		header_row.append(`<th>${__('Out')}</th>`);
		header_row.append(`<th>${__('In')}</th>`);
		header_row.append(`<th>${__('Current Balance')}</th>`);

		const tbody = $('<tbody></tbody>').appendTo(table);
		const totals = item.totals || {};
		const total_positive = Number(totals.positive || 0);
		const total_negative = Math.abs(Number(totals.negative || 0));
		const current_balance = snapshots[snapshots.length - 1]?.stock || 0;

		const variance_row = $('<tr class="variance-row"></tr>').appendTo(tbody);
		$('<td class="metric-label"></td>').text(__('Variance')).appendTo(variance_row);

		snapshots.forEach((snapshot, index) => {
			const cell = $('<td class="number-cell"></td>').appendTo(variance_row);
			if (index === 0) {
				cell.addClass('placeholder-cell').text('—');
				return;
			}

			const value = varianceByDate[snapshot.date];
			if (value === undefined || value === null) {
				cell.addClass('placeholder-cell').text('—');
				return;
			}

			cell.addClass(value >= 0 ? 'positive' : 'negative');
			this.render_number_cell(cell, value, { show_sign: true });
		});
		this.append_summary_placeholders(variance_row);

		const balance_row = $('<tr class="balance-row"></tr>').appendTo(tbody);
		$('<td class="metric-label"></td>').text(__('Balance')).appendTo(balance_row);

		snapshots.forEach((snapshot, index) => {
			const cell = $('<td class="number-cell"></td>').appendTo(balance_row);
			// Ensure first entry balance is always displayed correctly
			const stockValue = snapshot.stock !== undefined && snapshot.stock !== null 
				? Number(snapshot.stock) 
				: 0;
			this.render_number_cell(cell, stockValue, { show_sign: false, absolute: false });
		});
		this.append_summary_placeholders(balance_row);

		const price_row = $('<tr class="price-row"></tr>').appendTo(tbody);
		$('<td class="metric-label"></td>').text(__('Price')).appendTo(price_row);

		snapshots.forEach((snapshot) => {
			const priceCell = $('<td class="number-cell"></td>').appendTo(price_row);
			if (
				snapshot.price !== undefined &&
				snapshot.price !== null &&
				!Number.isNaN(Number(snapshot.price))
			) {
				priceCell.text(this.format_currency(snapshot.price));
			} else {
				priceCell.addClass('placeholder-cell').text('—');
			}
		});
		this.append_summary_placeholders(price_row);

		const totals_row = $('<tr class="totals-row"></tr>').appendTo(tbody);
		$('<td class="metric-label"></td>').text(__('Totals')).appendTo(totals_row);
		this.add_placeholder_cells(totals_row, dates.length);

		const totals_cells = [
			{ value: total_negative, className: 'number-cell total-negative', showSign: false },
			{ value: total_positive, className: 'number-cell total-positive', showSign: false },
			{ value: current_balance, className: 'number-cell current-balance-cell', showSign: false },
		];

		totals_cells.forEach(({ value, className, showSign }) => {
			const cell = $(`<td class="${className}"></td>`).appendTo(totals_row);
			this.render_number_cell(cell, value, { show_sign: showSign });
		});
	}

	append_summary_placeholders(row) {
		this.add_placeholder_cells(row, 3);
	}

	add_placeholder_cells(row, count, placeholderText = '—') {
		for (let i = 0; i < count; i += 1) {
			$('<td class="number-cell placeholder-cell"></td>').text(placeholderText).appendTo(row);
		}
	}

	extract_date_from_label(label = '') {
		if (!label) return '';
		const [datePart] = label.split(' ');
		return datePart;
	}

	render_chart(item, parent) {
		const history = item.history || [];
		if (!history.length) {
			$('<div class="text-muted small"></div>')
				.text(__('No stock snapshots available for this item.'))
				.appendTo(parent);
			return null;
		}

		const labels = history.map((entry) => entry.date || entry.label);
		const values = history.map((entry) => Number(entry.stock) || 0);
		const chart_container = $('<div></div>').appendTo(parent).get(0);

		return new frappe.Chart(chart_container, {
			type: 'line',
			height: 260,
			data: {
				labels,
				datasets: [
					{
						name: __('Stock Balance'),
						values,
					},
				],
			},
			colors: ['#2490ef'],
			lineOptions: {
				hideDots: false,
				dotSize: 4,
				regionFill: 1,
			},
			axisOptions: {
				xAxisMode: 'tick',
				xAxisLabel: __('Snapshot'),
				yAxisMode: 'span',
				yAxisLabel: __('Stock'),
			},
			tooltipOptions: {
				formatTooltipX: (d) => d,
				formatTooltipY: (d) => `${__('Stock')}: ${this.format_number(d)}`,
			},
		});
	}

	append_meta_line(container, label, value) {
		if (value === undefined || value === null || value === '') {
			return;
		}

		const line = $('<div class="stylus-sv-meta-line"></div>');
		$('<span class="meta-label"></span>')
			.text(`${label}:`)
			.appendTo(line);
		$('<span class="meta-value"></span>')
			.text(value)
			.appendTo(line);
		container.append(line);
	}

	get_opening_balance(item) {
		const history = item.history || [];
		if (!history.length) {
			return 0;
		}
		return Number(history[0].stock) || 0;
	}

	render_number_cell(cell, value, options = {}) {
		const number = Number(value) || 0;
		const show_sign = Boolean(options.show_sign);
		const use_absolute = options.absolute !== undefined ? options.absolute : show_sign;
		const display_value = use_absolute ? Math.abs(number) : number;
		const formatted = this.format_number(display_value);
		const sign_value = show_sign ? (number > 0 ? '+' : number < 0 ? '−' : '') : '';

		const text = sign_value ? `${sign_value} ${formatted}` : formatted;
		cell.addClass('number-cell').text(text);
	}

	format_number(value) {
		const number = Number(value) || 0;
		const formatter =
			(frappe.utils && frappe.utils.format_number) ||
			(function (val, opts) {
				const precision = opts?.precision ?? 3;
				return (val || 0).toFixed(precision);
			});

		return formatter(number, { precision: 3 });
	}

	format_currency(value) {
		if (value === undefined || value === null) {
			return '';
		}

		if (frappe.utils && frappe.utils.format_currency) {
			return frappe.utils.format_currency(value);
		}

		return this.format_number(value);
	}
};