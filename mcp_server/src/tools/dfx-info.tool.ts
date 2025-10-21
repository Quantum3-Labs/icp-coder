import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';

const execAsync = promisify(exec);

const DfxInfoArgsSchema = z.object({});

type DfxInfoArgs = z.infer<typeof DfxInfoArgsSchema>;

export function registerDfxInfo(server: McpServer) {
	server.registerTool(
		'dfx_info',
		{
			title: 'Get DFX Project Info',
			description:
				'Runs "dfx info" to get information about the current dfx project',
			inputSchema: DfxInfoArgsSchema.shape,
		},
		async (_args: DfxInfoArgs) => {
			try {
				const { stdout, stderr } = await execAsync('dfx info');

				return {
					content: [
						{
							type: 'text' as const,
							text: 'DFX Info retrieved successfully.',
						},
						{
							type: 'text' as const,
							text: `Output:\n${stdout}`,
						},
						...(stderr
							? [
									{
										type: 'text' as const,
										text: `Warnings/Errors:\n${stderr}`,
									},
							  ]
							: []),
					],
				};
			} catch (error) {
				const message =
					error instanceof Error ? error.message : String(error);
				throw new Error(`Failed to run dfx info: ${message}`);
			}
		},
	);
}
