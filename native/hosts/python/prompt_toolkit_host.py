#!/usr/bin/env python3
"""One-terminal-owner prompt_toolkit host for the current native SDK.

Only presentation, input translation and a monotonic host clock live here. Scene
semantics always execute in the C core. Ctrl-Q exits; F2 holds presentation time;
F4 selects the next composition; F1 and F6 go to native help and document recovery.
Shift movement selects; Alt-W copies, Ctrl-W cuts and Ctrl-Y pastes through the
framework clipboard buffer.
"""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import Frame, NativeScene
from document_store import load_document, save_document
from unicode_document_view import UnicodeDocumentView
from shortcut_profile import ShortcutProfile, parse_reservations
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.data_structures import Point
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, Window, HSplit
from prompt_toolkit.layout.controls import UIContent, UIControl, FormattedTextControl
from prompt_toolkit.mouse_events import MouseButton, MouseEvent, MouseEventType
from prompt_toolkit.utils import get_cwidth


def cell_symbol(glyph: int) -> str:
    """This ABI is a scalar-cell profile, not a general shaping engine.

    A host-unsupported width must not move following cells. The original scalar
    remains in canonical cells and complete source metadata for accessible export.
    """
    char = chr(glyph) if 32 <= glyph <= 0x10ffff and not 0xd800 <= glyph <= 0xdfff else ' '
    return char if get_cwidth(char) == 1 else '\ufffd'


def frame_lines(frame: Frame) -> list[list[tuple[str, str]]]:
    """Convert owned cells to framework fragments; never mutate the native frame."""
    words = frame.words()
    result = []
    for row in range(frame.height):
        fragments: list[tuple[str, str]] = []
        for glyph, foreground, background, _ in words[row * frame.width:(row + 1) * frame.width]:
            style = f'fg:#{foreground:06x} bg:#{background:06x}'
            symbol = cell_symbol(glyph)
            if fragments and fragments[-1][0] == style:
                fragments[-1] = (style, fragments[-1][1] + symbol)
            else:
                fragments.append((style, symbol))
        result.append(fragments)
    return result


class NativeControl(UIControl):
    """Copy current cells into a framework-owned control and translate input."""
    def __init__(self, scene: NativeScene):
        self.scene = scene
        self.unicode_view = None
        self.viewport: tuple[int, int] | None = None
        self._last: bytes | None = None
        self._lines: list[list[tuple[str, str]]] = []

    def is_focusable(self) -> bool:
        return True

    def create_content(self, width: int, height: int) -> UIContent:
        if width < 1 or height < 1:
            return UIContent(get_line=lambda i: [], line_count=0, show_cursor=False)
        viewport = (width, height)
        if viewport != self.viewport:
            self.scene.command({'op': 'resize', 'width': viewport[0], 'height': viewport[1]})
            self.viewport = viewport
            self._last = None
        if self.unicode_view and self.unicode_view.state(self.scene) is not None:
            return UIContent(get_line=lambda i: [('', ' '*width)],line_count=height,show_cursor=False)
        frame = self.scene.render()
        if frame.bytes != self._last:
            self._lines = frame_lines(frame)
            self._last = frame.bytes
        return UIContent(get_line=lambda i: self._lines[i] if i < len(self._lines) else [],
                         line_count=frame.height, show_cursor=False)

    def mouse_handler(self, event: MouseEvent):
        x, y = event.position.x, event.position.y
        modifiers = {getattr(m, 'value', str(m)).lower() for m in event.modifiers}
        if self.unicode_view:
            if event.event_type in (MouseEventType.SCROLL_UP,MouseEventType.SCROLL_DOWN):
                if self.unicode_view.scroll_by(self.scene,-3 if event.event_type==MouseEventType.SCROLL_UP else 3):return None
            else:
                phase={MouseEventType.MOUSE_DOWN:'down',MouseEventType.MOUSE_UP:'up',MouseEventType.MOUSE_MOVE:'move'}.get(event.event_type)
                if phase and self.unicode_view.pointer(self.scene,phase,x,y,'shift' in modifiers):return None

        if event.event_type in (MouseEventType.SCROLL_UP, MouseEventType.SCROLL_DOWN):
            self.scene.command({'op': 'wheel', 'x': x, 'y': y,
                                'delta': 1 if event.event_type == MouseEventType.SCROLL_UP else -1,
                                'shift': 'shift' in modifiers})
        else:
            phase = {MouseEventType.MOUSE_DOWN: 'down', MouseEventType.MOUSE_UP: 'up',
                     MouseEventType.MOUSE_MOVE: 'move'}.get(event.event_type)
            if phase is None:
                return NotImplemented
            button = {MouseButton.LEFT: 0, MouseButton.MIDDLE: 1, MouseButton.RIGHT: 2}.get(event.button, 0)
            self.scene.command({'op': 'pointer', 'phase': phase, 'x': x, 'y': y,
                                'button': button, 'shift': 'shift' in modifiers, 'alt': 'alt' in modifiers})
        return None


class UnicodeDocumentWindow(Window):
    """Copy native cluster geometry into framework-owned screen cells."""
    def write_to_screen(self,screen,mouse_handlers,write_position,parent_style,erase_bg,z_index):
        super().write_to_screen(screen,mouse_handlers,write_position,parent_style,erase_bg,z_index)
        control=self.content
        if control.unicode_view is None:return
        view=control.unicode_view.presentation(control.scene,write_position.width,write_position.height)
        if view is None:return
        left,top=write_position.xpos,write_position.ypos
        background='fg:#e4dacc bg:#0b121b'
        for y in range(write_position.height):
            for x in range(write_position.width):screen.data_buffer[top+y][left+x]=Char(' ',background)
        for x,char in enumerate(view['title']):screen.data_buffer[top][left+x]=Char(char,background)
        for x,y,width,cluster,bg in view['cells']:
            rgb=tuple(map(int,bg.split(';')));style=f'fg:#e4dacc bg:#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
            cell=Char(cluster,style);cell.width=width
            screen.data_buffer[top+y][left+x]=cell
            for column in range(1,width):screen.data_buffer[top+y][left+x+column]=Char('',style)
        screen.show_cursor=view['cursor'] is not None
        if view['cursor']:
            x,y=view['cursor'];screen.set_cursor_position(self,Point(left+x,top+y))


class FrameworkHost:
    def __init__(self, scene_name: str = 'autumn', fps: int = 60, seed: int = 2030,
                 reduced_motion: bool = False, *, input=None, output=None, unicode_document=False, reserved_shortcuts=()):
        if not 1 <= fps <= 120:
            raise ValueError('fps must be 1..120')
        self.scene = NativeScene(seed)
        self.seed, self.fps, self.reduced_motion = seed, fps, reduced_motion
        self.recipes = json.loads((ROOT / 'recipes.json').read_text())
        if not any(recipe['id'] == scene_name for recipe in self.recipes):
            raise ValueError('Unknown scene: ' + scene_name)
        self.current = 0
        self.held = False
        self.logical_us = 0.0
        self.wall = time.monotonic_ns()
        self.control = NativeControl(self.scene)
        if unicode_document:self.control.unicode_view=UnicodeDocumentView()
        self.load(scene_name)
        keys = KeyBindings()

        try:self.shortcut_profile = ShortcutProfile(self.scene,reserved_shortcuts)
        except Exception:
            self.scene.close();raise
        # Framework key registrations and visible hints share the exact native
        # assignment. Reserved and unassigned chords never receive a handler.
        for action,tokens in self.shortcut_profile.bindings:
            def managed_shortcut(event,action=action):
                self.shortcut_action(action,event)
            keys.add(*tokens)(managed_shortcut)

        @keys.add('c-c')
        def emergency_exit(event):
            event.app.exit()

        mapping = {'up': 'ArrowUp', 'down': 'ArrowDown', 'left': 'ArrowLeft', 'right': 'ArrowRight',
                   'home': 'Home', 'end': 'End', 'backspace': 'Backspace', 'delete': 'Delete',
                   'escape': 'Escape', 'pageup': 'PageUp', 'pagedown': 'PageDown'}
        for key, native in mapping.items():
            def translated(event, native=native):
                if not (self.control.unicode_view and self.control.unicode_view.move(self.scene,native)):self.scene.command({'op': 'key', 'key': native,'unit':'grapheme' if self.control.unicode_view else 'scalar'})
                event.app.invalidate()
            keys.add(key)(translated)
        for key, native in {'s-left':'ArrowLeft','s-right':'ArrowRight','s-up':'ArrowUp','s-down':'ArrowDown','s-home':'Home','s-end':'End'}.items():
            def selection_key(event,native=native):
                if not (self.control.unicode_view and self.control.unicode_view.move(self.scene,native,True)):self.scene.command({'op':'key','key':native,'shift':True})
                event.app.invalidate()
            keys.add(key)(selection_key)
        for letter in ('a', 'e', 'z'):
            def control_key(event, letter=letter):
                self.scene.command({'op': 'key', 'key': letter, 'ctrl': True})
                event.app.invalidate()
            keys.add('c-' + letter)(control_key)

        @keys.add('enter')
        def newline(event):
            self.scene.command({'op': 'key', 'key': 'Enter'})
            event.app.invalidate()

        # prompt_toolkit 3.0.52 emits unregistered CSI focus reports as these
        # ordinary keys. Register the complete sequence before <any> dispatch so
        # a focus notification cannot become document text or retain a drag.
        @keys.add('escape', '[', 'O')
        def focus_lost(event):
            if self.control.unicode_view:self.control.unicode_view.cancel_drag()
            self.scene.command({'op': 'pointer', 'phase': 'cancel', 'x': -1, 'y': -1})
            event.app.invalidate()

        @keys.add('escape', '[', 'I')
        def focus_gained(event):
            event.app.invalidate()

        @keys.add('tab')
        def tab(event):
            for _ in range(4):
                self.scene.command({'op': 'key', 'key': ' '})
            event.app.invalidate()

        @keys.add('<bracketed-paste>')
        def paste(event):
            self.scene.command({'op': 'paste', 'text': event.data})
            event.app.invalidate()

        @keys.add('<any>')
        def text(event):
            if event.data and all(ord(c) >= 32 for c in event.data):
                # Route normal keys through native Vim-style and modal ownership.
                self.scene.command({'op': 'key', 'key': event.data})
                event.app.invalidate()

        self.document_window=UnicodeDocumentWindow(self.control,wrap_lines=False)
        self.shortcut_toolbar=Window(FormattedTextControl(lambda:self.shortcut_profile.hints),height=1)
        self.application = Application(layout=Layout(HSplit([self.document_window,self.shortcut_toolbar])),
                                       key_bindings=keys, full_screen=True, mouse_support=True,
                                       min_redraw_interval=0, input=input, output=output)

    def shortcut_action(self,action,event):
        if action==1:event.app.exit();return
        if action==2:
            self.held=not self.held;self.wall=time.monotonic_ns()
        elif action==3:self.load(self.recipes[(self.current+1)%len(self.recipes)]['id'])
        elif action in (4,5,6):self.clipboard_action({4:'copy',5:'cut',6:'paste'}[action],event.app.clipboard)
        elif action in (7,8):self.scene.command({'op':'key','key':'F1' if action==7 else 'F6'})
        else:raise ValueError('Unknown host shortcut action')
        event.app.invalidate()

    def clipboard_action(self,action,clipboard):
        info=self.scene.info()
        if info.get('inputOwner')!='prompt':return
        prompt=info['prompt'];anchor=prompt['anchor'];caret=prompt['caret']
        if action=='paste':
            text=clipboard.get_data().text
            if text:self.scene.command({'op':'paste','text':text})
            return
        if action=='cut' and (anchor<0 or anchor==caret):return
        text=prompt['text'] if anchor<0 else self.scene.selected_text()
        if text is None:return
        clipboard.set_text(text)
        if action=='cut':self.scene.command({'op':'key','key':'Delete'})

    def load(self, name: str) -> None:
        if self.control.unicode_view:self.control.unicode_view.cancel_drag()
        preserve = getattr(self, 'document_loaded', False)
        self.current = next(i for i, recipe in enumerate(self.recipes) if recipe['id'] == name)
        self.scene.command({'op': 'reset', 'seed': self.seed, 'preservePrompt': preserve})
        for command in self.recipes[self.current]['commands']:
            if preserve and command['op'] in ('prompt', 'draft', 'input', 'paste', 'key'):
                continue
            self.scene.command(command)
        self.document_loaded = True
        self.scene.set_accessibility(reduced_motion=self.reduced_motion)
        self.control.viewport = None
        self.logical_us = 0.0
        self.wall = time.monotonic_ns()

    async def tick(self) -> None:
        while True:
            now = time.monotonic_ns()
            if not self.held:
                self.logical_us += (now - self.wall) / 1000.0
                # Bounded work, explicit catch-up. No simulation steps are skipped.
                self.scene.command({'op': 'time', 'timeUs': int(self.logical_us), 'budget': 12})
            self.wall = now
            self.application.invalidate()
            await asyncio.sleep(1 / self.fps)

    def run(self, max_seconds: float = 0) -> None:
        async def stop_later():
            await asyncio.sleep(max_seconds)
            self.application.exit()
        def start():
            self.application.output.write_raw('\x1b[?1004h')
            self.application.output.flush()
            self.application.create_background_task(self.tick())
            if max_seconds > 0:
                self.application.create_background_task(stop_later())
        try:
            self.application.run(pre_run=start)
        finally:
            self.application.output.write_raw('\x1b[?1004l')
            self.application.output.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', default='autumn')
    parser.add_argument('--fps', type=int, default=60)
    parser.add_argument('--seed', type=int, default=2030)
    parser.add_argument('--reduced-motion', action='store_true')
    parser.add_argument('--max-seconds', type=float, default=0)
    parser.add_argument('--info-on-exit', type=Path)
    parser.add_argument('--load-document', type=Path, help='Import a nocturne-document-v1 file before running')
    parser.add_argument('--save-document', type=Path, help='Atomically save the accepted document after normal exit')
    parser.add_argument('--unicode-document',action='store_true',help='Use native bidi/grapheme document presentation')
    parser.add_argument('--reserve-shortcut',action='append',default=[],help='Reserve a managed chord, e.g. Ctrl+q, Alt+w or F2; repeatable')
    args = parser.parse_args()
    try:reserved=parse_reservations(args.reserve_shortcut)
    except ValueError as error:parser.error(str(error))
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error('An interactive terminal is required.')
    host = FrameworkHost(args.scene, args.fps, args.seed, args.reduced_motion,unicode_document=args.unicode_document,reserved_shortcuts=reserved)
    try:
        if args.load_document:
            load_document(host.scene, args.load_document)
        host.run(args.max_seconds)
        if args.save_document:
            save_document(host.scene, args.save_document)
    finally:
        try:
            if args.info_on_exit:
                args.info_on_exit.write_text(json.dumps({**host.scene.info(), 'hostScene': host.recipes[host.current]['id']}, indent=2) + '\n')
        finally:
            host.scene.close()

if __name__ == '__main__':
    main()
