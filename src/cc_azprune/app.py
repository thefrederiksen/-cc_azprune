"""Main application window for cc_azprune."""

import subprocess
import threading
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from .logging_config import setup_logging, get_logger
from .scanner import AzureScanner
from .portal_links import open_in_portal
from .exporter import export_to_excel, export_to_csv
from .resource_info import get_resource_info, get_safety_display, RISK_LOW, RISK_MEDIUM, RISK_HIGH

# Initialize logging at module load
log = get_logger("app")


class AuthErrorDialog(ctk.CTkToplevel):
    """Custom dialog for authentication errors with helpful instructions."""

    AZURE_CLI_URL = "https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows"

    def __init__(self, parent, error_message: str):
        super().__init__(parent)

        self.title("Azure Authentication Required")
        self.geometry("550x480")
        self.resizable(False, False)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Check if Azure CLI is installed
        self.cli_installed = self._check_azure_cli()

        self._create_ui(error_message)

        # Focus this window
        self.focus_force()
        self.lift()

    def _check_azure_cli(self) -> bool:
        """Check if Azure CLI is installed."""
        try:
            result = subprocess.run(
                ["az", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _create_ui(self, error_message: str):
        """Create the dialog UI."""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # Header
        header = ctk.CTkLabel(
            container,
            text="Azure Authentication Required",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        header.pack(pady=(0, 15))

        # Status indicator
        if self.cli_installed:
            status_text = "[OK] Azure CLI is installed"
            status_color = "#4A7C4E"
        else:
            status_text = "[X] Azure CLI is NOT installed"
            status_color = "#C75050"

        status_label = ctk.CTkLabel(
            container,
            text=status_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=status_color,
        )
        status_label.pack(pady=(0, 15))

        # Instructions frame
        instructions_frame = ctk.CTkFrame(container)
        instructions_frame.pack(fill="x", pady=10)

        if not self.cli_installed:
            # Azure CLI not installed - show installation instructions
            step1_title = ctk.CTkLabel(
                instructions_frame,
                text="Step 1: Install Azure CLI",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            )
            step1_title.pack(fill="x", padx=15, pady=(15, 5))

            step1_desc = ctk.CTkLabel(
                instructions_frame,
                text="Azure CLI is a free command-line tool from Microsoft.\nNo administrator rights required for per-user install.",
                font=ctk.CTkFont(size=12),
                anchor="w",
                justify="left",
            )
            step1_desc.pack(fill="x", padx=15, pady=(0, 10))

            download_btn = ctk.CTkButton(
                instructions_frame,
                text="Download Azure CLI",
                width=200,
                height=32,
                fg_color="#0078D4",
                hover_color="#106EBE",
                command=self._open_download_page,
            )
            download_btn.pack(pady=(0, 15))

            step2_title = ctk.CTkLabel(
                instructions_frame,
                text="Step 2: Login to Azure",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            )
            step2_title.pack(fill="x", padx=15, pady=(10, 5))
        else:
            # Azure CLI installed - show login instructions
            step_title = ctk.CTkLabel(
                instructions_frame,
                text="Login to Azure",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            )
            step_title.pack(fill="x", padx=15, pady=(15, 5))

        login_desc = ctk.CTkLabel(
            instructions_frame,
            text="Open a command prompt or PowerShell and run:",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        login_desc.pack(fill="x", padx=15, pady=(0, 5))

        # Command box
        cmd_frame = ctk.CTkFrame(instructions_frame, fg_color="#1E1E1E")
        cmd_frame.pack(fill="x", padx=15, pady=5)

        cmd_label = ctk.CTkLabel(
            cmd_frame,
            text="az login",
            font=ctk.CTkFont(size=16, family="Consolas"),
            text_color="#4EC9B0",
        )
        cmd_label.pack(pady=12)

        login_note = ctk.CTkLabel(
            instructions_frame,
            text="This will open your browser to sign in with your Azure account.\nNo administrator rights are required.",
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
            text_color="#AAAAAA",
        )
        login_note.pack(fill="x", padx=15, pady=(5, 15))

        # Final step
        final_title = ctk.CTkLabel(
            instructions_frame,
            text="Then restart this application",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        final_title.pack(fill="x", padx=15, pady=(10, 15))

        # Error details (collapsible)
        if error_message:
            details_btn = ctk.CTkButton(
                container,
                text="Show Error Details",
                width=150,
                height=28,
                fg_color="transparent",
                border_width=1,
                text_color="#AAAAAA",
                hover_color="#333333",
                command=lambda: self._toggle_details(details_frame, details_btn),
            )
            details_btn.pack(pady=(10, 5))

            details_frame = ctk.CTkFrame(container, fg_color="#1E1E1E")
            details_label = ctk.CTkLabel(
                details_frame,
                text=error_message[:500],
                font=ctk.CTkFont(size=11),
                text_color="#CC7777",
                wraplength=480,
                justify="left",
            )
            details_label.pack(padx=10, pady=10)
            # Hidden by default
            details_frame.pack_forget()
            self._details_visible = False
            self._details_frame = details_frame
            self._details_btn = details_btn

        # Close button
        close_btn = ctk.CTkButton(
            container,
            text="Close",
            width=100,
            height=36,
            command=self.destroy,
        )
        close_btn.pack(pady=(20, 0))

    def _toggle_details(self, frame, btn):
        """Toggle error details visibility."""
        if self._details_visible:
            frame.pack_forget()
            btn.configure(text="Show Error Details")
            self._details_visible = False
        else:
            frame.pack(fill="x", pady=5)
            btn.configure(text="Hide Error Details")
            self._details_visible = True

    def _open_download_page(self):
        """Open Azure CLI download page."""
        webbrowser.open(self.AZURE_CLI_URL)


class ActivityLog(ctk.CTkFrame):
    """Activity log panel showing real-time operations."""

    def __init__(self, master, height: int = 150, **kwargs):
        kwargs['height'] = height
        super().__init__(master, **kwargs)
        self.pack_propagate(False)

        # Header row with label
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=25)
        header_frame.pack(fill="x", padx=10, pady=(5, 0))
        header_frame.pack_propagate(False)

        header = ctk.CTkLabel(
            header_frame,
            text="Activity Log",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        header.pack(side="left")

        # Log text area
        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=10, family="Consolas"),
            fg_color="#1A1A1A",
            text_color="#AAAAAA",
            wrap="none",
            height=height - 35,
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.log_text.configure(state="disabled")

    def log(self, message: str, level: str = "INFO"):
        """Add a message to the activity log.

        Args:
            message: The message to log
            level: Log level (INFO, OK, ERROR, WARN)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding
        if level == "OK":
            prefix = "[OK]"
        elif level == "ERROR":
            prefix = "[ERROR]"
        elif level == "WARN":
            prefix = "[!]"
        else:
            prefix = "[>]"

        formatted = f"{timestamp} {prefix} {message}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear(self):
        """Clear the activity log."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


class ResourceInfoPanel(ctk.CTkFrame):
    """Panel showing detailed information about a selected resource."""

    def __init__(self, master, height: int = 170, **kwargs):
        kwargs['height'] = height
        super().__init__(master, **kwargs)
        self.pack_propagate(False)

        # Header
        self.header_label = ctk.CTkLabel(
            self,
            text="Select a resource to see details",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.header_label.pack(fill="x", padx=15, pady=(10, 5))

        # Content area with scrollable textbox
        self.content = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=11),
            fg_color="#1E1E1E",
            text_color="#CCCCCC",
            wrap="word",
            height=height - 50,
        )
        self.content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.content.configure(state="disabled")

    def show_resource(self, resource: dict[str, Any]):
        """Display information about a resource."""
        if not resource:
            self._clear()
            return

        resource_type = resource.get("type", "")
        info = get_resource_info(resource_type)
        risk_level = resource.get("risk_level", "medium")

        # Build header with risk indicator
        risk_text, _ = get_safety_display(risk_level)
        name = resource.get("name", "Unknown")
        friendly_name = info.get("friendly_name", resource.get("type_display", "Resource"))
        header = f"{risk_text} {name} ({friendly_name})"
        self.header_label.configure(text=header)

        # Build content
        lines = []

        # What is this?
        lines.append("WHAT IS THIS?")
        lines.append(f"  {info.get('description', 'Azure resource.')}")
        lines.append("")

        # Why is it orphaned?
        lines.append("WHY ORPHANED?")
        lines.append(f"  {info.get('why_orphaned', 'Detected as potentially unused.')}")
        lines.append("")

        # Safe to delete?
        lines.append("SAFE TO DELETE?")
        safe_text = info.get("safe_to_delete", "Verify before deleting.")
        lines.append(f"  {safe_text}")
        lines.append("")

        # What to check before deleting
        check_text = info.get("check_before_delete", "Review resource details.")
        lines.append("BEFORE DELETING:")
        for line in check_text.split("\n"):
            lines.append(f"  {line}")
        lines.append("")

        # Deletion impact
        lines.append("DELETION IMPACT:")
        lines.append(f"  {info.get('deletion_impact', 'Unknown - verify with Azure documentation.')}")
        lines.append("")

        # Recovery info
        lines.append("RECOVERY:")
        lines.append(f"  {info.get('recovery_info', 'Varies by resource type.')}")

        # Update content
        self.content.configure(state="normal")
        self.content.delete("1.0", "end")
        self.content.insert("1.0", "\n".join(lines))
        self.content.configure(state="disabled")

    def _clear(self):
        """Clear the panel."""
        self.header_label.configure(text="Select a resource to see details")
        self.content.configure(state="normal")
        self.content.delete("1.0", "end")
        self.content.configure(state="disabled")


class ResourceGrid(ctk.CTkScrollableFrame):
    """Scrollable grid displaying orphaned resources."""

    COLUMNS = [
        ("Name", 200),
        ("Type", 100),
        ("Safety", 70),
        ("Resource Group", 130),
        ("Location", 85),
        ("Cost/Mo", 65),
        ("Details", 220),
        ("Open", 50),
        ("Copy", 50),
    ]

    def __init__(self, master, tenant_id_getter, on_select=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tenant_id_getter = tenant_id_getter
        self.on_select = on_select  # Callback when a row is selected
        self.resources: list[dict[str, Any]] = []
        self.filtered_resources: list[dict[str, Any]] = []
        self.sort_column: str | None = None
        self.sort_reverse: bool = False
        self.row_widgets: list[list[ctk.CTkLabel | ctk.CTkButton]] = []
        self.header_widgets: list[ctk.CTkButton | ctk.CTkLabel] = []
        self.selected_row: int | None = None
        self.selected_resource: dict[str, Any] | None = None
        self.risk_filter: str | None = None  # None = All, or "low", "medium", "high"

        self._create_headers()

    def _create_headers(self):
        """Create column headers with sort functionality."""
        col = 0
        for name, width in self.COLUMNS:
            # Button columns get empty headers
            if name in ("Open", "Copy"):
                lbl = ctk.CTkLabel(self, text="", width=width, height=30)
                lbl.grid(row=0, column=col, padx=2, pady=(5, 8))
                self.header_widgets.append(lbl)
            else:
                btn = ctk.CTkButton(
                    self,
                    text=name,
                    width=width,
                    height=30,
                    fg_color="#2B5B84",
                    hover_color="#1E4A6E",
                    command=lambda n=name: self._on_header_click(n),
                )
                btn.grid(row=0, column=col, padx=2, pady=(5, 8))
                self.header_widgets.append(btn)
            col += 1

    def _on_header_click(self, column_name: str):
        """Handle header click for sorting."""
        key_map = {
            "Name": "name",
            "Type": "type_display",
            "Safety": "risk_level",
            "Resource Group": "resource_group",
            "Location": "location",
            "Cost/Mo": "cost",
            "Details": "details",
        }
        key = key_map.get(column_name)
        if not key:
            return

        if self.sort_column == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = key
            self.sort_reverse = False

        self._sort_and_display()

    def _sort_and_display(self):
        """Sort filtered resources and redisplay."""
        if self.sort_column:
            self.filtered_resources.sort(
                key=lambda x: x.get(self.sort_column, ""),
                reverse=self.sort_reverse,
            )
        self._display_resources()

    def set_resources(self, resources: list[dict[str, Any]]):
        """Set the full list of resources."""
        self.resources = resources
        self.filtered_resources = resources.copy()
        self.sort_column = None
        self.sort_reverse = False
        self._display_resources()

    def add_resources(self, new_resources: list[dict[str, Any]]):
        """Add resources to the existing list (for streaming)."""
        self.resources.extend(new_resources)
        self.filtered_resources = self.resources.copy()
        if self.sort_column:
            self._sort_and_display()
        else:
            self._display_resources()

    def filter(self, search_text: str):
        """Filter resources by search text."""
        self._search_text = search_text
        self._apply_all_filters()

    def _apply_all_filters(self):
        """Apply all active filters (search + risk)."""
        filtered = self.resources.copy()

        # Apply risk filter
        if self.risk_filter:
            filtered = [r for r in filtered if r.get("risk_level") == self.risk_filter]

        # Apply search filter
        search_text = getattr(self, "_search_text", "")
        if search_text:
            search_lower = search_text.lower()
            filtered = [
                r for r in filtered
                if search_lower in r.get("name", "").lower()
                or search_lower in r.get("type_display", "").lower()
                or search_lower in r.get("resource_group", "").lower()
                or search_lower in r.get("location", "").lower()
            ]

        self.filtered_resources = filtered
        self._sort_and_display()

    def clear(self):
        """Clear all resources."""
        self.resources = []
        self.filtered_resources = []
        self._clear_rows()

    def _clear_rows(self):
        """Remove all row widgets."""
        for row in self.row_widgets:
            for widget in row:
                widget.destroy()
        self.row_widgets.clear()

    def _display_resources(self):
        """Display filtered resources in grid."""
        self._clear_rows()
        self.selected_row = None
        self.selected_resource = None

        for row_idx, resource in enumerate(self.filtered_resources):
            row_widgets = []
            col = 0

            # Alternate row colors
            bg_color = "#2B2B2B" if row_idx % 2 == 0 else "#333333"

            for name, width in self.COLUMNS:
                if name == "Name":
                    text = resource.get("name", "")
                elif name == "Type":
                    text = resource.get("type_display", "")
                elif name == "Safety":
                    # Special handling for Safety column with color
                    risk_level = resource.get("risk_level", "medium")
                    safety_text, safety_color = get_safety_display(risk_level)
                    lbl = ctk.CTkLabel(
                        self,
                        text=safety_text,
                        width=width,
                        height=24,
                        anchor="center",
                        fg_color=safety_color,
                        text_color="white",
                        corner_radius=4,
                        font=ctk.CTkFont(size=11, weight="bold"),
                    )
                    lbl.grid(row=row_idx + 1, column=col, padx=2, pady=1)
                    lbl.bind("<Button-1>", lambda e, idx=row_idx, r=resource: self._on_row_click(idx, r))
                    row_widgets.append(lbl)
                    col += 1
                    continue
                elif name == "Resource Group":
                    text = resource.get("resource_group", "")
                elif name == "Location":
                    text = resource.get("location", "")
                elif name == "Cost/Mo":
                    text = resource.get("cost_display", "$0")
                elif name == "Details":
                    text = resource.get("details", "")
                elif name == "Open":
                    # Open button
                    btn = ctk.CTkButton(
                        self,
                        text="Open",
                        width=width,
                        height=24,
                        fg_color="#4A7C4E",
                        hover_color="#3A6C3E",
                        command=lambda r=resource: self._open_resource(r),
                    )
                    btn.grid(row=row_idx + 1, column=col, padx=1, pady=1)
                    row_widgets.append(btn)
                    col += 1
                    continue
                elif name == "Copy":
                    # Copy URL button
                    btn = ctk.CTkButton(
                        self,
                        text="Copy",
                        width=width,
                        height=24,
                        fg_color="#555555",
                        hover_color="#666666",
                        command=lambda r=resource: self._copy_url(r),
                    )
                    btn.grid(row=row_idx + 1, column=col, padx=1, pady=1)
                    row_widgets.append(btn)
                    col += 1
                    continue
                else:
                    text = ""

                lbl = ctk.CTkLabel(
                    self,
                    text=text,
                    width=width,
                    height=24,
                    anchor="w",
                    fg_color=bg_color,
                    corner_radius=4,
                )
                lbl.grid(row=row_idx + 1, column=col, padx=2, pady=1, sticky="w")
                # Make row clickable
                lbl.bind("<Button-1>", lambda e, idx=row_idx, r=resource: self._on_row_click(idx, r))
                row_widgets.append(lbl)
                col += 1

            self.row_widgets.append(row_widgets)

    def _on_row_click(self, row_idx: int, resource: dict[str, Any]):
        """Handle row click for selection."""
        # Deselect previous row
        if self.selected_row is not None and self.selected_row < len(self.row_widgets):
            old_bg = "#2B2B2B" if self.selected_row % 2 == 0 else "#333333"
            for widget in self.row_widgets[self.selected_row]:
                if isinstance(widget, ctk.CTkLabel) and "[" not in (widget.cget("text") or ""):
                    # Skip safety labels (they have their own colors)
                    widget.configure(fg_color=old_bg)

        # Select new row
        self.selected_row = row_idx
        self.selected_resource = resource

        # Highlight selected row
        for widget in self.row_widgets[row_idx]:
            if isinstance(widget, ctk.CTkLabel):
                # Check if it's the safety column by looking at the text
                widget_text = widget.cget("text") or ""
                if widget_text not in ("[OK]", "[CHECK]", "[WARN]"):
                    widget.configure(fg_color="#3B4B5B")  # Selection highlight color

        # Trigger callback
        if self.on_select:
            self.on_select(resource)

    def filter_by_risk(self, risk_level: str | None):
        """Filter resources by risk level.

        Args:
            risk_level: None for all, or "low", "medium", "high"
        """
        self.risk_filter = risk_level
        self._apply_all_filters()

    def _open_resource(self, resource: dict[str, Any]):
        """Open resource in Azure Portal."""
        tenant_id = self.tenant_id_getter()
        resource_id = resource.get("id", "")
        if tenant_id and resource_id:
            open_in_portal(resource_id, tenant_id)

    def _copy_url(self, resource: dict[str, Any]):
        """Copy Azure Portal URL to clipboard."""
        tenant_id = self.tenant_id_getter()
        resource_id = resource.get("id", "")
        if tenant_id and resource_id:
            from .portal_links import get_portal_url
            url = get_portal_url(resource_id, tenant_id)
            self.clipboard_clear()
            self.clipboard_append(url)
            # Brief visual feedback would be nice but clipboard_append is enough

    def get_total_cost(self) -> float:
        """Get total estimated monthly cost."""
        return sum(r.get("cost", 0) for r in self.filtered_resources)

    def get_filtered_resources(self) -> list[dict[str, Any]]:
        """Get currently filtered resources."""
        return self.filtered_resources


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        log.info("Initializing application window")

        self.title("cc_azprune - Azure Orphaned Resource Finder")
        self.geometry("1100x650")
        self.minsize(900, 550)

        # Set dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.scanner = AzureScanner()
        self.resources: list[dict[str, Any]] = []
        self._scan_cancelled = False
        self._is_scanning = False
        self._subscriptions: list[dict[str, str]] = []

        self._create_ui()

        # Start maximized on Windows (must be after UI is created)
        self.after(100, lambda: self.state("zoomed"))

        self._start_auth()

    def _create_ui(self):
        """Create the main UI layout."""
        # === Header ===
        self.header_frame = ctk.CTkFrame(self, height=50)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.header_frame.pack_propagate(False)

        # Subscription label
        sub_text_label = ctk.CTkLabel(
            self.header_frame,
            text="Subscription:",
            font=ctk.CTkFont(size=12),
        )
        sub_text_label.pack(side="left", padx=(15, 5), pady=10)

        # Subscription dropdown
        self.sub_dropdown = ctk.CTkComboBox(
            self.header_frame,
            values=["Connecting..."],
            width=300,
            state="disabled",
            command=self._on_subscription_change,
        )
        self.sub_dropdown.pack(side="left", padx=5, pady=10)

        # Cancel/Rescan button (hidden initially)
        self.action_btn = ctk.CTkButton(
            self.header_frame,
            text="Cancel",
            width=100,
            height=32,
            fg_color="#8B4444",
            hover_color="#6B3333",
            command=self._on_action_btn,
        )
        # Don't pack yet - will show during scan

        # Search box
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Search...",
            width=150,
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="right", padx=10, pady=10)

        search_label = ctk.CTkLabel(self.header_frame, text="Search:")
        search_label.pack(side="right", pady=10)

        # Risk filter dropdown
        self.risk_filter_var = ctk.StringVar(value="All Resources")
        self.risk_filter_dropdown = ctk.CTkComboBox(
            self.header_frame,
            values=["All Resources", "Safe to Delete (Low)", "Needs Review (Medium)", "High Risk Only"],
            width=180,
            variable=self.risk_filter_var,
            command=self._on_risk_filter_change,
            state="readonly",
        )
        self.risk_filter_dropdown.pack(side="right", padx=5, pady=10)

        filter_label = ctk.CTkLabel(self.header_frame, text="Filter:")
        filter_label.pack(side="right", padx=(10, 5), pady=10)

        # === Main grid panel (takes most space) ===
        self.grid_panel = ctk.CTkFrame(self)
        self.grid_panel.pack(fill="both", expand=True, padx=10, pady=5)

        # Resource grid with horizontal scroll
        self.grid = ResourceGrid(
            self.grid_panel,
            tenant_id_getter=lambda: self.scanner.tenant_id,
            on_select=self._on_resource_select,
        )
        self.grid.pack(fill="both", expand=True, padx=5, pady=5)

        # === Resource Info Panel ===
        self.info_panel = ResourceInfoPanel(self, height=170)
        self.info_panel.pack(fill="x", padx=10, pady=5)

        # === Footer with totals ===
        self.footer_frame = ctk.CTkFrame(self, height=45)
        self.footer_frame.pack(fill="x", padx=10, pady=5)
        self.footer_frame.pack_propagate(False)

        # Totals
        self.count_label = ctk.CTkLabel(
            self.footer_frame,
            text="Orphaned: 0",
            font=ctk.CTkFont(size=12),
        )
        self.count_label.pack(side="left", padx=10, pady=10)

        self.cost_label = ctk.CTkLabel(
            self.footer_frame,
            text="Est. Savings: $0.00/mo",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.cost_label.pack(side="left", padx=10, pady=10)

        # Export button
        self.export_btn = ctk.CTkButton(
            self.footer_frame,
            text="Export to Excel",
            width=120,
            height=30,
            command=self._on_export,
            state="disabled",
        )
        self.export_btn.pack(side="right", padx=10, pady=10)

        # === Activity Log at bottom ===
        self.activity_log = ActivityLog(self, height=150)
        self.activity_log.pack(fill="x", padx=10, pady=(0, 10))

    def _log(self, message: str, level: str = "INFO"):
        """Log to both activity panel and file."""
        self.activity_log.log(message, level)
        if level == "ERROR":
            log.error(message)
        elif level == "WARN":
            log.warning(message)
        else:
            log.info(message)

    def _start_auth(self):
        """Start authentication process."""
        self._log("Starting Azure authentication...")

        def auth():
            try:
                self._log("Finding Azure CLI installation...")
                self.scanner.authenticate()
                self.after(0, self._auth_success)
            except Exception as e:
                self.after(0, lambda: self._auth_error(str(e)))

        thread = threading.Thread(target=auth, daemon=True)
        thread.start()

    def _auth_success(self):
        """Handle successful authentication - auto-start scan."""
        self._log(f"Connected to: {self.scanner.subscription_name}", "OK")
        self._log(f"Tenant: {self.scanner.tenant_id[:8]}...")

        # Load available subscriptions
        self._log("Loading available subscriptions...")
        self._subscriptions = self.scanner.list_subscriptions()

        if self._subscriptions:
            # Populate dropdown with subscription names
            sub_names = [s["name"] for s in self._subscriptions]
            self.sub_dropdown.configure(values=sub_names, state="readonly")

            # Set current subscription as selected
            current_name = self.scanner.subscription_name
            if current_name in sub_names:
                self.sub_dropdown.set(current_name)
            else:
                self.sub_dropdown.set(sub_names[0])

            self._log(f"Found {len(self._subscriptions)} subscriptions", "OK")
        else:
            self.sub_dropdown.configure(values=[self.scanner.subscription_name or "Unknown"])
            self.sub_dropdown.set(self.scanner.subscription_name or "Unknown")

        # Auto-start scan
        self.after(500, self._start_scan)

    def _on_subscription_change(self, selected_name: str):
        """Handle subscription dropdown change."""
        if self._is_scanning:
            self._log("Cannot change subscription while scanning", "WARN")
            # Reset dropdown to current subscription
            self.sub_dropdown.set(self.scanner.subscription_name or "")
            return

        # Find the selected subscription
        for sub in self._subscriptions:
            if sub["name"] == selected_name:
                if sub["id"] == self.scanner.subscription_id:
                    # Same subscription, no change needed
                    return

                self._log(f"Switching to subscription: {selected_name}")
                self.scanner.set_subscription(sub["id"], sub["name"], sub["tenantId"])
                self._log(f"Subscription changed to: {selected_name}", "OK")

                # Clear grid and start new scan
                self.grid.clear()
                self._update_totals()
                self.export_btn.configure(state="disabled")
                self.after(500, self._start_scan)
                return

        self._log(f"Subscription not found: {selected_name}", "ERROR")

    def _auth_error(self, error: str):
        """Handle authentication error."""
        self._log(f"Authentication failed: {error}", "ERROR")
        self.sub_dropdown.configure(values=["Not connected"])
        self.sub_dropdown.set("Not connected")
        AuthErrorDialog(self, error)

    def _start_scan(self):
        """Start the resource scan."""
        if self._is_scanning:
            return

        self._is_scanning = True
        self._scan_cancelled = False
        self.grid.clear()
        self._update_totals()

        # Show cancel button
        self.action_btn.configure(text="Cancel", fg_color="#8B4444", hover_color="#6B3333")
        self.action_btn.pack(side="left", padx=10, pady=10)

        self.export_btn.configure(state="disabled")

        self._log("Starting comprehensive scan for orphaned resources...")

        def scan():
            try:
                from .detectors import ALL_DETECTORS

                total_found = 0
                for resource_name, detector_func in ALL_DETECTORS:
                    if self._scan_cancelled:
                        return

                    self.after(0, lambda n=resource_name: self._log(f"Scanning {n}..."))

                    try:
                        results = detector_func(self.scanner._query)
                        # Ensure results is a list (handle None)
                        if results is None:
                            results = []
                    except Exception as e:
                        # Log error but continue with other detectors
                        self.after(0, lambda n=resource_name, err=str(e): self._log(
                            f"Error scanning {n}: {err}", "WARN"
                        ))
                        log.warning(f"Detector {resource_name} failed: {e}")
                        continue

                    if self._scan_cancelled:
                        return

                    if results:
                        count = len(results)
                        total_found += count
                        self.after(0, lambda n=resource_name, c=count: self._log(
                            f"Found {c} orphaned {n}", "OK"
                        ))
                        self.after(0, lambda r=results: self._add_results(r))

                self.after(0, self._scan_complete)

            except Exception as e:
                log.error(f"Scan failed: {e}")
                log.debug(traceback.format_exc())
                self.after(0, lambda: self._scan_error(str(e)))

        thread = threading.Thread(target=scan, daemon=True)
        thread.start()

    def _add_results(self, resources: list[dict[str, Any]]):
        """Add resources to the grid (streaming)."""
        self.grid.add_resources(resources)
        self._update_totals()

    def _scan_complete(self):
        """Handle scan completion."""
        self._is_scanning = False
        total = len(self.grid.resources)
        self._log(f"Scan complete. Found {total} orphaned resources.", "OK")

        # Change button to Rescan
        self.action_btn.configure(text="Rescan", fg_color="#2B5B84", hover_color="#1E4A6E")

        if total > 0:
            self.export_btn.configure(state="normal")

            # Auto-save results to CSV in logs directory
            self._auto_save_csv()

    def _auto_save_csv(self):
        """Auto-save scan results to CSV in logs directory."""
        try:
            resources = self.grid.get_filtered_resources()
            if not resources:
                return

            # Save to logs directory alongside the app
            logs_dir = Path(__file__).parent.parent.parent / "logs"

            csv_path = export_to_csv(
                resources=resources,
                output_dir=logs_dir,
                subscription_name=self.scanner.subscription_name or "",
                tenant_id=self.scanner.tenant_id or "",
            )
            self._log(f"Auto-saved to: {csv_path.name}", "OK")
            log.info(f"Auto-saved CSV: {csv_path}")

        except Exception as e:
            self._log(f"Auto-save failed: {e}", "WARN")
            log.error(f"Auto-save CSV failed: {e}")
            log.debug(traceback.format_exc())

    def _scan_error(self, error: str):
        """Handle scan error."""
        self._is_scanning = False
        self._log(f"Scan failed: {error}", "ERROR")
        self.action_btn.configure(text="Retry", fg_color="#2B5B84", hover_color="#1E4A6E")

    def _on_action_btn(self):
        """Handle action button click (Cancel/Rescan/Retry)."""
        if self._is_scanning:
            # Cancel
            self._scan_cancelled = True
            self._log("Scan cancelled by user", "WARN")
            self._is_scanning = False
            self.action_btn.configure(text="Rescan", fg_color="#2B5B84", hover_color="#1E4A6E")
        else:
            # Rescan
            self._start_scan()

    def _on_search(self, *args):
        """Handle search text change."""
        search_text = self.search_var.get()
        self.grid.filter(search_text)
        self._update_totals()

    def _on_risk_filter_change(self, selected: str):
        """Handle risk filter dropdown change."""
        filter_map = {
            "All Resources": None,
            "Safe to Delete (Low)": RISK_LOW,
            "Needs Review (Medium)": RISK_MEDIUM,
            "High Risk Only": RISK_HIGH,
        }
        risk_level = filter_map.get(selected)
        self.grid.filter_by_risk(risk_level)
        self._update_totals()

    def _on_resource_select(self, resource: dict[str, Any]):
        """Handle resource selection in the grid."""
        self.info_panel.show_resource(resource)

    def _update_totals(self):
        """Update total count and cost labels."""
        filtered = self.grid.get_filtered_resources()
        count = len(filtered)
        total_cost = self.grid.get_total_cost()

        self.count_label.configure(text=f"Orphaned: {count}")
        self.cost_label.configure(text=f"Est. Savings: ${total_cost:.2f}/mo")

    def _on_export(self):
        """Handle Export to Excel button click."""
        log.info("Export button clicked")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"azure-orphans-{self._get_date_str()}.xlsx",
        )
        if not filepath:
            log.debug("Export cancelled by user")
            return

        try:
            resources = self.grid.get_filtered_resources()
            self._log(f"Exporting {len(resources)} resources...")
            export_to_excel(resources, filepath, self.scanner.tenant_id or "")
            self._log(f"Exported to {Path(filepath).name}", "OK")
            messagebox.showinfo("Export Complete", f"Exported to:\n{filepath}")
        except Exception as e:
            self._log(f"Export failed: {e}", "ERROR")
            log.debug(traceback.format_exc())
            messagebox.showerror("Export Error", f"Error exporting:\n\n{e}")

    def _get_date_str(self) -> str:
        """Get current date as string."""
        return datetime.now().strftime("%Y-%m-%d")


def main():
    """Main entry point."""
    # Initialize logging first
    setup_logging()
    log.info("Application starting")

    try:
        app = App()
        app.mainloop()
    except Exception as e:
        log.critical(f"Application crashed: {e}")
        log.debug(traceback.format_exc())
        raise
    finally:
        log.info("Application closed")


if __name__ == "__main__":
    main()
