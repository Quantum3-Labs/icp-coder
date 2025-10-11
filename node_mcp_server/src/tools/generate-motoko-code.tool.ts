import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const BACKEND_URL_ENV = 'BACKEND_URL';
const DEFAULT_BACKEND_BASE_URL = 'http://localhost:8080';
const RAG_GENERATE_PATH = '/api/v1/rag/generate';

const GenerateMotokoCodeArgsSchema = z.object({
	query: z
		.string()
		.min(1)
		.describe('Your code generation request'),
	temperature: z
		.number()
		.min(0)
		.max(2)
		.optional()
		.describe(
			'Controls output creativity. Values near 0 are deterministic; higher values are more diverse.',
		),
	max_tokens: z
		.number()
		.int()
		.positive()
		.optional()
		.describe('Maximum tokens to request from the code generation provider.'),
});

type GenerateMotokoCodeArgs = z.infer<typeof GenerateMotokoCodeArgsSchema>;

type ToolOptions = {
	apiKey: string;
	baseUrl?: string;
};

type GenerateCodeResponse = {
	code?: string;
	explanation?: string;
	error?: string;
};

function resolveBackendBaseUrl(candidate?: string): string {
	const explicit = candidate?.trim();
	if (explicit) {
		return explicit.replace(/\/+$/, '');
	}

	const fromEnv = process.env[BACKEND_URL_ENV]?.trim();
	if (fromEnv) {
		return fromEnv.replace(/\/+$/, '');
	}

	return DEFAULT_BACKEND_BASE_URL;
}

export function registerGenerateMotokoCode(
	server: McpServer,
	options: ToolOptions,
) {
	const apiKey = options.apiKey.trim();

	if (!apiKey) {
		throw new Error(
			'API key is required to register generate_motoko_code tool.',
		);
	}

	const backendBaseUrl = resolveBackendBaseUrl(options.baseUrl);

	server.registerTool(
		'generate_motoko_code',
		{
			title: 'Generate Motoko Code',
			description:
				'Generates Motoko code using backend RAG context and the configured LLM provider.',
			inputSchema: GenerateMotokoCodeArgsSchema.shape,
		},
		async (args: GenerateMotokoCodeArgs) => {
			const payload: Record<string, unknown> = {
				query: args.query.trim(),
			};

			if (typeof args.temperature === 'number') {
				payload.temperature = args.temperature;
			}
			if (typeof args.max_tokens === 'number') {
				payload.max_tokens = args.max_tokens;
			}

			try {
				const response = await fetch(
					`${backendBaseUrl}${RAG_GENERATE_PATH}`,
					{
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
							'x-api-key': apiKey,
						},
						body: JSON.stringify(payload),
					},
				);

				const rawBody = await response.text();
				const parsedBody: GenerateCodeResponse | undefined =
					rawBody.length > 0 ? JSON.parse(rawBody) : undefined;

				if (!response.ok) {
					const backendError =
						parsedBody?.error ??
						`Backend returned status ${response.status}`;
					throw new Error(backendError);
				}

				if (!parsedBody) {
					throw new Error('Backend response was empty.');
				}

				const normalizedCode = parsedBody.code?.trim() ?? '';
				const normalizedExplanation =
					parsedBody.explanation?.trim() ?? '';

				const summaryParts = [
					normalizedCode.length > 0
						? 'Generated Motoko code snippet available.'
						: 'Backend returned an empty code snippet.',
				];

				if (normalizedExplanation.length > 0) {
					summaryParts.push('Explanation included in response.');
				}

				return {
					content: [
						{
							type: 'text' as const,
							text: summaryParts.join(' '),
						},
						{
							type: 'text' as const,
							text:
								normalizedCode.length > 0
									? `Generated code:\n${normalizedCode}`
									: 'No code returned.',
						},
						{
							type: 'text' as const,
							text:
								normalizedExplanation.length > 0
									? `Explanation:\n${normalizedExplanation}`
									: 'No explanation returned.',
						},
					],
				};
			} catch (error) {
				const message =
					error instanceof Error ? error.message : String(error);
				throw new Error(`Failed to generate Motoko code: ${message}`);
			}
		},
	);
}
