import json
import os
from time import sleep

from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.InputBases import KeyAction

from evdev import ecodes, UInput
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from loguru import logger as log


log.debug("Init HELLDIVERS 2")


# Default settings
DEFAULT_KEY_DELAY = 0.03
DEFAULT_MODIFIER_KEY = "KEY_LEFTCTRL"
DEFAULT_HOLD_MODIFIER = True  # False = press/release, True = hold during sequence
DEFAULT_SHOW_LABELS = True  # Show text labels on buttons

# Available modifier keys
MODIFIER_KEYS = {
    "Left Ctrl": "KEY_LEFTCTRL",
    "Right Ctrl": "KEY_RIGHTCTRL",
    "Left Alt": "KEY_LEFTALT",
    "Right Alt": "KEY_RIGHTALT",
    "Left Shift": "KEY_LEFTSHIFT",
    "Right Shift": "KEY_RIGHTSHIFT",
}


class StratagemHeroButton(KeyAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        self.show()

    def on_key_down(self, data=None):
        self.plugin_base.hero_mode = not self.plugin_base.hero_mode
        self.show()

    def on_key_up(self, data=None):
        pass

    def on_key_short_up(self, data=None):
        pass

    def show(self):
        if self.plugin_base.get_show_labels():
            self.set_top_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.top", ""))
            self.set_center_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.center", "Stratagem"))
            self.set_bottom_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.bottom", "Hero"))
        else:
            self.set_top_label("")
            self.set_center_label("")
            self.set_bottom_label("")

        fname = "hero_off.png"
        if self.plugin_base.hero_mode:
            fname = "hero_on.png"
        self.set_media(
            media_path=os.path.join(self.plugin_base.PATH, "assets", "icons", fname)
        )


# Direction key mappings for the sequence editor
DIRECTION_KEYS = ["UP", "DOWN", "LEFT", "RIGHT"]
DIRECTION_ARROWS = {"UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→"}


class CustomStratagemButton(KeyAction):
    """
    A custom stratagem button that allows users to define their own key sequences.
    Useful for stratagems not yet added to the plugin's mapping.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

    def on_ready(self):
        self.show()

    def get_sequence(self) -> list:
        """Get the user-defined key sequence."""
        settings = self.get_settings()
        return settings.get("sequence", [])
    
    def get_custom_name(self) -> str:
        """Get the user-defined name for this stratagem."""
        settings = self.get_settings()
        return settings.get("name", "Custom")
    
    def get_custom_labels(self) -> dict:
        """Get the user-defined labels for this stratagem."""
        settings = self.get_settings()
        return settings.get("labels", {"top": "", "center": "", "bottom": "Custom"})

    def show(self):
        if self.plugin_base.get_show_labels():
            labels = self.get_custom_labels()
            self.set_top_label(labels.get("top", ""))
            self.set_center_label(labels.get("center", ""))
            self.set_bottom_label(labels.get("bottom", "Custom"))
        else:
            self.set_top_label("")
            self.set_center_label("")
            self.set_bottom_label("")
        
        # Use custom icon if set, otherwise use default
        settings = self.get_settings()
        custom_icon = settings.get("icon_path")
        if custom_icon and os.path.exists(custom_icon):
            self.set_media(media_path=custom_icon)
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "icons", "custom.png"))

    def get_config_rows(self) -> list:
        """Build the configuration UI for the custom stratagem."""
        rows = []
        
        # Name entry row
        self.name_row = Adw.EntryRow(
            title=self.plugin_base.lm.get("actions.CustomStratagem.config.name", "Stratagem Name")
        )
        self.name_row.set_text(self.get_custom_name())
        self.name_row.connect("changed", self._on_name_changed)
        rows.append(self.name_row)
        
        # Labels configuration
        labels = self.get_custom_labels()
        
        self.top_label_row = Adw.EntryRow(
            title=self.plugin_base.lm.get("actions.CustomStratagem.config.top_label", "Top Label")
        )
        self.top_label_row.set_text(labels.get("top", ""))
        self.top_label_row.connect("changed", self._on_labels_changed)
        rows.append(self.top_label_row)
        
        self.center_label_row = Adw.EntryRow(
            title=self.plugin_base.lm.get("actions.CustomStratagem.config.center_label", "Center Label")
        )
        self.center_label_row.set_text(labels.get("center", ""))
        self.center_label_row.connect("changed", self._on_labels_changed)
        rows.append(self.center_label_row)
        
        self.bottom_label_row = Adw.EntryRow(
            title=self.plugin_base.lm.get("actions.CustomStratagem.config.bottom_label", "Bottom Label")
        )
        self.bottom_label_row.set_text(labels.get("bottom", "Custom"))
        self.bottom_label_row.connect("changed", self._on_labels_changed)
        rows.append(self.bottom_label_row)
        
        # Sequence editor row
        sequence_row = SequenceEditorRow(self)
        rows.append(sequence_row)
        
        return rows
    
    def _on_name_changed(self, entry):
        """Handle name change."""
        settings = self.get_settings()
        settings["name"] = entry.get_text()
        self.set_settings(settings)
    
    def _on_labels_changed(self, entry):
        """Handle label change."""
        settings = self.get_settings()
        settings["labels"] = {
            "top": self.top_label_row.get_text(),
            "center": self.center_label_row.get_text(),
            "bottom": self.bottom_label_row.get_text()
        }
        self.set_settings(settings)
        self.show()

    def on_key_down(self, data=None):
        if self.plugin_base.ui is None:
            log.error("UInput not initialized! Check /dev/uinput permissions.")
            log.error("Try: sudo usermod -aG input $USER (then logout/login)")
            return
        
        sequence = self.get_sequence()
        if not sequence:
            log.warning(f"No sequence configured for custom stratagem '{self.get_custom_name()}'!")
            return
        
        if self.plugin_base.executing:
            log.debug("Currently executing other stratagem! Aborting!")
            return
        
        self.plugin_base.executing = True
        modifier_pressed = False
        
        # Get settings
        key_delay = self.plugin_base.get_key_delay()
        modifier_key = self.plugin_base.get_modifier_key()
        hold_modifier = self.plugin_base.get_hold_modifier()
        
        try:
            log.info(f"Execute Custom Stratagem: {self.get_custom_name()}: {sequence}")
            
            if not self.plugin_base.hero_mode:
                log.debug(f"Not in Hero mode - pressing {modifier_key}")
                modifier_code = ecodes.ecodes.get(modifier_key, ecodes.KEY_LEFTCTRL)
                self.plugin_base.ui.write(ecodes.EV_KEY, modifier_code, 1)
                self.plugin_base.ui.syn()
                sleep(key_delay)
                modifier_pressed = True
                
                # If not holding, release modifier before sequence
                if not hold_modifier:
                    self.plugin_base.ui.write(ecodes.EV_KEY, modifier_code, 0)
                    self.plugin_base.ui.syn()
                    sleep(key_delay)
            
            for key in sequence:
                self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.ecodes[f"KEY_{key}"], 1)
                self.plugin_base.ui.syn()
                sleep(key_delay)
                self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.ecodes[f"KEY_{key}"], 0)
                self.plugin_base.ui.syn()
                sleep(key_delay)
        except Exception as e:
            log.error(f"Error executing custom stratagem: {e}")
        finally:
            # Release modifier if we were holding it
            if modifier_pressed and hold_modifier and not self.plugin_base.hero_mode:
                modifier_code = ecodes.ecodes.get(modifier_key, ecodes.KEY_LEFTCTRL)
                self.plugin_base.ui.write(ecodes.EV_KEY, modifier_code, 0)
                self.plugin_base.ui.syn()
                sleep(key_delay)
            self.plugin_base.executing = False

    def on_key_up(self, data=None):
        pass

    def on_key_short_up(self, data=None):
        pass


class SequenceEditorRow(Adw.PreferencesRow):
    """A custom row for editing the stratagem key sequence."""
    
    def __init__(self, action: CustomStratagemButton):
        super().__init__(title="Key Sequence")
        self.action = action
        self.build_ui()
        self.update_sequence_display()
    
    def build_ui(self):
        """Build the sequence editor UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=12, margin_end=12, margin_top=8, margin_bottom=8)
        self.set_child(main_box)
        
        # Header with title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_bottom=8)
        main_box.append(header_box)
        
        title_label = Gtk.Label(
            label=self.action.plugin_base.lm.get("actions.CustomStratagem.config.sequence", "Key Sequence"),
            xalign=0,
            hexpand=True,
            css_classes=["title"]
        )
        header_box.append(title_label)
        
        # Clear button
        clear_button = Gtk.Button(icon_name="edit-clear-symbolic", tooltip_text="Clear sequence")
        clear_button.connect("clicked", self._on_clear)
        header_box.append(clear_button)
        
        # Current sequence display
        sequence_frame = Gtk.Frame(margin_bottom=8)
        main_box.append(sequence_frame)
        
        self.sequence_display = Gtk.Label(
            label="(empty)",
            margin_start=8,
            margin_end=8,
            margin_top=8,
            margin_bottom=8,
            wrap=True,
            css_classes=["monospace"]
        )
        sequence_frame.set_child(self.sequence_display)
        
        # Direction buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.CENTER)
        main_box.append(button_box)
        
        for direction in DIRECTION_KEYS:
            btn = Gtk.Button(label=DIRECTION_ARROWS[direction], tooltip_text=f"Add {direction}")
            btn.set_size_request(48, 48)
            btn.connect("clicked", self._on_direction_clicked, direction)
            button_box.append(btn)
        
        # Backspace button to remove last key
        backspace_btn = Gtk.Button(icon_name="edit-undo-symbolic", tooltip_text="Remove last key")
        backspace_btn.set_size_request(48, 48)
        backspace_btn.connect("clicked", self._on_backspace)
        button_box.append(backspace_btn)
    
    def update_sequence_display(self):
        """Update the sequence display label."""
        sequence = self.action.get_sequence()
        if sequence:
            arrows = [DIRECTION_ARROWS.get(k, k) for k in sequence]
            self.sequence_display.set_text(" ".join(arrows))
        else:
            self.sequence_display.set_text("(empty)")
    
    def _on_direction_clicked(self, button, direction):
        """Handle direction button click."""
        settings = self.action.get_settings()
        sequence = settings.get("sequence", [])
        sequence.append(direction)
        settings["sequence"] = sequence
        self.action.set_settings(settings)
        self.update_sequence_display()
    
    def _on_backspace(self, button):
        """Remove the last key from the sequence."""
        settings = self.action.get_settings()
        sequence = settings.get("sequence", [])
        if sequence:
            sequence.pop()
            settings["sequence"] = sequence
            self.action.set_settings(settings)
            self.update_sequence_display()
    
    def _on_clear(self, button):
        """Clear the entire sequence."""
        settings = self.action.get_settings()
        settings["sequence"] = []
        self.action.set_settings(settings)
        self.update_sequence_display()


class StratagemButton(KeyAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.stratagem_key = self.action_id.split("::", 1)[1]
        self.stratagem = self.plugin_base.stratagems.get(self.stratagem_key)
        
        if self.stratagem is None:
            log.error(f"Stratagem '{self.stratagem_key}' not found in stratagems.json!")
            self.stratagem = []  # Empty sequence to prevent crashes

    def show(self):
        if self.plugin_base.get_show_labels():
            self.set_top_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.top", ""))
            self.set_center_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.center", ""))
            self.set_bottom_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.bottom", self.plugin_base.lm.get(f"actions.{self.stratagem_key}.name")))
        else:
            self.set_top_label("")
            self.set_center_label("")
            self.set_bottom_label("")
        self.set_media(
            media_path=os.path.join(self.plugin_base.PATH, "assets", "icons", self.stratagem_key + ".png")
        )


    def on_ready(self):
        self.show()

    def on_key_down(self, data=None):
        if self.plugin_base.ui is None:
            log.error("UInput not initialized! Check /dev/uinput permissions.")
            log.error("Try: sudo usermod -aG input $USER (then logout/login)")
            return
        
        if not self.stratagem:
            log.error(f"No sequence for stratagem '{self.stratagem_key}'!")
            return
        
        if self.plugin_base.executing:
            log.debug("Currently executing other stratagem! Aborting!")
            return
        
        self.plugin_base.executing = True
        modifier_pressed = False
        
        # Get settings
        key_delay = self.plugin_base.get_key_delay()
        modifier_key = self.plugin_base.get_modifier_key()
        hold_modifier = self.plugin_base.get_hold_modifier()
        
        try:
            log.info(f"Execute Stratagem: {self.stratagem_key}: {self.stratagem}")
            
            if not self.plugin_base.hero_mode:
                log.debug(f"Not in Hero mode - pressing {modifier_key}")
                modifier_code = ecodes.ecodes.get(modifier_key, ecodes.KEY_LEFTCTRL)
                self.plugin_base.ui.write(ecodes.EV_KEY, modifier_code, 1)
                self.plugin_base.ui.syn()
                sleep(key_delay)
                modifier_pressed = True
                
                # If not holding, release modifier before sequence
                if not hold_modifier:
                    self.plugin_base.ui.write(ecodes.EV_KEY, modifier_code, 0)
                    self.plugin_base.ui.syn()
                    sleep(key_delay)
            
            for key in self.stratagem:
                self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.ecodes[f"KEY_{key}"], 1)
                self.plugin_base.ui.syn()
                sleep(key_delay)
                self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.ecodes[f"KEY_{key}"], 0)
                self.plugin_base.ui.syn()
                sleep(key_delay)
        except Exception as e:
            log.error(f"Error executing stratagem: {e}")
        finally:
            # Release modifier if we were holding it
            if modifier_pressed and hold_modifier and not self.plugin_base.hero_mode:
                modifier_code = ecodes.ecodes.get(modifier_key, ecodes.KEY_LEFTCTRL)
                self.plugin_base.ui.write(ecodes.EV_KEY, modifier_code, 0)
                self.plugin_base.ui.syn()
                sleep(key_delay)
            self.plugin_base.executing = False

    def on_key_up(self, data=None):
        pass

    def on_key_short_up(self, data=None):
        pass


class HellDiversPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.init_locale_manager()
        self.lm = self.locale_manager
        
        # Enable plugin settings
        self.has_plugin_settings = True
        
        self.ui = None
        self.init_input()

        self.stratagems = None
        self.init_stratagems()

        self.hero_mode = False

        self.executing = False

        for stratagem in self.stratagems:
            try:
                self.add_action_holder(ActionHolder(
                    plugin_base=self,
                    action_base=StratagemButton,
                    action_id=f"net_jslay_helldivers_2::{stratagem}",
                    action_name=self.lm.get(f"actions.{stratagem}.name")
                ))
            except Exception as e:
                log.error(e)

        self.add_action_holder(ActionHolder(
            plugin_base=self,
            action_base=StratagemHeroButton,
            action_id="net_jslay_helldivers_2::StratagemHeroToggle",
            action_name=self.lm.get("actions.StratagemHeroToggle.name")
        ))

        # Add custom stratagem action
        self.add_action_holder(ActionHolder(
            plugin_base=self,
            action_base=CustomStratagemButton,
            action_id="net_jslay_helldivers_2::CustomStratagem",
            action_name=self.lm.get("actions.CustomStratagem.name", "Custom Stratagem")
        ))

        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/jslay88/streamcontroller_helldivers_2",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )

    
    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

    def init_input(self):
        self.ui = None
        try:
            self.ui = UInput({ecodes.EV_KEY: range(0, 300),
                         ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y]}, name="stream-controller-helldivers-2-plugin")
            log.info("UInput initialized successfully")
        except PermissionError as e:
            log.error(f"Permission denied creating UInput: {e}")
            log.error("Fix: Add user to input group: sudo usermod -aG input $USER")
            log.error("Then logout and login again, or reboot.")
        except Exception as e:
            log.error(f"Failed to create UInput: {e}")

    def init_stratagems(self):
        with open(os.path.join(self.PATH, "assets", "data", "stratagems.json")) as f:
            self.stratagems = json.load(f)

    # ---- Settings Helpers ----
    
    def get_key_delay(self) -> float:
        """Get the delay between key presses in seconds."""
        settings = self.get_settings()
        return settings.get("key_delay", DEFAULT_KEY_DELAY)
    
    def get_modifier_key(self) -> str:
        """Get the modifier key to use for opening stratagem menu."""
        settings = self.get_settings()
        return settings.get("modifier_key", DEFAULT_MODIFIER_KEY)
    
    def get_hold_modifier(self) -> bool:
        """Get whether to hold the modifier key during the sequence."""
        settings = self.get_settings()
        return settings.get("hold_modifier", DEFAULT_HOLD_MODIFIER)
    
    def get_show_labels(self) -> bool:
        """Get whether to show labels on buttons."""
        settings = self.get_settings()
        return settings.get("show_labels", DEFAULT_SHOW_LABELS)
    
    def _save_setting(self, key: str, value):
        """Save a single setting."""
        settings = self.get_settings()
        settings[key] = value
        self.set_settings(settings)
    
    # ---- Settings UI ----
    
    def get_settings_area(self):
        """Build and return the settings UI."""
        group = Adw.PreferencesGroup(
            title="Stratagem Settings",
            description="Configure how stratagems are executed and displayed"
        )
        
        # Execution settings
        group.add(self._create_key_delay_row())
        group.add(self._create_modifier_key_row())
        group.add(self._create_hold_modifier_row())
        
        # Display settings
        group.add(self._create_show_labels_row())
        
        return group
    
    def _create_key_delay_row(self) -> Adw.ActionRow:
        """Create the key delay slider row."""
        row = Adw.ActionRow(
            title="Key Delay",
            subtitle="Delay between key presses (seconds). Increase if stratagems fail."
        )
        
        adjustment = Gtk.Adjustment(
            value=self.get_key_delay(),
            lower=0.01,
            upper=0.20,
            step_increment=0.01,
            page_increment=0.05
        )
        
        scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=adjustment,
            digits=2,
            draw_value=True,
            hexpand=True
        )
        scale.set_size_request(200, -1)
        scale.connect("value-changed", self._on_key_delay_changed)
        
        row.add_suffix(scale)
        return row
    
    def _on_key_delay_changed(self, scale):
        """Handle key delay slider change."""
        value = round(scale.get_value(), 2)
        self._save_setting("key_delay", value)
    
    def _create_modifier_key_row(self) -> Adw.ComboRow:
        """Create the modifier key combo row."""
        row = Adw.ComboRow(
            title="Modifier Key",
            subtitle="Key to open stratagem menu (when not in Hero mode)"
        )
        
        # Create string list for combo
        string_list = Gtk.StringList()
        modifier_names = list(MODIFIER_KEYS.keys())
        for name in modifier_names:
            string_list.append(name)
        
        row.set_model(string_list)
        
        # Set current selection
        current_key = self.get_modifier_key()
        for i, name in enumerate(modifier_names):
            if MODIFIER_KEYS[name] == current_key:
                row.set_selected(i)
                break
        
        row.connect("notify::selected", self._on_modifier_key_changed, modifier_names)
        return row
    
    def _on_modifier_key_changed(self, row, _, modifier_names):
        """Handle modifier key combo change."""
        selected = row.get_selected()
        if selected < len(modifier_names):
            name = modifier_names[selected]
            key = MODIFIER_KEYS[name]
            self._save_setting("modifier_key", key)
    
    def _create_hold_modifier_row(self) -> Adw.SwitchRow:
        """Create the hold modifier switch row."""
        row = Adw.SwitchRow(
            title="Hold Modifier Key",
            subtitle="Hold modifier during entire sequence (off = press and release before sequence)"
        )
        
        row.set_active(self.get_hold_modifier())
        row.connect("notify::active", self._on_hold_modifier_changed)
        return row
    
    def _on_hold_modifier_changed(self, row, _):
        """Handle hold modifier switch change."""
        self._save_setting("hold_modifier", row.get_active())
    
    def _create_show_labels_row(self) -> Adw.SwitchRow:
        """Create the show labels switch row."""
        row = Adw.SwitchRow(
            title="Show Labels",
            subtitle="Display text labels on stratagem buttons"
        )
        
        row.set_active(self.get_show_labels())
        row.connect("notify::active", self._on_show_labels_changed)
        return row
    
    def _on_show_labels_changed(self, row, _):
        """Handle show labels switch change."""
        self._save_setting("show_labels", row.get_active())
        # Refresh all action displays
        self._refresh_all_actions()
    
    def _refresh_all_actions(self):
        """Refresh all action buttons to apply label visibility changes."""
        import globals as gl
        
        if not hasattr(gl, 'deck_manager') or gl.deck_manager is None:
            return
        
        # Iterate through all deck controllers
        for deck_controller in gl.deck_manager.deck_controller:
            if deck_controller.active_page is None:
                continue
            
            # Get all actions on the active page
            for action in deck_controller.active_page.get_all_actions():
                # Check if this action belongs to our plugin
                if hasattr(action, 'plugin_base') and action.plugin_base is self:
                    if hasattr(action, 'show'):
                        try:
                            action.show()
                        except Exception as e:
                            log.debug(f"Failed to refresh action: {e}")
