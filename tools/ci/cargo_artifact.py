"""Require the real example executable from a completed Cargo JSON build log."""
import argparse,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'native/scripts'))
from cargo_example import executableFromMessages

def executable(log, target):
    path=executableFromMessages(Path(log).read_text(),target)
    if not path.is_file() or not os.access(path,os.X_OK):
        raise ValueError('Cargo executable is absent or not executable: '+str(path))
    return path

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path);parser.add_argument('--target',default='qualification')
    args=parser.parse_args();print(executable(args.log,args.target))
