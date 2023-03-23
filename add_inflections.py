import argparse
import gzip
import json
import os
import sys

from pyglossary.glossary_v2 import Glossary

# Unmunched Hunspell dictionary format, see: https://gist.github.com/anezih/5e0fc6d68c9166fe2ea3ffc05bc68476
# [
#     ...
#     {
#     "build": {
#       "PFX": [],
#       "SFX": [
#         "building",
#         "builds"
#       ],
#       "Cross": []
#     }
#   },
#   {
#     "builder": {
#       "PFX": [],
#       "SFX": [
#         "builders",
#         "builder's"
#       ],
#       "Cross": []
#     }
#   },
#   ...
# ]

class INFL():
    def __init__(self, unmunched: str) -> None:
        if unmunched.endswith(".gz"):
            try:
                with gzip.open(unmunched, "rt", encoding="utf-8") as f:
                    temp = json.load(f)
            except:
                sys.exit("Couldn't open gzipped json file. Check the filename/path.")
        else:
            try:
                with open(unmunched, "r", encoding="utf-8") as f:
                    temp = json.load(f)
            except:
                sys.exit("Couldn't open json file. Check the filename/path.")
        self.j = {}
        for it in temp:
         for key, val in it.items():
            if key in self.j.keys():
                self.j[key]["PFX"]   += val["PFX"]
                self.j[key]["SFX"]   += val["SFX"]
                self.j[key]["Cross"] += val["Cross"]
            else:
                self.j[key] = val

    def get_afx(self, word: str, pfx: bool = False, cross: bool = False) -> list:
        afx = []
        afx_lst = self.j.get(word)
        if afx_lst:
            afx += afx_lst["SFX"]
            if pfx:
                afx += afx_lst["PFX"]
            if cross:
                afx += afx_lst["Cross"]
        return afx

def add_infl(dict_: str, infl_dict: INFL, pfx: bool = False, cross: bool = False, input_format: str = None, output_format: str = None) -> None:
    glos = Glossary()
    glos_syn = Glossary()

    if not os.path.exists(dict_):
        sys.exit("Couldn't find input dictionary file. Check the filename/path.")

    if input_format:
        glos.directRead(filename=dict_, format=input_format)
    else:
        glos.directRead(filename=dict_)

    for entry in glos:
        suffixes = list(set(infl_dict.get_afx(word=entry.l_word[0], pfx=pfx, cross=cross)))
        if entry.l_word[0] in suffixes:
            suffixes.remove(entry.l_word[0])

        glos_syn.addEntry(
            glos_syn.newEntry(
                word=(entry.l_word + suffixes), defi=entry.defi, defiFormat="h"
            )
        )

    glos_syn.setInfo("title", glos.getInfo("title"))
    glos_syn.setInfo("description", glos.getInfo("description"))
    glos_syn.setInfo("author", glos.getInfo("author"))

    outname = os.path.splitext(os.path.basename(dict_))[0]
    outdir = f"{outname}_with_inflections"
    try:
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        os.chdir(outdir)
    except:
        sys.exit("Couldn't create or enter the output directory.")

    # for format parameter check the PyGlossary README > Supported formats > your preferred format > "Name" attribute
    glos_syn.write(f"{outname}", format=output_format)

if __name__ == '__main__':
    Glossary.init()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--dict-file", dest="df",
        help="Input dictionary path.", required=True)
    parser.add_argument("-j", "--unmunched-json", dest="json",
        help=f"<language>.json(.gz)", required=True)
    parser.add_argument("--input-format", dest="informat",
        default=None, choices=Glossary.readFormats, 
        help=f"Allowed values: {', '.join(Glossary.readFormats)}", metavar="")
    parser.add_argument("--output-format", dest="outformat", default="Stardict",
        choices=Glossary.writeFormats,
        help=f"Allowed values: {', '.join(Glossary.writeFormats)}", metavar="")
    parser.add_argument("-p", "--add-prefixes", dest="pfx", action="store_true", default=False)
    parser.add_argument("-c", "--add-cross-products", dest="cross", action="store_true", default=False)
    args = parser.parse_args()

    infl = INFL(args.json)
    add_infl(
        dict_=args.df, infl_dict=infl, pfx=args.pfx, 
        cross=args.cross, input_format=args.informat, 
        output_format=args.outformat
    )