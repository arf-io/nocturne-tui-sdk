"""Host-side terminal output and two-clock scheduling. Not part of the renderer."""
from __future__ import annotations
from dataclasses import dataclass
from nocturne import Frame


@dataclass
class MotionClock:
    """Sample a monotonic host clock at fps without gating data events.

    advance(nowMs) returns True only for a new motion sample. A data event should
    render immediately at lastMotionMs without calling advance. Pausing preserves
    the sampled time and resuming excludes the paused interval.
    """
    fps: int=30
    lastMotionMs: int=0
    playing: bool=True
    epochMs: float=0
    offsetMs: int=0
    frameIndex: int=-1

    def __post_init__(self):
        if type(self.fps) is not int or not 1 <= self.fps <= 240:
            raise ValueError('fps must be an integer in 1..240')

    def advance(self,nowMs: float) -> bool:
        """Sample, skipping missed presentation frames. Does not simulate catch-up."""
        if not self.playing:
            return False
        index=int(max(0,self.offsetMs+nowMs-self.epochMs)*self.fps//1000)
        if index==self.frameIndex:
            return False
        self.frameIndex=index
        self.lastMotionMs=index*1000//self.fps
        return True

    def setPlaying(self,playing: bool,nowMs: float) -> None:
        """Pause/resume without resetting the visual phase or holding data updates."""
        self.playing=playing
        self.offsetMs=self.lastMotionMs
        self.epochMs=nowMs
        self.frameIndex=-1

    def untilNextMs(self,nowMs: float) -> float:
        """Return time until the next motion deadline, or 100 ms while paused."""
        if not self.playing:
            return 100.0
        elapsed=self.offsetMs+nowMs-self.epochMs
        nextTime=(int(max(0,elapsed)*self.fps//1000)+1)*1000/self.fps
        return max(0,nextTime-elapsed)


class AnsiWriter:
    """Generate changed runs only; never write or change terminal mode by itself.

    The caller serializes returned strings through one output owner. The host
    explicitly opts into synchronized output after establishing terminal support.
    lastChangedCells and lastBytes are instrumentation, not latency guarantees.
    """
    def __init__(self,synchronized: bool=False):
        self.previous: Frame | None=None
        self.synchronized=synchronized
        self.lastChangedCells=0
        self.lastBytes=0

    def invalidate(self) -> None:
        """Forget prior cells after a resize or another renderer taking ownership."""
        self.previous=None

    def encode(self,frame: Frame) -> str:
        """Return ANSI updates for this frame. Empty string means no cell changes."""
        before=self.previous
        full=before is None or before.width!=frame.width or before.height!=frame.height
        pieces=[]
        lastFg=lastBg=-1
        changed=0
        for y in range(frame.height):
            cursorX=-1
            for x in range(frame.width):
                index=y*frame.width+x
                cell=frame.cells[index]
                if not full:
                    old=before.cells[index]
                    if (cell.glyph,cell.fg,cell.bg,cell.flags)==(old.glyph,old.fg,old.bg,old.flags):
                        continue
                if cursorX!=x:
                    pieces.append(f'\x1b[{y+1};{x+1}H')
                if cell.fg!=lastFg:
                    c=cell.fg;pieces.append(f'\x1b[38;2;{c>>16};{c>>8&255};{c&255}m');lastFg=c
                if cell.bg!=lastBg:
                    c=cell.bg;pieces.append(f'\x1b[48;2;{c>>16};{c>>8&255};{c&255}m');lastBg=c
                pieces.append(chr(cell.glyph));cursorX=x+1;changed+=1
        self.previous=frame
        self.lastChangedCells=changed
        if not pieces:
            self.lastBytes=0
            return ''
        result=('\x1b[?2026h' if self.synchronized else '')+''.join(pieces)+'\x1b[0m'+('\x1b[?2026l' if self.synchronized else '')
        self.lastBytes=len(result.encode())
        return result
