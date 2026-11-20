"""macOS menu bar status item: recording dot plus running elapsed timer."""
import os
import struct
import sys
import zlib

_LOG_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "lyrro_menubar.log")


def _log(message):
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except Exception:
        pass


def _fmt_short(seconds):
    s = int(max(0, seconds))
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%d:%02d" % (m, s)


def _fmt_long(seconds):
    s = int(max(0, seconds))
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return "%d:%02d:%02d:%02d" % (d, h, m, s)


def _png_rgba(rows, px):
    """Encode rows of (r, g, b, a) tuples or None as an RGBA PNG."""
    raw = bytearray()
    for y in range(px):
        raw.append(0)
        row = rows[y]
        for x in range(px):
            cell = row[x]
            raw.extend(b"\x00\x00\x00\x00" if cell is None else bytes(cell))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", px, px, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


class MenuBarStatus:
    """Shows recording/playback state in the macOS menu bar.

    Does nothing on other platforms or if PyObjC is unavailable, so a
    failure here can never stop the app from starting.
    """

    def __init__(self, main_app):
        self.main_app = main_app
        self.item = None
        self._last = None
        self._ak = None
        self._has_icon = False
        if sys.platform != "darwin":
            return
        try:
            from AppKit import (
                NSColor, NSFont, NSFontAttributeName, NSForegroundColorAttributeName,
                NSMutableAttributedString, NSStatusBar, NSVariableStatusItemLength,
            )
        except Exception:
            return
        self._ak = {
            "NSColor": NSColor, "NSFont": NSFont, "NSFontAttributeName": NSFontAttributeName,
            "NSForegroundColorAttributeName": NSForegroundColorAttributeName,
            "NSMutableAttributedString": NSMutableAttributedString,
        }
        try:
            self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(
                NSVariableStatusItemLength
            )
            if self.item is None:
                return
            self.item.button().setFont_(NSFont.systemFontOfSize_(12))
            self.item.button().setToolTip_("Lyrro's Macro Recorder")
            self._attach_icon()
            self._build_menu()
            _log("created: item=%s button=%s icon=%s" % (self.item is not None, self.item.button() is not None, self._has_icon))
        except Exception as exc:
            self.item = None
            _log("creation failed: %r" % (exc,))

    def _build_menu(self):
        """Clicking the item offers Open Macro / Quit Macro."""
        try:
            from AppKit import NSMenu, NSMenuItem, NSObject
        except Exception as exc:
            _log("menu import failed: %r" % (exc,))
            return
        app = self.main_app

        class _Actions(NSObject):
            def openMacro_(self, sender):
                # Only set a flag: calling Tcl from an AppKit menu action aborted
                # the process (SIGABRT in PyEval_RestoreThread). The Tk loop
                # picks this up on its next dashboard tick.
                try:
                    app._open_requested = True
                except Exception:
                    pass

            def quitMacro_(self, sender):
                # Never re-enter Tcl to quit: Tk delivering an event to Python
                # while the interpreter tears down is what aborted the process
                # ("quit unexpectedly", SIGABRT in PyEval_RestoreThread).
                try:
                    self.remove()
                except Exception:
                    pass
                try:
                    import threading
                    import time as _time

                    def _leave():
                        _time.sleep(0.25)
                        os._exit(0)

                    threading.Thread(target=_leave, daemon=True).start()
                except Exception:
                    pass

        try:
            self._actions = _Actions.alloc().init()
            menu = NSMenu.alloc().init()
            open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Open Macro", "openMacro:", ""
            )
            open_item.setTarget_(self._actions)
            menu.addItem_(open_item)
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit Macro", "quitMacro:", ""
            )
            quit_item.setTarget_(self._actions)
            menu.addItem_(quit_item)
            self.item.setMenu_(menu)
            _log("menu attached")
        except Exception as exc:
            _log("menu failed: %r" % (exc,))

    def remove(self):
        """Take the item out of the menu bar (used on quit)."""
        try:
            if self.item is not None:
                from AppKit import NSStatusBar
                NSStatusBar.systemStatusBar().removeStatusItem_(self.item)
                _log("status item removed")
        except Exception as exc:
            _log("remove failed: %r" % (exc,))
        self.item = None

    def _attach_icon(self):
        """White line-art of the app mark: ring, disc, outlined cursor."""
        try:
            from AppKit import NSApplication, NSImageLeft
            icon = self._white_glyph()
            if icon is None:
                icon = NSApplication.sharedApplication().applicationIconImage()
                if icon is not None:
                    icon.setSize_((17.0, 17.0))
                _log("icon: colour app icon fallback")
            if icon is None:
                _log("no icon available")
                return
            self.item.button().setImage_(icon)
            self.item.button().setImagePosition_(NSImageLeft)
            self._has_icon = True
            _log("icon attached size=%s template=%s" % (icon.size(), bool(icon.isTemplate())))
        except Exception as exc:
            _log("icon failed: %r" % (exc,))

    def _white_glyph(self):
        """Ring around a filled disc, cursor knocked out and outlined.

        Drawn at 64 px with 2x2 supersampling so the edges are smooth at 17 pt.
        The cursor tail runs past the disc, which is where its white outline is
        actually visible; inside the white disc an outline cannot show.
        """
        try:
            from AppKit import NSImage
            from Foundation import NSData
            n = 64
            cx = cy = n / 2.0
            r_disc = 25.5
            r_ring_in = 27.5
            r_ring_out = 30.0
            arrow = [(0.0, 0.0), (0.0, 17.0), (4.0, 13.0), (7.0, 19.0),
                     (10.0, 17.5), (7.0, 12.0), (12.0, 12.0)]
            scale = 2.3
            ox, oy = 26.0, 17.0
            poly = [(ox + px * scale, oy + py * scale) for px, py in arrow]
            edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
            stroke = 1.7

            def inside(px, py):
                hit = False
                for (x1, y1), (x2, y2) in edges:
                    if (y1 > py) != (y2 > py):
                        if px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                            hit = not hit
                return hit

            def near(px, py):
                for (x1, y1), (x2, y2) in edges:
                    dx, dy = x2 - x1, y2 - y1
                    length2 = dx * dx + dy * dy
                    if length2 <= 0:
                        continue
                    t = ((px - x1) * dx + (py - y1) * dy) / length2
                    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                    qx, qy = x1 + t * dx, y1 + t * dy
                    if (px - qx) ** 2 + (py - qy) ** 2 <= stroke * stroke:
                        return True
                return False

            sub = 2
            step = 1.0 / sub
            total = float(sub * sub)
            rows = []
            for y in range(n):
                row = []
                for x in range(n):
                    hits = 0
                    for sy in range(sub):
                        py = y + (sy + 0.5) * step
                        for sx in range(sub):
                            px = x + (sx + 0.5) * step
                            if inside(px, py):
                                continue
                            d2 = (px - cx) ** 2 + (py - cy) ** 2
                            if d2 <= r_disc * r_disc:
                                hits += 1
                            elif r_ring_in * r_ring_in <= d2 <= r_ring_out * r_ring_out:
                                hits += 1
                            elif near(px, py):
                                hits += 1
                    if hits:
                        row.append((255, 255, 255, int(round(255.0 * hits / total))))
                    else:
                        row.append(None)
                rows.append(row)
            payload = _png_rgba(rows, n)
            data = NSData.dataWithBytes_length_(payload, len(payload))
            image = NSImage.alloc().initWithData_(data)
            if image is None:
                _log("glyph: image from PNG failed")
                return None
            image.setTemplate_(True)
            image.setSize_((17.5, 17.5))
            _log("glyph: white png %d bytes" % len(payload))
            return image
        except Exception as exc:
            _log("glyph build failed: %r" % (exc,))
            return None

    @staticmethod
    def _fmt_hotkey(keys):
        if not keys:
            return ""
        try:
            from utils.key_names import format_key_name
        except Exception:
            def format_key_name(value):
                return str(value).replace("Key.", "")
        parts = []
        for key in keys:
            name = format_key_name(key)
            if not name:
                continue
            parts.append(name.upper() if len(name) == 1 else name)
        return "+".join(parts)

    def _hotkey_label(self, start_name, stop_name):
        try:
            hotkeys = self.main_app.settings.settings_dict.get("Hotkeys", {}) or {}
        except Exception:
            return ""
        start = self._fmt_hotkey(hotkeys.get(start_name))
        stop = self._fmt_hotkey(hotkeys.get(stop_name))
        if start and stop and start == stop:
            return start
        if start and stop:
            return "%s / %s" % (start, stop)
        return start or stop or ""

    def update(self, recording, counting, countdown_left, playing, rec_elapsed, play_elapsed):
        if self.item is None:
            return
        cfg = self.main_app.settings.settings_dict.get("Menu_Bar", {})
        if not cfg.get("Show_Status", True):
            text, dot, dot_red = "", False, False
        elif counting:
            text, dot, dot_red = "%ds" % int(max(0, countdown_left)), True, True
        elif recording:
            text, dot, dot_red = _fmt_short(rec_elapsed), True, True
        elif playing:
            label = self._hotkey_label("Playback_Start", "Playback_Stop")
            if cfg.get("Show_Playback_Timer", False):
                text = _fmt_long(play_elapsed) + (("   " + label) if label else "")
            else:
                text = label or "Playing"
            dot, dot_red = True, False
        else:
            text, dot, dot_red = "", False, False
        if text == self._last:
            return
        self._last = text
        _log("title=%r recording=%s playing=%s" % (text, recording, playing))
        try:
            button = self.item.button()
            if not text:
                title = ""
            elif self._has_icon:
                # The glyph carries recording/playback; the text is the timer.
                title = text
            elif playing and not recording:
                title = "\u25B6 " + text
            elif dot or dot_red:
                title = "\u25CF " + text
            else:
                title = text
            button.setTitle_(title)
            # Variable length: macOS sizes the item to its content, exactly like
            # every other menu bar extra, instead of a hand-computed width.
            try:
                from AppKit import NSVariableStatusItemLength
                if not title and self._has_icon:
                    # Icon only: trim the slot to the artwork plus a small pad,
                    # which is tighter than AppKit's variable-length padding.
                    width = float(self.item.button().image().size().width)
                    self.item.setLength_(width + 6.0)
                else:
                    self.item.setLength_(NSVariableStatusItemLength)
            except Exception as length_exc:
                _log("setLength failed: %r" % (length_exc,))
            _log("drew title=%r length=%s" % (title, self.item.length()))
        except Exception as exc:
            _log("setTitle failed: %r" % (exc,))
            try:
                self.item.button().setTitle_(text)
            except Exception:
                pass
