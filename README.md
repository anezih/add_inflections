Add inflection information to any dictionary format supported by PyGlossary.

# Usage
```
python add_inflections.py --help
```
```
usage: add_inflections.py [-h] -i INPUT_DICTIONARY_PATH [-u UNMUNCHED_PATH] [--glos-infl-sources INFL_GLOS_SOURCE_PATHS [INFL_GLOS_SOURCE_PATHS ...]]
                          [--glos-infl-source-formats  [...]] [-hu  [...]] [--input-format] [--output-format] [-p] [-c] [-k]

Add inflection information to any dictionary format supported by PyGlossary.

options:
  -h, --help            show this help message and exit
  -i INPUT_DICTIONARY_PATH, --input-dictionary INPUT_DICTIONARY_PATH
                        Input dictionary path. (default: None)
  -u UNMUNCHED_PATH, --unmunched-json UNMUNCHED_PATH
                        <language>.json(.gz) (default: None)
  --glos-infl-sources INFL_GLOS_SOURCE_PATHS [INFL_GLOS_SOURCE_PATHS ...]
                        Paths of dictionaries that will be used as an inflection source by-themselves or together with unmunched json file. Separate
                        multiple sources with a space between them. (default: [])
  --glos-infl-source-formats  [ ...]
                        --glos-infl-sources dictionary format(s), allowed values are same as --input-format. Separate multiple formats with a space
                        between them. (default: [])
  -hu  [ ...], --hunspell-dic-paths  [ ...]
                        Paths of the Hunspell .dic or .aff files. Separate multiple sources with a space between them. (default: [])
  --input-format        Allowed values: Aard2Slob, ABCMedicalNotes, Almaany, AppleDictBin, BabylonBgl, CC-CEDICT, cc-kedict, CrawlerDir, Csv, Dicformids,
                        Dictcc, Dictcc_split, DictOrg, Dictunformat, DigitalNK, ABBYYLingvoDSL, Dictfile, Edlin, FreeDict, GettextPo, Info, IUPACGoldbook,
                        JMDict, JMnedict, LingoesLDF, OctopusMdict, Stardict, StardictTextual, Tabfile, Wordset, Xdxf, Zim (default: None)
  --output-format       Allowed values: Aard2Slob, AppleDict, CrawlerDir, Csv, Dicformids, DictOrg, DictOrgSource, DiktJson, Epub2, Kobo, Dictfile, Mobi,
                        Edlin, GettextPo, HtmlDir, Info, Json, LingoesLDF, Sql, Stardict, StardictTextual, Tabfile, Yomichan (default: Stardict)
  -p, --add-prefixes    Add prefixes from the unmunched json. (default: False)
  -c, --add-cross-products
                        Add cross products from the unmunched json. (default: False)
  -k, --keep            Keep existing inflections. (default: False)
```

## Example Usage
To illustrate, in order to add inflections from multiple sources to a DSL dictionary and saving the output in Stardict Textual Dictionary Format call the script as below:

```
python .\add_inflections.py -i .\test\fra_tur.dsl -u .\inflection_data\French.json.gz --glos-infl-sources '.\test\MOBI_FR.xml' .\test\Babylon_FR.xml --glos-infl-source-formats StardictTextual StardictTextual -hu .\test\fr.dic --output-format StardictTextual
```

In the example above we have used 4 inflection sources:
- French.json.gz from the inflection_data folder,
- MOBI_FR.xml StardictTextual dictionary,
- Babylon_FR.xml StardictTextual dictionary,
- fr.dic Hunspell dictionary

### Some Notes:
- If you omit the `--input-format`, PyGlossary will try to infer the format from the file extension.
- If you omit the `--output-format`, output will default to StarDict format.
- It is safer to specify all --glos-infl-sources formats in the --glos-infl-source-formats rather than expecting PyGlossary to infer the formats.

# Required Packages

```
pip install pyglossary==4.6.1
pip install spylls
```