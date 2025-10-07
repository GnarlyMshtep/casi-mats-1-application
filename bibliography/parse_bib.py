import bibtexparser
from IPython import embed
from bibtexparser.customization import author, splitname
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--arxiv-warn', action='store_true', 
                        help='alert about arxiv citations')
parser.add_argument('--allow-articles', action='store_true', 
                        help='if not specified, will yell at you to put things into inproceedings fmt')
parser.add_argument('--keep-keys', action='store_true',
                        help='do not update bibtex keys')
args = parser.parse_args()

ignored = ["the", "do", "how", "on", "many", "a", "an", 
           "is", "are", "(un)", "what", "we", "de"]
disallowed = [":", "{", "}", ",", "-", r"\'", r"\`", "`", "\\", '"', '.', ' ', '(', ')', "'"]

def find_first_word(title):
    candidates = title.split()
    for cand in candidates:
        unhyphenated = cand.split("-")
        for tok in unhyphenated:
            if (tok not in ignored):
                return tok
    raise ValueError("No valid first word found in title", title)

def make_key(entry, allow_hyphen_author=False):
    good_author = splitname(entry['author'][0])["last"][0].lower() 
    if not allow_hyphen_author:
        good_author = good_author.split("-")[0]
    good_title = find_first_word(entry['title'].lower())
    key = good_author + entry['year'].lower() + good_title
    for c in disallowed:
        key = key.replace(c, "")
    return key

class ArticleException(ValueError):
    pass

with open('bib.bib') as bibtex_file:
    bib_database = bibtexparser.load(bibtex_file)
    entries = bib_database.entries
    new_entries = []
    num_bad = 0
    for e in entries:
        try:
            new_e = {k: e[k] for k in e}
            formatted_key = make_key(author(new_e), True)
            new_e = {k: e[k] for k in e}
            formatted_key_2 = make_key(author(new_e), False)
            new_e = {k: e[k] for k in e}
            if not args.allow_articles and (new_e['ENTRYTYPE'] == 'article'):
                raise ArticleException('No articles allowed!')
            if (formatted_key != e['ID']) and (formatted_key_2 != e['ID']):
                new_e['ID'] = formatted_key
                num_bad += 1
                print("New:", formatted_key, " | Old:",  e['ID'])
            if (new_e['ENTRYTYPE'] == 'inproceedings') and ('journal' in new_e):
                if 'booktitle' in new_e:
                    raise ValueError(f"Entry {new_e['ID']} has both journal and booktitle")
                new_e['booktitle'] = new_e['journal']
                del new_e['journal']

            new_entries.append(new_e)
        except Exception as ee:
            print('Errored on', e, ee)
            new_entries.append(e)

    print('-' * 80)
    if args.arxiv_warn:
        for e in new_entries:
            if 'booktitle' in e and 'arxiv' in e['booktitle'].lower():
                print('Is there a newer version of', e['title'], '?')

    bib_database.entries = new_entries
    with open('fmt_bib.bib', 'w') as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file)
