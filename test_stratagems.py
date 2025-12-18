#!/usr/bin/env python3
"""
Stratagem Input Validator

A simple window that captures keyboard input and matches it to stratagems.
Press your Stream Deck buttons and see which stratagem was detected.

Usage:
    python test_stratagems.py

Controls:
    - Focus the window
    - Press arrow keys (with or without modifier)
    - The tool will match sequences to stratagems
    - Press Escape to clear the current sequence
"""

import json
import os
import sys

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STRATAGEMS_PATH = os.path.join(SCRIPT_DIR, "assets", "data", "stratagems.json")

# Arrow key mappings
KEY_TO_DIRECTION = {
    Gdk.KEY_Up: "UP",
    Gdk.KEY_Down: "DOWN",
    Gdk.KEY_Left: "LEFT",
    Gdk.KEY_Right: "RIGHT",
}

DIRECTION_DISPLAY = {
    "UP": "↑",
    "DOWN": "↓",
    "LEFT": "←",
    "RIGHT": "→",
}

# Modifier key mappings
MODIFIER_KEYS = {
    Gdk.KEY_Control_L: "Left Ctrl",
    Gdk.KEY_Control_R: "Right Ctrl",
    Gdk.KEY_Alt_L: "Left Alt",
    Gdk.KEY_Alt_R: "Right Alt",
    Gdk.KEY_Shift_L: "Left Shift",
    Gdk.KEY_Shift_R: "Right Shift",
    Gdk.KEY_Super_L: "Left Super",
    Gdk.KEY_Super_R: "Right Super",
}

# State mask to modifier name
STATE_TO_MODIFIER = {
    Gdk.ModifierType.CONTROL_MASK: "Ctrl",
    Gdk.ModifierType.ALT_MASK: "Alt",
    Gdk.ModifierType.SHIFT_MASK: "Shift",
    Gdk.ModifierType.SUPER_MASK: "Super",
}


class StratagemValidator(Adw.ApplicationWindow):
    def __init__(self, app, stratagems: dict):
        super().__init__(application=app, title="Stratagem Input Validator")
        self.stratagems = stratagems
        self.current_sequence = []
        
        # Modifier tracking
        self.modifier_key = None  # Which modifier was pressed
        self.modifier_held = False  # Was it held for the whole sequence?
        self.modifier_pressed_at_start = False  # Was modifier down when sequence started?
        self.modifier_released_during = False  # Was modifier released during sequence?
        self.keys_with_modifier = 0  # How many keys pressed while modifier held
        self.keys_without_modifier = 0  # How many keys pressed without modifier
        
        # Build reverse lookup: sequence tuple -> stratagem name
        self.sequence_lookup = {}
        for name, sequence in stratagems.items():
            key = tuple(sequence)
            self.sequence_lookup[key] = name
        
        self.set_default_size(500, 450)
        self.build_ui()
        self.setup_key_capture()
    
    def build_ui(self):
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        header = Adw.HeaderBar()
        
        # Instructions
        instructions = Gtk.Label(
            label="Press arrow keys to input a stratagem sequence.\n"
                  "Press Escape to clear."
        )
        instructions.set_wrap(True)
        instructions.add_css_class("dim-label")
        main_box.append(instructions)
        
        # Current sequence display
        sequence_frame = Gtk.Frame(label="Input Sequence")
        self.sequence_label = Gtk.Label(label="(waiting for input)")
        self.sequence_label.set_margin_top(15)
        self.sequence_label.set_margin_bottom(15)
        self.sequence_label.add_css_class("title-1")
        sequence_frame.set_child(self.sequence_label)
        main_box.append(sequence_frame)
        
        # Modifier info
        modifier_frame = Gtk.Frame(label="Modifier Key")
        modifier_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        modifier_box.set_margin_top(10)
        modifier_box.set_margin_bottom(10)
        modifier_box.set_margin_start(10)
        modifier_box.set_margin_end(10)
        
        self.modifier_label = Gtk.Label(label="None detected")
        self.modifier_label.add_css_class("title-3")
        modifier_box.append(self.modifier_label)
        
        self.modifier_mode_label = Gtk.Label(label="")
        self.modifier_mode_label.add_css_class("dim-label")
        modifier_box.append(self.modifier_mode_label)
        
        modifier_frame.set_child(modifier_box)
        main_box.append(modifier_frame)
        
        # Match result
        result_frame = Gtk.Frame(label="Matched Stratagem")
        result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        result_box.set_margin_top(10)
        result_box.set_margin_bottom(10)
        result_box.set_margin_start(10)
        result_box.set_margin_end(10)
        
        self.result_label = Gtk.Label(label="—")
        self.result_label.add_css_class("title-2")
        result_box.append(self.result_label)
        
        self.partial_label = Gtk.Label(label="")
        self.partial_label.add_css_class("dim-label")
        self.partial_label.set_wrap(True)
        result_box.append(self.partial_label)
        
        result_frame.set_child(result_box)
        main_box.append(result_frame)
        
        # Clear button
        clear_button = Gtk.Button(label="Clear (Esc)")
        clear_button.connect("clicked", lambda _: self.clear_sequence())
        clear_button.set_halign(Gtk.Align.CENTER)
        main_box.append(clear_button)
        
        # Stats
        stats_label = Gtk.Label(label=f"Loaded {len(self.stratagems)} stratagems")
        stats_label.add_css_class("dim-label")
        main_box.append(stats_label)
        
        # Set content
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        toolbar_view.set_content(main_box)
        self.set_content(toolbar_view)
    
    def setup_key_capture(self):
        # Key controller for capturing keys
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        key_controller.connect("key-released", self.on_key_released)
        self.add_controller(key_controller)
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        # Escape clears
        if keyval == Gdk.KEY_Escape:
            self.clear_sequence()
            return True
        
        # Track modifier key presses
        if keyval in MODIFIER_KEYS:
            if self.modifier_key is None:
                self.modifier_key = MODIFIER_KEYS[keyval]
                self.modifier_pressed_at_start = len(self.current_sequence) == 0
            self.update_modifier_display()
            return True
        
        # Check if it's an arrow key
        direction = KEY_TO_DIRECTION.get(keyval)
        if direction:
            # Check if modifier is currently held
            modifier_active = self.is_modifier_active(state)
            
            if modifier_active:
                self.keys_with_modifier += 1
            else:
                self.keys_without_modifier += 1
            
            # Detect which modifier from state if we haven't seen a key press
            if self.modifier_key is None and modifier_active:
                self.modifier_key = self.get_modifier_from_state(state)
                self.modifier_pressed_at_start = len(self.current_sequence) == 0
            
            self.add_key(direction)
            self.update_modifier_display()
            return True
        
        return False
    
    def on_key_released(self, controller, keyval, keycode, state):
        # Track when modifier is released
        if keyval in MODIFIER_KEYS:
            if len(self.current_sequence) > 0:
                self.modifier_released_during = True
            self.update_modifier_display()
        return False
    
    def is_modifier_active(self, state) -> bool:
        """Check if any modifier key is currently held."""
        return bool(state & (
            Gdk.ModifierType.CONTROL_MASK |
            Gdk.ModifierType.ALT_MASK |
            Gdk.ModifierType.SHIFT_MASK |
            Gdk.ModifierType.SUPER_MASK
        ))
    
    def get_modifier_from_state(self, state) -> str:
        """Get modifier name from state mask."""
        for mask, name in STATE_TO_MODIFIER.items():
            if state & mask:
                return name
        return "Unknown"
    
    def add_key(self, direction: str):
        self.current_sequence.append(direction)
        self.update_display()
    
    def clear_sequence(self):
        self.current_sequence = []
        self.modifier_key = None
        self.modifier_held = False
        self.modifier_pressed_at_start = False
        self.modifier_released_during = False
        self.keys_with_modifier = 0
        self.keys_without_modifier = 0
        
        self.sequence_label.set_text("(waiting for input)")
        self.result_label.set_text("—")
        self.partial_label.set_text("")
        self.modifier_label.set_text("None detected")
        self.modifier_mode_label.set_text("")
        self.result_label.remove_css_class("success")
        self.result_label.remove_css_class("error")
    
    def update_modifier_display(self):
        if self.modifier_key is None:
            self.modifier_label.set_text("None detected")
            self.modifier_mode_label.set_text("")
            return
        
        self.modifier_label.set_text(self.modifier_key)
        
        # Determine if held or pressed-and-released
        total_keys = len(self.current_sequence)
        if total_keys == 0:
            self.modifier_mode_label.set_text("(modifier pressed, waiting for sequence)")
        elif self.keys_with_modifier == total_keys and not self.modifier_released_during:
            self.modifier_mode_label.set_text("✓ HELD during entire sequence")
        elif self.keys_with_modifier == 0:
            self.modifier_mode_label.set_text("⚡ PRESSED then released before sequence")
        elif self.keys_without_modifier > 0:
            self.modifier_mode_label.set_text(
                f"⚠ Mixed: {self.keys_with_modifier} keys with, "
                f"{self.keys_without_modifier} without modifier"
            )
        else:
            self.modifier_mode_label.set_text("✓ HELD during sequence")
    
    def update_display(self):
        # Update sequence display
        display = " ".join(DIRECTION_DISPLAY.get(d, d) for d in self.current_sequence)
        self.sequence_label.set_text(display if display else "(waiting for input)")
        
        # Check for exact match
        seq_tuple = tuple(self.current_sequence)
        exact_match = self.sequence_lookup.get(seq_tuple)
        
        if exact_match:
            self.result_label.set_text(f"✓ {exact_match}")
            self.result_label.remove_css_class("error")
            self.result_label.add_css_class("success")
            self.partial_label.set_text("")
        else:
            # Find partial matches (stratagems that start with current sequence)
            partial_matches = []
            for name, sequence in self.stratagems.items():
                if len(sequence) >= len(self.current_sequence):
                    if sequence[:len(self.current_sequence)] == self.current_sequence:
                        partial_matches.append(name)
            
            if partial_matches:
                self.result_label.set_text("(partial match)")
                self.result_label.remove_css_class("success")
                self.result_label.remove_css_class("error")
                
                if len(partial_matches) <= 5:
                    self.partial_label.set_text(f"Possible: {', '.join(partial_matches)}")
                else:
                    self.partial_label.set_text(f"{len(partial_matches)} possible matches...")
            else:
                self.result_label.set_text("✗ No match")
                self.result_label.remove_css_class("success")
                self.result_label.add_css_class("error")
                self.partial_label.set_text("")


class ValidatorApp(Adw.Application):
    def __init__(self, stratagems: dict):
        super().__init__(application_id="com.jslay.stratagem-validator")
        self.stratagems = stratagems
    
    def do_activate(self):
        window = StratagemValidator(self, self.stratagems)
        window.present()


def load_stratagems() -> dict:
    """Load stratagems from JSON file."""
    if not os.path.exists(STRATAGEMS_PATH):
        print(f"Error: Stratagems file not found: {STRATAGEMS_PATH}")
        print("Run 'python -m update generate-all' to generate it.")
        return {}
    
    with open(STRATAGEMS_PATH, "r") as f:
        return json.load(f)


def main():
    stratagems = load_stratagems()
    
    if not stratagems:
        print("No stratagems loaded. Exiting.")
        sys.exit(1)
    
    print(f"Loaded {len(stratagems)} stratagems")
    print("Focus the window and press arrow keys to test.")
    
    app = ValidatorApp(stratagems)
    app.run(sys.argv)


if __name__ == "__main__":
    main()
