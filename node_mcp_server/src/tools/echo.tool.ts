import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const EchoArgsSchema = z.object({
	text: z
		.string()
		.min(1)
		.optional()
		.describe('What should the server say back?'),
	uppercase: z
		.boolean()
		.optional()
		.describe(
			'Convert the echoed text to uppercase before returning it (requires API key).',
		),
});

type EchoArgs = z.infer<typeof EchoArgsSchema>;

type ToolOptions = {
	apiKey: string;
};

/**
 * Register the echo tool
 */
export function registerEcho(server: McpServer, options: ToolOptions) {
	const configuredKey = options.apiKey.trim();
	const serverHasKey = configuredKey.length > 0;

	server.tool(
		'echo',
		'Returns the text you send to it. Uppercase responses are enabled automatically when the server is started with an API key.',
		EchoArgsSchema.shape,
		async (args: EchoArgs) => {
			const rawText =
				typeof args.text === 'string' &&
				args.text.trim().length > 0
					? args.text.trim()
					: 'Hello from icp-coder-mcp-server!';

			const wantsUppercase = args.uppercase ?? false;
			const hasAccess = serverHasKey;
			// Downstream services can reuse `configuredKey` for authenticated requests.
			const text =
				wantsUppercase && hasAccess ? rawText.toUpperCase() : rawText;

			const metaLines = [
				hasAccess
					? 'Server API key loaded and available for downstream calls.'
					: 'Server missing API key; running in read-only mode.',
			];

			if (hasAccess) {
				metaLines.push(
					`Configured API key length: ${configuredKey.length}.`,
				);
			}

			if (wantsUppercase && !hasAccess) {
				metaLines.push(
					'Uppercase transformation requires the server to be started with a valid API key.',
				);
			}

			return {
				content: [
					{
						type: 'text' as const,
						text,
					},
					{
						type: 'text' as const,
						text: metaLines.join(' '),
					},
				],
			};
		},
	);
}
