"""
WristComp - A Pip-Boy style smartwatch terminal application.
A compact, retro-digital interface for tracking personal stats and inventory.
"""
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    ProgressBar,
    Static,
)

from data_store import DataStore


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

class BatteryIndicator(Static):
    """Simulated battery level indicator."""
    
    battery_level = reactive(87)
    
    def render(self) -> str:
        bars = int(self.battery_level / 10)
        empty = 10 - bars
        bar_str = "█" * bars + "░" * empty
        return f"[b]BAT[/b] [{bar_str}] {self.battery_level}%"


class ClockDisplay(Static):
    """Real-time clock display."""
    
    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)
    
    def update_clock(self) -> None:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        self.update(f"[b]{time_str}[/b]\n[dim]{date_str}[/dim]")


class StatBar(Static):
    """Compact stat bar with icon, label, and progress."""
    
    def __init__(self, name: str, icon: str, value: int, color: str):
        super().__init__()
        self.stat_name = name
        self.icon = icon
        self.value = value
        self.color = color
    
    def render(self) -> str:
        bar_len = 10
        filled = int(self.value / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        return f"{self.icon} [b]{self.stat_name.upper()[:4]}[/b] [{self.color}]{bar}[/{self.color}] {self.value}%"


class DeviceFrame(Container):
    """Container that gives the wrist device aesthetic."""
    
    DEFAULT_CSS = """
    DeviceFrame {
        border: solid $primary;
        padding: 1;
        height: 100%;
    }
    """


class ScreenTitle(Static):
    """Header showing current screen name."""
    
    def __init__(self, title: str):
        super().__init__(f"[b]◄ {title} ►[/b]")


# ═══════════════════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

class DashboardScreen(Screen):
    """Main dashboard - the home screen of the device."""
    
    BINDINGS = [
        ("1", "switch_screen('stats')", "Stats"),
        ("2", "switch_screen('inventory')", "Inv"),
        ("3", "switch_screen('settings')", "Set"),
        ("q", "app_quit", "Quit"),
    ]
    
    def action_switch_screen(self, screen_name: str) -> None:
        self.app.action_switch_screen(screen_name)

    def action_app_quit(self) -> None:
        self.app.action_quit()

    def on_screen_resume(self) -> None:
        """Refresh when returning to this screen."""
        self.refresh(recompose=True)
    
    def compose(self) -> ComposeResult:
        store = self.app.store  # type: ignore
        stats = store.stats
        
        yield Container(
            # Header row: Title + Clock + Battery
            Horizontal(
                Static("[b]WRISTCOMP[/b] [dim]v1.0[/dim]", classes="header-left"),
                ClockDisplay(classes="clock"),
                BatteryIndicator(classes="battery"),
                classes="top-bar"
            ),
            
            # Main stats display
            Container(
                Static("[b]STATUS MONITOR[/b]", classes="section-title"),
                StatBar("hydration", "💧", stats.get("hydration", 0), "cyan"),
                StatBar("energy", "⚡", stats.get("energy", 0), "yellow"),
                StatBar("urination", "🚻", stats.get("urination", 0), "blue"),
                StatBar("stress", "😰", stats.get("stress", 0), "red"),
                classes="stats-container"
            ),
            
            # Quick inventory preview
            Container(
                Static("[b]INVENTORY[/b]", classes="section-title"),
                *self._inventory_items(store),
                classes="inventory-preview"
            ),
            
            # Navigation hints
            Static("[dim]NAV: [1]Stats [2]Inv [3]Set [Q]Quit[/dim]", classes="nav-hint"),
            
            classes="dashboard"
        )
    
    def _inventory_items(self, store) -> list:
        items = store.inventory[:3]  # Show first 3 items
        if not items:
            return [Static("[dim]No items[/dim]")]
        return [Static(f"• {item['name']} x{item['quantity']}") for item in items]
    
    def on_mount(self) -> None:
        self.set_interval(2, self.refresh_stats)
    
    def refresh_stats(self) -> None:
        """Refresh the stats display."""
        self.refresh(recompose=True)


class StatsScreen(Screen):
    """Detailed stats management screen."""
    
    BINDINGS = [
        ("escape", "switch_screen('dashboard')", "Back"),
        ("1", "switch_screen('dashboard')", "Home"),
        ("2", "switch_screen('inventory')", "Inv"),
        ("3", "switch_screen('settings')", "Set"),
        ("q", "app_quit", "Quit"),
    ]
    
    def action_switch_screen(self, screen_name: str) -> None:
        self.app.action_switch_screen(screen_name)

    def action_app_quit(self) -> None:
        self.app.action_quit()

    def on_screen_resume(self) -> None:
        """Refresh when returning to this screen."""
        self._update_display()
    
    def compose(self) -> ComposeResult:
        store = self.app.store  # type: ignore
        
        yield Container(
            ScreenTitle("STATS"),
            
            Container(
                self._stat_control("hydration", "💧 HYDRATION", store.get_stat("hydration")),
                self._stat_control("energy", "⚡ ENERGY", store.get_stat("energy")),
                self._stat_control("urination", "🚻 URINATION", store.get_stat("urination")),
                self._stat_control("stress", "😰 STRESS", store.get_stat("stress")),
                classes="stat-controls"
            ),
            
            Static("[dim]NAV: [Esc]Back [1]Home [2]Inv [3]Set[/dim]", classes="nav-hint"),
            classes="stats-screen"
        )
    
    def _stat_control(self, stat_id: str, label: str, value: int) -> Container:
        return Container(
            Static(f"[b]{label}[/b]", classes="stat-label"),
            Horizontal(
                Button("-", id=f"{stat_id}_dec", classes="adjust-btn"),
                Static(f"[b]{value}%[/b]", id=f"{stat_id}_val", classes="stat-value"),
                Button("+", id=f"{stat_id}_inc", classes="adjust-btn"),
                classes="stat-row"
            ),
            classes="stat-control"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        store = self.app.store  # type: ignore
        btn_id = event.button.id
        
        if btn_id and "_" in btn_id:
            stat_name, action = btn_id.rsplit("_", 1)
            if action == "inc":
                store.update_stat(stat_name, 5)
            elif action == "dec":
                store.update_stat(stat_name, -5)
            self._update_display()
    
    def _update_display(self) -> None:
        store = self.app.store  # type: ignore
        for stat in ["hydration", "energy", "urination", "stress"]:
            val_widget = self.query_one(f"#{stat}_val", Static)
            val_widget.update(f"[b]{store.get_stat(stat)}%[/b]")


class InventoryScreen(Screen):
    """EDC inventory management screen."""
    
    BINDINGS = [
        ("escape", "switch_screen('dashboard')", "Back"),
        ("1", "switch_screen('dashboard')", "Home"),
        ("2", "switch_screen('stats')", "Stats"),
        ("3", "switch_screen('settings')", "Set"),
        ("a", "add_item", "Add"),
        ("e", "edit_item", "Edit"),
        ("d", "delete_item", "Delete"),
        ("enter", "view_item", "View"),
        ("q", "app_quit", "Quit"),
    ]
    
    def action_switch_screen(self, screen_name: str) -> None:
        self.app.action_switch_screen(screen_name)

    def action_app_quit(self) -> None:
        self.app.action_quit()

    def on_screen_resume(self) -> None:
        """Refresh when returning to this screen."""
        self.refresh_inventory()
    
    def compose(self) -> ComposeResult:
        yield Container(
            ScreenTitle("INVENTORY"),
            
            Container(
                Static("[b]EDC ITEMS[/b]", classes="section-title"),
                ListView(
                    *self._inventory_items(),
                    id="inventory_list"
                ),
                classes="inventory-list"
            ),
            
            Container(
                Static("[b]ACTIONS[/b]", classes="section-title"),
                Horizontal(
                    Button("Add (A)", id="btn_add", variant="primary"),
                    Button("Edit (E)", id="btn_edit", variant="warning"),
                    Button("Delete (D)", id="btn_delete", variant="error"),
                    classes="action-buttons"
                ),
                classes="actions"
            ),
            
            Static("[dim]NAV: [Enter]View [Esc]Back [1]Home [2]Stats [3]Set[/dim]", classes="nav-hint"),
            classes="inventory-screen"
        )
    
    def _inventory_items(self) -> list:
        store = self.app.store  # type: ignore
        items = store.inventory
        if not items:
            return [ListItem(Static("[dim]Empty[/dim]"))]
        return [
            ListItem(Static(f"{item['name']} [{item['category']}] x{item['quantity']}", classes="list-line"))
            for item in items
        ]
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_add":
            self.action_add_item()
        elif btn_id == "btn_edit":
            self.action_edit_item()
        elif btn_id == "btn_delete":
            self.action_delete_item()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_view_item()
    
    def _selected_item_name(self) -> Optional[str]:
        list_view = self.query_one("#inventory_list", ListView)
        store = self.app.store  # type: ignore
        if list_view.index is None:
            return None
        items = store.inventory
        if 0 <= list_view.index < len(items):
            return items[list_view.index]["name"]
        return None
    
    def action_view_item(self) -> None:
        selected = self._selected_item_name()
        if selected:
            self.app.push_screen(ItemDetailScreen(selected))

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.action_switch_screen(screen_name)
    
    def action_add_item(self) -> None:
        self.app.push_screen(ItemEditorModal())
    
    def action_edit_item(self) -> None:
        selected = self._selected_item_name()
        if selected:
            self.app.push_screen(ItemEditorModal(selected))
    
    def action_delete_item(self) -> None:
        selected = self._selected_item_name()
        if selected:
            self.app.push_screen(DeleteItemModal(selected))
    
    def refresh_inventory(self) -> None:
        list_view = self.query_one("#inventory_list", ListView)
        list_view.clear()
        for item in self._inventory_items():
            list_view.append(item)


class ItemDetailScreen(Screen):
    """Shows details for a selected item."""
    
    BINDINGS = [
        ("escape", "switch_screen('inventory')", "Back"),
        ("b", "switch_screen('inventory')", "Back"),
    ]
    
    def action_switch_screen(self, screen_name: str) -> None:
        self.app.action_switch_screen(screen_name)
    
    def __init__(self, item_name: str):
        super().__init__()
        self.item_name = item_name
    
    def compose(self) -> ComposeResult:
        store = self.app.store  # type: ignore
        item = store.get_item(self.item_name)
        
        yield Container(
            ScreenTitle("ITEM DETAILS"),
            
            Container(
                Static(f"[b]NAME[/b]: {item.get('name', '-') if item else '-'}", classes="detail-line"),
                Static(f"[b]CATEGORY[/b]: {item.get('category', '-') if item else '-'}", classes="detail-line"),
                Static(f"[b]QUANTITY[/b]: {item.get('quantity', '-') if item else '-'}", classes="detail-line"),
                Static(f"[b]WEIGHT[/b]: {item.get('weight', '-') if item else '-'} kg", classes="detail-line"),
                classes="detail-panel"
            ),
            
            Static("[dim]NAV: [B]Back [Esc]Back[/dim]", classes="nav-hint"),
            classes="detail-screen"
        )


class ItemEditorModal(Screen):
    """Modal for adding/editing an item."""
    
    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
    ]
    
    def __init__(self, item_name: Optional[str] = None):
        super().__init__()
        self.item_name = item_name
    
    def compose(self) -> ComposeResult:
        store = self.app.store  # type: ignore
        item = store.get_item(self.item_name) if self.item_name else {}
        
        yield Container(
            Static("[b]ITEM EDITOR[/b]", classes="modal-title"),
            Input(value=item.get("name", ""), placeholder="Item name...", id="item_name"),
            Input(value=item.get("category", ""), placeholder="Category (e.g. Essentials)", id="item_category"),
            Input(value=str(item.get("quantity", 1)), placeholder="Quantity", id="item_quantity"),
            Input(value=str(item.get("weight", 0.0)), placeholder="Weight (kg)", id="item_weight"),
            Horizontal(
                Button("Cancel", id="btn_cancel", variant="primary"),
                Button("Save", id="btn_save", variant="success"),
                classes="modal-buttons"
            ),
            classes="modal"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss()
            return
        if event.button.id == "btn_save":
            self._save_item()
    
    def _save_item(self) -> None:
        store = self.app.store  # type: ignore
        name_input = self.query_one("#item_name", Input)
        category_input = self.query_one("#item_category", Input)
        quantity_input = self.query_one("#item_quantity", Input)
        weight_input = self.query_one("#item_weight", Input)
        
        name = name_input.value.strip()
        category = category_input.value.strip() or "Uncategorized"
        try:
            quantity = int(quantity_input.value)
        except ValueError:
            quantity = 1
        try:
            weight = float(weight_input.value)
        except ValueError:
            weight = 0.0
        
        if name:
            if self.item_name:
                store.update_item(self.item_name, name, category, quantity, weight)
            else:
                store.add_item(name, category, quantity, weight)
            self.dismiss()
            inventory_screen = self.app.get_screen("inventory")
            if isinstance(inventory_screen, InventoryScreen):
                inventory_screen.refresh_inventory()


class DeleteItemModal(Screen):
    """Confirm deletion of an item."""
    
    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
    ]
    
    def __init__(self, item_name: str):
        super().__init__()
        self.item_name = item_name
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("[b]DELETE ITEM?[/b]", classes="modal-title"),
            Static(f"Remove [b]{self.item_name}[/b] from inventory?", classes="detail-line"),
            Horizontal(
                Button("Cancel", id="btn_cancel", variant="primary"),
                Button("Delete", id="btn_delete", variant="error"),
                classes="modal-buttons"
            ),
            classes="modal"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss()
        elif event.button.id == "btn_delete":
            store = self.app.store  # type: ignore
            store.remove_item(self.item_name)
            self.dismiss()
            inventory_screen = self.app.get_screen("inventory")
            if isinstance(inventory_screen, InventoryScreen):
                inventory_screen.refresh_inventory()


class SettingsScreen(Screen):
    """Device settings screen."""
    
    BINDINGS = [
        ("escape", "switch_screen('dashboard')", "Back"),
        ("1", "switch_screen('dashboard')", "Home"),
        ("2", "switch_screen('stats')", "Stats"),
        ("3", "switch_screen('inventory')", "Inv"),
        ("q", "app_quit", "Quit"),
    ]
    
    def action_switch_screen(self, screen_name: str) -> None:
        self.app.action_switch_screen(screen_name)

    def action_app_quit(self) -> None:
        self.app.action_quit()
    
    def compose(self) -> ComposeResult:
        store = self.app.store  # type: ignore
        settings = store.settings
        
        yield Container(
            ScreenTitle("SETTINGS"),
            
            Container(
                Static("[b]DEVICE INFO[/b]", classes="section-title"),
                Static(f"Name: {settings.get('device_name', 'WristComp')}"),
                Static(f"Auto-save: {'ON' if settings.get('auto_save') else 'OFF'}"),
                classes="settings-section"
            ),
            
            Container(
                Static("[b]DATA MANAGEMENT[/b]", classes="section-title"),
                Horizontal(
                    Button("Reset Stats", id="btn_reset_stats", variant="warning"),
                    Button("Reset All", id="btn_reset_all", variant="error"),
                    classes="settings-buttons"
                ),
                classes="settings-section"
            ),
            
            Static("[dim]NAV: [Esc]Back [1]Home [2]Stats [3]Inv[/dim]", classes="nav-hint"),
            classes="settings-screen"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        store = self.app.store  # type: ignore
        
        if event.button.id == "btn_reset_stats":
            store.reset_stats()
            self.notify("Stats reset to defaults")
        elif event.button.id == "btn_reset_all":
            store.reset_all()
            self.notify("All data reset to defaults")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class WristDeviceApp(App):
    """Main wrist device application."""
    
    CSS = """
    /* ═══════════════════════════════════════════════════════════════════════
       BASE STYLES - Compact wrist device aesthetic
       ═══════════════════════════════════════════════════════════════════════ */
    
    Screen {
        align: center middle;
    }
    
    /* Main container - simulates device screen */
    .dashboard, .stats-screen, .inventory-screen, .settings-screen, .detail-screen {
        width: 60;
        height: auto;
        max-height: 100%;
        border: solid $primary;
        padding: 1 2;
        background: $surface;
    }
    
    /* Top bar layout */
    .top-bar {
        height: 3;
        margin-bottom: 1;
    }
    
    .header-left {
        width: 40%;
        content-align: left middle;
    }
    
    .clock {
        width: 30%;
        content-align: center middle;
        text-align: center;
    }
    
    .battery {
        width: 30%;
        content-align: right middle;
        color: $success;
    }
    
    /* Section titles */
    .section-title {
        text-style: underline;
        margin-top: 1;
        margin-bottom: 1;
        color: $primary;
    }
    
    /* Stats display */
    .stats-container {
        margin: 1 0;
    }
    
    StatBar {
        height: 1;
        margin: 1 0;
    }
    
    /* Inventory preview */
    .inventory-preview {
        margin: 1 0;
    }
    
    .inventory-preview Static {
        height: 1;
    }
    
    /* Navigation hints */
    .nav-hint {
        margin-top: 1;
        text-align: center;
        color: $text-muted;
    }
    
    /* Stats screen specific */
    .stat-controls {
        margin: 1 0;
    }
    
    .stat-control {
        margin: 1 0;
        height: 3;
    }
    
    .stat-label {
        height: 1;
    }
    
    .stat-row {
        height: 2;
    }
    
    .stat-value {
        width: 6;
        content-align: center middle;
    }
    
    .adjust-btn {
        width: 3;
        min-width: 3;
    }
    
    /* Inventory screen */
    .inventory-list {
        height: 10;
        border: solid $primary-darken-2;
        padding: 0 1;
    }

    .detail-panel {
        margin: 1 0;
        border: solid $primary-darken-2;
        padding: 1;
    }

    .detail-line {
        height: 1;
        margin: 1 0;
    }
    
    ListView {
        height: 100%;
        border: none;
    }
    
    ListItem {
        height: 1;
    }
    
    .actions {
        margin-top: 1;
    }
    
    .action-buttons {
        height: 3;
    }
    
    .action-buttons Button {
        width: 1fr;
    }
    
    /* Settings screen */
    .settings-section {
        margin: 1 0;
    }
    
    .settings-buttons {
        height: 3;
    }
    
    .settings-buttons Button {
        width: 1fr;
    }
    
    /* Modal */
    .modal {
        width: 40;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    
    .modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .modal Input {
        margin: 1 0;
    }
    
    .modal-buttons {
        height: 3;
        margin-top: 1;
    }
    
    .modal-buttons Button {
        width: 1fr;
    }
    
    /* Screen title */
    ScreenTitle {
        text-align: center;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    """
    
    SCREENS = {
        "dashboard": DashboardScreen,
        "stats": StatsScreen,
        "inventory": InventoryScreen,
        "settings": SettingsScreen,
    }
    
    def __init__(self):
        super().__init__()
        self.store = DataStore()
    
    def on_mount(self) -> None:
        self.push_screen("dashboard")

    def action_switch_screen(self, screen_name: str) -> None:
        """Switch between named screens."""
        if screen_name in self.SCREENS:
            self.switch_screen(screen_name)

    def action_quit(self) -> None:
        """Quit the application from any screen."""
        self.exit()


if __name__ == "__main__":
    app = WristDeviceApp()
    app.run()