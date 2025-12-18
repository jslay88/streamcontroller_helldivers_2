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
        self.set_top_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.top", ""))
        self.set_center_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.center", "Stratagem"))
        self.set_bottom_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.bottom", "Hero"))

        fname = "hero_off.png"
        if self.plugin_base.hero_mode:
            fname = "hero_on.png"
        self.set_media(
            media_path=os.path.join(self.plugin_base.PATH, "assets", "icons", fname)
        )


class StratagemButton(KeyAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.stratagem_key = self.action_id.split("::", 1)[1]
        self.stratagem = self.plugin_base.stratagems.get(self.stratagem_key)
        
        if self.stratagem is None:
            log.error(f"Stratagem '{self.stratagem_key}' not found in stratagems.json!")
            self.stratagem = []  # Empty sequence to prevent crashes

    def show(self):
        self.set_top_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.top", ""))
        self.set_center_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.center", ""))
        self.set_bottom_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.bottom", self.plugin_base.lm.get(f"actions.{self.stratagem_key}.name")))
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
            description="Configure how stratagems are executed"
        )
        
        # Key Delay Setting
        key_delay_row = self._create_key_delay_row()
        group.add(key_delay_row)
        
        # Modifier Key Setting
        modifier_key_row = self._create_modifier_key_row()
        group.add(modifier_key_row)
        
        # Hold Modifier Setting
        hold_modifier_row = self._create_hold_modifier_row()
        group.add(hold_modifier_row)
        
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
        
