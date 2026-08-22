"""Convert RGB LED colour specifications into RGB bytes."""

from __future__ import annotations

import re

import webcolors


class ColourError(ValueError):
    """A configured colour cannot be represented as three RGB bytes."""


_RGB_FUNCTION = re.compile(
    r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)",
    re.IGNORECASE,
)


def colour_to_rgb(colour: str) -> tuple[int, int, int]:
    """Accept a CSS colour name, ``#RRGGBB``/``#RGB``, or ``rgb(r,g,b)``."""

    if not isinstance(colour, str) or not colour.strip():
        raise ColourError("colour must be a non-empty CSS name, hex value, or rgb() value")
    value = colour.strip().lower()
    rgb_match = _RGB_FUNCTION.fullmatch(value)
    if rgb_match is not None:
        channels = tuple(int(channel) for channel in rgb_match.groups())
        if any(channel > 255 for channel in channels):
            raise ColourError("rgb() channels must each be from 0 through 255")
        return channels
    try:
        if value.startswith("#"):
            converted = webcolors.hex_to_rgb(value)
        else:
            converted = webcolors.name_to_rgb(value, spec="css3")
    except ValueError as error:
        raise ColourError(
            "colour must be a CSS3 name, #RRGGBB/#RGB value, or rgb(r,g,b)"
        ) from error
    return (converted.red, converted.green, converted.blue)
