import uasyncio as asyncio
import time

# Default fade duration in milliseconds
DEFAULT_FADE_DURATION_MS = 500
# Number of steps for the fade effect
FADE_STEPS = 20

async def _fade(screen_manager, start_brightness, end_brightness, duration_ms):
    """Helper function to fade backlight."""
    delta = (end_brightness - start_brightness) / FADE_STEPS
    step_delay = duration_ms // FADE_STEPS

    current_brightness = start_brightness
    for _ in range(FADE_STEPS):
        current_brightness += delta
        # Clamp brightness between 0.0 and 1.0
        clamped_brightness = max(0.0, min(1.0, current_brightness))
        screen_manager.display.set_backlight(clamped_brightness)
        await asyncio.sleep_ms(step_delay)

    # Ensure final brightness is set exactly
    screen_manager.display.set_backlight(end_brightness)

async def fade_out(screen_manager, duration_ms=DEFAULT_FADE_DURATION_MS):
    """Fade the screen backlight out (to black)."""
    print("[Transition] Fading out...")
    current_brightness = screen_manager.display.get_backlight() # Assuming get_backlight() exists or use a default like 1.0
    # Pimoroni library might not have get_backlight, assume it starts at 1.0 if unavailable
    # For now, let's assume it fades from 1.0
    await _fade(screen_manager, 1.0, 0.0, duration_ms)
    print("[Transition] Fade out complete.")


async def fade_in(screen_manager, duration_ms=DEFAULT_FADE_DURATION_MS):
    """Fade the screen backlight in (from black)."""
    print("[Transition] Fading in...")
    # Ensure screen starts black before fading in
    screen_manager.display.set_backlight(0.0)
    await asyncio.sleep_ms(50) # Small delay to ensure backlight is off
    await _fade(screen_manager, 0.0, 1.0, duration_ms)
    print("[Transition] Fade in complete.")


# Dictionary mapping transition names to their functions (or None)
# We store tuples: (exit_transition_func, entry_transition_func)
TRANSITIONS = {
    "None": (None, None),
    "Fade": (fade_out, fade_in),
    # Add more transitions here in the future
}

# List of available transition names for the UI
AVAILABLE_TRANSITIONS = list(TRANSITIONS.keys())
