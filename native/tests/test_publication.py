"""Private publication policy uses a labelled service double; Git custody tests are real."""
from pathlib import Path
import sys,tempfile,subprocess,json,hashlib,unittest,os
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/release'))
try:from publish_github import ensurePrivateDestination,restoreHistory,validateRepository
except ImportError:ensurePrivateDestination=restoreHistory=validateRepository=None
class PublicationDouble:
    def __init__(self,states):self.states=iter(states);self.calls=[]
    def lookup(self,repo):self.calls.append(('lookup',repo));state=next(self.states);return state
    def create(self,repo):self.calls.append(('create-private',repo))
class PublicationPolicyTests(unittest.TestCase):
    def testNewPrivateCreationVerifiedBeforePush(self):
        self.assertIsNotNone(ensurePrivateDestination);d=PublicationDouble([None,{'full_name':'owner/repo','private':True}])
        ensurePrivateDestination(d,'owner/repo',False)
        self.assertEqual([x[0] for x in d.calls],['lookup','create-private','lookup'])
    def testExistingRefusedWithoutExplicitUpdate(self):
        self.assertIsNotNone(ensurePrivateDestination);d=PublicationDouble([{'full_name':'owner/repo','private':True}])
        with self.assertRaises(RuntimeError):ensurePrivateDestination(d,'owner/repo',False)
        self.assertEqual(len(d.calls),1)
    def testPublicAlwaysRefused(self):
        self.assertIsNotNone(ensurePrivateDestination)
        for state in ([{'full_name':'owner/repo','private':False}],[None,{'full_name':'owner/repo','private':False}]):
            with self.assertRaises(RuntimeError):ensurePrivateDestination(PublicationDouble(state),'owner/repo',True)
    def testPrivacyMustBeBoolean(self):
        self.assertIsNotNone(ensurePrivateDestination)
        with self.assertRaises(RuntimeError):ensurePrivateDestination(PublicationDouble([None,{'full_name':'owner/repo','private':'true'}]),'owner/repo',False)
    def testDifferentDestinationRefused(self):
        self.assertIsNotNone(ensurePrivateDestination)
        with self.assertRaises(RuntimeError):ensurePrivateDestination(PublicationDouble([None,{'full_name':'other/repo','private':True}]),'owner/repo',False)
    def testRepositoryNameValidation(self):
        self.assertIsNotNone(validateRepository)
        self.assertEqual(validateRepository('owner/nocturne-sdk'),'owner/nocturne-sdk')
        for s in ('/tmp/repo','a/b/c','a/../b','--private','a/.git','a/re po','https://github.com/a/b'):
            with self.assertRaises(ValueError):validateRepository(s)
    def testHistoryRestoredFromCurrentBundleWithoutCheckoutOverwrite(self):
        self.assertIsNotNone(restoreHistory)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';dst=root/'copy';src.mkdir();dst.mkdir();(dst/'git').mkdir()
            def git(*args):return subprocess.check_output(['git','-C',str(src),*args],text=True,stderr=subprocess.DEVNULL).strip()
            git('init','-q','-b','candidate');git('config','user.name','Test');git('config','user.email','test@localhost')
            (src/'file.txt').write_text('source');git('add','file.txt');git('commit','-qm','baseline')
            commit=git('rev-parse','HEAD');git('update-ref','refs/archive/older/build',commit)
            bundle=dst/'git/current.bundle';git('bundle','create',str(bundle),'--all')
            (dst/'file.txt').write_text('source');(dst/'untracked.txt').write_text('preserve me')
            (dst/'MANIFEST.json').write_text(json.dumps({'sourceCommit':commit,'branch':'candidate','files':{'git/current.bundle':{'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bytes':bundle.stat().st_size}}}))
            restoreHistory(dst)
            self.assertEqual(subprocess.check_output(['git','-C',str(dst),'rev-parse','HEAD'],text=True).strip(),commit)
            self.assertEqual(subprocess.check_output(['git','-C',str(dst),'rev-parse','refs/archive/older/build'],text=True).strip(),commit)
            self.assertEqual((dst/'untracked.txt').read_text(),'preserve me')
            self.assertEqual(subprocess.check_output(['git','-C',str(dst),'status','--porcelain','--untracked-files=no'],text=True),'')
    def testHistoryImportDoesNotConflictWithDefaultCheckedOutBranch(self):
        """A union bundle can contain the receiver's init.defaultBranch."""
        self.assertIsNotNone(restoreHistory)
        for defaultBranch in ('master','main'):
            with self.subTest(defaultBranch=defaultBranch), tempfile.TemporaryDirectory() as d:
                root=Path(d);src=root/'source';dst=root/'copy'
                src.mkdir();dst.mkdir();(dst/'git').mkdir()
                config=root/'gitconfig'
                config.write_text('[init]\n    defaultBranch = '+defaultBranch+'\n')
                with patch.dict(os.environ,{'GIT_CONFIG_GLOBAL':str(config),'GIT_CONFIG_NOSYSTEM':'1'}):
                    def git(*args):
                        return subprocess.check_output(['git','-C',str(src),*args],text=True,stderr=subprocess.DEVNULL).strip()
                    git('init','-q');git('config','user.name','Test');git('config','user.email','test@localhost')
                    (src/'file.txt').write_text('old');git('add','file.txt');git('commit','-qm','old trunk')
                    old=git('rev-parse','HEAD');git('tag','old-release')
                    git('checkout','-qb','feature/current')
                    (src/'file.txt').write_text('current');git('commit','-qam','current source')
                    current=git('rev-parse','HEAD');git('update-ref','refs/archive/previous/trunk',old)
                    bundle=dst/'git/current.bundle';git('bundle','create',str(bundle),'--all')
                    (dst/'file.txt').write_text('current');(dst/'draft.txt').write_text('keep my work')
                    manifest={'sourceCommit':current,'branch':'feature/current','files':{'git/current.bundle':{
                        'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bytes':bundle.stat().st_size}}}
                    (dst/'MANIFEST.json').write_text(json.dumps(manifest))
                    restoreHistory(dst)
                    def restored(*args):
                        return subprocess.check_output(['git','-C',str(dst),*args],text=True).strip()
                    self.assertEqual(restored('symbolic-ref','--short','HEAD'),'feature/current')
                    self.assertEqual(restored('rev-parse','HEAD'),current)
                    self.assertEqual(restored('rev-parse','refs/heads/'+defaultBranch),old)
                    self.assertEqual(restored('rev-parse','refs/archive/previous/trunk'),old)
                    self.assertEqual(restored('rev-parse','refs/tags/old-release'),old)
                    self.assertEqual(restored('rev-parse','--is-bare-repository'),'false')
                    self.assertEqual(restored('status','--porcelain','--untracked-files=no'),'')
                    self.assertEqual((dst/'draft.txt').read_text(),'keep my work')
                    self.assertEqual((dst/'file.txt').read_text(),'current')

    def testHistoryRestorePreservesModifiedPayloadForReview(self):
        """Rehydrating Git must not check out over an operator's changed file."""
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';dst=root/'copy';src.mkdir();dst.mkdir();(dst/'git').mkdir()
            def git(*args):
                return subprocess.check_output(['git','-C',str(src),*args],text=True,stderr=subprocess.DEVNULL).strip()
            git('init','-q','-b','candidate');git('config','user.name','Test');git('config','user.email','test@localhost')
            (src/'file.txt').write_text('committed');git('add','file.txt');git('commit','-qm','baseline')
            current=git('rev-parse','HEAD');bundle=dst/'git/current.bundle';git('bundle','create',str(bundle),'--all')
            (dst/'file.txt').write_text('my local modification')
            (dst/'MANIFEST.json').write_text(json.dumps({'sourceCommit':current,'branch':'candidate',
                'files':{'git/current.bundle':{'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bytes':bundle.stat().st_size}}}))
            restoreHistory(dst)
            self.assertEqual((dst/'file.txt').read_text(),'my local modification')
            self.assertIn(' M file.txt',subprocess.check_output(['git','-C',str(dst),'status','--porcelain','--untracked-files=no'],text=True))

    def testTamperedBundleRefused(self):
        self.assertIsNotNone(restoreHistory)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'git').mkdir();(root/'git/current.bundle').write_bytes(b'bad')
            (root/'MANIFEST.json').write_text(json.dumps({'sourceCommit':'a'*40,'files':{'git/current.bundle':{'sha256':'0'*64,'bytes':3}}}))
            with self.assertRaises(RuntimeError):restoreHistory(root)
            self.assertFalse((root/'.git').exists())
if __name__=='__main__':unittest.main()
