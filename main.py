import json
import os
from time import sleep

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase

from evdev import ecodes, UInput
from gi.repository import Gtk
from loguru import logger as log
from PIL import Image


log.debug("Init HELLDIVERS 2")


SLEEP_DELAY = 0.03


class StratagemHeroButton(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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

    def on_key_down(self):
        if self.plugin_base.executing:
            log.debug("Currently executing other stratagem! Aborting!")
            return
        self.plugin_base.executing = True
        log.debug(f"Execute Stratagem: {self.stratagem_key}: {self.stratagem}")
        if not self.plugin_base.hero_mode:
            log.debug("Not Heroing")
            self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
            self.plugin_base.ui.syn()
            sleep(SLEEP_DELAY)
        try:
            for key in self.stratagem:
                self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.ecodes[f"KEY_{key}"], 1)
                self.plugin_base.ui.syn()
                sleep(SLEEP_DELAY)
                self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.ecodes[f"KEY_{key}"], 0)
                self.plugin_base.ui.syn()
                sleep(SLEEP_DELAY)
        finally:
            self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
            self.plugin_base.ui.syn()
            sleep(SLEEP_DELAY)
            self.plugin_base.executing = False


class HellDiversPlugin(PluginBase):
    def __init__(self):
        super().__init__()

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
        except Exception as e:
            log.error(e)

    def init_stratagems(self):
        with open(os.path.join(self.PATH, "assets", "data", "stratagems.json")) as f:
            self.stratagems = json.load(f)
        
