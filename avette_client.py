"""macOS modifier events for Avette's Fn dictation shortcut."""

import ctypes


_cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
_cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
_cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
_cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
_cg.CGEventSetType.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_cg.CGEventSetType.restype = None
_cg.CGEventSetFlags.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
_cg.CGEventSetFlags.restype = None
_cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
_cg.CGEventPost.restype = None
_cf.CFRelease.argtypes = [ctypes.c_void_p]
_cf.CFRelease.restype = None


def dictation_key(down: bool) -> None:
    """Post a modifier transition, rather than an ordinary key-down/up event."""
    event = _cg.CGEventCreateKeyboardEvent(None, 63, down)
    if not event:
        raise RuntimeError("Could not create Fn event")
    try:
        # kCGEventFlagsChanged; kCGEventFlagMaskSecondaryFn on press.
        _cg.CGEventSetType(event, 12)
        _cg.CGEventSetFlags(event, 0x800000 if down else 0)
        _cg.CGEventPost(0, event)  # kCGHIDEventTap
    finally:
        _cf.CFRelease(event)
