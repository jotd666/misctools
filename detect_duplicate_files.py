import filecmp,hashlib,subprocess,sys,os,collections,json
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="directory to scan")
parser.add_argument("-o","--output-file", help="output file (json)")
parser.add_argument("-r","--recursive", help="recursive",
                    action="store_true")
args = parser.parse_args()

filelist = []
if args.recursive:
    for root,_,files in os.walk(args.directory):
        for f in files:
            filelist.append(os.path.join(root,f))
else:
    filelist = [os.path.join(args.directory,f) for f in os.listdir(args.directory)]
    filelist = [f for f in filelist if os.path.isfile(f)]

def contents(fn):
    with open(fn,"rb") as f:
        return f.read()
hashdict = {f:hashlib.md5(contents(f)).hexdigest() for f in filelist}

invhash = collections.defaultdict(list)

for fn,h in hashdict.items():
    invhash[h].append(fn)

dupes = {h:sorted(lf) for h,lf in invhash.items() if len(lf)>1}

with open(args.output_file,"w") as f:
    json.dump(dupes,f,indent=2,sort_keys=True)
