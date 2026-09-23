import math
from _runner import EffectRunner, lerp, hex_color

runner = EffectRunner("HP Symbol Breathe")

HP_BLUE = (0, 150, 214)      # #0096D6 - classic HP blue
HP_SILVER = (225, 235, 240)  # highlight at peak brightness
BG_COLOR = (4, 9, 18)        # dim, nearly-static navy background for contrast

BREATHE_PERIOD = 3.5  # seconds per full breathe cycle

# Actual keyboard rows sit at y ~= 0, 0.178, 0.389, 0.589, 0.8, 1.0.
# Strokes are kept thin (a single row/column band each) and separated by a
# clear gap between the two letters so they read as distinct "H" "P" shapes
# instead of blurring into a solid block.

H_LEFT_X = (0.0, 0.06)
H_RIGHT_X = (0.24, 0.30)
H_BAR_Y = (0.33, 0.45)          # crossbar: single middle row only

P_VERT_X = (0.42, 0.48)
P_TOP_Y = (0.0, 0.05)           # bowl top: single top row only
P_BOWL_RIGHT_X = (0.62, 0.68)
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

    colors = {}
    for lamp in device.lamps:
        if device.is_mouse or device.is_headset or device.is_strip:
            # Ambient accessories just breathe HP blue softly
            color = lerp(BG_COLOR, HP_BLUE, 0.3 + 0.7 * breathe)
        else:
            x, y = lamp["x"] - CENTER_OFFSET_X, lamp["y"]
            color = lit if (in_h(x, y) or in_p(x, y)) else bg
        colors[str(lamp["idx"])] = hex_color(*[int(c) for c in color])
    return colors


runner.run(render_frame, fps=8)
