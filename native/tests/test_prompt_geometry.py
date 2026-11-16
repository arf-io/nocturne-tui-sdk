"""Pointer selection must invert the actual rendered prompt geometry."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PromptGeometry(unittest.TestCase):
    def setUp(self):
        self.s=NativeScene();self.addCleanup(self.s.close)
        self.s.command(dict(op='resize',width=24,height=18))
        self.s.command(dict(op='pause',paused=True))
    def clickGlyph(self,glyph):
        frame=self.s.render();cells=frame.words()
        positions=[(i%frame.width,i//frame.width) for i,c in enumerate(cells) if c[0]==ord(glyph) and c[3]==0x40000000]
        self.assertEqual(len(positions),1,'test glyph must be visible and unambiguous')
        x,y=positions[0];before=self.s.info()
        self.s.command(dict(op='pointer',phase='down',x=x,y=y))
        self.s.command(dict(op='pointer',phase='up',x=x,y=y))
        after=self.s.info()
        self.assertEqual(after['prompt']['text'],before['prompt']['text'])
        self.assertEqual(after['prompt']['revision'],before['prompt']['revision'])
        self.assertEqual(after['clock'],before['clock'])
        self.assertEqual(after['fieldCount'],before['fieldCount'])
        return after['prompt']['caret']
    def testNewlineCoordinatesInEveryMultilinePromptMode(self):
        for mode in ['grow','vim-inline','vim-full']:
            self.s.command(dict(op='prompt',mode=mode,minRows=2,maxRows=6))
            self.s.command(dict(op='draft',text='A\nQRS',emitWeather=False))
            self.assertEqual(self.clickGlyph('Q'),2,mode)
    def testScrolledGrowPromptSelectsTheVisibleSourceOffset(self):
        self.s.command(dict(op='prompt',mode='grow',minRows=2,maxRows=2))
        self.s.command(dict(op='draft',text='AAA\nBBB\nCCC\nDDD\nQRS',emitWeather=False))
        self.assertEqual(self.clickGlyph('Q'),16)
    def testMarqueeOffsetIsPartOfTheHitMap(self):
        self.s.command(dict(op='resize',width=10,height=18))
        self.s.command(dict(op='prompt',mode='marquee'))
        self.s.command(dict(op='draft',text='abcdefghijQrstuv',emitWeather=False))
        self.assertEqual(self.clickGlyph('Q'),10)
    def testWrappedVimChromeDoesNotAddDocumentOffsets(self):
        self.s.command(dict(op='resize',width=10,height=18))
        self.s.command(dict(op='prompt',mode='vim-full'))
        self.s.command(dict(op='draft',text='abcdefghiQrstuv',emitWeather=False))
        self.assertEqual(self.clickGlyph('Q'),9)
    def testNewlineAfterExactWidthWrapSelectsTheFollowingGlyph(self):
        self.s.command(dict(op='resize',width=10,height=18))
        self.s.command(dict(op='prompt',mode='grow',minRows=3,maxRows=3))
        self.s.command(dict(op='draft',text='abcdef\nQRS',emitWeather=False))
        self.assertEqual(self.clickGlyph('Q'),7)
    def testMaximumDocumentUsesTheVisibleSourceIndex(self):
        self.s.command(dict(op='prompt',mode='grow',minRows=2,maxRows=2))
        self.s.command(dict(op='draft',text='a'*2047+'Q',emitWeather=False))
        self.assertEqual(self.clickGlyph('Q'),2047)
if __name__=='__main__':unittest.main()
