import * as path from 'path';
import { workspace, ExtensionContext } from 'vscode';
import { LanguageClient, LanguageClientOptions, ServerOptions, TransportKind } from 'vscode-languageclient';

let client: LanguageClient | undefined;

export function activate(context: ExtensionContext): void {
    const config = workspace.getConfiguration('zhc');
    const serverPath = config.get<string>('languageServer.path', 'zhc-lsp');
    const traceServer = config.get<string>('trace.server', 'off');

    const serverOptions: ServerOptions = {
        run: {
            command: serverPath,
            args: config.get<string[]>('languageServer.args', []),
            transport: TransportKind.stdio,
        },
        debug: {
            command: serverPath,
            args: ['--debug'],
            transport: TransportKind.stdio,
        },
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ language: 'zhc' }],
        traceOutputChannel: traceServer === 'verbose' ? console : undefined,
        trace: traceServer === 'off' ? undefined : traceServer as 'off' | 'messages' | 'verbose',
        synchronize: {
            fileEvents: workspace.createFileSystemWatcher('**/*.zhc'),
        },
    };

    client = new LanguageClient('zhc', 'ZHC Language Server', serverOptions, clientOptions);

    client.start();

    client.onReady().then(() => {
        console.log('ZHC Language Server is now active!');
    });

    // 注册重启命令
    context.subscriptions.push(
        workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('zhc')) {
                restartServer();
            }
        })
    );
}

export function deactivate(): void {
    if (client) {
        client.stop();
    }
}

async function restartServer(): Promise<void> {
    if (client) {
        await client.stop();
        client.start();
    }
}
