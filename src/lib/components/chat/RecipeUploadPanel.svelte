<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Upload, FileSpreadsheet, FileText, X, Check, AlertCircle } from 'lucide-svelte';
	
	const dispatch = createEventDispatcher();
	
	export let isVisible = false;
	
	let files: FileList | null = null;
	let schemaText = '';
	let dragActive = false;
	let uploadProgress = 0;
	let uploadStatus: 'idle' | 'uploading' | 'success' | 'error' = 'idle';
	let errorMessage = '';
	
	// Sample schema template
	const sampleSchema = `{
  "type": "object",
  "properties": {
    "name": {"type": "string", "description": "Recipe name"},
    "ingredients": {
      "type": "array",
      "items": {
        "type": "object", 
        "properties": {
          "name": {"type": "string"},
          "amount": {"type": "string"},
          "unit": {"type": "string"}
        },
        "required": ["name", "amount"]
      }
    },
    "instructions": {"type": "string"},
    "prep_time": {"type": "string"},
    "cook_time": {"type": "string"},
    "servings": {"type": "integer"},
    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["name", "ingredients", "instructions"]
}`;

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragActive = true;
	}
	
	function handleDragLeave(e: DragEvent) {
		e.preventDefault();
		dragActive = false;
	}
	
	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragActive = false;
		
		const droppedFiles = e.dataTransfer?.files;
		if (droppedFiles) {
			files = droppedFiles;
			validateFiles();
		}
	}
	
	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		files = target.files;
		validateFiles();
	}
	
	function validateFiles() {
		if (!files) return;
		
		const validExtensions = ['.xlsx', '.xls'];
		let allValid = true;
		
		for (let i = 0; i < files.length; i++) {
			const file = files[i];
			const extension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
			
			if (!validExtensions.includes(extension)) {
				allValid = false;
				errorMessage = `Invalid file type: ${file.name}. Only Excel files (.xlsx, .xls) are allowed.`;
				break;
			}
			
			// Check file size (max 10MB)
			if (file.size > 10 * 1024 * 1024) {
				allValid = false;
				errorMessage = `File too large: ${file.name}. Maximum size is 10MB.`;
				break;
			}
		}
		
		if (allValid) {
			uploadStatus = 'idle';
			errorMessage = '';
		} else {
			uploadStatus = 'error';
		}
	}
	
	function validateSchema() {
		if (!schemaText.trim()) return true;
		
		try {
			JSON.parse(schemaText);
			return true;
		} catch (e) {
			errorMessage = 'Invalid JSON schema format';
			return false;
		}
	}
	
	function loadSampleSchema() {
		schemaText = sampleSchema;
	}
	
	async function handleSubmit() {
		if (!files || files.length === 0) {
			errorMessage = 'Please select at least one Excel file';
			uploadStatus = 'error';
			return;
		}
		
		if (!validateSchema()) {
			uploadStatus = 'error';
			return;
		}
		
		uploadStatus = 'uploading';
		uploadProgress = 0;
		
		// Simulate upload progress
		const progressInterval = setInterval(() => {
			uploadProgress += 10;
			if (uploadProgress >= 100) {
				clearInterval(progressInterval);
				uploadStatus = 'success';
				
				// Dispatch event with files and schema
				dispatch('upload', {
					files: Array.from(files!),
					schema: schemaText ? JSON.parse(schemaText) : null
				});
				
				setTimeout(() => {
					isVisible = false;
				}, 1500);
			}
		}, 200);
	}
	
	function removeFile(index: number) {
		if (!files) return;
		
		const dt = new DataTransfer();
		for (let i = 0; i < files.length; i++) {
			if (i !== index) {
				dt.items.add(files[i]);
			}
		}
		files = dt.files;
		
		if (files.length === 0) {
			uploadStatus = 'idle';
		}
	}
	
	function close() {
		isVisible = false;
		// Reset state
		files = null;
		schemaText = '';
		uploadStatus = 'idle';
		uploadProgress = 0;
		errorMessage = '';
	}
</script>

{#if isVisible}
	<div class="recipe-upload-overlay">
		<div class="recipe-upload-modal">
			<div class="modal-header">
				<h2 class="modal-title">Recipe Processing Setup</h2>
				<button class="close-btn" on:click={close}>
					<X size={20} />
				</button>
			</div>
			
			<div class="modal-content">
				<!-- File Upload Section -->
				<div class="upload-section">
					<h3 class="section-title">
						<FileSpreadsheet size={18} />
						Upload Recipe Files
					</h3>
					<p class="section-description">
						Upload Excel files (.xlsx, .xls) containing your recipe data
					</p>
					
					<div 
						class="file-drop-zone"
						class:drag-active={dragActive}
						class:has-files={files && files.length > 0}
						on:dragover={handleDragOver}
						on:dragleave={handleDragLeave}
						on:drop={handleDrop}
						role="button"
						tabindex="0"
					>
						{#if files && files.length > 0}
							<div class="selected-files">
								{#each Array.from(files) as file, i}
									<div class="file-item">
										<FileSpreadsheet size={16} class="text-green-600" />
										<span class="file-name">{file.name}</span>
										<span class="file-size">({(file.size / 1024 / 1024).toFixed(1)} MB)</span>
										<button class="remove-file" on:click={() => removeFile(i)}>
											<X size={14} />
										</button>
									</div>
								{/each}
							</div>
						{:else}
							<div class="drop-zone-content">
								<Upload size={32} class="text-gray-400" />
								<p class="drop-text">Drag and drop Excel files here, or</p>
								<button class="browse-btn">Browse files</button>
							</div>
						{/if}
						
						<input 
							type="file" 
							multiple 
							accept=".xlsx,.xls"
							class="file-input"
							on:change={handleFileSelect}
						/>
					</div>
				</div>
				
				<!-- Schema Section -->
				<div class="schema-section">
					<div class="schema-header">
						<h3 class="section-title">
							<FileText size={18} />
							JSON Schema (Optional)
						</h3>
						<button class="sample-btn" on:click={loadSampleSchema}>
							Load Sample Schema
						</button>
					</div>
					<p class="section-description">
						Define the structure for your output JSON. Leave empty to use auto-detection.
					</p>
					
					<textarea
						class="schema-textarea"
						placeholder="Paste your JSON schema here..."
						bind:value={schemaText}
						rows="8"
					></textarea>
				</div>
				
				{#if errorMessage}
					<div class="error-message">
						<AlertCircle size={16} />
						{errorMessage}
					</div>
				{/if}
				
				{#if uploadStatus === 'uploading'}
					<div class="upload-progress">
						<div class="progress-bar">
							<div class="progress-fill" style="width: {uploadProgress}%"></div>
						</div>
						<span class="progress-text">Uploading... {uploadProgress}%</span>
					</div>
				{/if}
				
				{#if uploadStatus === 'success'}
					<div class="success-message">
						<Check size={16} />
						Files uploaded successfully! Starting recipe processing...
					</div>
				{/if}
			</div>
			
			<div class="modal-footer">
				<button class="cancel-btn" on:click={close} disabled={uploadStatus === 'uploading'}>
					Cancel
				</button>
				<button 
					class="process-btn" 
					on:click={handleSubmit}
					disabled={!files || files.length === 0 || uploadStatus === 'uploading'}
				>
					{#if uploadStatus === 'uploading'}
						Processing...
					{:else}
						Start Processing
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.recipe-upload-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 2rem;
	}
	
	.recipe-upload-modal {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
		max-width: 600px;
		width: 100%;
		max-height: 80vh;
		overflow-y: auto;
	}
	
	:global(.dark) .recipe-upload-modal {
		background: #1f2937;
		border: 1px solid #374151;
	}
	
	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.5rem 2rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	:global(.dark) .modal-header {
		border-color: #374151;
	}
	
	.modal-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: #1f2937;
		margin: 0;
	}
	
	:global(.dark) .modal-title {
		color: #f3f4f6;
	}
	
	.close-btn {
		padding: 0.5rem;
		border: none;
		background: none;
		cursor: pointer;
		border-radius: 0.375rem;
		color: #6b7280;
		transition: all 0.2s;
	}
	
	.close-btn:hover {
		background: #f3f4f6;
		color: #374151;
	}
	
	:global(.dark) .close-btn:hover {
		background: #374151;
		color: #d1d5db;
	}
	
	.modal-content {
		padding: 2rem;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.section-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 1rem;
		font-weight: 600;
		color: #1f2937;
		margin: 0 0 0.5rem 0;
	}
	
	:global(.dark) .section-title {
		color: #f3f4f6;
	}
	
	.section-description {
		color: #6b7280;
		font-size: 0.875rem;
		margin: 0 0 1rem 0;
		line-height: 1.5;
	}
	
	.file-drop-zone {
		position: relative;
		border: 2px dashed #d1d5db;
		border-radius: 0.5rem;
		padding: 2rem;
		text-align: center;
		transition: all 0.2s;
		cursor: pointer;
		min-height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.file-drop-zone:hover,
	.file-drop-zone.drag-active {
		border-color: #3b82f6;
		background: #eff6ff;
	}
	
	:global(.dark) .file-drop-zone {
		border-color: #4b5563;
	}
	
	:global(.dark) .file-drop-zone:hover,
	:global(.dark) .file-drop-zone.drag-active {
		border-color: #3b82f6;
		background: #1e3a8a;
	}
	
	.file-drop-zone.has-files {
		border-color: #10b981;
		background: #f0fdf4;
		padding: 1rem;
	}
	
	:global(.dark) .file-drop-zone.has-files {
		background: #064e3b;
	}
	
	.file-input {
		position: absolute;
		inset: 0;
		opacity: 0;
		cursor: pointer;
	}
	
	.drop-zone-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}
	
	.drop-text {
		color: #6b7280;
		margin: 0;
	}
	
	.browse-btn {
		padding: 0.5rem 1rem;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 0.375rem;
		cursor: pointer;
		font-size: 0.875rem;
		transition: background 0.2s;
	}
	
	.browse-btn:hover {
		background: #2563eb;
	}
	
	.selected-files {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		width: 100%;
	}
	
	.file-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
	}
	
	:global(.dark) .file-item {
		background: #374151;
		border-color: #4b5563;
	}
	
	.file-name {
		flex: 1;
		font-weight: 500;
		color: #1f2937;
	}
	
	:global(.dark) .file-name {
		color: #f3f4f6;
	}
	
	.file-size {
		font-size: 0.8125rem;
		color: #6b7280;
	}
	
	.remove-file {
		padding: 0.25rem;
		background: none;
		border: none;
		cursor: pointer;
		color: #ef4444;
		border-radius: 0.25rem;
		transition: background 0.2s;
	}
	
	.remove-file:hover {
		background: #fef2f2;
	}
	
	:global(.dark) .remove-file:hover {
		background: #7f1d1d;
	}
	
	.schema-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
	}
	
	.sample-btn {
		padding: 0.375rem 0.75rem;
		background: none;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		cursor: pointer;
		font-size: 0.8125rem;
		color: #374151;
		transition: all 0.2s;
	}
	
	.sample-btn:hover {
		background: #f3f4f6;
		border-color: #9ca3af;
	}
	
	:global(.dark) .sample-btn {
		border-color: #4b5563;
		color: #d1d5db;
	}
	
	:global(.dark) .sample-btn:hover {
		background: #374151;
		border-color: #6b7280;
	}
	
	.schema-textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.8125rem;
		resize: vertical;
		min-height: 150px;
	}
	
	.schema-textarea:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	
	:global(.dark) .schema-textarea {
		background: #374151;
		border-color: #4b5563;
		color: #f3f4f6;
	}
	
	.error-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.375rem;
		color: #dc2626;
		font-size: 0.875rem;
	}
	
	:global(.dark) .error-message {
		background: #7f1d1d;
		border-color: #b91c1c;
		color: #fca5a5;
	}
	
	.success-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 0.375rem;
		color: #16a34a;
		font-size: 0.875rem;
	}
	
	:global(.dark) .success-message {
		background: #064e3b;
		border-color: #059669;
		color: #86efac;
	}
	
	.upload-progress {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}
	
	.progress-fill {
		height: 100%;
		background: #3b82f6;
		transition: width 0.3s ease;
	}
	
	.progress-text {
		font-size: 0.875rem;
		color: #6b7280;
		text-align: center;
	}
	
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
		padding: 1.5rem 2rem;
		border-top: 1px solid #e5e7eb;
	}
	
	:global(.dark) .modal-footer {
		border-color: #374151;
	}
	
	.cancel-btn,
	.process-btn {
		padding: 0.625rem 1.25rem;
		border: none;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		transition: all 0.2s;
	}
	
	.cancel-btn {
		background: none;
		color: #6b7280;
		border: 1px solid #d1d5db;
	}
	
	.cancel-btn:hover:not(:disabled) {
		background: #f3f4f6;
		color: #374151;
	}
	
	.process-btn {
		background: #3b82f6;
		color: white;
	}
	
	.process-btn:hover:not(:disabled) {
		background: #2563eb;
	}
	
	.process-btn:disabled,
	.cancel-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>