import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import type { ErrorObject } from 'ajv';

// Type definitions
export interface SchemaDefinition {
	type?: string;
	properties?: Record<string, unknown>;
	required?: string[];
	oneOf?: SchemaDefinition[];
	[key: string]: unknown;
}

export interface UISchema {
	$schema: string;
	title: string;
	description: string;
	version: string;
	definitions: Record<string, SchemaDefinition>;
	type: string;
	properties: Record<string, SchemaDefinition>;
	required: string[];
}

export interface ValidationResult {
	isValid: boolean;
	errors: ErrorObject[];
	warnings: ErrorObject[];
}

export interface ComponentValidationResult {
	isValid: boolean;
	errors: ErrorObject[];
}

export interface RequiredPropertiesResult {
	missing: string[];
	hasAll: boolean;
}

export interface FormComponent {
	type: string;
	id: string;
	[key: string]: unknown;
}

export interface FormData {
	version: string;
	type: string;
	components: FormComponent[];
	metadata?: Record<string, unknown>;
	layout?: Record<string, unknown>;
	state?: Record<string, unknown>;
	actions?: Record<string, unknown>;
	theme?: Record<string, unknown>;
}

// Schema validation utility for UI Agent Forms
class SchemaValidator {
	private ajv: Ajv;
	private schema: UISchema | null = null;
	private schemaLoaded: boolean = false;

	constructor() {
		this.ajv = new Ajv({
			allErrors: true,
			verbose: true,
			removeAdditional: false,
			strict: false
		});

		// Add format validators
		addFormats(this.ajv);
	}

	/**
	 * Load schema from backend API
	 */
	async loadSchema(): Promise<UISchema> {
		if (this.schemaLoaded && this.schema) {
			return this.schema;
		}

		try {
			const response = await fetch('/api/v1/schema/ui-agent-form');
			if (!response.ok) {
				throw new Error(`Failed to load schema: ${response.statusText}`);
			}
			this.schema = await response.json();
			this.schemaLoaded = true;
			return this.schema as UISchema;
		} catch (error) {
			console.error('Error loading schema:', error);
			throw error;
		}
	}

	/**
	 * Validate form data against the schema
	 */
	async validateFormData(formData: FormData): Promise<ValidationResult> {
		try {
			if (!this.schema) {
				await this.loadSchema();
			}

			const validate = this.ajv.compile(this.schema!);
			const isValid = !!validate(formData);

			return {
				isValid,
				errors: (validate.errors || []) as ErrorObject[],
				warnings: [] // Could be extended for warnings
			};
		} catch (error) {
			console.error('Validation error:', error);
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			return {
				isValid: false,
				errors: [
					{
						instancePath: '',
						schemaPath: '',
						keyword: 'error',
						params: {},
						message: `Validation failed: ${errorMessage}`,
						dataPath: ''
					} as unknown as ErrorObject
				],
				warnings: []
			};
		}
	}

	/**
	 * Validate individual component
	 */
	async validateComponent(component: FormComponent): Promise<ComponentValidationResult> {
		try {
			if (!this.schema) {
				await this.loadSchema();
			}

			// Get component schema from definitions
			const componentSchema = this.schema!.definitions?.component;
			if (!componentSchema) {
				return {
					isValid: false,
					errors: [
						{
							instancePath: '',
							schemaPath: '',
							keyword: 'error',
							params: {},
							message: 'Component schema not found',
							dataPath: ''
						} as unknown as ErrorObject
					]
				};
			}

			const validate = this.ajv.compile(componentSchema);
			const isValid = !!validate(component);

			return {
				isValid,
				errors: (validate.errors || []) as ErrorObject[]
			};
		} catch (error) {
			console.error('Component validation error:', error);
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			return {
				isValid: false,
				errors: [
					{
						instancePath: '',
						schemaPath: '',
						keyword: 'error',
						params: {},
						message: `Component validation failed: ${errorMessage}`,
						dataPath: ''
					} as unknown as ErrorObject
				]
			};
		}
	}

	/**
	 * Get available component types from schema
	 */
	async getComponentTypes(): Promise<string[]> {
		try {
			if (!this.schema) {
				await this.loadSchema();
			}

			const componentDef = this.schema!.definitions?.component as SchemaDefinition;
			const oneOfArray = componentDef?.oneOf || [];
			return oneOfArray
				.map((def: SchemaDefinition) => {
					const typeProperty = def.properties?.type as SchemaDefinition;
					return typeProperty?.const as string;
				})
				.filter((type: string) => type);
		} catch (error) {
			console.error('Error getting component types:', error);
			return [];
		}
	}

	/**
	 * Get schema for specific component type
	 */
	async getComponentSchema(type: string): Promise<SchemaDefinition | null> {
		try {
			if (!this.schema) {
				await this.loadSchema();
			}

			return this.schema!.definitions?.[type] || null;
		} catch (error) {
			console.error(`Error getting schema for ${type}:`, error);
			return null;
		}
	}

	/**
	 * Format validation errors for display
	 */
	formatErrors(errors: ErrorObject[]): string[] {
		return errors.map((error) => {
			const path = error.instancePath || '';
			const message = error.message || 'Unknown validation error';
			return path ? `${path}: ${message}` : message;
		});
	}

	/**
	 * Check if form data has required properties
	 */
	async checkRequiredProperties(formData: FormData): Promise<RequiredPropertiesResult> {
		try {
			if (!this.schema) {
				await this.loadSchema();
			}

			const required = this.schema!.required || [];
			const missing = required.filter((prop: string) => !(prop in formData));

			return {
				missing,
				hasAll: missing.length === 0
			};
		} catch (error) {
			console.error('Error checking required properties:', error);
			return {
				missing: [],
				hasAll: false
			};
		}
	}
}

// Export singleton instance
export const schemaValidator = new SchemaValidator();
export default schemaValidator;
