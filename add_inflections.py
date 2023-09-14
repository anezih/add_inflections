import argparse
import gzip
import json
import os
import sys

from pyglossary.glossary_v2 import Glossary
from pyglossary.glossary_type import EntryType

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

def get_base_name(name: str) -> str:
    return os.path.splitext(os.path.basename(name))[0]

def sort_glos(_glos: Glossary) -> list[EntryType]:
    lst = [g for g in _glos]
    lst.sort(key=lambda x: (x.l_word[0].encode("utf-8").lower(), x.l_word[0]))
    return lst

class INFL():
    def __init__(self, source: str, glos_format: str = "") -> None:
        self._infl_dict: dict[str,list[str]] = {}
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
                    temp: list[dict[str,dict[str,list[str]]]] = json.load(f)
            except:
                sys.exit("[!] Couldn't open gzipped json file. Check the filename/path.")
        else:
            try:
                with open(source, "r", encoding="utf-8") as f:
                    temp: list[dict[str,dict[str,list[str]]]] = json.load(f)
            except:
                sys.exit("[!] Couldn't open json file. Check the filename/path.")
        for it in temp:
         for key, val in it.items():
            if key in self._infl_dict.keys():
                self._infl_dict[key]["PFX"]   += val["PFX"]
                self._infl_dict[key]["SFX"]   += val["SFX"]
                self._infl_dict[key]["Cross"] += val["Cross"]
            else:
                self._infl_dict[key] = val

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> list[str]:
        afx = []
        afx_lst = self._infl_dict.get(word)
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
            if len(entry.l_word) > 1:
                hw = entry.l_word[0]
                if hw in self._infl_dict.keys():
                    self._infl_dict[hw] += entry.l_word[1:]
                else:
                    self._infl_dict[hw] = entry.l_word[1:]

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> list[str]:
        return self._infl_dict.get(word, [])

def add_infl(dict_: str, infl_dicts: list[INFL], pfx: bool = False, cross: bool = False,
             input_format: str = None, output_format: str = None, keep: bool = False, sort=False) -> None:
    if not os.path.exists(dict_):
        sys.exit("[!] Couldn't find input dictionary file. Check the filename/path.")
    glos = Glossary()
    glos_syn = Glossary()

    print(f"\r{'Reading the input dictionary...':<35}", end="")
    if input_format:
        glos.directRead(filename=dict_, format=input_format)
    else:
        glos.directRead(filename=dict_)
    print(f"{'Done.' :>6}")

    glos_len = glos.__len__()
    glos_syn.setInfo("title", glos.getInfo("title"))
    glos_syn.setInfo("description", glos.getInfo("description"))
    glos_syn.setInfo("author", glos.getInfo("author"))

    # if the out format is stardict sort the input just in case
    if sort or output_format == "Stardict":
        print(f"\r{'Sorting the input dictionary...':<35}", end="")
        glos = sort_glos(glos)
        print(f"{'Done.' :>6}")

    cnt = 0
    total_infl_found = 0
    for entry in glos:
        suffixes_set = {
            _infl
            for infl_dict in infl_dicts
            for _infl in infl_dict.get_infl(word=entry.l_word[0], pfx=pfx, cross=cross)
        }
        suffixes = list(suffixes_set)
        if entry.l_word[0] in suffixes:
            suffixes.remove(entry.l_word[0])

        total_infl_found += len(suffixes)

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
        cnt += 1
        print(f"\r> Processed {cnt:,} / {glos_len:,} words. Total new inflections to be added: {total_infl_found:,}", end="\r")
    print(f"\n{'Writing the output file(s)...':<35}", end="")
    outname = get_base_name(dict_)
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
    print(f"{'Done.' :>6}")

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
    print(f"\r{'Preparing the inflection sources...':<35}", end="")
    if args.json:
        infl_json = Unmunched(source=args.json)
        infl_list.append(infl_json)
    if args.gs:
        infl_glos = GlosSource(source=args.gs, glos_format=args.gsf)
        infl_list.append(infl_glos)
    print(f"{'Done.' :>6}")
    add_infl(
        dict_=args.df, infl_dicts=infl_list, pfx=args.pfx,
        cross=args.cross, input_format=args.informat,
        output_format=args.outformat, keep=args.keep, sort=args.sort
    )