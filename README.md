Add inflection information to any dictionary format supported by PyGlossary.

# Usage
```
python add_inflections.py --help
```
```
usage: add_inflections.py [-h] -d DF -j JSON [--input-format] [--output-format] [-p] [-c]

options:
  -h, --help            show this help message and exit
  -d DF, --dict-file DF
                        Input dictionary path. (default: None)
  -j JSON, --unmunched-json JSON
                        <language>.json(.gz) (default: None)
  --input-format        Allowed values: Aard2Slob, ABCMedicalNotes, Almaany, AppleDictBin, BabylonBgl, CC-CEDICT, cc-
                        kedict, CrawlerDir, Csv, Dicformids, Dictcc, Dictcc_split, DictOrg, Dictunformat, DigitalNK,
                        ABBYYLingvoDSL, Dictfile, Edlin, FreeDict, GettextPo, Info, IUPACGoldbook, JMDict, JMnedict,
                        LingoesLDF, OctopusMdict, Stardict, StardictTextual, Tabfile, Wordset, Xdxf, Zim (default:
                        None)
  --output-format       Allowed values: Aard2Slob, AppleDict, CrawlerDir, Csv, Dicformids, DictOrg, DictOrgSource,
                        DiktJson, Epub2, Kobo, Dictfile, Mobi, Edlin, GettextPo, HtmlDir, Info, Json, LingoesLDF, Sql,
                        Stardict, StardictTextual, Tabfile, Yomichan (default: Stardict)
  -p, --add-prefixes
  -c, --add-cross-products
```

## Example Usage
To illustrate, in order to add inflections to a DSL dictionary and saving the output in Stardict Textual Dictionary Format call the script as below:

``` 
python add_inflections.py -d dict_without_inflections.dsl -j '.\inflection_data\English (American).json.gz' --output-format StardictTextual
```

- If you omit the `--input-format`, PyGlossary will try to infer the format from the file extension.
- If you omit the `--output-format`, output will default to StarDict format.

# Required Packages

```
pip install pyglossary==4.6.1
```