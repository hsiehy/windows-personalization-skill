import math
from _runner import EffectRunner, lerp, hex_color

runner = EffectRunner("HP Symbol Breathe")

HP_BLUE = (0, 150, 214)      # #0096D6 - classic HP blue
HP_SILVER = (225, 235, 240)  # highlight at peak brightness
BG_COLOR = (4, 9, 18)        # dim, nearly-static navy background for contrast

BREATHE_PERIOD = 3.5  # seconds per full breathe cycle

# Coordinate-window matching (below) is fragile: on a real staggered keyboard
# grid, a window can miss a row entirely (gap) or catch two lamps in one row
# (kink). For this specific 120-lamp OMEN keyboard we instead hardcode the
# exact lamp indices for each stroke, picked directly from the device's
# reported lamp table, so every stroke is a single, continuous, straight
# column/row with no gaps or doubled lamps. Any other keyboard (different
# lamp count) falls back to the old ratio/window-based approximation.

KNOWN_KEYBOARD_LAMP_COUNT = 120

# Row 0 (F-keys): 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19
# Row 1 (numbers): 20..39   Row 2 (QWERTY): 40..59
# Row 3 (ASDF): 60..79      Row 4 (ZXCV): 80..99   Row 5 (bottom/space): 100..119
# Strokes stop at row 4 (ZXCV) rather than reaching into row 5: row 5 is almost
# entirely the wide spacebar + Alt/Copilot keys, so lighting only 1-2 lamps
# there looks like stray dots on a single keycap and risks bleeding light into
# neighboring special keys (Alt, Copilot) instead of reading as a stroke.
H_LEFT_IDX = {4, 24, 45, 65, 84}
H_RIGHT_IDX = {8, 28, 49, 69, 88}
H_BAR_IDX = {45, 46, 47, 48, 49}            # crossbar, row 2 only, bridges left->right

P_VERT_IDX = {11, 31, 52, 72, 91}
P_TOP_IDX = {11, 12, 13, 14, 15}            # bowl top, row 0 only, bridges vert->bowl-right
P_BOWL_RIGHT_IDX = {15, 35, 55}             # upper 3 rows only (bowl stays in top third)
P_MID_IDX = {52, 53, 54, 55}                # bowl bottom, row 2 only, bridges vert->bowl-right

HP_IDX = H_LEFT_IDX | H_RIGHT_IDX | H_BAR_IDX | P_VERT_IDX | P_TOP_IDX | P_BOWL_RIGHT_IDX | P_MID_IDX

# --- Fallback (ratio-based) for keyboards with a different lamp layout ---
H_LEFT_X = (0.0, 0.06)
H_RIGHT_X = (0.24, 0.30)
H_BAR_Y = (0.33, 0.45)          # crossbar: single middle row only

P_VERT_X = (0.415, 0.47)
P_TOP_Y = (0.0, 0.05)           # bowl top: single top row only
P_BOWL_RIGHT_X = (0.605, 0.66)
P_BOWL_RIGHT_Y = (0.0, 0.40)    # bowl right side: upper rows only (not full height)
P_MID_Y = (0.33, 0.45)          # bowl bottom: closes the loop, same row as H's bar

# The "HP" glyph spans x = 0.0..0.68 in its own local coordinates; shift it
# right so it's centered on the keyboard (local width 0.68 -> center offset).
GLYPH_WIDTH = P_BOWL_RIGHT_X[1]
CENTER_OFFSET_X = (1.0 - GLYPH_WIDTH) / 2.0


def in_h(x, y):
    """Left/right vertical strokes + a single-row horizontal crossbar."""
    if H_LEFT_X[0] <= x <= H_LEFT_X[1]:
        return True
    if H_RIGHT_X[0] <= x <= H_RIGHT_X[1]:
        return True
    if H_BAR_Y[0] <= y <= H_BAR_Y[1] and H_LEFT_X[0] <= x <= H_RIGHT_X[1]:
        return True
    return False


def in_p(x, y):
    """Vertical stroke + a thin closed bowl in the upper third."""
    if P_VERT_X[0] <= x <= P_VERT_X[1]:
        return True
    if P_TOP_Y[0] <= y <= P_TOP_Y[1] and P_VERT_X[0] <= x <= P_BOWL_RIGHT_X[1]:
        return True
    if P_BOWL_RIGHT_Y[0] <= y <= P_BOWL_RIGHT_Y[1] and P_BOWL_RIGHT_X[0] <= x <= P_BOWL_RIGHT_X[1]:
        return True
    if P_MID_Y[0] <= y <= P_MID_Y[1] and P_VERT_X[0] <= x <= P_BOWL_RIGHT_X[1]:
        return True
    return False


def render_frame(device, t):
    phase = (t % BREATHE_PERIOD) / BREATHE_PERIOD
    breathe = (1 - math.cos(phase * math.tau)) * 0.5  # smooth 0..1 ease

    # Letters stay bright and readable at all times; only their color shifts
    # from blue toward silver at the peak. Background stays dim and mostly
    # static so it never competes with the letters for attention.
    level = 0.55 + 0.45 * breathe
    if breathe < 0.85:
        glow = HP_BLUE
    else:
        glow = lerp(HP_BLUE, HP_SILVER, (breathe - 0.85) / 0.15)
    lit = tuple(c * level for c in glow)
    bg = lerp(BG_COLOR, tuple(c * 0.6 for c in BG_COLOR), breathe)

    use_exact_idx = (
        not device.is_mouse and not device.is_headset and not device.is_strip
        and len(device.lamps) == KNOWN_KEYBOARD_LAMP_COUNT
    )

    colors = {}
    for lamp in device.lamps:
        if device.is_mouse or device.is_headset or device.is_strip:
            # Ambient accessories just breathe HP blue softly
            color = lerp(BG_COLOR, HP_BLUE, 0.3 + 0.7 * breathe)
        elif use_exact_idx:
            color = lit if lamp["idx"] in HP_IDX else bg
        else:
            x, y = lamp["x"] - CENTER_OFFSET_X, lamp["y"]
            color = lit if (in_h(x, y) or in_p(x, y)) else bg
        colors[str(lamp["idx"])] = hex_color(*[int(c) for c in color])
    return colors


runner.run(render_frame, fps=8)
