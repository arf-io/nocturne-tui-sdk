"""Multiline navigation follows document rows, including offscreen source."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PromptVertical(unittest.TestCase):
    def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
    def draft(self,text,caret,mode='grow',width=24):
        self.s.command(dict(op='resize',width=width,height=18))
        self.s.command(dict(op='prompt',mode=mode,minRows=2,maxRows=2))
        self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False))
    def key(self,key,unit='scalar'):
        before=self.s.info();self.s.command(dict(op='key',key=key,unit=unit));after=self.s.info()
        self.assertEqual(after['prompt']['text'],before['prompt']['text'])
        self.assertEqual(after['prompt']['revision'],before['prompt']['revision'])
        self.assertEqual(after['clock'],before['clock'])
        self.assertEqual(after['fieldCount'],before['fieldCount'])
        return after['prompt']['caret']
    def testNewlinesAndDocumentEdgesInEveryMultilineMode(self):
        for mode in ['grow','vim-inline','vim-full']:
            for unit in ['scalar','grapheme']:
                self.draft('ab\ncdef\nghij',10,mode)
                for key,expected in [('ArrowUp',5),('ArrowUp',2),('ArrowUp',2),('ArrowDown',5),('ArrowDown',10),('ArrowDown',10)]:
                    self.assertEqual(self.key(key,unit),expected,(mode,unit,key))
    def testVimVerticalKeysMatchArrowsWithoutEditing(self):
        for mode in ['vim-inline','vim-full']:
            for unit in ['scalar','grapheme']:
                for text,caret in [('ab\ncdef\nghij',10),('ab\néx',4),('aa\nbb\ncc\ndd\nee',13)]:
                    self.draft(text,caret,mode)
                    self.s.command(dict(op='key',key='Escape'))
                    expected=self.key('ArrowUp',unit)
                    self.draft(text,caret,mode)
                    self.s.command(dict(op='key',key='Escape'))
                    self.assertEqual(self.key('k',unit),expected)
                    self.draft(text,caret,mode)
                    self.s.command(dict(op='key',key='Escape'))
                    expected=self.key('ArrowDown',unit)
                    self.draft(text,caret,mode)
                    self.s.command(dict(op='key',key='Escape'))
                    self.assertEqual(self.key('j',unit),expected)
    def testVimVerticalKeysRemainTextInInsertAndGrowModes(self):
        for mode in ['grow','vim-inline','vim-full']:
            self.draft('ab',1,mode)
            if mode.startswith('vim'):
                self.s.command(dict(op='key',key='Escape'))
                self.s.command(dict(op='key',key='i'))
            for key in ['j','k']:self.s.command(dict(op='key',key=key))
            self.assertEqual(self.s.info()['prompt']['text'],'ajkb')
    def testShortAndEmptyRowsChooseNearestColumn(self):
        self.draft('abcdef\nx\nQRSTUV',13)
        self.assertEqual(self.key('ArrowUp'),8)
        self.draft('abc\n\nXYZ',7)
        self.assertEqual(self.key('ArrowUp'),4)
    def testWrappedRowsUseRenderedColumns(self):
        self.draft('abcdefghijklmnop',14,width=10)
        self.assertEqual(self.key('ArrowUp'),8)
        self.assertEqual(self.key('ArrowUp'),2)
        self.assertEqual(self.key('ArrowDown'),8)
    def testOffscreenRowsRemainKeyboardAccessible(self):
        text='aa\nbb\ncc\ndd\nee\nff'
        self.draft(text,16)
        for expected in [13,10,7,4,1]:self.assertEqual(self.key('ArrowUp'),expected)
        for expected in [4,7,10,13,16]:self.assertEqual(self.key('ArrowDown'),expected)
    def testGraphemeMovementNeverSelectsAnInteriorBoundary(self):
        self.draft('ab\néx',1)
        self.assertEqual(self.key('ArrowDown','grapheme'),3)
        self.draft('ab\néx',4)
        self.assertEqual(self.key('ArrowUp','grapheme'),0)
    def testMarqueeRetainsItsHorizontalPagingContract(self):
        self.draft('abcdefghijklmnop',10,mode='marquee',width=10)
        self.assertEqual(self.key('ArrowUp'),4)
        self.assertEqual(self.key('ArrowDown'),10)
    def testClusterSpanningScalarRowsCanStillBeLeftAtomically(self):
        text='A'+'\u0301'*20
        self.draft(text,len(text),width=10)
        self.assertEqual(self.key('ArrowUp','grapheme'),0)
        self.assertEqual(self.key('ArrowDown','grapheme'),len(text))
if __name__=='__main__':unittest.main()
