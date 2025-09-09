<script lang="ts">
	import { agentState, togglePanel } from '$lib/stores/agentState';
	import { File, Code, FileText, Image, Download, ExternalLink, Copy, Check, X } from 'lucide-svelte';
	import { onMount } from 'svelte';
	
	$: artifacts = $agentState.artifacts;
	
	let copiedArtifact = '';
	
	function getArtifactIcon(type: string) {
		switch (type) {
			case 'code':
				return Code;
			case 'document':
				return FileText;
			case 'diagram':
				return Image;
			default:
				return File;
		}
	}
	
	function getArtifactColor(type: string) {
		switch (type) {
			case 'code':
				return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30';
			case 'document':
				return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
			case 'diagram':
				return 'text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/30';
			default:
				return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
		}
	}
	
	function formatFileSize(content: string): string {
		const bytes = new Blob([content]).size;
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
	
	function copyToClipboard(content: string, artifactId: string) {
		navigator.clipboard.writeText(content).then(() => {
			copiedArtifact = artifactId;
			setTimeout(() => {
				copiedArtifact = '';
			}, 2000);
		});
	}
	
	function downloadArtifact(artifact: any) {
		const blob = new Blob([artifact.content], { 
			type: artifact.type === 'code' ? 'text/plain' : 'text/markdown' 
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${artifact.title}${artifact.language ? '.' + artifact.language : '.txt'}`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}
</script>

<div class="artifacts-panel-container h-full flex flex-col">
	<div class="panel-header p-4 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center justify-between mb-2">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">
				Generated Artifacts
			</h2>
			<div class="flex items-center gap-2">
				<span class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
					{artifacts.length} items
				</span>
				<button
					class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
					title="Close Panel"
					on:click={() => togglePanel('artifacts')}
				>
					<X size={16} />
				</button>
			</div>
		</div>
		<p class="text-sm text-gray-600 dark:text-gray-400">
			Code, documents, and files generated during conversation
		</p>
	</div>

	<div class="panel-content flex-1 overflow-y-auto">
		{#if artifacts.length > 0}
			<div class="artifacts-list p-4 space-y-3">
				{#each artifacts as artifact}
					<div class="artifact-item bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
						<div class="artifact-header p-3 border-b border-gray-200 dark:border-gray-700">
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-2">
									<div class="artifact-icon {getArtifactColor(artifact.type)}">
										<svelte:component this={getArtifactIcon(artifact.type)} size={16} />
									</div>
									<div class="artifact-meta">
										<div class="artifact-title font-medium text-gray-900 dark:text-gray-100">
											{artifact.title}
										</div>
										<div class="artifact-info text-xs text-gray-500 dark:text-gray-400">
											{artifact.type} • {formatFileSize(artifact.content)} • v{artifact.version}
										</div>
									</div>
								</div>
								
								<div class="artifact-actions flex gap-1">
									<button
										class="action-btn"
										on:click={() => copyToClipboard(artifact.content, artifact.id)}
										title="Copy to clipboard"
									>
										{#if copiedArtifact === artifact.id}
											<Check size={14} class="text-green-600" />
										{:else}
											<Copy size={14} />
										{/if}
									</button>
									<button
										class="action-btn"
										on:click={() => downloadArtifact(artifact)}
										title="Download"
									>
										<Download size={14} />
									</button>
								</div>
							</div>
						</div>
						
						<div class="artifact-content">
							{#if artifact.type === 'code'}
								<div class="code-preview">
									{#if artifact.language}
										<div class="code-language text-xs px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
											{artifact.language}
										</div>
									{/if}
									<pre class="code-content"><code>{artifact.content.slice(0, 500)}{artifact.content.length > 500 ? '\n...' : ''}</code></pre>
								</div>
							{:else if artifact.type === 'document'}
								<div class="document-preview p-3">
									<div class="prose prose-sm dark:prose-invert max-w-none">
										{@html artifact.content.slice(0, 300).replace(/\n/g, '<br>')}
										{#if artifact.content.length > 300}
											<div class="text-gray-500 dark:text-gray-400 text-sm mt-2">...</div>
										{/if}
									</div>
								</div>
							{:else}
								<div class="generic-preview p-3 text-sm text-gray-600 dark:text-gray-300">
									{artifact.content.slice(0, 200)}{artifact.content.length > 200 ? '...' : ''}
								</div>
							{/if}
						</div>
						
						<div class="artifact-footer px-3 py-2 bg-gray-50 dark:bg-gray-900/50 text-xs text-gray-500 dark:text-gray-400">
							Created: {artifact.createdAt.toLocaleDateString()} {artifact.createdAt.toLocaleTimeString()}
							{#if artifact.modifiedAt.getTime() !== artifact.createdAt.getTime()}
								• Modified: {artifact.modifiedAt.toLocaleDateString()} {artifact.modifiedAt.toLocaleTimeString()}
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="empty-state flex flex-col items-center justify-center h-full text-center p-8">
				<File size={48} class="text-gray-300 dark:text-gray-600 mb-4" />
				<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No artifacts yet</h3>
				<p class="text-gray-500 dark:text-gray-400 text-sm max-w-sm">
					Code, documents, and other files generated by the AI will appear here
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.artifacts-panel-container {
		width: 100%;
		background: var(--panel-bg, white);
	}
	
	.artifact-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: 0.375rem;
	}
	
	.artifact-meta {
		min-width: 0;
		flex: 1;
	}
	
	.artifact-title {
		font-size: 0.875rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.artifact-actions {
		opacity: 0;
		transition: opacity 0.2s;
	}
	
	.artifact-item:hover .artifact-actions {
		opacity: 1;
	}
	
	.action-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		padding: 0;
		background: none;
		border: 1px solid #d1d5db;
		border-radius: 0.25rem;
		cursor: pointer;
		transition: all 0.2s;
		color: #6b7280;
	}
	
	:global(.dark) .action-btn {
		border-color: #4b5563;
		color: #9ca3af;
	}
	
	.action-btn:hover {
		background: #f3f4f6;
		border-color: #9ca3af;
	}
	
	:global(.dark) .action-btn:hover {
		background: #374151;
		border-color: #6b7280;
	}
	
	.code-preview {
		overflow: hidden;
	}
	
	.code-language {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		border-bottom: 1px solid #e5e7eb;
	}
	
	:global(.dark) .code-language {
		border-color: #374151;
	}
	
	.code-content {
		padding: 1rem;
		margin: 0;
		font-size: 0.8125rem;
		line-height: 1.5;
		background: #f9fafb;
		border: none;
		overflow-x: auto;
		white-space: pre;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
	}
	
	:global(.dark) .code-content {
		background: #111827;
		color: #e5e7eb;
	}
	
	.document-preview {
		max-height: 200px;
		overflow-y: auto;
	}
	
	.generic-preview {
		max-height: 150px;
		overflow-y: auto;
		line-height: 1.5;
	}
	
	.artifact-item {
		transition: all 0.2s;
	}
	
	.artifact-item:hover {
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
	
	:global(.dark) .artifact-item:hover {
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}
	
	:global(.dark) .artifacts-panel-container {
		--panel-bg: rgb(17 24 39);
	}
</style>