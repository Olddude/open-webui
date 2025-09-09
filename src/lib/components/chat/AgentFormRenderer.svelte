<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { marked } from 'marked';
	import hljs from 'highlight.js';
	import { Chart, registerables } from 'chart.js';
	
	// Register Chart.js components
	Chart.register(...registerables);
	
	export let formData: any = {};
	export let sessionId: string = '';
	export let onAction: (action: string, data: any) => void = () => {};
	
	// Component state management
	let componentState: Record<string, any> = formData.state || {};
	let componentRefs: Record<string, HTMLElement> = {};
	let charts: Record<string, Chart> = {};
	
	// Configure marked with a custom renderer for syntax highlighting
	const renderer = new marked.Renderer();
	const originalCodeRenderer = renderer.code.bind(renderer);
	renderer.code = (code: string, language: string | undefined, isEscaped: boolean) => {
		if (language && hljs.getLanguage(language)) {
			const highlighted = hljs.highlight(code, { language }).value;
			return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`;
		}
		return originalCodeRenderer(code, language, isEscaped);
	};
	
	// Render markdown content
	function renderMarkdown(content: string): string {
		return marked(content, {
			breaks: true,
			gfm: true,
			renderer: renderer
		});
	}
	
	// Handle component actions
	function handleAction(component: any, actionType: string, payload: any) {
		const action = formData.actions?.[`${component.id}_${actionType}`];
		if (action) {
			onAction(action.type, { ...action.params, ...payload });
		}
		
		// Update component state
		if (payload.value !== undefined) {
			componentState[component.id] = payload.value;
		}
	}
	
	// Render individual component based on type
	function renderComponent(component: any): string {
		if (!component.visible !== false) {
			return '';
		}
		
		const className = component.className || '';
		const style = component.style ? Object.entries(component.style).map(([k, v]) => `${k}: ${v}`).join('; ') : '';
		
		switch (component.type) {
			case 'container':
				return renderContainer(component, className, style);
			case 'text':
				return renderText(component, className, style);
			case 'markdown':
				return renderMarkdownComponent(component, className, style);
			case 'button':
				return renderButton(component, className, style);
			case 'input':
				return renderInput(component, className, style);
			case 'textarea':
				return renderTextarea(component, className, style);
			case 'select':
				return renderSelect(component, className, style);
			case 'checkbox':
				return renderCheckbox(component, className, style);
			case 'radio':
				return renderRadio(component, className, style);
			case 'slider':
				return renderSlider(component, className, style);
			case 'progress':
				return renderProgress(component, className, style);
			case 'alert':
				return renderAlert(component, className, style);
			case 'badge':
				return renderBadge(component, className, style);
			case 'divider':
				return renderDivider(component, className, style);
			case 'code':
				return renderCode(component, className, style);
			case 'image':
				return renderImage(component, className, style);
			case 'chart':
				return renderChart(component, className, style);
			case 'table':
				return renderTable(component, className, style);
			case 'fileUpload':
				return renderFileUpload(component, className, style);
			case 'metric':
				return renderMetric(component, className, style);
			case 'tabs':
				return renderTabs(component, className, style);
			case 'accordion':
				return renderAccordion(component, className, style);
			default:
				return `<div>Unknown component type: ${component.type}</div>`;
		}
	}
	
	// Container component
	function renderContainer(component: any, className: string, style: string): string {
		const layoutClass = getLayoutClass(component.layout);
		const gap = component.gap ? `gap: ${component.gap}` : '';
		const columns = component.columns ? `grid-template-columns: repeat(${component.columns}, 1fr)` : '';
		
		return `
			<div id="${component.id}" class="agent-container ${layoutClass} ${className}" style="${style}; ${gap}; ${columns}">
				${component.children?.map((child: any) => renderComponent(child)).join('') || ''}
			</div>
		`;
	}
	
	// Text component
	function renderText(component: any, className: string, style: string): string {
		const variantTag = getTextTag(component.variant);
		const color = component.color ? `color: ${component.color}` : '';
		
		return `
			<${variantTag} id="${component.id}" class="agent-text ${className}" style="${style}; ${color}">
				${component.content || ''}
			</${variantTag}>
		`;
	}
	
	// Markdown component
	function renderMarkdownComponent(component: any, className: string, style: string): string {
		const content = component.sanitize !== false 
			? sanitizeHtml(renderMarkdown(component.content || ''))
			: renderMarkdown(component.content || '');
		
		return `
			<div id="${component.id}" class="agent-markdown ${className}" style="${style}">
				${content}
			</div>
		`;
	}
	
	// Button component
	function renderButton(component: any, className: string, style: string): string {
		const variantClass = `btn-${component.variant || 'primary'}`;
		const sizeClass = `btn-${component.size || 'medium'}`;
		const disabled = component.disabled ? 'disabled' : '';
		const icon = component.icon ? `<i class="icon-${component.icon}"></i>` : '';
		
		return `
			<button 
				id="${component.id}" 
				class="agent-button ${variantClass} ${sizeClass} ${className}" 
				style="${style}"
				${disabled}
				data-action='${JSON.stringify(component.action || {})}'
			>
				${icon} ${component.label || ''}
			</button>
		`;
	}
	
	// Input component
	function renderInput(component: any, className: string, style: string): string {
		const value = componentState[component.id] || component.value || component.defaultValue || '';
		const disabled = component.disabled ? 'disabled' : '';
		const required = component.required ? 'required' : '';
		
		return `
			<div class="agent-input-wrapper">
				${component.label ? `<label for="${component.id}">${component.label}</label>` : ''}
				<input 
					id="${component.id}"
					type="${component.inputType || 'text'}"
					class="agent-input ${className}"
					style="${style}"
					value="${value}"
					placeholder="${component.placeholder || ''}"
					${disabled}
					${required}
					${component.min !== undefined ? `min="${component.min}"` : ''}
					${component.max !== undefined ? `max="${component.max}"` : ''}
					${component.step !== undefined ? `step="${component.step}"` : ''}
					${component.validation?.pattern ? `pattern="${component.validation.pattern}"` : ''}
				/>
				${component.helperText ? `<small class="helper-text">${component.helperText}</small>` : ''}
			</div>
		`;
	}
	
	// Progress component
	function renderProgress(component: any, className: string, style: string): string {
		const value = component.value || 0;
		const colorClass = `progress-${component.color || 'primary'}`;
		const percentage = component.showPercentage !== false ? `${value}%` : '';
		
		if (component.variant === 'circular') {
			return `
				<div id="${component.id}" class="agent-progress-circular ${colorClass} ${className}" style="${style}">
					<svg viewBox="0 0 36 36">
						<path class="progress-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
						<path class="progress-fill" stroke-dasharray="${value}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
						<text x="18" y="20.35" class="percentage">${percentage}</text>
					</svg>
					${component.label ? `<div class="progress-label">${component.label}</div>` : ''}
				</div>
			`;
		}
		
		return `
			<div id="${component.id}" class="agent-progress ${colorClass} ${className}" style="${style}">
				${component.label ? `<div class="progress-label">${component.label}</div>` : ''}
				<div class="progress-bar-wrapper">
					<div class="progress-bar" style="width: ${value}%"></div>
				</div>
				${percentage ? `<span class="progress-percentage">${percentage}</span>` : ''}
			</div>
		`;
	}
	
	// Alert component
	function renderAlert(component: any, className: string, style: string): string {
		const variantClass = `alert-${component.variant || 'info'}`;
		const icon = component.icon !== false ? getAlertIcon(component.variant) : '';
		const dismissButton = component.dismissible ? '<button class="alert-dismiss">×</button>' : '';
		
		return `
			<div id="${component.id}" class="agent-alert ${variantClass} ${className}" style="${style}">
				${icon}
				<div class="alert-content">
					${component.title ? `<div class="alert-title">${component.title}</div>` : ''}
					<div class="alert-message">${component.message || ''}</div>
				</div>
				${dismissButton}
			</div>
		`;
	}
	
	// File upload component
	function renderFileUpload(component: any, className: string, style: string): string {
		const multiple = component.multiple ? 'multiple' : '';
		const accept = component.accept || '';
		
		return `
			<div id="${component.id}" class="agent-file-upload ${className}" style="${style}">
				${component.label ? `<label>${component.label}</label>` : ''}
				<div class="file-upload-zone ${component.dragDrop !== false ? 'drag-drop' : ''}" data-max-size="${component.maxSize || ''}">
					<input type="file" ${multiple} accept="${accept}" />
					<div class="upload-placeholder">
						<svg class="upload-icon" viewBox="0 0 24 24">
							<path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
						</svg>
						<p>Drop files here or click to browse</p>
						<small>${component.maxSize ? `Max size: ${component.maxSize}` : ''}</small>
					</div>
					${component.showPreview !== false ? '<div class="file-preview"></div>' : ''}
				</div>
			</div>
		`;
	}
	
	// Helper functions
	function getLayoutClass(layout: string): string {
		switch (layout) {
			case 'horizontal': return 'flex-row';
			case 'vertical': return 'flex-col';
			case 'grid': return 'grid';
			case 'columns': return 'grid';
			default: return 'flex-col';
		}
	}
	
	function getTextTag(variant: string): string {
		switch (variant) {
			case 'h1': case 'h2': case 'h3': case 'h4': case 'h5': case 'h6':
				return variant;
			case 'caption': return 'small';
			case 'code': return 'code';
			default: return 'p';
		}
	}
	
	function getAlertIcon(variant: string): string {
		const icons: Record<string, string> = {
			info: '📘',
			success: '✅',
			warning: '⚠️',
			error: '❌'
		};
		return icons[variant] || icons.info;
	}
	
	function sanitizeHtml(html: string): string {
		// Basic HTML sanitization (in production, use a proper library like DOMPurify)
		return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
	}
	
	// Additional component renderers...
	function renderTextarea(component: any, className: string, style: string): string {
		const value = componentState[component.id] || component.value || '';
		const disabled = component.disabled ? 'disabled' : '';
		const rows = component.rows || 4;
		
		return `
			<div class="agent-textarea-wrapper">
				${component.label ? `<label for="${component.id}">${component.label}</label>` : ''}
				<textarea 
					id="${component.id}"
					class="agent-textarea ${className}"
					style="${style}"
					rows="${rows}"
					placeholder="${component.placeholder || ''}"
					${disabled}
					${component.maxLength ? `maxlength="${component.maxLength}"` : ''}
				>${value}</textarea>
			</div>
		`;
	}
	
	function renderSelect(component: any, className: string, style: string): string {
		const value = componentState[component.id] || component.value || '';
		const disabled = component.disabled ? 'disabled' : '';
		const multiple = component.multiple ? 'multiple' : '';
		
		const options = component.options?.map((opt: any) => {
			const optValue = typeof opt === 'string' ? opt : opt.value;
			const optLabel = typeof opt === 'string' ? opt : opt.label;
			const optDisabled = typeof opt === 'object' && opt.disabled ? 'disabled' : '';
			const selected = optValue === value ? 'selected' : '';
			
			return `<option value="${optValue}" ${selected} ${optDisabled}>${optLabel}</option>`;
		}).join('') || '';
		
		return `
			<div class="agent-select-wrapper">
				${component.label ? `<label for="${component.id}">${component.label}</label>` : ''}
				<select 
					id="${component.id}"
					class="agent-select ${className}"
					style="${style}"
					${disabled}
					${multiple}
				>
					${component.placeholder ? `<option value="">${component.placeholder}</option>` : ''}
					${options}
				</select>
			</div>
		`;
	}
	
	function renderCheckbox(component: any, className: string, style: string): string {
		const checked = componentState[component.id] || component.checked ? 'checked' : '';
		const disabled = component.disabled ? 'disabled' : '';
		
		return `
			<div class="agent-checkbox-wrapper">
				<input 
					type="checkbox"
					id="${component.id}"
					class="agent-checkbox ${className}"
					style="${style}"
					${checked}
					${disabled}
				/>
				${component.label ? `<label for="${component.id}">${component.label}</label>` : ''}
			</div>
		`;
	}
	
	function renderRadio(component: any, className: string, style: string): string {
		const value = componentState[component.id] || component.value || '';
		const disabled = component.disabled ? 'disabled' : '';
		const inline = component.inline ? 'inline' : '';
		
		const options = component.options?.map((opt: any, idx: number) => {
			const optValue = typeof opt === 'string' ? opt : opt.value;
			const optLabel = typeof opt === 'string' ? opt : opt.label;
			const optDisabled = typeof opt === 'object' && opt.disabled ? 'disabled' : '';
			const checked = optValue === value ? 'checked' : '';
			
			return `
				<div class="radio-option ${inline}">
					<input 
						type="radio"
						id="${component.id}_${idx}"
						name="${component.id}"
						value="${optValue}"
						${checked}
						${optDisabled || disabled}
					/>
					<label for="${component.id}_${idx}">${optLabel}</label>
				</div>
			`;
		}).join('') || '';
		
		return `
			<div class="agent-radio-wrapper">
				${component.label ? `<div class="radio-label">${component.label}</div>` : ''}
				<div class="radio-options ${inline}">
					${options}
				</div>
			</div>
		`;
	}
	
	function renderSlider(component: any, className: string, style: string): string {
		const value = componentState[component.id] || component.value || component.min || 0;
		const disabled = component.disabled ? 'disabled' : '';
		
		return `
			<div class="agent-slider-wrapper">
				${component.label ? `<label for="${component.id}">${component.label}</label>` : ''}
				<div class="slider-container">
					<input 
						type="range"
						id="${component.id}"
						class="agent-slider ${className}"
						style="${style}"
						min="${component.min || 0}"
						max="${component.max || 100}"
						step="${component.step || 1}"
						value="${value}"
						${disabled}
					/>
					${component.showValue !== false ? `<span class="slider-value">${value}</span>` : ''}
				</div>
			</div>
		`;
	}
	
	function renderBadge(component: any, className: string, style: string): string {
		const variantClass = `badge-${component.variant || 'primary'}`;
		const sizeClass = `badge-${component.size || 'medium'}`;
		
		return `
			<span id="${component.id}" class="agent-badge ${variantClass} ${sizeClass} ${className}" style="${style}">
				${component.label || ''}
			</span>
		`;
	}
	
	function renderDivider(component: any, className: string, style: string): string {
		const orientationClass = component.orientation === 'vertical' ? 'divider-vertical' : 'divider-horizontal';
		const variantClass = `divider-${component.variant || 'solid'}`;
		
		return `
			<div id="${component.id}" class="agent-divider ${orientationClass} ${variantClass} ${className}" style="${style}">
				${component.label ? `<span class="divider-label">${component.label}</span>` : ''}
			</div>
		`;
	}
	
	function renderCode(component: any, className: string, style: string): string {
		const highlighted = hljs.highlight(component.content || '', { 
			language: component.language || 'plaintext' 
		}).value;
		
		const lineNumbers = component.showLineNumbers ? 'line-numbers' : '';
		const themeClass = `theme-${component.theme || 'auto'}`;
		
		return `
			<div id="${component.id}" class="agent-code ${themeClass} ${className}" style="${style}">
				${component.copyButton !== false ? '<button class="copy-button">Copy</button>' : ''}
				<pre class="${lineNumbers}"><code class="language-${component.language || 'plaintext'}">${highlighted}</code></pre>
			</div>
		`;
	}
	
	function renderImage(component: any, className: string, style: string): string {
		const width = component.width ? `width: ${component.width}${typeof component.width === 'number' ? 'px' : ''}` : '';
		const height = component.height ? `height: ${component.height}${typeof component.height === 'number' ? 'px' : ''}` : '';
		const objectFit = component.objectFit ? `object-fit: ${component.objectFit}` : '';
		
		return `
			<figure id="${component.id}" class="agent-image ${className}" style="${style}">
				<img 
					src="${component.src || ''}"
					alt="${component.alt || ''}"
					style="${width}; ${height}; ${objectFit}"
				/>
				${component.caption ? `<figcaption>${component.caption}</figcaption>` : ''}
			</figure>
		`;
	}
	
	function renderChart(component: any, className: string, style: string): string {
		// Chart will be initialized after mount
		return `
			<div id="${component.id}" class="agent-chart ${className}" style="${style}; height: ${component.height || '300px'}">
				<canvas data-chart='${JSON.stringify(component)}'></canvas>
			</div>
		`;
	}
	
	function renderTable(component: any, className: string, style: string): string {
		const tableClass = [
			component.striped ? 'table-striped' : '',
			component.bordered !== false ? 'table-bordered' : '',
			component.hoverable !== false ? 'table-hover' : ''
		].join(' ');
		
		const headers = component.columns?.map((col: any) => 
			`<th style="${col.width ? `width: ${col.width}` : ''}; text-align: ${col.align || 'left'}">${col.label}</th>`
		).join('') || '';
		
		const rows = component.data?.map((row: any) => 
			`<tr>${component.columns?.map((col: any) => 
				`<td style="text-align: ${col.align || 'left'}">${row[col.key] || ''}</td>`
			).join('') || ''}</tr>`
		).join('') || '';
		
		return `
			<div id="${component.id}" class="agent-table-wrapper ${className}" style="${style}">
				${component.searchable ? '<input type="text" class="table-search" placeholder="Search..." />' : ''}
				<table class="agent-table ${tableClass}">
					<thead><tr>${headers}</tr></thead>
					<tbody>${rows}</tbody>
				</table>
				${component.paginated ? '<div class="table-pagination"></div>' : ''}
			</div>
		`;
	}
	
	function renderMetric(component: any, className: string, style: string): string {
		const deltaIcon = component.deltaType === 'increase' ? '↑' : component.deltaType === 'decrease' ? '↓' : '';
		const deltaClass = `delta-${component.deltaType || 'neutral'}`;
		
		return `
			<div id="${component.id}" class="agent-metric ${className}" style="${style}">
				${component.icon ? `<div class="metric-icon">${component.icon}</div>` : ''}
				<div class="metric-content">
					<div class="metric-label">${component.label || ''}</div>
					<div class="metric-value">
						${component.prefix || ''}${component.value || ''}${component.suffix || ''}
					</div>
					${component.delta ? `
						<div class="metric-delta ${deltaClass}">
							${deltaIcon} ${component.delta}
						</div>
					` : ''}
				</div>
			</div>
		`;
	}
	
	function renderTabs(component: any, className: string, style: string): string {
		const activeTab = componentState[`${component.id}_activeTab`] || component.activeTab || component.tabs?.[0]?.id;
		const variantClass = `tabs-${component.variant || 'default'}`;
		
		const tabHeaders = component.tabs?.map((tab: any) => `
			<button 
				class="tab-header ${tab.id === activeTab ? 'active' : ''} ${tab.disabled ? 'disabled' : ''}"
				data-tab="${tab.id}"
				${tab.disabled ? 'disabled' : ''}
			>
				${tab.icon ? `<i class="icon-${tab.icon}"></i>` : ''}
				${tab.label}
			</button>
		`).join('') || '';
		
		const tabContents = component.tabs?.map((tab: any) => `
			<div class="tab-content ${tab.id === activeTab ? 'active' : ''}" data-tab-content="${tab.id}">
				${tab.content?.map((child: any) => renderComponent(child)).join('') || ''}
			</div>
		`).join('') || '';
		
		return `
			<div id="${component.id}" class="agent-tabs ${variantClass} ${className}" style="${style}">
				<div class="tabs-header">${tabHeaders}</div>
				<div class="tabs-body">${tabContents}</div>
			</div>
		`;
	}
	
	function renderAccordion(component: any, className: string, style: string): string {
		const items = component.items?.map((item: any) => {
			const expanded = componentState[`${component.id}_${item.id}`] || item.expanded;
			
			return `
				<div class="accordion-item ${expanded ? 'expanded' : ''}">
					<button class="accordion-header" data-accordion="${item.id}">
						${item.title}
						<span class="accordion-icon">${expanded ? '−' : '+'}</span>
					</button>
					<div class="accordion-content" style="${expanded ? '' : 'display: none'}">
						${item.content?.map((child: any) => renderComponent(child)).join('') || ''}
					</div>
				</div>
			`;
		}).join('') || '';
		
		return `
			<div id="${component.id}" class="agent-accordion ${className}" style="${style}" data-multiple="${component.multiple || false}">
				${items}
			</div>
		`;
	}
	
	// Initialize charts after mount
	function initializeCharts() {
		const chartElements = document.querySelectorAll('[data-chart]');
		chartElements.forEach((element: any) => {
			const canvas = element.querySelector('canvas');
			if (canvas) {
				const config = JSON.parse(element.dataset.chart);
				const ctx = canvas.getContext('2d');
				
				charts[config.id] = new Chart(ctx, {
					type: config.chartType || 'line',
					data: config.data,
					options: config.options || {}
				});
			}
		});
	}
	
	// Attach event listeners
	function attachEventListeners() {
		// Button clicks
		document.querySelectorAll('.agent-button').forEach((btn: any) => {
			btn.addEventListener('click', (e: Event) => {
				const action = JSON.parse(btn.dataset.action || '{}');
				handleAction({ id: btn.id }, 'click', { action });
			});
		});
		
		// Input changes
		document.querySelectorAll('.agent-input, .agent-textarea, .agent-select').forEach((input: any) => {
			input.addEventListener('change', (e: Event) => {
				handleAction({ id: input.id }, 'change', { value: input.value });
			});
		});
		
		// Checkbox changes
		document.querySelectorAll('.agent-checkbox').forEach((cb: any) => {
			cb.addEventListener('change', (e: Event) => {
				handleAction({ id: cb.id }, 'change', { value: cb.checked });
			});
		});
		
		// Radio changes
		document.querySelectorAll('input[type="radio"]').forEach((radio: any) => {
			radio.addEventListener('change', (e: Event) => {
				handleAction({ id: radio.name }, 'change', { value: radio.value });
			});
		});
		
		// Slider changes
		document.querySelectorAll('.agent-slider').forEach((slider: any) => {
			slider.addEventListener('input', (e: Event) => {
				const valueDisplay = slider.parentElement.querySelector('.slider-value');
				if (valueDisplay) {
					valueDisplay.textContent = slider.value;
				}
				handleAction({ id: slider.id }, 'change', { value: slider.value });
			});
		});
		
		// Alert dismiss
		document.querySelectorAll('.alert-dismiss').forEach((btn: any) => {
			btn.addEventListener('click', (e: Event) => {
				btn.closest('.agent-alert').style.display = 'none';
			});
		});
		
		// Tab switching
		document.querySelectorAll('.tab-header').forEach((tab: any) => {
			tab.addEventListener('click', (e: Event) => {
				const tabId = tab.dataset.tab;
				const container = tab.closest('.agent-tabs');
				
				// Update headers
				container.querySelectorAll('.tab-header').forEach((t: any) => {
					t.classList.toggle('active', t.dataset.tab === tabId);
				});
				
				// Update contents
				container.querySelectorAll('.tab-content').forEach((c: any) => {
					c.classList.toggle('active', c.dataset.tabContent === tabId);
				});
				
				handleAction({ id: container.id }, 'tabChange', { activeTab: tabId });
			});
		});
		
		// Accordion toggling
		document.querySelectorAll('.accordion-header').forEach((header: any) => {
			header.addEventListener('click', (e: Event) => {
				const itemId = header.dataset.accordion;
				const container = header.closest('.agent-accordion');
				const item = header.closest('.accordion-item');
				const isMultiple = container.dataset.multiple === 'true';
				
				if (!isMultiple) {
					// Close other items
					container.querySelectorAll('.accordion-item').forEach((i: any) => {
						if (i !== item) {
							i.classList.remove('expanded');
							i.querySelector('.accordion-content').style.display = 'none';
						}
					});
				}
				
				// Toggle current item
				item.classList.toggle('expanded');
				const content = item.querySelector('.accordion-content');
				content.style.display = item.classList.contains('expanded') ? 'block' : 'none';
				
				handleAction({ id: container.id }, 'accordionToggle', { itemId, expanded: item.classList.contains('expanded') });
			});
		});
		
		// File upload
		document.querySelectorAll('.file-upload-zone input[type="file"]').forEach((input: any) => {
			const zone = input.closest('.file-upload-zone');
			
			// Click to upload
			zone.addEventListener('click', (e: Event) => {
				if (e.target === input) return;
				input.click();
			});
			
			// Drag and drop
			if (zone.classList.contains('drag-drop')) {
				zone.addEventListener('dragover', (e: DragEvent) => {
					e.preventDefault();
					zone.classList.add('drag-over');
				});
				
				zone.addEventListener('dragleave', (e: DragEvent) => {
					zone.classList.remove('drag-over');
				});
				
				zone.addEventListener('drop', (e: DragEvent) => {
					e.preventDefault();
					zone.classList.remove('drag-over');
					
					const files = e.dataTransfer?.files;
					if (files) {
						input.files = files;
						handleFileUpload(input);
					}
				});
			}
			
			// File selection
			input.addEventListener('change', (e: Event) => {
				handleFileUpload(input);
			});
		});
		
		// Copy code button
		document.querySelectorAll('.agent-code .copy-button').forEach((btn: any) => {
			btn.addEventListener('click', async (e: Event) => {
				const code = btn.parentElement.querySelector('code').textContent;
				await navigator.clipboard.writeText(code);
				btn.textContent = 'Copied!';
				setTimeout(() => btn.textContent = 'Copy', 2000);
			});
		});
	}
	
	function handleFileUpload(input: any) {
		const zone = input.closest('.file-upload-zone');
		const preview = zone.querySelector('.file-preview');
		const files = Array.from(input.files);
		
		if (preview) {
			preview.innerHTML = files.map((f: any) => `
				<div class="file-item">
					<span class="file-name">${f.name}</span>
					<span class="file-size">${(f.size / 1024).toFixed(2)} KB</span>
				</div>
			`).join('');
		}
		
		handleAction({ id: input.closest('.agent-file-upload').id }, 'fileUpload', { files });
	}
	
	onMount(() => {
		// Initialize charts and attach event listeners after DOM is ready
		setTimeout(() => {
			initializeCharts();
			attachEventListeners();
		}, 100);
	});
	
	onDestroy(() => {
		// Cleanup charts
		Object.values(charts).forEach((chart: Chart) => chart.destroy());
	});
</script>

<div class="agent-form-renderer" data-session="{sessionId}">
	{#if formData.metadata}
		<div class="form-metadata">
			{#if formData.metadata.title}
				<h2 class="form-title">{formData.metadata.title}</h2>
			{/if}
			{#if formData.metadata.description}
				<p class="form-description">{formData.metadata.description}</p>
			{/if}
		</div>
	{/if}
	
	<div class="form-components layout-{formData.layout?.type || 'single'}">
		{@html formData.components?.map(renderComponent).join('') || ''}
	</div>
</div>

<style>
	.agent-form-renderer {
		padding: 1rem;
		font-family: var(--font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif);
	}
	
	/* Layout styles */
	.flex-row {
		display: flex;
		flex-direction: row;
	}
	
	.flex-col {
		display: flex;
		flex-direction: column;
	}
	
	.grid {
		display: grid;
	}
	
	/* Component styles */
	.agent-container {
		margin-bottom: 1rem;
	}
	
	.agent-text {
		margin-bottom: 0.5rem;
	}
	
	.agent-markdown {
		margin-bottom: 1rem;
	}
	
	.agent-markdown :global(h1),
	.agent-markdown :global(h2),
	.agent-markdown :global(h3) {
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	/* Button styles */
	.agent-button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 0.25rem;
		cursor: pointer;
		font-size: 1rem;
		transition: all 0.2s;
	}
	
	.agent-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.btn-primary {
		background: var(--color-primary, #007bff);
		color: white;
	}
	
	.btn-secondary {
		background: var(--color-secondary, #6c757d);
		color: white;
	}
	
	.btn-success {
		background: var(--color-success, #28a745);
		color: white;
	}
	
	.btn-danger {
		background: var(--color-danger, #dc3545);
		color: white;
	}
	
	.btn-warning {
		background: var(--color-warning, #ffc107);
		color: black;
	}
	
	.btn-info {
		background: var(--color-info, #17a2b8);
		color: white;
	}
	
	.btn-small {
		padding: 0.25rem 0.5rem;
		font-size: 0.875rem;
	}
	
	.btn-large {
		padding: 0.75rem 1.5rem;
		font-size: 1.125rem;
	}
	
	/* Input styles */
	.agent-input-wrapper,
	.agent-textarea-wrapper,
	.agent-select-wrapper {
		margin-bottom: 1rem;
	}
	
	.agent-input-wrapper label,
	.agent-textarea-wrapper label,
	.agent-select-wrapper label {
		display: block;
		margin-bottom: 0.25rem;
		font-weight: 500;
	}
	
	.agent-input,
	.agent-textarea,
	.agent-select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid var(--border-color, #ced4da);
		border-radius: 0.25rem;
		font-size: 1rem;
	}
	
	.agent-input:focus,
	.agent-textarea:focus,
	.agent-select:focus {
		outline: none;
		border-color: var(--color-primary, #007bff);
		box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
	}
	
	.helper-text {
		display: block;
		margin-top: 0.25rem;
		font-size: 0.875rem;
		color: var(--text-muted, #6c757d);
	}
	
	/* Progress styles */
	.agent-progress {
		margin-bottom: 1rem;
	}
	
	.progress-label {
		margin-bottom: 0.25rem;
		font-weight: 500;
	}
	
	.progress-bar-wrapper {
		height: 1rem;
		background: var(--progress-bg, #e9ecef);
		border-radius: 0.25rem;
		overflow: hidden;
		position: relative;
	}
	
	.progress-bar {
		height: 100%;
		background: var(--color-primary, #007bff);
		transition: width 0.3s ease;
	}
	
	.progress-percentage {
		display: inline-block;
		margin-left: 0.5rem;
		font-size: 0.875rem;
	}
	
	.progress-primary .progress-bar {
		background: var(--color-primary, #007bff);
	}
	
	.progress-success .progress-bar {
		background: var(--color-success, #28a745);
	}
	
	.progress-warning .progress-bar {
		background: var(--color-warning, #ffc107);
	}
	
	.progress-danger .progress-bar {
		background: var(--color-danger, #dc3545);
	}
	
	.progress-info .progress-bar {
		background: var(--color-info, #17a2b8);
	}
	
	/* Alert styles */
	.agent-alert {
		display: flex;
		align-items: flex-start;
		padding: 0.75rem 1rem;
		margin-bottom: 1rem;
		border-radius: 0.25rem;
		position: relative;
	}
	
	.alert-info {
		background: var(--alert-info-bg, #d1ecf1);
		color: var(--alert-info-color, #0c5460);
		border: 1px solid var(--alert-info-border, #bee5eb);
	}
	
	.alert-success {
		background: var(--alert-success-bg, #d4edda);
		color: var(--alert-success-color, #155724);
		border: 1px solid var(--alert-success-border, #c3e6cb);
	}
	
	.alert-warning {
		background: var(--alert-warning-bg, #fff3cd);
		color: var(--alert-warning-color, #856404);
		border: 1px solid var(--alert-warning-border, #ffeeba);
	}
	
	.alert-error {
		background: var(--alert-error-bg, #f8d7da);
		color: var(--alert-error-color, #721c24);
		border: 1px solid var(--alert-error-border, #f5c6cb);
	}
	
	.alert-content {
		flex: 1;
		margin-left: 0.5rem;
	}
	
	.alert-title {
		font-weight: 600;
		margin-bottom: 0.25rem;
	}
	
	.alert-dismiss {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		background: none;
		border: none;
		font-size: 1.5rem;
		line-height: 1;
		cursor: pointer;
		opacity: 0.5;
		transition: opacity 0.2s;
	}
	
	.alert-dismiss:hover {
		opacity: 1;
	}
	
	/* Badge styles */
	.agent-badge {
		display: inline-block;
		padding: 0.25rem 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		border-radius: 0.25rem;
		margin: 0.125rem;
	}
	
	.badge-primary {
		background: var(--color-primary, #007bff);
		color: white;
	}
	
	.badge-secondary {
		background: var(--color-secondary, #6c757d);
		color: white;
	}
	
	.badge-success {
		background: var(--color-success, #28a745);
		color: white;
	}
	
	.badge-danger {
		background: var(--color-danger, #dc3545);
		color: white;
	}
	
	.badge-warning {
		background: var(--color-warning, #ffc107);
		color: black;
	}
	
	.badge-info {
		background: var(--color-info, #17a2b8);
		color: white;
	}
	
	.badge-small {
		font-size: 0.75rem;
		padding: 0.125rem 0.25rem;
	}
	
	.badge-large {
		font-size: 1rem;
		padding: 0.375rem 0.75rem;
	}
	
	/* File upload styles */
	.file-upload-zone {
		border: 2px dashed var(--border-color, #ced4da);
		border-radius: 0.5rem;
		padding: 2rem;
		text-align: center;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.file-upload-zone.drag-over {
		border-color: var(--color-primary, #007bff);
		background: rgba(0, 123, 255, 0.05);
	}
	
	.file-upload-zone input[type="file"] {
		display: none;
	}
	
	.upload-icon {
		width: 3rem;
		height: 3rem;
		margin-bottom: 1rem;
		opacity: 0.5;
	}
	
	.file-preview {
		margin-top: 1rem;
		text-align: left;
	}
	
	.file-item {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem;
		background: var(--bg-light, #f8f9fa);
		border-radius: 0.25rem;
		margin-bottom: 0.5rem;
	}
	
	/* Table styles */
	.agent-table-wrapper {
		overflow-x: auto;
		margin-bottom: 1rem;
	}
	
	.agent-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.agent-table th,
	.agent-table td {
		padding: 0.75rem;
		text-align: left;
	}
	
	.table-bordered th,
	.table-bordered td {
		border: 1px solid var(--border-color, #dee2e6);
	}
	
	.table-striped tbody tr:nth-child(odd) {
		background: var(--bg-light, #f8f9fa);
	}
	
	.table-hover tbody tr:hover {
		background: var(--bg-hover, #e9ecef);
	}
	
	/* Tabs styles */
	.agent-tabs {
		margin-bottom: 1rem;
	}
	
	.tabs-header {
		display: flex;
		border-bottom: 2px solid var(--border-color, #dee2e6);
		margin-bottom: 1rem;
	}
	
	.tab-header {
		padding: 0.5rem 1rem;
		background: none;
		border: none;
		cursor: pointer;
		font-size: 1rem;
		transition: all 0.2s;
		position: relative;
	}
	
	.tab-header.active {
		color: var(--color-primary, #007bff);
	}
	
	.tab-header.active::after {
		content: '';
		position: absolute;
		bottom: -2px;
		left: 0;
		right: 0;
		height: 2px;
		background: var(--color-primary, #007bff);
	}
	
	.tab-header:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.tab-content {
		display: none;
	}
	
	.tab-content.active {
		display: block;
	}
	
	/* Accordion styles */
	.accordion-item {
		border: 1px solid var(--border-color, #dee2e6);
		border-radius: 0.25rem;
		margin-bottom: 0.5rem;
	}
	
	.accordion-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		padding: 0.75rem 1rem;
		background: var(--bg-light, #f8f9fa);
		border: none;
		text-align: left;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.accordion-header:hover {
		background: var(--bg-hover, #e9ecef);
	}
	
	.accordion-content {
		padding: 1rem;
	}
	
	.accordion-icon {
		font-size: 1.25rem;
		transition: transform 0.2s;
	}
	
	.accordion-item.expanded .accordion-icon {
		transform: rotate(45deg);
	}
	
	/* Metric styles */
	.agent-metric {
		display: flex;
		align-items: center;
		padding: 1rem;
		background: var(--bg-light, #f8f9fa);
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}
	
	.metric-icon {
		font-size: 2rem;
		margin-right: 1rem;
	}
	
	.metric-content {
		flex: 1;
	}
	
	.metric-label {
		font-size: 0.875rem;
		color: var(--text-muted, #6c757d);
		margin-bottom: 0.25rem;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 600;
	}
	
	.metric-delta {
		font-size: 0.875rem;
		margin-top: 0.25rem;
	}
	
	.delta-increase {
		color: var(--color-success, #28a745);
	}
	
	.delta-decrease {
		color: var(--color-danger, #dc3545);
	}
	
	.delta-neutral {
		color: var(--text-muted, #6c757d);
	}
	
	/* Responsive styles */
	@media (max-width: 768px) {
		.flex-row {
			flex-direction: column;
		}
		
		.grid {
			grid-template-columns: 1fr !important;
		}
	}
	
	/* Dark mode support */
	@media (prefers-color-scheme: dark) {
		.agent-form-renderer {
			--bg-light: #2d3748;
			--bg-hover: #4a5568;
			--border-color: #4a5568;
			--text-muted: #a0aec0;
		}
		
		.agent-input,
		.agent-textarea,
		.agent-select {
			background: #2d3748;
			color: #e2e8f0;
		}
		
		.agent-code.theme-auto {
			background: #1a202c;
		}
	}
</style>
