from talon import Module, app, cron, settings, ui
from talon.canvas import Canvas
from talon.skia.canvas import Canvas as SkiaCanvas
from talon.skia.imagefilter import ImageFilter
from talon.types import Rect

mod = Module()

mod.setting(
    "flash_text_size",
    int,
    default=80,
    desc="Font size for flash text in pixels",
)
mod.setting(
    "flash_text_color",
    str,
    default="ffffff",
    desc="Flash text color (hex without #)",
)
mod.setting(
    "flash_text_color_outline",
    str,
    default="000000",
    desc="Flash text outline color (hex without #)",
)
mod.setting(
    "flash_text_max_width",
    float,
    default=0.9,
    desc="Maximum width as a fraction of the screen before shrinking text",
)
mod.setting(
    "flash_text_timeout_per_char",
    int,
    default=50,
    desc="Extra ms to show for each character",
)
mod.setting(
    "flash_text_timeout_min",
    int,
    default=900,
    desc="Minimum display time in ms",
)
mod.setting(
    "flash_text_timeout_max",
    int,
    default=2500,
    desc="Maximum display time in ms",
)
mod.setting(
    "flash_text_y",
    float,
    default=0.85,
    desc="Vertical position as a fraction of screen height (0=top, 1=bottom)",
)

_canvases: list[Canvas] = []
_close_job = None


def _setting(name: str):
    return settings.get(f"user.flash_text_{name}")


def _calculate_timeout(text: str) -> int:
    ms_per_char = _setting("timeout_per_char")
    ms_min = _setting("timeout_min")
    ms_max = _setting("timeout_max")
    return min(ms_max, max(ms_min, len(text) * ms_per_char))


def _set_text_size_and_get_rect(c: SkiaCanvas, size: int, text: str) -> Rect:
    while True:
        c.paint.textsize = size
        rect = c.paint.measure_text(text)[1]
        if rect.width < c.width * _setting("max_width"):
            return rect
        size *= 0.9


def _close_canvas(canvas: Canvas):
    if canvas in _canvases:
        canvas.close()
        _canvases.remove(canvas)


def _on_draw(c: SkiaCanvas, screen: ui.Screen, text: str):
    scale = screen.scale if app.platform != "mac" else 1
    size = _setting("size") * scale
    rect = _set_text_size_and_get_rect(c, size, text)
    x = c.rect.center.x - rect.center.x
    y = max(
        min(
            c.rect.y + _setting("y") * c.rect.height + c.paint.textsize / 2,
            c.rect.bot - rect.bot,
        ),
        c.rect.top - rect.top,
    )

    c.paint.imagefilter = ImageFilter.drop_shadow(0, 2, 2, 2, "000000")
    c.paint.style = c.paint.Style.FILL
    c.paint.color = _setting("color")
    c.draw_text(text, x, y)

    c.paint.imagefilter = None
    c.paint.style = c.paint.Style.STROKE
    c.paint.color = _setting("color_outline")
    c.draw_text(text, x, y)


def _show_text(text: str):
    global _close_job
    if not text:
        return
    if _close_job:
        cron.cancel(_close_job)
        _close_job = None
    if _canvases:
        _close_canvas(_canvases[-1])
    screen = ui.main_screen()
    if not screen:
        return
    canvas = Canvas.from_screen(screen)
    canvas.register("draw", lambda c: _on_draw(c, screen, text))
    canvas.freeze()
    _canvases.append(canvas)
    _close_job = cron.after(
        f"{_calculate_timeout(text)}ms", lambda: _close_canvas(canvas)
    )


@mod.action_class
class Actions:
    def flash_text(text: str):
        """Show temporary on-screen text similar to Talon subtitles."""
        _show_text(text)
