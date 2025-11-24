"""Main Textual TUI application for AI Summit CLI."""

import subprocess
import traceback
from datetime import datetime
from typing import Optional

from rich.markdown import Markdown
from textual import log
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Input, Static

from ..agent import create_agent


class ChatMessage(Static):
    """A chat message widget with role styling."""

    def __init__(self, message: str, role: str = "user", **kwargs) -> None:
        """Initialize a chat message.

        Args:
            message: The message content
            role: Either 'user' or 'assistant'
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.message = message
        self.role = role
        self.add_class(f"message-{role}")

    def compose(self) -> ComposeResult:
        """Compose the message content."""
        if self.role == "assistant":
            yield Static(Markdown(self.message), classes="message-content")
        else:
            yield Static(self.message, classes="message-content")


class InfoPanel(Static):
    """Right-side information panel."""

    def __init__(self, **kwargs) -> None:
        """Initialize the info panel."""
        super().__init__(**kwargs)
        self.border_title = "Info"

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        from pathlib import Path

        yield Static("[dim]Model:[/dim] claude-sonnet-4-5-20250929\n", classes="panel-section", id="info-model")

        # Working directory (full path)
        workdir = str(Path.cwd())
        yield Static(f"[dim]Working Dir:[/dim] [cyan]{workdir}[/cyan]", classes="panel-section", id="info-workdir")

        # Git branch (with ID so we can update it)
        branch = self.get_git_branch()
        if branch:
            yield Static(f"[dim]Branch:[/dim] [yellow]{branch}[/yellow]", classes="panel-section", id="info-branch")
        else:
            yield Static("", classes="panel-section", id="info-branch")

    def get_git_branch(self) -> Optional[str]:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def refresh_branch(self) -> None:
        """Refresh the branch display."""
        branch = self.get_git_branch()
        try:
            branch_widget = self.query_one("#info-branch", Static)
            if branch:
                branch_widget.update(f"[dim]Branch:[/dim] [yellow]{branch}[/yellow]")
            else:
                branch_widget.update("")
        except Exception:
            pass  # Widget not found or other error


class ToolCallsPanel(Static):
    """Panel showing real-time tool call status."""

    def __init__(self, **kwargs) -> None:
        """Initialize the tool calls panel."""
        super().__init__(**kwargs)
        self.border_title = "Tool Calls"
        self.tool_calls: list[dict] = []
        self.query_count = 0
        self.needs_separator = False  # Track if we need to add separator on next tool call

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        yield Static("", id="tool-calls-content")

    def start_new_query(self) -> None:
        """Mark that a new query is starting (separator will be added on first tool call)."""
        self.needs_separator = True

    def add_tool_call(self, tool_name: str, tool_id: str, args: str = "{}") -> None:
        """Add a new tool call.

        Args:
            tool_name: Name of the tool being called
            tool_id: Unique identifier for this tool call
            args: JSON string with tool arguments
        """
        # Add separator before first tool call if needed
        if self.needs_separator:
            self.query_count += 1
            self.tool_calls.append({
                "type": "separator",
                "query_number": self.query_count,
                "timestamp": datetime.now(),
            })
            self.needs_separator = False

        self.tool_calls.append({
            "type": "tool_call",
            "name": tool_name,
            "id": tool_id,
            "args": args,
            "start_time": datetime.now(),
            "end_time": None,
            "status": "running",
        })
        self.update_display()

    def complete_tool_call(self, tool_id: str) -> None:
        """Mark a tool call as completed."""
        for tool_call in self.tool_calls:
            if tool_call.get("type") == "tool_call" and tool_call["id"] == tool_id:
                tool_call["end_time"] = datetime.now()
                tool_call["status"] = "completed"
                break
        self.update_display()

    def clear_tool_calls(self) -> None:
        """Clear all tool calls."""
        self.tool_calls = []
        self.query_count = 0
        self.update_display()

    def update_display(self) -> None:
        """Update the display with current tool calls."""
        import json

        if not self.tool_calls:
            content = "[dim]No tool calls yet[/dim]"
        else:
            lines = []
            for item in self.tool_calls:
                # Handle separator
                if item.get("type") == "separator":
                    timestamp = item["timestamp"].strftime("%H:%M:%S")
                    # Same format for all queries
                    lines.append("")
                    lines.append(f"[dim]{'─' * 40}[/dim]")
                    lines.append(f"[dim]Query #{item['query_number']} at {timestamp}[/dim]")
                    lines.append(f"[dim]{'─' * 40}[/dim]")
                    lines.append("")
                    continue

                # Handle tool call
                tool_call = item
                duration = ""
                if tool_call.get("end_time"):
                    elapsed = (tool_call["end_time"] - tool_call["start_time"]).total_seconds()
                    duration = f" [dim]({elapsed:.2f}s)[/dim]"

                if tool_call.get("status") == "running":
                    icon = "⏳"
                    status = "[yellow]running...[/yellow]"
                elif tool_call.get("status") == "completed":
                    icon = "✓"
                    status = f"[green]completed[/green]{duration}"
                else:
                    icon = "✗"
                    status = "[red]failed[/red]"

                lines.append(f"{icon} [cyan]{tool_call['name']}[/cyan]")

                # Parse and display arguments
                try:
                    args = json.loads(tool_call.get("args", "{}"))
                    if args:
                        # Format args as key=value pairs
                        arg_parts = []
                        for key, value in args.items():
                            # Truncate long values
                            value_str = str(value)
                            if len(value_str) > 50:
                                value_str = value_str[:47] + "..."
                            arg_parts.append(f"{key}={value_str}")
                        args_display = ", ".join(arg_parts)
                        lines.append(f"  [dim]{args_display}[/dim]")
                except (json.JSONDecodeError, Exception):
                    # If args can't be parsed, skip displaying them
                    pass

                lines.append(f"  {status}")

            content = "\n".join(lines)

        try:
            content_widget = self.query_one("#tool-calls-content", Static)
            content_widget.update(content)
        except Exception:
            pass


class AISummitApp(App):
    """AI Summit 2025 CLI - Textual TUI Application."""

    TITLE = "🚀 AI Summit 2025 CLI"
    SUB_TITLE = "LLM-powered assistant"

    CSS = """
    /* Header customization */
    Header {
        dock: top;
        height: 3;
        background: $primary-darken-1;
    }

    /* Header text styling for better readability */
    Header .header--title {
        color: white;
        text-style: bold;
    }

    Header .header--subtitle {
        color: $text-muted;
        text-style: italic;
    }

    /* Footer */
    Footer {
        dock: bottom;
    }

    /* Main layout */
    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    /* Chat panel (left) */
    #chat-panel {
        width: 2fr;
        height: 1fr;
        border: solid $primary;
        padding: 0;
    }

    #chat-view {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }

    #input-container {
        height: auto;
        dock: bottom;
        background: $surface;
        padding: 1;
        border-top: solid $primary;
    }

    Input {
        width: 1fr;
    }

    /* Message styles */
    .message-user {
        margin: 1 0;
        padding: 1;
        background: $boost;
        border-left: thick $accent;
    }

    .message-assistant {
        margin: 1 0;
        padding: 1;
        background: $panel;
        border-left: thick $success;
    }

    .message-content {
        padding: 0;
    }

    /* Side panels container (right) */
    #side-panels {
        layout: vertical;
        width: 1fr;
        height: 1fr;
    }

    #info-panel {
        height: auto;
        max-height: 12;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
        margin-bottom: 1;
    }

    #tool-calls-panel {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
    }

    .panel-section {
        margin-bottom: 1;
    }

    .feature-item {
        padding-left: 2;
        color: $text-muted;
    }

    /* Loading indicator */
    .loading {
        padding: 1;
        text-align: center;
        color: $warning;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=True),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark", show=False),
    ]

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", **kwargs) -> None:
        """Initialize the TUI app.

        Args:
            model: The LLM model to use
            **kwargs: Additional app arguments
        """
        super().__init__(**kwargs)
        self.model = model
        self.is_processing = False
        self.message_history: list = []  # Store conversation history

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()

        with Container(id="main-container"):
            # Left: Chat panel
            with Container(id="chat-panel"):
                with VerticalScroll(id="chat-view"):
                    yield ChatMessage(
                        "👋 Welcome to AI Summit 2025 CLI!\n\n"
                        "Ask me anything about code, git, or software development.",
                        role="assistant",
                    )
                with Container(id="input-container"):
                    yield Input(placeholder="Type your question here...", id="user-input")

            # Right: Side panels container
            with Container(id="side-panels"):
                yield InfoPanel(id="info-panel")
                yield ToolCallsPanel(id="tool-calls-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Focus the input field
        self.query_one("#user-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission.

        Args:
            event: The input submission event
        """
        log("Input submitted event triggered")

        if self.is_processing:
            log("Already processing, ignoring input")
            return

        user_input = event.value.strip()
        if not user_input:
            log("Empty input, ignoring")
            return

        log(f"Processing user input: {user_input}")

        # Clear input
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""

        # Get chat view
        chat_view = self.query_one("#chat-view", VerticalScroll)

        # Add user message
        await chat_view.mount(ChatMessage(user_input, role="user"))
        chat_view.scroll_end(animate=False)
        log("User message added to chat")

        # Add loading indicator
        loading = Static("🤔 Thinking...", classes="loading")
        await chat_view.mount(loading)
        chat_view.scroll_end(animate=False)
        log("Loading indicator added")

        # Process query with streaming
        self.is_processing = True

        # Remove loading indicator and create response message widget
        loading.remove()
        log("Loading indicator removed")

        # Create a message widget for streaming response
        response_message = ChatMessage("", role="assistant")
        await chat_view.mount(response_message)
        chat_view.scroll_end(animate=False)
        log("Response message widget created")

        # Accumulate the full response
        full_response = ""

        try:
            log(f"Starting stream with history length: {len(self.message_history)}")

            # Create agent
            agent = create_agent(self.model)
            log("Agent created")

            # Create agent dependencies
            from pathlib import Path
            from aisummit_cli.agent import AgentDeps
            deps = AgentDeps(workspace_root=Path.cwd())
            log("Agent deps created")

            # Use run_stream_events() to properly handle tool execution
            log("Starting run_stream_events() iteration")

            chunk_count = 0
            event_count = 0
            final_result = None
            tools_called = False  # Track if tools were called
            final_response_started = False  # Track if we've received final response text

            # Get tool calls panel for status updates
            tool_calls_panel = self.query_one("#tool-calls-panel", ToolCallsPanel)
            tool_calls_panel.start_new_query()  # Mark new query (separator added on first tool call)

            try:
                from pydantic_ai import (
                    AgentRunResultEvent,
                    PartDeltaEvent,
                    PartStartEvent,
                    PartEndEvent,
                    FunctionToolCallEvent,
                    FunctionToolResultEvent,
                    TextPartDelta,
                    TextPart,
                )

                # Stream all events including tool calls
                async for event in agent.run_stream_events(user_input, deps=deps, message_history=self.message_history):
                    event_count += 1
                    event_type = type(event).__name__

                    if isinstance(event, PartStartEvent):
                        # Part is starting - capture beginning text
                        if isinstance(event.part, TextPart):
                            log(f"📝 Text part starting: {event.part.content[:50]}...")

                            # Mark that we've started streaming
                            if not final_response_started:
                                final_response_started = True
                                log(f"🎯 Starting response with part start")

                            # Add the start text
                            full_response += event.part.content

                            # Update UI with the start text
                            try:
                                content_widget = response_message.query_one(".message-content", Static)
                                content_widget.update(Markdown(full_response))
                                chat_view.scroll_end(animate=False)
                            except Exception as ui_error:
                                log.error(f"UI update error: {ui_error}")

                    elif isinstance(event, PartDeltaEvent):
                        # Text delta from the LLM - stream it immediately
                        if isinstance(event.delta, TextPartDelta):
                            chunk_count += 1

                            # Mark that we've started streaming
                            if not final_response_started:
                                final_response_started = True
                                log(f"🎯 Starting response stream")

                            # Accumulate the response
                            full_response += event.delta.content_delta

                            if chunk_count % 5 == 0:
                                log(f"Text delta {chunk_count}: +{len(event.delta.content_delta)} chars")

                            # Update UI - stream token by token
                            try:
                                content_widget = response_message.query_one(".message-content", Static)
                                content_widget.update(Markdown(full_response))
                                chat_view.scroll_end(animate=False)
                            except Exception as ui_error:
                                log.error(f"UI update error: {ui_error}")

                    elif isinstance(event, PartEndEvent):
                        # Part ended - add spacing if transitioning to non-text part
                        if isinstance(event.part, TextPart):
                            log(f"📝 Text part ended, next_part_kind: {event.next_part_kind}")

                            # Add spacing when transitioning from text to non-text (tool-call, thinking, etc.)
                            if event.next_part_kind and event.next_part_kind != 'text':
                                full_response += "\n\n"

                                # Update UI with separator
                                try:
                                    content_widget = response_message.query_one(".message-content", Static)
                                    content_widget.update(Markdown(full_response))
                                    chat_view.scroll_end(animate=False)
                                except Exception as ui_error:
                                    log.error(f"UI update error: {ui_error}")

                    elif isinstance(event, FunctionToolCallEvent):
                        # Tool is being called - show indicator
                        if not tools_called:
                            tools_called = True
                            log(f"🔧 First tool call - showing tool execution")

                        log(f"🔧 Tool call: {event.part.tool_name} with args={event.part.args}")

                        # Add to tool calls panel with arguments
                        tool_calls_panel.add_tool_call(
                            event.part.tool_name,
                            event.part.tool_call_id,
                            event.part.args
                        )

                    elif isinstance(event, FunctionToolResultEvent):
                        # Tool returned a result
                        log(f"✓ Tool result: {str(event.result.content)[:100]}...")

                        # Mark tool as completed in panel
                        tool_calls_panel.complete_tool_call(event.result.tool_call_id)

                        # If this was a checkout_branch call, refresh the Info panel branch
                        # Find the tool call to check its name
                        for tool_call in tool_calls_panel.tool_calls:
                            if tool_call.get("id") == event.result.tool_call_id:
                                if tool_call.get("name") == "checkout_branch":
                                    info_panel = self.query_one("#info-panel", InfoPanel)
                                    info_panel.refresh_branch()
                                    log("🔄 Refreshed branch display after checkout")
                                break

                    elif isinstance(event, AgentRunResultEvent):
                        # Final result contains the complete response after tool execution
                        log(f"📝 Final result received for history")
                        final_result = event.result

                        # Only use final result if we didn't stream the final response
                        # (fallback for queries without text delta streaming)
                        if not final_response_started:
                            full_response = event.result.output
                            log(f"📝 Using final result output (no text deltas streamed, length: {len(full_response)})")

                            # Update UI with final complete response
                            try:
                                content_widget = response_message.query_one(".message-content", Static)
                                content_widget.update(Markdown(full_response))
                                chat_view.scroll_end(animate=False)
                            except Exception as ui_error:
                                log.error(f"UI update error: {ui_error}")
                        else:
                            log(f"📝 Keeping streamed response (length: {len(full_response)}, started streaming: {final_response_started})")

                log(f"✓ Stream finished: {event_count} events, {chunk_count} text deltas")

            except StopAsyncIteration:
                log(f"Stream ended with StopAsyncIteration")
            except Exception as stream_error:
                log.error(f"❌ Stream error: {stream_error}")
                log.error(traceback.format_exc())
                raise

            # Update message history from final result
            if final_result:
                self.message_history = final_result.all_messages()
                log(f"Message history updated, new length: {len(self.message_history)}")

        except Exception as e:
            # Log full traceback
            log.error(f"Error during streaming: {e}")
            log.error(traceback.format_exc())

            # Show error in the response message
            error_msg = f"❌ Error: {str(e)}\n\nCheck the console for details."
            try:
                content_widget = response_message.query_one(".message-content", Static)
                content_widget.update(error_msg)
            except Exception as widget_error:
                log.error(f"Failed to update error message: {widget_error}")
            chat_view.scroll_end(animate=False)

        finally:
            self.is_processing = False
            input_widget.focus()
            log("Input processing completed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_clear_chat(self) -> None:
        """Clear the chat history."""
        chat_view = self.query_one("#chat-view", VerticalScroll)
        # Remove all messages except the welcome message
        for message in chat_view.query(ChatMessage):
            if message != chat_view.query(ChatMessage).first():
                message.remove()

        # Clear message history to start fresh conversation
        self.message_history = []

        # Clear tool calls panel
        tool_calls_panel = self.query_one("#tool-calls-panel", ToolCallsPanel)
        tool_calls_panel.clear_tool_calls()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def run_tui(model: str = "claude-sonnet-4-5-20250929") -> None:
    """Run the Textual TUI application.

    Args:
        model: The LLM model to use
    """
    app = AISummitApp(model=model)
    app.run()
