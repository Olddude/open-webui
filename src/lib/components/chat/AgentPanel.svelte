<script lang="ts">
	import { agentState, togglePanel, loadDemoData, resetAgentState } from '$lib/stores/agentState';
	import { taskQueue } from '$lib/stores/taskQueue';
	import TaskPlanning from './Messages/TaskPlanning.svelte';
	import ReasoningDisplay from './Messages/ReasoningDisplay.svelte';
	import TaskMonitor from './Messages/TaskMonitor.svelte';
	import RecipeUploadPanel from './RecipeUploadPanel.svelte';
	import { ChevronDown, ChevronRight, Brain, ListTodo, Activity, Settings, Play, RotateCcw, ChefHat, X } from 'lucide-svelte';
	
	let showRecipeUpload = false;

	$: showTaskPanel = $agentState.showTaskPanel;
	$: showReasoningPanel = $agentState.showReasoningPanel;
	$: activeTasks = $agentState.activeTasks;
	$: reasoningChain = $agentState.reasoningChain;
	$: currentPlan = $agentState.currentPlan;
	$: queuedTasks = $taskQueue.queue;
	$: runningTasks = $taskQueue.running;
	
	function loadRecipeDemoData() {
		// Load recipe processing demo data
		const recipeTasks = [
			{
				id: 'recipe-task-1',
				title: 'File Validation',
				description: 'Validating uploaded Excel files and checking format',
				status: 'completed' as const,
				progress: 100,
				children: [
					{
						id: 'recipe-task-1-1',
						title: 'Check file extensions',
						description: 'Verify .xlsx/.xls format',
						status: 'completed' as const,
						progress: 100,
						children: [],
						dependencies: []
					},
					{
						id: 'recipe-task-1-2', 
						title: 'Verify Excel format',
						description: 'Parse Excel structure',
						status: 'completed' as const,
						progress: 100,
						children: [],
						dependencies: []
					}
				],
				dependencies: [],
				startTime: new Date(Date.now() - 120000),
				endTime: new Date(Date.now() - 100000)
			},
			{
				id: 'recipe-task-2',
				title: 'RAG Processing',
				description: 'Using RAG to enhance and structure recipe data (15/25 recipes)',
				status: 'executing' as const,
				progress: 60,
				children: [],
				dependencies: ['recipe-task-1'],
				startTime: new Date(Date.now() - 80000)
			},
			{
				id: 'recipe-task-3',
				title: 'JSON Generation',
				description: 'Generating final structured JSON output',
				status: 'pending' as const,
				progress: 0,
				children: [],
				dependencies: ['recipe-task-2']
			}
		];

		const recipeReasoning = [
			{
				id: 'recipe-reason-1',
				type: 'analysis' as const,
				content: 'Processing 3 Excel files with 25 total recipes. Schema provided specifies required fields: name, ingredients, instructions with optional prep/cook times.',
				timestamp: new Date(Date.now() - 150000),
				confidence: 0.95
			},
			{
				id: 'recipe-reason-2',
				type: 'strategy' as const,
				content: 'Using RAG to standardize ingredient names and enhance instruction clarity. Processing in chunks of 5 recipes for optimal performance.',
				timestamp: new Date(Date.now() - 120000),
				confidence: 0.9,
				alternatives: ['Batch all at once', 'Individual processing'],
				selected: true
			},
			{
				id: 'recipe-reason-3',
				type: 'thinking' as const,
				content: 'Detected inconsistent ingredient formatting across files. Applying normalization rules and unit conversions.',
				timestamp: new Date(Date.now() - 60000),
				confidence: 0.85
			}
		];

		const recipeArtifacts = [
			{
				id: 'recipe-artifact-1',
				type: 'document' as const,
				title: 'Processing Summary',
				content: `# Recipe Processing Report

## Files Processed
- recipes_batch_1.xlsx (8 recipes)
- recipes_batch_2.xlsx (12 recipes) 
- recipes_batch_3.xlsx (5 recipes)

## Progress Status
- ✅ File validation completed
- ⏳ RAG processing: 15/25 recipes (60%)
- ⏸️ JSON generation pending

## Identified Issues
- Ingredient units normalized (cups → metric)
- 3 recipes missing prep time (estimated)
- Standardized difficulty levels

## Next Steps
- Complete RAG processing for remaining 10 recipes
- Apply final schema validation
- Generate structured JSON output`,
				version: 1,
				createdAt: new Date(Date.now() - 90000),
				modifiedAt: new Date(Date.now() - 30000)
			},
			{
				id: 'recipe-json-output',
				type: 'code' as const,
				title: 'recipes_output.json',
				content: JSON.stringify({
					metadata: {
						total_recipes: 25,
						processed_at: new Date().toISOString(),
						schema_version: "1.0",
						processing_time: "2m 15s",
						success_rate: "96%"
					},
					recipes: [
						{
							id: "recipe_001",
							name: "Classic Margherita Pizza",
							ingredients: [
								{ name: "pizza dough", amount: "1 lb", unit: "pound" },
								{ name: "tomato sauce", amount: "1/2 cup", unit: "cup" },
								{ name: "fresh mozzarella", amount: "8 oz", unit: "ounce" },
								{ name: "fresh basil", amount: "10 leaves", unit: "pieces" },
								{ name: "olive oil", amount: "2 tbsp", unit: "tablespoon" }
							],
							instructions: "Preheat oven to 475°F. Roll out pizza dough on floured surface. Spread tomato sauce evenly. Add torn mozzarella and drizzle with olive oil. Bake 12-15 minutes until crust is golden. Top with fresh basil before serving.",
							prep_time: "15 minutes",
							cook_time: "15 minutes",
							servings: 4,
							difficulty: "easy",
							tags: ["italian", "vegetarian", "pizza"]
						},
						{
							id: "recipe_002", 
							name: "Chocolate Chip Cookies",
							ingredients: [
								{ name: "all-purpose flour", amount: "2 1/4 cups", unit: "cup" },
								{ name: "butter", amount: "1 cup", unit: "cup" },
								{ name: "brown sugar", amount: "3/4 cup", unit: "cup" },
								{ name: "granulated sugar", amount: "1/2 cup", unit: "cup" },
								{ name: "eggs", amount: "2 large", unit: "pieces" },
								{ name: "vanilla extract", amount: "1 tsp", unit: "teaspoon" },
								{ name: "chocolate chips", amount: "2 cups", unit: "cup" }
							],
							instructions: "Cream butter and sugars. Beat in eggs and vanilla. Mix in flour. Fold in chocolate chips. Drop rounded tablespoons on baking sheet. Bake at 375°F for 9-11 minutes.",
							prep_time: "20 minutes",
							cook_time: "10 minutes",
							servings: 48,
							difficulty: "easy",
							tags: ["dessert", "cookies", "chocolate"]
						},
						{
							id: "recipe_003",
							name: "Grilled Salmon with Lemon",
							ingredients: [
								{ name: "salmon fillets", amount: "4 pieces", unit: "pieces" },
								{ name: "lemon", amount: "2 large", unit: "pieces" },
								{ name: "olive oil", amount: "3 tbsp", unit: "tablespoon" },
								{ name: "garlic", amount: "3 cloves", unit: "pieces" },
								{ name: "dill", amount: "2 tbsp", unit: "tablespoon" }
							],
							instructions: "Marinate salmon in olive oil, lemon juice, garlic and dill for 30 minutes. Preheat grill to medium-high. Grill salmon 6-8 minutes per side until flakes easily.",
							prep_time: "35 minutes",
							cook_time: "15 minutes", 
							servings: 4,
							difficulty: "medium",
							tags: ["seafood", "healthy", "grilled"]
						}
					]
				}, null, 2),
				language: 'json',
				version: 1,
				createdAt: new Date(Date.now() - 10000),
				modifiedAt: new Date(Date.now() - 10000)
			}
		];

		agentState.update(state => ({
			...state,
			activeTasks: recipeTasks,
			reasoningChain: recipeReasoning,
			artifacts: recipeArtifacts,
			currentPlan: {
				id: 'recipe-plan',
				title: 'Process Recipe Collection',
				description: 'Convert Excel recipe files to structured JSON using RAG enhancement',
				status: 'executing' as const,
				progress: 60,
				children: recipeTasks,
				dependencies: [],
				startTime: new Date(Date.now() - 120000)
			}
		}));
	}
	
	function handleRecipeUpload(event) {
		const { files, schema } = event.detail;
		console.log('Recipe files uploaded:', files);
		console.log('Schema:', schema);
		
		// Start recipe processing demo
		setTimeout(() => {
			loadRecipeDemoData();
		}, 1000);
	}
</script>

<div class="agent-panel-container h-full flex flex-col">
	<div class="panel-header p-4 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center justify-between mb-2">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">
				Agent Activity
			</h2>
			<div class="flex gap-1">
				<button
					class="p-1 hover:bg-orange-100 dark:hover:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded transition-colors"
					title="Process Recipes (Demo)"
					on:click={() => showRecipeUpload = true}
				>
					<ChefHat size={16} />
				</button>
				<button
					class="p-1 hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600 dark:text-green-400 rounded transition-colors"
					title="Load Demo Data"
					on:click={loadDemoData}
				>
					<Play size={16} />
				</button>
				<button
					class="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 rounded transition-colors"
					title="Reset Data"
					on:click={resetAgentState}
				>
					<RotateCcw size={16} />
				</button>
				<button
					class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
					title="Settings"
				>
					<Settings size={16} />
				</button>
				<button
					class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
					title="Close Panel"
					on:click={() => {
						// Close both task and reasoning panels to hide the entire AgentPanel
						agentState.update(state => ({
							...state,
							showTaskPanel: false,
							showReasoningPanel: false
						}));
					}}
				>
					<X size={16} />
				</button>
			</div>
		</div>
		<div class="flex gap-2 text-xs">
			<span class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
				{runningTasks.length} Active
			</span>
			<span class="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
				{queuedTasks.length} Queued
			</span>
		</div>
	</div>

	<div class="panel-content flex-1 overflow-y-auto">
		<!-- Task Planning Section -->
		<div class="section border-b border-gray-200 dark:border-gray-700">
			<button
				class="section-header w-full p-3 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				on:click={() => togglePanel('task')}
			>
				<div class="flex items-center gap-2">
					<ListTodo size={16} class="text-blue-600 dark:text-blue-400" />
					<span class="font-medium text-gray-700 dark:text-gray-300">Task Planning</span>
					{#if activeTasks.length > 0}
						<span class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full">
							{activeTasks.length}
						</span>
					{/if}
				</div>
				{#if showTaskPanel}
					<ChevronDown size={16} class="text-gray-500" />
				{:else}
					<ChevronRight size={16} class="text-gray-500" />
				{/if}
			</button>
			
			{#if showTaskPanel}
				<div class="section-content p-3">
					{#if currentPlan}
						<TaskPlanning task={currentPlan} />
					{:else if activeTasks.length > 0}
						<TaskMonitor tasks={activeTasks} />
					{:else}
						<div class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
							No active tasks
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Reasoning Display Section -->
		<div class="section border-b border-gray-200 dark:border-gray-700">
			<button
				class="section-header w-full p-3 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				on:click={() => togglePanel('reasoning')}
			>
				<div class="flex items-center gap-2">
					<Brain size={16} class="text-purple-600 dark:text-purple-400" />
					<span class="font-medium text-gray-700 dark:text-gray-300">Agent Reasoning</span>
					{#if reasoningChain.length > 0}
						<span class="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full">
							{reasoningChain.length}
						</span>
					{/if}
				</div>
				{#if showReasoningPanel}
					<ChevronDown size={16} class="text-gray-500" />
				{:else}
					<ChevronRight size={16} class="text-gray-500" />
				{/if}
			</button>
			
			{#if showReasoningPanel}
				<div class="section-content p-3">
					{#if reasoningChain.length > 0}
						<ReasoningDisplay steps={reasoningChain} />
					{:else}
						<div class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
							No reasoning steps yet
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Execution Monitor Section -->
		<div class="section">
			<div class="section-header p-3 flex items-center gap-2">
				<Activity size={16} class="text-green-600 dark:text-green-400" />
				<span class="font-medium text-gray-700 dark:text-gray-300">Execution Monitor</span>
			</div>
			<div class="section-content p-3">
				{#if runningTasks.length > 0}
					<div class="space-y-2">
						{#each runningTasks as task}
							<div class="task-item p-2 bg-gray-50 dark:bg-gray-800 rounded">
								<div class="flex items-center justify-between mb-1">
									<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
										{task.name}
									</span>
									<span class="text-xs text-gray-500 dark:text-gray-400">
										{task.progress}%
									</span>
								</div>
								<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
									<div 
										class="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
										style="width: {task.progress}%"
									></div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
						No running tasks
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<RecipeUploadPanel bind:isVisible={showRecipeUpload} on:upload={handleRecipeUpload} />

<style>
	.agent-panel-container {
		width: 100%;
		background: var(--panel-bg, white);
	}

	.section {
		position: relative;
	}

	.section-header {
		text-align: left;
		outline: none;
	}

	.section-header:focus-visible {
		box-shadow: inset 0 0 0 2px rgba(99, 102, 241, 0.5);
	}

	.section-content {
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.task-item {
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	:global(.dark) .agent-panel-container {
		--panel-bg: rgb(17 24 39);
	}
</style>