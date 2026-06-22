import unittest

from key_mapping import (
    DEFAULT_DIRECTION_KEY_LAYOUT,
    get_direction_key,
    normalize_direction_key_layout,
)


class DirectionKeyMappingTests(unittest.TestCase):
    def test_arrow_key_layout(self):
        self.assertEqual(get_direction_key("UP", "arrow_keys"), "KEY_UP")
        self.assertEqual(get_direction_key("DOWN", "arrow_keys"), "KEY_DOWN")
        self.assertEqual(get_direction_key("LEFT", "arrow_keys"), "KEY_LEFT")
        self.assertEqual(get_direction_key("RIGHT", "arrow_keys"), "KEY_RIGHT")

    def test_wasd_key_layout(self):
        self.assertEqual(get_direction_key("UP", "wasd"), "KEY_W")
        self.assertEqual(get_direction_key("DOWN", "wasd"), "KEY_S")
        self.assertEqual(get_direction_key("LEFT", "wasd"), "KEY_A")
        self.assertEqual(get_direction_key("RIGHT", "wasd"), "KEY_D")

    def test_unknown_layout_uses_backward_compatible_default(self):
        self.assertEqual(
            normalize_direction_key_layout("removed-layout"),
            DEFAULT_DIRECTION_KEY_LAYOUT,
        )
        self.assertEqual(get_direction_key("UP", "removed-layout"), "KEY_UP")

    def test_unknown_direction_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported stratagem direction"):
            get_direction_key("FORWARD", "wasd")


if __name__ == "__main__":
    unittest.main()
