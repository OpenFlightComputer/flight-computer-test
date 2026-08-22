from __future__ import annotations

import unittest

from fc_test.tests.rgb_led.colours import ColourError, colour_to_rgb


class ColourTests(unittest.TestCase):
    def test_css_name_is_converted_to_rgb(self) -> None:
        self.assertEqual(colour_to_rgb("turquoise"), (64, 224, 208))

    def test_hex_allows_any_rgb_triplet(self) -> None:
        self.assertEqual(colour_to_rgb("#28DCC8"), (40, 220, 200))

    def test_rgb_function_allows_any_rgb_triplet(self) -> None:
        self.assertEqual(colour_to_rgb("rgb(40, 220, 200)"), (40, 220, 200))

    def test_unknown_colour_is_rejected(self) -> None:
        with self.assertRaisesRegex(ColourError, "CSS3 name"):
            colour_to_rgb("interstellar teal")


if __name__ == "__main__":
    unittest.main()
