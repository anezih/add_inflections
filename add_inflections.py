import argparse
import gzip
import json
import os
import sys

from pyglossary.glossary_v2 import Glossary, EntryType

# Unmunched Hunspell dictionary format, see: https://github.com/anezih/HunspellWordForms
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
    def __init__(self, source: str, glos_format: str = "") -> None:
        self.j = {}
        self.populate_dict(source=source, glos_format=glos_format)

    def populate_dict(self, source: str, glos_format: str = "") -> None:
        raise NotImplementedError

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> list[str]:
        raise NotImplementedError

class Unmunched(INFL):
    def populate_dict(self, source: str, glos_format: str = "") -> None:
        if source.endswith(".gz"):
            try:
                with gzip.open(source, "rt", encoding="utf-8") as f:
                    temp = json.load(f)
            except:
                sys.exit("[!] Couldn't open gzipped json file. Check the filename/path.")
        else:
            try:
                with open(source, "r", encoding="utf-8") as f:
                    temp = json.load(f)
            except:
                sys.exit("[!] Couldn't open json file. Check the filename/path.")
        for it in temp:
         for key, val in it.items():
            if key in self.j.keys():
                self.j[key]["PFX"]   += val["PFX"]
                self.j[key]["SFX"]   += val["SFX"]
                self.j[key]["Cross"] += val["Cross"]
            else:
                self.j[key] = val

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> list[str]:
        afx = []
        afx_lst = self.j.get(word)
        if afx_lst:
            afx += afx_lst["SFX"]
            if pfx:
                afx += afx_lst["PFX"]
            if cross:
                afx += afx_lst["Cross"]
        return afx

class GlosSource(INFL):
    def populate_dict(self, source: str, glos_format: str = "") -> None:
        if not os.path.exists(source):
            sys.exit("[!] Couldn't find dictionary file for inflection source. Check the filename/path.")
        glos = Glossary()
        if glos_format:
            glos.directRead(filename=source, format=glos_format)
        else:
            glos.directRead(filename=source)
        for entry in glos:
            if len(entry.l_word) < 2:
                continue
            hw = entry.l_word[0]
            if hw in self.j.keys():
                self.j[hw] += entry.l_word[1:]
            else:
                self.j[hw] = entry.l_word[1:]

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> list[str]:
        return self.j.get(word, [])

def sort_glos(_glos: Glossary) -> list[EntryType]:
    lst = [g for g in _glos]
    lst.sort(key=lambda x: (x.l_word[0].encode("utf-8").lower(), x.l_word[0]))
    return lst

def add_infl(dict_: str, infl_dicts: list[INFL], pfx: bool = False, cross: bool = False,
             input_format: str = None, output_format: str = None, keep: bool = False, sort=False) -> None:
    if not os.path.exists(dict_):
        sys.exit("[!] Couldn't find input dictionary file. Check the filename/path.")
    glos = Glossary()
    glos_syn = Glossary()

    if input_format:
        glos.directRead(filename=dict_, format=input_format)
    else:
        glos.directRead(filename=dict_)
    
    glos_syn.setInfo("title", glos.getInfo("title"))
    glos_syn.setInfo("description", glos.getInfo("description"))
    glos_syn.setInfo("author", glos.getInfo("author"))
    
    if sort:
        glos = sort_glos(glos)

    for entry in glos:
        suffixes_set = {
            _infl
            for infl_dict in infl_dicts
            for _infl in infl_dict.get_infl(word=entry.l_word[0], pfx=pfx, cross=cross)
        }
        suffixes = list(suffixes_set)
        if entry.l_word[0] in suffixes:
            suffixes.remove(entry.l_word[0])

        if keep and (len(entry.l_word) > 1):
            temp = list(set(suffixes + entry.l_word[1:]))
            temp.insert(0, entry.l_word[0])
            word_suffixes = temp
        else:
            suffixes.insert(0, entry.l_word[0])
            word_suffixes = suffixes

        glos_syn.addEntry(
            glos_syn.newEntry(
                word=word_suffixes, defi=entry.defi, defiFormat=entry.defiFormat
            )
        )

    outname = os.path.splitext(os.path.basename(dict_))[0]
    outdir = f"{outname}_with_inflections"
    try:
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        os.chdir(outdir)
    except:
        sys.exit("[!] Couldn't create or enter the output directory.")

    # for format parameter check the PyGlossary README > Supported formats > your preferred format > "Name" attribute
    if output_format == "Stardict":
        glos_syn.write(f"{outname}", format=output_format, dictzip=False)
    else:
        glos_syn.write(f"{outname}", format=output_format)

if __name__ == '__main__':
    Glossary.init()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--dict-file", dest="df",
        help="Input dictionary path.", required=True)

    parser.add_argument("-j", "--unmunched-json", dest="json",
        help=f"<language>.json(.gz)")

    parser.add_argument("--glos-infl-source", dest="gs",
        help="Dictionary that will be used as an inflection source by-itself or together with json file.")

    parser.add_argument("--glos-infl-source-format", dest="gsf",
        default="", choices=Glossary.readFormats, metavar="",
        help="--glos-infl-source dictionary format, allowed values are same as --input-format")

    parser.add_argument("--input-format", dest="informat",
        default=None, choices=Glossary.readFormats,
        help=f"Allowed values: {', '.join(Glossary.readFormats)}", metavar="")

    parser.add_argument("--output-format", dest="outformat", default="Stardict",
        choices=Glossary.writeFormats,
        help=f"Allowed values: {', '.join(Glossary.writeFormats)}", metavar="")

    parser.add_argument("-p", "--add-prefixes", dest="pfx", action="store_true", default=False)
    parser.add_argument("-c", "--add-cross-products", dest="cross", action="store_true", default=False)
    parser.add_argument("-k", "--keep", dest="keep", action="store_true", default=False,
                        help="Keep existing inflections.")
    parser.add_argument("--sort", dest="sort", action="store_true", default=False, help="Sort input dictionary.")
    args = parser.parse_args()
    if not (args.json or args.gs):
        sys.exit("[!] You need to specify at least one inflection source: --unmunched-json, --glos-infl-source or both.")
    infl_list = []
    if args.json:
        infl_json = Unmunched(source=args.json)
        infl_list.append(infl_json)
    if args.gs:
        infl_glos = GlosSource(source=args.gs, glos_format=args.gsf)
        infl_list.append(infl_glos)
    add_infl(
        dict_=args.df, infl_dicts=infl_list, pfx=args.pfx,
        cross=args.cross, input_format=args.informat,
        output_format=args.outformat, keep=args.keep, sort=args.sort
    )