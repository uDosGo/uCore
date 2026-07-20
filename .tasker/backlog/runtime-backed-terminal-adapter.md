# Replace Terminal Demo Shell With Runtime-Backed Adapter

Status: in-progress
Priority: P1
Area: uCode / GridCore / runtime bridge
Created: 2026-07-18

## Current Status

- `TerminalSurface` is a demo/local terminal shell rendered through the GridCore canvas path.
- The uCode Terminal tab is a local GridCore buffer demo inside the uCode hub.
- GridCore is the rendering/data primitive layer: `GridBuffer`, `GridCell`, canvas sizing, palette, and font rendering.
- A real uCode/BBC BASIC/terminal runtime bridge is not wired yet.

## Goal

Replace the terminal demo shell with a runtime-backed adapter while keeping GridCore runtime-agnostic. The adapter should own runtime I/O, transport, lifecycle, and conversion from runtime output into `GridBuffer` updates.

## Contract To Define First

- Command/input stream from the frontend into the selected runtime.
- Runtime output stream back to the frontend as ordered text, control events, or `GridBuffer` patches/snapshots.
- Transport shape: REST for request/response commands, WebSocket for interactive terminal/PTY streaming.
- Buffer mapping rules from runtime output into `GridBuffer` cells.
- Runtime target selection: shell/PTY, BBC BASIC, uCode VM, or GridSmith world runner.
- Runtime lifecycle events: start, stop, resize, reset, exit, and error.

## Acceptance Criteria

- `TerminalSurface` and the uCode Terminal tab no longer pretend demo buffers are runtime-backed.
- A typed adapter contract exists for runtime input, runtime output, lifecycle state, and buffer updates.
- The first runtime target is explicitly chosen and documented before implementation.
- GridCore remains a renderer/data primitive package and does not learn backend/runtime details.
- The selected transport has one focused integration check proving input reaches the runtime and output maps to the rendered buffer.

## Progress

- First runtime target selected: local shell/PTY.
- Backend scaffold added at `/api/terminal/runtime/ws` using `aiohttp.web.WebSocketResponse`.
- Frontend uCode Terminal tab now connects to the runtime WebSocket, forwards key input, and maps text output into the GridCore canvas buffer.
- Direct PTY smoke test passes: shell starts, input reaches the process, and output returns through the adapter queue.
- Browser-level verification passes: typed terminal input reaches the PTY and sentinel output appears in the GridCore canvas buffer.
- PTY sessions now set `TERM=xterm-256color`; `clear` emits terminal control sequences instead of a TERM error.
- Initial ANSI/control handling supports OSC skip, CSI home, clear-screen, and clear-line sequences.

## Remaining

- ANSI/control-sequence handling beyond the initial home/clear-line/clear-screen path.
- Decide whether standalone `TerminalSurface` should share this adapter or be retired in favor of the uCode Terminal tab.
