import argparse
import gzip
import json
import sys
from functools import cached_property
from itertools import zip_longest
from pathlib import Path

from pyglossary.glossary_types import EntryType
from pyglossary.glossary_v2 import Glossary
from spylls.hunspell.data.aff import Aff
from spylls.hunspell.data.dic import Word
from spylls.hunspell.dictionary import Dictionary

SCRIPT_DIR = Path(__file__).resolve().parent

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

class InflBase:
    def __init__(self, source_path: str, glos_format: str = "") -> None:
        self.source_path = source_path
        self.glos_format = glos_format

    @cached_property
    def path(self) -> Path:
        return Path(self.source_path).resolve()

    @cached_property
    def InflDict(self) -> dict[str,list[str]]:
        raise NotImplementedError

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> set[str]:
        raise NotImplementedError

class Unmunched(InflBase):
    @cached_property
    def InflDict(self) -> dict[str,dict[str,list[str]]]:
        if not self.path.exists():
            raise FileNotFoundError(f"Couldn't find Unmunched dictionary at: {self.source_path}")
        temp: list[dict[str,dict[str,list[str]]]] = list()
        if self.path.name.endswith(".gz"):
            try:
                with gzip.open(self.path, "rt", encoding="utf-8") as f:
                    temp: list[dict[str,dict[str,list[str]]]] = json.load(f)
            except:
                raise Exception("[!] Couldn't open gzipped json file. Check the filename/path.")
        elif self.path.name.endswith(".json"):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    temp: list[dict[str,dict[str,list[str]]]] = json.load(f)
            except:
                raise Exception("[!] Couldn't open json file. Check the filename/path.")
        _infl_dict: dict[str,dict[str, list[str]]] = dict()
        for it in temp:
            for key, val in it.items():
                if key in _infl_dict.keys():
                    _infl_dict[key]["PFX"]   += val["PFX"]
                    _infl_dict[key]["SFX"]   += val["SFX"]
                    _infl_dict[key]["Cross"] += val["Cross"]
                else:
                    _infl_dict[key] = val
        return _infl_dict

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> set[str]:
        afx = set()
        afx_dict = self.InflDict.get(word)
        if afx_dict:
            afx.update(afx_dict["SFX"])
            if pfx:
                afx.update(afx_dict["PFX"])
            if cross:
                afx.update(afx_dict["Cross"])
        return afx

class InflGlosSource(InflBase):
    @cached_property
    def InflDict(self) -> dict[str,set[str]]:
        if not self.path.exists():
            raise FileNotFoundError(f"Couldn't find InflGlosSource dictionary at: {self.source_path}")
        glos = Glossary()
        if self.glos_format:
            glos.directRead(filename=str(self.path), formatName=self.glos_format)
        else:
            glos.directRead(filename=str(self.path))
        _infl_dict: dict[str,set[str]] = dict()
        for entry in glos:
            if len(entry.l_word) > 1:
                headword = entry.l_word[0]
                if headword in _infl_dict.keys():
                    _infl_dict[headword].update(entry.l_word[1:])
                else:
                    _infl_dict[headword] = set(entry.l_word[1:])
        return _infl_dict

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> set[str]:
        return self.InflDict.get(word, set())

class HunspellDic(InflBase):
    # Taken from: https://gist.github.com/zverok/c574b7a9c42cc17bdc2aa396e3edd21a
    def unmunch(self, word: Word, aff: Aff) -> dict[str,dict[str,set[str]]]:
        result = {
            word.stem : {
                "PFX"   : set(),
                "SFX"   : set(),
                "Cross" : set()
            }
        }

        if aff.FORBIDDENWORD and aff.FORBIDDENWORD in word.flags:
            return result

        suffixes = [
            suffix
            for flag in word.flags
            for suffix in aff.SFX.get(flag, [])
            if suffix.cond_regexp.search(word.stem)
        ]
        prefixes = [
            prefix
            for flag in word.flags
            for prefix in aff.PFX.get(flag, [])
            if prefix.cond_regexp.search(word.stem)
        ]

        for suffix in suffixes:
            root = word.stem[0:-len(suffix.strip)] if suffix.strip else word.stem
            suffixed = root + suffix.add
            if not (aff.NEEDAFFIX and aff.NEEDAFFIX in suffix.flags):
                result[word.stem]["SFX"].add(suffixed)

            secondary_suffixes = [
                suffix2
                for flag in suffix.flags
                for suffix2 in aff.SFX.get(flag, [])
                if suffix2.cond_regexp.search(suffixed)
            ]
            for suffix2 in secondary_suffixes:
                root = suffixed[0:-len(suffix2.strip)] if suffix2.strip else suffixed
                result[word.stem]["SFX"].add(root + suffix2.add)

        for prefix in prefixes:
            root = word.stem[len(prefix.strip):]
            prefixed = prefix.add + root
            if not (aff.NEEDAFFIX and aff.NEEDAFFIX in prefix.flags):
                result[word.stem]["PFX"].add(prefixed)

            if prefix.crossproduct:
                additional_suffixes = [
                    suffix
                    for flag in prefix.flags
                    for suffix in aff.SFX.get(flag, [])
                    if suffix.crossproduct and not suffix in suffixes and suffix.cond_regexp.search(prefixed)
                ]
                for suffix in suffixes + additional_suffixes:
                    root = prefixed[0:-len(suffix.strip)] if suffix.strip else prefixed
                    suffixed = root + suffix.add
                    result[word.stem]["Cross"].add(suffixed)

                    secondary_suffixes = [
                        suffix2
                        for flag in suffix.flags
                        for suffix2 in aff.SFX.get(flag, [])
                        if suffix2.crossproduct and suffix2.cond_regexp.search(suffixed)
                    ]
                    for suffix2 in secondary_suffixes:
                        root = suffixed[0:-len(suffix2.strip)] if suffix2.strip else suffixed
                        result[word.stem]["Cross"].add(root + suffix2.add)
        return result

    @cached_property
    def InflDict(self) -> dict[str,dict[str,list[str]]]:
        if not self.path.exists():
            raise FileNotFoundError(f"Couldn't find Hunspell dictionary at: {self.source_path}")
        base_name = self.path.parent / self.path.stem
        hunspell_dictionary = Dictionary.from_files(str(base_name))
        aff: Aff = hunspell_dictionary.aff
        all_words: list[Word] = hunspell_dictionary.dic.words
        results: list[dict[str,dict[str,set[str]]]] = list()
        for word in all_words:
            unmunched = self.unmunch(word, aff)
            if any([unmunched[word.stem]["SFX"], unmunched[word.stem]["PFX"], unmunched[word.stem]["Cross"]]):
                results.append(unmunched)

        _infl_dict: dict[str,dict[str, set[str]]] = dict()
        for it in results:
            for key, val in it.items():
                if key in _infl_dict.keys():
                    _infl_dict[key]["PFX"].update(val["PFX"])
                    _infl_dict[key]["SFX"].update(val["SFX"])
                    _infl_dict[key]["Cross"].update(val["Cross"])
                else:
                    _infl_dict[key] = val
        return _infl_dict

    def get_infl(self, word: str, pfx: bool = False, cross: bool = False) -> set[str]:
        afx = set()
        afx_dict = self.InflDict.get(word)
        if afx_dict:
            afx.update(afx_dict["SFX"])
            if pfx:
                afx.update(afx_dict["PFX"])
            if cross:
                afx.update(afx_dict["Cross"])
        return afx

class AddInflections:
    def __init__(self, input_dictionary_path: str, input_dictionary_format: str,
                 output_format: str, pfx: bool, cross: bool, keep_existing_inflections: bool,
                 infl_glos_source_paths: list[str], infl_glos_formats: list[str],
                 hunspell_dic_paths: list[str], unmunched_path: str) -> None:
        self.input_dictionary_path = input_dictionary_path
        self.input_dictionary_format = input_dictionary_format
        self.output_format = output_format
        self.pfx = pfx
        self.cross = cross
        self.keep_existing_inflections = keep_existing_inflections
        self.infl_glos_source_paths = infl_glos_source_paths
        self.infl_glos_formats = infl_glos_formats
        self.hunspell_dic_paths = hunspell_dic_paths
        self.unmunched_path = unmunched_path

    def get_path(self, path: str) -> Path:
        p = Path(path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Couldn't find file at: {path}")
        return p.resolve()

    def sort_glos(self, glos: Glossary) -> list[EntryType]:
        entrytype_lst = [g for g in glos if g.defiFormat != "b"]
        entrytype_lst.sort(key=lambda x: (x.l_word[0].encode("utf-8").lower(), x.l_word[0]))
        return entrytype_lst

    @property
    def OutputFormat(self) -> str:
        return self.output_format if self.output_format else "Stardict"

    @cached_property
    def BaseName(self) -> str:
        p = self.get_path(self.input_dictionary_path)
        return p.stem

    @cached_property
    def OutDir(self) -> Path:
        p = SCRIPT_DIR / f"{self.BaseName}_With_Inflections"
        if not p.exists():
            p.mkdir()
        return p

    @property
    def OutPath(self) -> Path:
        return self.OutDir / self.BaseName

    @cached_property
    def InflDicts(self) -> list[InflBase]:
        infl_lst: list[InflBase] = list()
        if self.unmunched_path:
            infl_lst.append(Unmunched(source_path=self.unmunched_path))
        if self.infl_glos_source_paths:
            for p,f in zip_longest(self.infl_glos_source_paths, self.infl_glos_formats):
                infl_lst.append(
                    InflGlosSource(source_path=p, glos_format=f)
                )
        if self.hunspell_dic_paths:
            for hu in self.hunspell_dic_paths:
                infl_lst.append(
                    HunspellDic(source_path=hu)
                )
        print(f"> Created {len(infl_lst)} inflection {'dictionaries' if len(infl_lst) > 1 else 'dictionary'}.")
        return infl_lst

    def get_infl(self, word: str) -> set[str]:
        res: set[str] = set()
        for infl_dict in self.InflDicts:
            res.update(infl_dict.get_infl(word, self.pfx, self.cross))
        if word in res:
            res.remove(word)
        return res

    @cached_property
    def InputGlos(self) -> Glossary:
        glos = Glossary()
        glos.directRead(filename=self.input_dictionary_path, formatName=self.input_dictionary_format)
        print("> Read input dictionary.")
        return glos

    @cached_property
    def SortedInputGlos(self) -> list[EntryType]:
        _sorted = self.sort_glos(self.InputGlos)
        print("> Sorted input dictionary.")
        return _sorted

    @cached_property
    def InputGlosLength(self) -> int:
        return len(self.SortedInputGlos)

    @cached_property
    def OutputGlos(self) -> Glossary:
        glos_syn = Glossary()
        glos_syn.setInfo("title", self.InputGlos.getInfo("title"))
        glos_syn.setInfo("description", self.InputGlos.getInfo("description"))
        glos_syn.setInfo("author", self.InputGlos.getInfo("author"))
        for data_entry in self.InputGlos:
            if data_entry.defiFormat == "b":
                glos_syn.addEntry(
                    glos_syn.newDataEntry(
                        data_entry.s_word, data_entry.data
                    )
                )
        print("> Created output dictionary.")
        return glos_syn

    def main(self) -> None:
        cnt = 0
        total_new_inflections_found = 0
        for entry in self.SortedInputGlos:
            headword = entry.l_word[0]
            inflections = self.get_infl(headword)
            total_new_inflections_found += len(inflections)
            if self.keep_existing_inflections and (len(entry.l_word) > 1):
                inflections.update(entry.l_word[1:])
            l_word = [headword, *inflections]
            self.OutputGlos.addEntry(
                self.OutputGlos.newEntry(
                    word=l_word,
                    defi=entry.defi,
                    defiFormat=entry.defiFormat
                )
            )
            cnt += 1
            print(
                f"\r> Processed {cnt:,} / {self.InputGlosLength:,} words. Total new inflections found: {total_new_inflections_found:,}",
                end="\r")
        print("")
        if self.output_format == "Stardict":
            self.OutputGlos.write(filename=str(self.OutPath), formatName=self.output_format, dictzip=False)
        else:
            self.OutputGlos.write(filename=str(self.OutPath), formatName=self.output_format)

class ArgparseNS:
    input_dictionary_path: str = None
    input_dictionary_format: str = None
    output_format: str = "Stardict"
    pfx: bool = False
    cross: bool = False
    keep_existing_inflections: bool = False
    infl_glos_source_paths: list[str] = list()
    infl_glos_formats: list[str] = list()
    hunspell_dic_paths: list[str] = list()
    unmunched_path: str = None

if __name__ == '__main__':
    Glossary.init()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=
    """
        Add inflection information to any dictionary format supported by PyGlossary.
    """)
    parser.add_argument("-i", "--input-dictionary", dest="input_dictionary_path",
        help="Input dictionary path.", required=True)

    parser.add_argument("-u", "--unmunched-json", dest="unmunched_path",
        help=f"<language>.json(.gz)")

    parser.add_argument("--glos-infl-sources", dest="infl_glos_source_paths", nargs="+", default=list(),
        help="""Paths of dictionaries that will be used as an inflection source by-themselves or together with unmunched json file.
         Separate multiple sources with a space between them.""")

    parser.add_argument("--glos-infl-source-formats", dest="infl_glos_formats", nargs="+", default=list(),
        choices=Glossary.readFormats, metavar="", help="""--glos-infl-sources dictionary format(s),
         allowed values are same as --input-format. Separate multiple formats with a space between them.""")

    parser.add_argument("-hu", "--hunspell-dic-paths", dest="hunspell_dic_paths", nargs="+", default=list(),
        metavar="", help="""Paths of the Hunspell .dic or .aff files.
        Separate multiple sources with a space between them.""")

    parser.add_argument("--input-format", dest="input_dictionary_format",
        default=None, choices=Glossary.readFormats,
        help=f"Allowed values: {', '.join(Glossary.readFormats)}", metavar="")

    parser.add_argument("--output-format", dest="output_format", default="Stardict",
        choices=Glossary.writeFormats,
        help=f"Allowed values: {', '.join(Glossary.writeFormats)}", metavar="")

    parser.add_argument("-p", "--add-prefixes", dest="pfx", action="store_true", default=False,
                        help="""Add prefixes from the unmunched json.""")
    parser.add_argument("-c", "--add-cross-products", dest="cross", action="store_true", default=False,
                        help="""Add cross products from the unmunched json.""")
    parser.add_argument("-k", "--keep", dest="keep_existing_inflections", action="store_true", default=False,
                        help="Keep existing inflections.")
    args = parser.parse_args(namespace=ArgparseNS)
    if not (args.unmunched_path or args.infl_glos_source_paths or args.hunspell_dic_paths):
        sys.exit("[!] You need to specify at least one inflection source: --unmunched-json, --glos-infl-sources, --hunspell-paths or all.")
    add_inflections = AddInflections(
        input_dictionary_path=args.input_dictionary_path,
        input_dictionary_format=args.input_dictionary_format,
        output_format=args.output_format,
        pfx=args.pfx,
        cross=args.cross,
        keep_existing_inflections=args.keep_existing_inflections,
        infl_glos_source_paths=args.infl_glos_source_paths,
        infl_glos_formats=args.infl_glos_formats,
        hunspell_dic_paths=args.hunspell_dic_paths,
        unmunched_path=args.unmunched_path
    )
    add_inflections.main()