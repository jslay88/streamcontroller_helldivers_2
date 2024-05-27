import json
import os
from time import sleep

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase

from evdev import ecodes, UInput
from loguru import logger as log
from PIL import Image

# Gtk
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk


log.debug("Init HELLDIVERS 2")


class StratagemHeroButton(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
                         deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        self.show()

    def on_ready(self):
        self.show()

    def on_key_down(self):
        self.plugin_base.hero_mode = not self.plugin_base.hero_mode
        self.show()

    def show(self):
        self.set_top_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.top", ""))
        self.set_center_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.center", "Stratagem"))
        self.set_bottom_label(self.plugin_base.lm.get("actions.StratagemHeroToggle.labels.bottom", "Hero"))

        fname = "hero_off.png"
        if self.plugin_base.hero_mode:
            fname = "hero_on.png"
        self.set_media(
            media_path=os.path.join(self.plugin_base.PATH, "assets", "icons", fname),
            size=1.00,
            valign=-1
        )


class StratagemButton(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
                         deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        self.stratagem_key = self.action_id.split("::", 1)[1]
        self.stratagem = self.plugin_base.stratagems[self.stratagem_key]
        self.show()

    def show(self):
        self.set_top_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.top", ""))
        self.set_center_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.center", ""))
        self.set_bottom_label(self.plugin_base.lm.get(f"actions.{self.stratagem_key}.labels.bottom", self.plugin_base.lm.get(f"actions.{self.stratagem_key}.name")))
        self.set_media(
            media_path=os.path.join(self.plugin_base.PATH, "assets", "icons", self.stratagem_key + ".png"),
            size=1.00,
            valign=-1
        )

    def on_ready(self):
        self.show()

    def get_config_rows(self) -> list:
        plugin_config_row = PluginConfigRow(self.plugin_base)
        return [plugin_config_row]

    def on_key_down(self):
        bindings = self.plugin_base.bindings
        delays = self.plugin_base.delays

        if self.plugin_base.executing:
            log.debug("Currently executing other stratagem! Aborting!")
            return

        self.plugin_base.executing = True
        log.debug(f"Execute Stratagem: {self.stratagem_key}: {self.stratagem}")

        if not self.plugin_base.hero_mode:
            log.debug("Not Heroing, press activator")
            self.plugin_base.ui.write(ecodes.EV_KEY, bindings["activator"], 1)
            self.plugin_base.ui.syn()
            sleep(delays["pressed"])

        try:
            for key in self.stratagem:
                self.plugin_base.ui.write(ecodes.EV_KEY, bindings[key], 1)
                self.plugin_base.ui.syn()
                sleep(delays["pressed"])
                self.plugin_base.ui.write(ecodes.EV_KEY, bindings[key], 0)
                self.plugin_base.ui.syn()
                sleep(delays["released"])
        finally:
            self.plugin_base.ui.write(ecodes.EV_KEY, bindings["activator"], 0)
            self.plugin_base.ui.syn()
            sleep(delays["released"])
            self.plugin_base.executing = False


class HellDiversPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self._settings = None

        self.init_locale_manager()
        self.lm = self.locale_manager
        
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
            app_version="1.5.0-beta"
        )

    
    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

    def init_input(self):
        self.ui = None
        try:
            self.ui = UInput({ecodes.EV_KEY: range(0, 300),
                         ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y]}, name="stream-controller-helldivers-2-plugin")
        except Exception as e:
            log.error(e)

    def init_stratagems(self):
        with open(os.path.join(self.PATH, "assets", "data", "stratagems.json")) as f:
            self.stratagems = json.load(f)

    def default_settings(self):
        log.debug("Defaulting Settings for HELLDIVERS 2")
        settings = {
            "bindings": {
                "activator": ecodes.KEY_LEFTCTRL,
                "LEFT": ecodes.KEY_LEFT,
                "RIGHT": ecodes.KEY_RIGHT,
                "UP": ecodes.KEY_UP,
                "DOWN": ecodes.KEY_DOWN
            },
            "delays": {
                "pressed": 0.03,
                "released": 0.03
            }
        }
        self.set_settings(settings)
        return settings

    @property
    def settings(self):
        if self._settings:
            return self._settings
        self._settings = self.get_settings()
        if not self._settings:
            self._settings = self.default_settings()
        return self._settings
        
    @property
    def bindings(self):
        return self.settings.get("bindings")

    @property
    def delays(self):
        return self.settings.get("delays")


class PluginConfigRow(Adw.PreferencesRow):
    def __init__(self, plugin_base: HellDiversPlugin):
        super().__init__(title="Plugin Config:")
        self.plugin_base = plugin_base
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.set_child(self.main_box)

        self.main_box.append(Gtk.Label(
            hexpand=True,
            label=self.plugin_base.lm.get("config.row.label"),
            xalign=0,
            margin_start=12
        ))

        self.config_button = Gtk.Button(label=self.plugin_base.lm.get("config.button.label"))
        self.config_button.connect("clicked", self.open_config)
        self.main_box.append(self.config_button)

    def open_config(self, _):
        window = PluginConfigWindow(self.plugin_base)
        window.present()


class PluginConfigWindow(Gtk.ApplicationWindow):
    def __init__(self, plugin_base: HellDiversPlugin, *args, **kwargs):
        self.GTK_CODE_DIFFERENCE = 0
        super().__init__(*args, **kwargs)
        self.plugin_base = plugin_base
        settings = self.plugin_base.settings

        self.rebinding = False
        self.seat = None

        self.set_default_size(600, 300)
        self.set_title(self.plugin_base.lm.get("config.window.title"))
        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            focus_on_click=True, 
            focusable=True, 
            can_focus=True
        )
        self.set_child(self.main_box)

        self.pressed_delay_row = Adw.SpinRow.new_with_range(min=0, max=1, step=0.01)
        self.pressed_delay_row.set_title(self.plugin_base.lm.get("config.pressed_delay.title"))
        self.pressed_delay_row.set_subtitle(self.plugin_base.lm.get("config.pressed_delay.subtitle"))
        self.pressed_delay_row.set_value(settings.get("delays").get("pressed", 0.03))
        self.pressed_delay_row.key = "pressed"
        self.pressed_delay_row.connect("changed", self.on_delay_changed)
        self.main_box.append(self.pressed_delay_row)

        self.released_delay_row = Adw.SpinRow.new_with_range(min=0, max=1, step=0.01)
        self.released_delay_row.set_title(self.plugin_base.lm.get("config.released_delay.title"))
        self.released_delay_row.set_subtitle(self.plugin_base.lm.get("config.released_delay.subtitle"))
        self.released_delay_row.set_value(settings.get("delays").get("released", 0.03))
        self.released_delay_row.key = "released"
        self.released_delay_row.connect("changed", self.on_delay_changed)
        self.main_box.append(self.released_delay_row)

        for row in ["activator", "UP", "DOWN", "LEFT", "RIGHT"]:
            binding_row = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                hexpand=True
            )
            binding_row.append(Gtk.Label(
                hexpand=True,
                label=self.plugin_base.lm.get(f"config.{row}_binding.label"),
                xalign=0,
                margin_start=12,
                margin_top=15,
                margin_bottom=15
            ))
            log.debug(ecodes.KEY[settings.get("bindings").get(row)])
            key_label = Gtk.Label(
                label=ecodes.KEY[settings.get("bindings").get(row)].replace("KEY_", "") + "     ",
                xalign=0.5,
                margin_start=12,
                margin_top=15,
                margin_bottom=15,
            )
            binding_row.append(key_label)
            button = Gtk.Button(label=self.plugin_base.lm.get("config.rebind.label"), margin_top=15, margin_bottom=15)
            button.key = row
            button.key_label = key_label
            button.connect("clicked", self.on_rebind)
            binding_row.append(button)
            self.main_box.append(binding_row)

    def on_delay_changed(self, spin_row: Adw.SpinRow):
        settings = self.plugin_base.settings
        settings["delays"][spin_row.key] = spin_row.get_value()
        self.plugin_base.set_settings(settings)

    def on_rebind(self, button: Gtk.Button):
        if self.rebinding:
            return
        self.rebinding = True

        def on_key_down(controller, key_value, key_code, state):
            settings = self.plugin_base.settings
            settings["bindings"][button.key] = key_code - 8
            log.debug(f"{controller}, {key_value}, {key_code}, {state}")
            self.plugin_base.set_settings(settings)
            button.key_label.set_label(ecodes.KEY[key_code - 8].replace("KEY_", "") + "     ")
            self.rebinding = False
            return True

        button.key_label.set_label(self.plugin_base.lm.get("config.rebinding.label") + "     ")
        self.eck = Gtk.EventControllerKey()
        self.eck.connect("key-pressed", on_key_down)
        self.add_controller(self.eck)
        self.seat = self.get_display().get_default_seat()

