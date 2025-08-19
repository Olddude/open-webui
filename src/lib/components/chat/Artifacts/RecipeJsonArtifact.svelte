<script lang="ts">
	import { Copy, Check, Download, Eye, ChevronDown, ChevronRight } from 'lucide-svelte';
	
	export let artifact: any;
	
	let copiedToClipboard = false;
	let viewMode: 'formatted' | 'raw' = 'formatted';
	let expandedSections: Record<string, boolean> = { metadata: true, recipes: true };
	
	$: jsonData = typeof artifact.content === 'string' 
		? JSON.parse(artifact.content) 
		: artifact.content;
	
	function copyToClipboard() {
		const text = JSON.stringify(jsonData, null, 2);
		navigator.clipboard.writeText(text).then(() => {
			copiedToClipboard = true;
			setTimeout(() => {
				copiedToClipboard = false;
			}, 2000);
		});
	}
	
	function downloadJson() {
		const text = JSON.stringify(jsonData, null, 2);
		const blob = new Blob([text], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${artifact.title || 'recipes'}.json`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}
	
	function toggleSection(section: string) {
		expandedSections[section] = !expandedSections[section];
	}
	
	function formatValue(value: any): string {
		if (typeof value === 'string') return value;
		if (typeof value === 'number') return value.toString();
		if (Array.isArray(value)) return `Array(${value.length})`;
		if (typeof value === 'object' && value !== null) return 'Object';
		return String(value);
	}
</script>

<div class="recipe-json-artifact">
	<div class="artifact-header">
		<div class="header-info">
			<h3 class="artifact-title">{artifact.title}</h3>
			<p class="artifact-subtitle">
				{jsonData.recipes?.length || 0} recipes • 
				Generated {artifact.createdAt.toLocaleString()}
			</p>
		</div>
		
		<div class="header-actions">
			<div class="view-toggle">
				<button 
					class="toggle-btn"
					class:active={viewMode === 'formatted'}
					on:click={() => viewMode = 'formatted'}
				>
					<Eye size={14} />
					Formatted
				</button>
				<button 
					class="toggle-btn"
					class:active={viewMode === 'raw'}
					on:click={() => viewMode = 'raw'}
				>
					Raw
				</button>
			</div>
			
			<button class="action-btn" on:click={copyToClipboard} title="Copy JSON">
				{#if copiedToClipboard}
					<Check size={14} class="text-green-600" />
				{:else}
					<Copy size={14} />
				{/if}
			</button>
			
			<button class="action-btn" on:click={downloadJson} title="Download JSON">
				<Download size={14} />
			</button>
		</div>
	</div>
	
	<div class="artifact-content">
		{#if viewMode === 'formatted'}
			<div class="formatted-view">
				<!-- Metadata Section -->
				<div class="json-section">
					<button 
						class="section-header"
						on:click={() => toggleSection('metadata')}
					>
						{#if expandedSections.metadata}
							<ChevronDown size={16} />
						{:else}
							<ChevronRight size={16} />
						{/if}
						<span class="section-title">Metadata</span>
						<span class="section-count">
							{Object.keys(jsonData.metadata || {}).length} fields
						</span>
					</button>
					
					{#if expandedSections.metadata && jsonData.metadata}
						<div class="section-content">
							{#each Object.entries(jsonData.metadata) as [key, value]}
								<div class="field-row">
									<span class="field-key">{key}:</span>
									<span class="field-value">{formatValue(value)}</span>
								</div>
							{/each}
						</div>
					{/if}
				</div>
				
				<!-- Recipes Section -->
				<div class="json-section">
					<button 
						class="section-header"
						on:click={() => toggleSection('recipes')}
					>
						{#if expandedSections.recipes}
							<ChevronDown size={16} />
						{:else}
							<ChevronRight size={16} />
						{/if}
						<span class="section-title">Recipes</span>
						<span class="section-count">
							{jsonData.recipes?.length || 0} items
						</span>
					</button>
					
					{#if expandedSections.recipes && jsonData.recipes}
						<div class="section-content">
							{#each jsonData.recipes as recipe, i}
								<div class="recipe-card">
									<div class="recipe-header">
										<h4 class="recipe-name">{recipe.name}</h4>
										<span class="recipe-id">#{recipe.id || i + 1}</span>
									</div>
									
									<div class="recipe-details">
										<div class="recipe-row">
											<span class="detail-label">Ingredients:</span>
											<span class="detail-value">
												{recipe.ingredients?.length || 0} items
											</span>
										</div>
										
										{#if recipe.prep_time}
											<div class="recipe-row">
												<span class="detail-label">Prep Time:</span>
												<span class="detail-value">{recipe.prep_time}</span>
											</div>
										{/if}
										
										{#if recipe.cook_time}
											<div class="recipe-row">
												<span class="detail-label">Cook Time:</span>
												<span class="detail-value">{recipe.cook_time}</span>
											</div>
										{/if}
										
										{#if recipe.servings}
											<div class="recipe-row">
												<span class="detail-label">Servings:</span>
												<span class="detail-value">{recipe.servings}</span>
											</div>
										{/if}
									</div>
									
									{#if recipe.ingredients && recipe.ingredients.length > 0}
										<div class="ingredients-preview">
											<span class="ingredients-label">Ingredients:</span>
											<div class="ingredients-list">
												{#each recipe.ingredients.slice(0, 3) as ingredient}
													<span class="ingredient-tag">
														{ingredient.name} ({ingredient.amount})
													</span>
												{/each}
												{#if recipe.ingredients.length > 3}
													<span class="more-ingredients">
														+{recipe.ingredients.length - 3} more
													</span>
												{/if}
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		{:else}
			<div class="raw-view">
				<pre class="json-code"><code>{JSON.stringify(jsonData, null, 2)}</code></pre>
			</div>
		{/if}
	</div>
</div>

<style>
	.recipe-json-artifact {
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		overflow: hidden;
		background: white;
	}
	
	:global(.dark) .recipe-json-artifact {
		background: #1f2937;
		border-color: #374151;
	}
	
	.artifact-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem;
		border-bottom: 1px solid #e5e7eb;
		background: #f9fafb;
	}
	
	:global(.dark) .artifact-header {
		background: #111827;
		border-color: #374151;
	}
	
	.header-info {
		flex: 1;
	}
	
	.artifact-title {
		font-size: 1rem;
		font-weight: 600;
		color: #1f2937;
		margin: 0 0 0.25rem 0;
	}
	
	:global(.dark) .artifact-title {
		color: #f3f4f6;
	}
	
	.artifact-subtitle {
		font-size: 0.8125rem;
		color: #6b7280;
		margin: 0;
	}
	
	.header-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.view-toggle {
		display: flex;
		background: #e5e7eb;
		border-radius: 0.375rem;
		padding: 0.125rem;
	}
	
	:global(.dark) .view-toggle {
		background: #374151;
	}
	
	.toggle-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.75rem;
		font-size: 0.8125rem;
		background: none;
		border: none;
		border-radius: 0.25rem;
		cursor: pointer;
		color: #6b7280;
		transition: all 0.2s;
	}
	
	.toggle-btn.active {
		background: white;
		color: #1f2937;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
	}
	
	:global(.dark) .toggle-btn.active {
		background: #1f2937;
		color: #f3f4f6;
	}
	
	.action-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		background: none;
		border: 1px solid #d1d5db;
		border-radius: 0.25rem;
		cursor: pointer;
		color: #6b7280;
		transition: all 0.2s;
	}
	
	.action-btn:hover {
		background: #f3f4f6;
		border-color: #9ca3af;
	}
	
	:global(.dark) .action-btn {
		border-color: #4b5563;
		color: #9ca3af;
	}
	
	:global(.dark) .action-btn:hover {
		background: #374151;
		border-color: #6b7280;
	}
	
	.artifact-content {
		max-height: 400px;
		overflow-y: auto;
	}
	
	.json-section {
		border-bottom: 1px solid #f3f4f6;
	}
	
	:global(.dark) .json-section {
		border-color: #374151;
	}
	
	.json-section:last-child {
		border-bottom: none;
	}
	
	.section-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		text-align: left;
		cursor: pointer;
		transition: background 0.2s;
	}
	
	.section-header:hover {
		background: #f9fafb;
	}
	
	:global(.dark) .section-header:hover {
		background: #111827;
	}
	
	.section-title {
		font-weight: 500;
		color: #1f2937;
	}
	
	:global(.dark) .section-title {
		color: #f3f4f6;
	}
	
	.section-count {
		font-size: 0.8125rem;
		color: #6b7280;
		margin-left: auto;
	}
	
	.section-content {
		padding: 0 1rem 1rem 1rem;
	}
	
	.field-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.25rem 0;
		font-size: 0.875rem;
	}
	
	.field-key {
		font-weight: 500;
		color: #374151;
		min-width: 120px;
	}
	
	:global(.dark) .field-key {
		color: #d1d5db;
	}
	
	.field-value {
		color: #6b7280;
	}
	
	.recipe-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
		padding: 0.75rem;
		margin-bottom: 0.75rem;
	}
	
	.recipe-card:last-child {
		margin-bottom: 0;
	}
	
	:global(.dark) .recipe-card {
		background: #111827;
		border-color: #374151;
	}
	
	.recipe-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
	}
	
	.recipe-name {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1f2937;
		margin: 0;
	}
	
	:global(.dark) .recipe-name {
		color: #f3f4f6;
	}
	
	.recipe-id {
		font-size: 0.8125rem;
		color: #6b7280;
		background: #e5e7eb;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
	}
	
	:global(.dark) .recipe-id {
		background: #374151;
		color: #9ca3af;
	}
	
	.recipe-details {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}
	
	.recipe-row {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.detail-label {
		font-size: 0.75rem;
		font-weight: 500;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}
	
	.detail-value {
		font-size: 0.8125rem;
		color: #374151;
	}
	
	:global(.dark) .detail-value {
		color: #d1d5db;
	}
	
	.ingredients-preview {
		margin-top: 0.5rem;
	}
	
	.ingredients-label {
		font-size: 0.75rem;
		font-weight: 500;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.025em;
		margin-bottom: 0.375rem;
		display: block;
	}
	
	.ingredients-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}
	
	.ingredient-tag {
		background: #ddd6fe;
		color: #5b21b6;
		padding: 0.125rem 0.5rem;
		border-radius: 9999px;
		font-size: 0.75rem;
	}
	
	:global(.dark) .ingredient-tag {
		background: #5b21b6;
		color: #ddd6fe;
	}
	
	.more-ingredients {
		background: #f3f4f6;
		color: #6b7280;
		padding: 0.125rem 0.5rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-style: italic;
	}
	
	:global(.dark) .more-ingredients {
		background: #374151;
		color: #9ca3af;
	}
	
	.raw-view {
		padding: 1rem;
	}
	
	.json-code {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.8125rem;
		line-height: 1.5;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
		padding: 1rem;
		margin: 0;
		white-space: pre-wrap;
		overflow-x: auto;
	}
	
	:global(.dark) .json-code {
		background: #111827;
		border-color: #374151;
		color: #e5e7eb;
	}
</style>