# Linux support

User intent: FCU_CLOCK must work on this Arch/KDE Wayland computer and be installable by other GitHub users. The user delegated implementation choices and declined a design approval discussion.

Keep one Python project, shared HID protocol/mappings/weather, and the existing Windows action and volume implementations unchanged. Select a Linux backend at runtime. Use evdev/uinput for keys and scrolling on Wayland and X11, pactl for PulseAudio/PipeWire volume, kdotool for active KDE windows and xdotool for X11. Resolve descendant processes for browser audio. Fall back to default output volume when foreground identification or matching streams is unavailable. KDE show-desktop uses D-Bus; other desktops use configurable shortcuts. Unsupported features must fail with actionable messages without killing the clock.

Ship Linux installation instructions, scoped udev permissions, a local launcher, diagnostics, and Windows/Linux CI. No root GUI/application, no publishing or pushing without a request. Test actual HID writes and virtual input creation locally; physical button/visual confirmation requires the user.

Alternatives: a Windows compatibility layer would obscure device permissions; separate forks would duplicate protocol fixes. A platform backend matches the existing architecture and the requested shared project. Other Wayland compositors do not have a universal foreground-process API; document master-volume fallback honestly.
