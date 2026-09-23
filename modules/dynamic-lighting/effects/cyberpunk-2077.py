import math
import random
from _runner import EffectRunner, lerp, hex_color

runner = EffectRunner("Cyberpunk 2077")

# Night City / Cyberpunk 2077 HUD palette
CP_BLACK = (6, 4, 10)
CP_YELLOW = (252, 238, 10)   # signature CP2077 yellow
CP_CYAN = (0, 232, 255)
CP_MAGENTA = (255, 0, 144)
CP_WHITE = (255, 255, 255)

GLITCH_PERIOD = 3.2   # seconds between glitch bursts
GLITCH_LEN = 0.22     # burst duration in seconds


def render_frame(device, t):
    if device.is_mouse or device.is_headset or device.is_strip:
        # Ambient accessories: slow neon color cycle between cyan/magenta/yellow
        cycle = (t * 0.25) % 3.0
        if cycle < 1.0:
            color = lerp(CP_CYAN, CP_MAGENTA, cycle)
        elif cycle < 2.0:
            color = lerp(CP_MAGENTA, CP_YELLOW, cycle - 1.0)
        else:
            color = lerp(CP_YELLOW, CP_CYAN, cycle - 2.0)
        return {str(lamp["idx"]): hex_color(*[int(c) for c in color]) for lamp in device.lamps}

    cycle_pos = t % GLITCH_PERIOD
    glitching = cycle_pos < GLITCH_LEN

    colors = {}
    if glitching:
        # Digital-corruption burst: fast-changing seed per frame during the glitch
        rng = random.Random(int(t * 40))
        for lamp in device.lamps:
            # Horizontal "tearing" stripes of random width
            stripe = int(lamp["y"] * 6) + int(t * 40)
            if rng.random() < 0.45:
                pick = rng.choice([CP_CYAN, CP_MAGENTA, CP_WHITE])
                color = pick
            elif stripe % 3 == 0:
                color = CP_YELLOW
            else:
                color = CP_BLACK
            colors[str(lamp["idx"])] = hex_color(*[int(c) for c in color])
        return colors

    # Normal state: a yellow neon scanline sweeps top-to-bottom over a black HUD,
    # with a cyan/magenta edge glow trailing behind it.
    scan_y = (t * 0.4) % 1.2 - 0.1  # sweep slightly past both edges
    for lamp in device.lamps:
        x, y = lamp["x"], lamp["y"]
        dist = abs(y - scan_y)

        if dist < 0.05:
            color = CP_YELLOW
        elif dist < 0.18:
            glow = 1.0 - (dist - 0.05) / 0.13
            edge = CP_CYAN if (int(x * 10) % 2 == 0) else CP_MAGENTA
            color = lerp(CP_BLACK, edge, glow * 0.7)
        else:
            # Faint circuit-like background flicker
            flicker = (math.sin(x * 30 + t * 2) * math.sin(y * 20 - t * 1.5) + 1) * 0.5
            color = lerp(CP_BLACK, (20, 15, 30), flicker * 0.5)

        colors[str(lamp["idx"])] = hex_color(*[int(c) for c in color])
    return colors


runner.run(render_frame, fps=10)
