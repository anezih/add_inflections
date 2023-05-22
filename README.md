Add inflection information to any dictionary format supported by PyGlossary.

# Usage
```
python add_inflections.py --help
```
```
usage: add_inflections.py [-h] -d DF [-j JSON] [--glos-infl-source GS] [--glos-infl-source-format] [--input-format]
                          [--output-format] [-p] [-c] [-k]

options:
  -h, --help            show this help message and exit
  -d DF, --dict-file DF
                        Input dictionary path. (default: None)
  -j JSON, --unmunched-json JSON
                        <language>.json(.gz) (default: None)
  --glos-infl-source GS
                        Dictionary that will be used as an inflection source by-itself or together with json file.
                        (default: None)
  --glos-infl-source-format
                        --glos-infl-source dictionary format, allowed values are same as --input-format (default: )
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
  -k, --keep            Keep existing inflections. (default: False)
```

## Example Usage
To illustrate, in order to add inflections to a DSL dictionary and saving the output in Stardict Textual Dictionary Format call the script as below:

``` 
python add_inflections.py -d dict_without_inflections.dsl -j '.\inflection_data\English (American).json.gz' --output-format StardictTextual
```

- If you omit the `--input-format`, PyGlossary will try to infer the format from the file extension.
- If you omit the `--output-format`, output will default to StarDict format.

Passing another dictionary as an inflection data source together with unmunched json (FR.xml is a StardictTextual dictionary.):
```
python add_inflections.py -d fra_tur.dsl --glos-infl-source FR.xml --glos-infl-source-format StardictTextual -j .\inflection_data\French.json.gz
```
# Required Packages

```
pip install pyglossary==4.6.1
```
