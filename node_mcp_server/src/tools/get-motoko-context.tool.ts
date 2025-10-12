import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const BACKEND_URL_ENV = 'BACKEND_URL';
const DEFAULT_BACKEND_BASE_URL = 'http://localhost:8080';
const RAG_RETRIEVE_PATH = '/api/v1/rag/retrieve';

const GetMotokoContextArgsSchema = z.object({
	query: z
		.string()
		.min(1)
		.describe("What you're looking for"),
	n_results: z
		.number()
		.int()
		.min(1)
		.max(20)
		.optional()
		.describe('How many matches to return (1-20, defaults to 5).'),
});

type GetMotokoContextArgs = z.infer<typeof GetMotokoContextArgsSchema>;

type ToolOptions = {
	apiKey: string;
	baseUrl?: string;
};

type RetrieveContextResponse = {
	code_contexts?: string[];
	code_distances?: number[];
	docs_contexts?: string[];
	docs_distances?: number[];
	warning?: string;
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

export function registerGetMotokoContext(
	server: McpServer,
	options: ToolOptions,
) {
	const apiKey = options.apiKey.trim();

	if (!apiKey) {
		throw new Error(
			'API key is required to register get_motoko_context tool.',
		);
	}

	const backendBaseUrl = resolveBackendBaseUrl(options.baseUrl);

	server.registerTool(
		'get_motoko_context',
		{
			title: 'Retrieve Motoko Context',
			description:
				'Fetches relevant Motoko code and documentation snippets from the backend RAG service.',
			inputSchema: GetMotokoContextArgsSchema.shape,
		},
		async ({ query, n_results }: GetMotokoContextArgs) => {
			const payload = {
				query: query.trim(),
				n_results: n_results ?? 5,
			};

			try {
				const response = await fetch(
					`${backendBaseUrl}${RAG_RETRIEVE_PATH}`,
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
				const parsedBody: RetrieveContextResponse | undefined =
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

				const codeCount = parsedBody.code_contexts?.length ?? 0;
				const docsCount = parsedBody.docs_contexts?.length ?? 0;

				const summaryPieces = [
					`Retrieved ${codeCount} code context${codeCount === 1 ? '' : 's'}.`,
					`Retrieved ${docsCount} documentation context${docsCount === 1 ? '' : 's'}.`,
				];

				if (parsedBody.warning) {
					summaryPieces.push(`Warning: ${parsedBody.warning}`);
				}

				return {
					content: [
						{
							type: 'text' as const,
							text: summaryPieces.join(' '),
						},
						{
							type: 'text' as const,
							text: `Raw RAG response:\n${JSON.stringify(parsedBody, null, 2)}`,
						},
					],
				};
			} catch (error) {
				const message =
					error instanceof Error ? error.message : String(error);
				throw new Error(
					`Failed to retrieve Motoko context: ${message}`,
				);
			}
		},
	);
}
