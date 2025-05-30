import uasyncio as asyncio
import time

# Default fade duration in milliseconds
DEFAULT_FADE_DURATION_MS = 500
# Number of steps for the fade/wipe effect
EFFECT_STEPS = 20
# Default wipe duration
DEFAULT_WIPE_DURATION_MS = 400

async def _fade(screen_manager, start_brightness, end_brightness, duration_ms):
    """Helper function to fade backlight."""
    delta = (end_brightness - start_brightness) / EFFECT_STEPS
    step_delay = duration_ms // EFFECT_STEPS

    current_brightness = start_brightness
    for _ in range(EFFECT_STEPS):
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
    try:
        # Ensure backlight is fully on before starting fade out
        screen_manager.display.set_backlight(1.0)
        await asyncio.sleep_ms(20) # Small delay to ensure it takes effect
        # Fade from 1.0 to 0.0
        await _fade(screen_manager, 1.0, 0.0, duration_ms)
        print("[Transition] Fade out complete.")
    except Exception as e:
        print(f"[Transition] Error during fade out: {e}")
        # Ensure backlight is off in case of error during fade
        screen_manager.display.set_backlight(0.0)


async def fade_in(screen_manager, duration_ms=DEFAULT_FADE_DURATION_MS):
    """Fade the screen backlight in (from black)."""
    print("[Transition] Fading in...")
    try:
        # Ensure screen starts black before fading in
        screen_manager.display.set_backlight(0.0)
        await asyncio.sleep_ms(50) # Small delay to ensure backlight is off
        await _fade(screen_manager, 0.0, 1.0, duration_ms)
        print("[Transition] Fade in complete.")
    except Exception as e:
        print(f"[Transition] Error during fade in: {e}")
        # Ensure backlight is on in case of error during fade
        screen_manager.display.set_backlight(1.0)


async def wipe_out_to_black_ltr(screen_manager, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the current screen content out to black, left to right."""
    print("[Transition] Wiping out LTR...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"]) # Use background color

        for i in range(EFFECT_STEPS + 1):
            current_width = (width * i) // EFFECT_STEPS
            display.set_pen(black_pen)
            display.rectangle(0, 0, current_width, height)
            display.update()
            await asyncio.sleep_ms(step_delay)
        print("[Transition] Wipe out LTR complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe out LTR: {e}")
        # Ensure screen is black in case of error
        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()


async def wipe_in_from_black_ltr(screen_manager, applet_to_draw, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the new applet content in over black, left to right."""
    print("[Transition] Wiping in LTR...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        # Start with a black screen
        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()
        await asyncio.sleep_ms(50) # Short delay

        # Store original clip if available, otherwise assume full screen
        original_clip = None
        # Note: PicoGraphics doesn't seem to have get_clip(), manage manually if needed
        # For now, we assume we always reset to full screen clip later

        for i in range(1, EFFECT_STEPS + 1):
            current_width = (width * i) // EFFECT_STEPS
            # Set clipping region to the area to be revealed
            display.set_clip(0, 0, current_width, height)

            # Redraw the applet content within the clipped region
            # Important: Clear within the clip first to avoid overdraw artifacts
            display.set_pen(black_pen)
            display.clear() # Clear clipped area
            await applet_to_draw.draw() # Applet draws its content

            display.update() # Update the screen
            await asyncio.sleep_ms(step_delay)

        # Remove clipping region to restore full screen drawing
        display.remove_clip()
        # Final full draw to ensure consistency
        await applet_to_draw.draw()
        display.update()
        print("[Transition] Wipe in LTR complete.")

    except Exception as e:
        print(f"[Transition] Error during wipe in LTR: {e}")
        # Ensure full applet is drawn in case of error
        display.remove_clip() # Ensure clip is removed
        # Perform a final, unclipped draw to ensure the full screen is correct
        await applet_to_draw.draw()
        display.update()
    finally:
        # Ensure clip is always removed, even if errors occurred above
        # Using screen_manager instance as 'display' might not be defined if error happened early
        screen_manager.display.remove_clip()


async def wipe_out_to_black_rtl(screen_manager, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the current screen content out to black, right to left."""
    print("[Transition] Wiping out RTL...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        for i in range(EFFECT_STEPS + 1):
            current_x = width - ((width * i) // EFFECT_STEPS)
            display.set_pen(black_pen)
            display.rectangle(current_x, 0, width - current_x, height) # Draw from right edge inwards
            display.update()
            await asyncio.sleep_ms(step_delay)
        print("[Transition] Wipe out RTL complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe out RTL: {e}")
        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()


async def wipe_in_from_black_rtl(screen_manager, applet_to_draw, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the new applet content in over black, right to left."""
    print("[Transition] Wiping in RTL...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()
        await asyncio.sleep_ms(50)

        for i in range(1, EFFECT_STEPS + 1):
            current_width = (width * i) // EFFECT_STEPS
            current_x = width - current_width
            display.set_clip(current_x, 0, current_width, height) # Clip from right edge inwards

            display.set_pen(black_pen)
            display.clear()
            await applet_to_draw.draw()

            display.update()
            await asyncio.sleep_ms(step_delay)

        display.remove_clip()
        await applet_to_draw.draw()
        display.update()
        print("[Transition] Wipe in RTL complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe in RTL: {e}")
        display.remove_clip()
        await applet_to_draw.draw()
        display.update()
    finally:
        screen_manager.display.remove_clip()


async def wipe_out_to_black_ttb(screen_manager, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the current screen content out to black, top to bottom."""
    print("[Transition] Wiping out TTB...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        for i in range(EFFECT_STEPS + 1):
            current_height = (height * i) // EFFECT_STEPS
            display.set_pen(black_pen)
            display.rectangle(0, 0, width, current_height) # Draw from top edge downwards
            display.update()
            await asyncio.sleep_ms(step_delay)
        print("[Transition] Wipe out TTB complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe out TTB: {e}")
        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()


async def wipe_in_from_black_ttb(screen_manager, applet_to_draw, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the new applet content in over black, top to bottom."""
    print("[Transition] Wiping in TTB...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()
        await asyncio.sleep_ms(50)

        for i in range(1, EFFECT_STEPS + 1):
            current_height = (height * i) // EFFECT_STEPS
            display.set_clip(0, 0, width, current_height) # Clip from top edge downwards

            display.set_pen(black_pen)
            display.clear()
            await applet_to_draw.draw()

            display.update()
            await asyncio.sleep_ms(step_delay)

        display.remove_clip()
        await applet_to_draw.draw()
        display.update()
        print("[Transition] Wipe in TTB complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe in TTB: {e}")
        display.remove_clip()
        await applet_to_draw.draw()
        display.update()
    finally:
        screen_manager.display.remove_clip()


async def wipe_out_to_black_btt(screen_manager, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the current screen content out to black, bottom to top."""
    print("[Transition] Wiping out BTT...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        for i in range(EFFECT_STEPS + 1):
            current_height = (height * i) // EFFECT_STEPS
            current_y = height - current_height
            display.set_pen(black_pen)
            display.rectangle(0, current_y, width, current_height) # Draw from bottom edge upwards
            display.update()
            await asyncio.sleep_ms(step_delay)
        print("[Transition] Wipe out BTT complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe out BTT: {e}")
        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()


async def wipe_in_from_black_btt(screen_manager, applet_to_draw, duration_ms=DEFAULT_WIPE_DURATION_MS):
    """Wipe the new applet content in over black, bottom to top."""
    print("[Transition] Wiping in BTT...")
    try:
        display = screen_manager.display
        width, height = display.get_bounds()
        step_delay = duration_ms // EFFECT_STEPS
        black_pen = screen_manager.get_pen(screen_manager.theme["BACKGROUND_COLOR"])

        display.set_pen(black_pen)
        display.rectangle(0, 0, width, height)
        display.update()
        await asyncio.sleep_ms(50)

        for i in range(1, EFFECT_STEPS + 1):
            current_height = (height * i) // EFFECT_STEPS
            current_y = height - current_height
            display.set_clip(0, current_y, width, current_height) # Clip from bottom edge upwards

            display.set_pen(black_pen)
            display.clear()
            await applet_to_draw.draw()

            display.update()
            await asyncio.sleep_ms(step_delay)

        display.remove_clip()
        await applet_to_draw.draw()
        display.update()
        print("[Transition] Wipe in BTT complete.")
    except Exception as e:
        print(f"[Transition] Error during wipe in BTT: {e}")
        display.remove_clip()
        await applet_to_draw.draw()
        display.update()
    finally:
        screen_manager.display.remove_clip()


# Dictionary mapping transition names to their functions (or None)
# We store tuples: (exit_transition_func, entry_transition_func)
# Entry transition functions might require the applet instance as the second argument.
TRANSITIONS = {
    "None": (None, None),
    "Fade": (fade_out, fade_in),
    "Wipe Left-To-Right": (wipe_out_to_black_ltr, wipe_in_from_black_ltr),
    "Wipe Right-To-Left": (wipe_out_to_black_rtl, wipe_in_from_black_rtl),
    "Wipe Top-To-Bottom": (wipe_out_to_black_ttb, wipe_in_from_black_ttb),
    "Wipe Bottom-To-Top": (wipe_out_to_black_btt, wipe_in_from_black_btt),
    # Add more transitions here in the future
}

# List of available transition names for the UI, in the desired order
AVAILABLE_TRANSITIONS = [
    "None",
    "Fade",
    "Wipe Left-To-Right",
    "Wipe Right-To-Left",
    "Wipe Top-To-Bottom",
    "Wipe Bottom-To-Top",
]
