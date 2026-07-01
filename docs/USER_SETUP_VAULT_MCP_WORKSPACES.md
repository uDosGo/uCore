# User Setup Guide: Vault Integration, MCP, and Workspace Switching

This guide provides steps for setting up and integrating Vault, MCP, and workspace switching with uCore and AppFlowy.

## Prerequisites

*   **uCore Installation**: Ensure uCore is installed and running. Refer to the main README for installation instructions.
*   **AppFlowy Installation**: Ensure AppFlowy is installed and running. Refer to the official AppFlowy documentation for installation.
*   **Vault**: A local or remote Vault instance accessible by uCore. Configuration details can be found in `config/vault-sync.example.yaml`.
*   **MCP Server**: Ensure MCP servers (e.g., Firewatch, Zapier) are installed and configured if needed. Refer to MCP documentation for setup.
*   **Zen Browser**: Recommended UI shell for development and automation.
*   **Playwright**: Automation driver for Zen Browser and other headless tasks.

## 1. Vault Integration

### 1.1. Local Vault Configuration

1.  **Locate Vault Configuration**: Find the `vault-sync.example.yaml` file in the `config/` directory.
2.  **Copy and Modify**: Copy this file to `config/vault-sync.yaml` and update the following parameters:
    *   `vault_url`: The URL of your Vault instance.
    *   `api_key`: Your Vault API key.
    *   `local_path`: The local directory where Vault data will be synced.
3.  **Enable Vault Sync**: Ensure the Vault sync skill is enabled in uCore's configuration. This is typically done via environment variables or a central configuration file.

### 1.2. Running Vault Sync

You can initiate a manual Vault sync using the Cline CLI:

```bash
cline --yolo "Run Vault sync"
```

This command will trigger the `vault_sync` skill, which synchronizes data between your Vault and AppFlowy. Scheduled syncs are configured to run daily.

## 2. MCP Integration

### 2.1. MCP Server Setup

MCP servers provide tools and resources that uCore can leverage. Ensure the necessary MCP servers are running and accessible locally.

*   **Firewatch MCP**: For browser automation. Install globally (`npm install -g firewatch-mcp`) and configure in Cline settings. Refer to `docs/ZEN_PLAYWRIGHT_AUTOMATION_TOOLCHAIN.md` for detailed setup.
*   **Zapier MCP**: For connecting to Zapier's ecosystem. Refer to Zapier MCP documentation for setup.

### 2.2. Using MCP Tools

MCP tools are accessed via the Cline CLI or directly through API calls.

*   **Cline CLI**:
    ```bash
    cline --yolo "Use Firewatch to navigate to http://localhost:5173 and click 'Import'"
    ```
*   **API Calls**: Refer to `backend/app/api/mcp/` for direct API endpoint usage.

## 3. Workspace Switching with AppFlowy CLI

### 3.1. Listing Workspaces

Use the `appflowy-cli` to manage your AppFlowy workspaces:

```bash
appflowy-cli workspaces
```

This command lists all available workspaces.

### 3.2. Switching Workspaces

To switch to a specific workspace, use the `use` command:

```bash
appflowy-cli use "My Workspace Name"
```

Replace `"My Workspace Name"` with the exact name of the workspace you want to use. This command sets the context for subsequent operations.

## 4. Integrating with n8n

For visual workflow automation, the community n8n node for AppFlowy can be utilized.

1.  **Install n8n**: Follow the official n8n installation guide.
2.  **Add AppFlowy Node**: Install the community n8n node for AppFlowy. Refer to the n8n community nodes documentation.
3.  **Build Workflows**: Use the n8n interface to create workflows. AppFlowy can act as a trigger (e.g., "Row Added to Database") or an action (e.g., "Create Database Item").

## 5. Scheduling Automation

Scheduling can be achieved by scripting `appflowy-cli` commands and running them with system schedulers:

*   **macOS/Linux**: Use `cron` jobs.
*   **Windows**: Use Task Scheduler.

Example `cron` entry to run a daily workspace sync at 4:00 AM:

```cron
0 4 * * * /path/to/appflowy-cli use "My Workspace" && /path/to/appflowy-cli sync --all >> /var/log/appflowy_sync.log 2>&1
```

## 6. Zen Browser and Playwright for Development

Zen Browser, recommended as the UI shell, works seamlessly with Playwright for automation.

### 6.1. Zen Browser Setup

1.  **Install Zen Browser**:
    *   macOS: `brew install zen-browser`
    *   Linux: Download from zen-browser.com
2.  **Install Playwright Browsers**:
    ```bash
    npx playwright install firefox
    # or for Python:
    # playwright install firefox
    ```

### 6.2. Playwright Automation

Playwright can be used to control Zen Browser for various development tasks:

*   **Navigation and Interaction**: Automate browser actions like visiting pages, clicking elements, and filling forms.
*   **Console Log Capture**: Capture logs for debugging.
*   **Data Extraction**: Extract text content, HTML, or perform evaluations.

Refer to `docs/ZEN_PLAYWRIGHT_AUTOMATION_TOOLCHAIN.md` for detailed examples and advanced usage.

---

**Last Updated**: 2026-06-22T21:45:00+08:00
**Session**: Phase 9B Developer wiring and endpoint verification
**Status**: Ready for user setup documentation completion.