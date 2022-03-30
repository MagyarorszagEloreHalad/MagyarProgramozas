#!/usr/bin/env python3
import sys
import codecs
import os
import os.path

source_to_translated = {}
translated_to_source = {}

class ParsedWord:
    def __init__(self, string):
        self.orig   = string
        self.string = string

    def __repr__(self):
        return "ParsedWord(%s)" % self.string

    def collect(self):
        return self.string

    def match(self, to):
        return self.orig == to

    def translate(self, to):
        self.string = to

class ParsedSpecialCharacters:
    def __init__(self, string):
        self.string = string

    def __repr__(self):
        return "%s" % self.string

    def collect(self):
        return self.string

class ParsedString:
    def __init__(self, string):
        self.string = string

    def __repr__(self):
        return "%s" % self.string

    def collect(self):
        return self.string

class ParsedText:
    def __init__(self):
        self.elems = []

    def add_elem(self, elem):
        self.elems.append(elem)

    def __repr__(self):
        return "".join(repr(x) for x in self.elems)

    def collect(self):
        return "".join((x.collect() for x in self.elems))

    def words(self):
        words = [x.string for x in self.elems if isinstance(x, ParsedWord)]
        words = set(words)
        return words

    def translate(self, tl_src, tl_to):
        for i in range(0, len(self.elems)):
            elem = self.elems[i]

            if isinstance(elem, ParsedWord) and elem.match(tl_src):
                elem.translate(tl_to)

def boundary(word, i):
    ch = word[i]

    if not ch.isupper():
        return False

    if i < len(word) - 1:
        next = word[i + 1]

        if next.islower():
            return True

    if i == len(word) - 1:
        prev = word[i - 1]

        if prev.islower():
            return True

    return False

def split_word(word):
    results = []
    temp    = []

    for i in range(0, len(word)):
        ch = word[i]

        if boundary(word, i) and len(temp) > 0:
            results.append("".join(temp))
            temp = []

        temp.append(ch)

    if len(temp) > 0:
        results.append("".join(temp))

    return results

def parse(content):
    result = ParsedText()

    if len(content) == 0:
        return result

    last_was_alpha = content[0].isalpha()
    temp = []
    i = 0

    while i < len(content):
        ch = content[i]
        curr_is_alpha = ch.isalpha()

        if last_was_alpha and not curr_is_alpha:
            result.add_elem(ParsedWord("".join(temp)))
            temp = []
        elif not last_was_alpha and curr_is_alpha:
            result.add_elem(ParsedSpecialCharacters("".join(temp)))
            temp = []

        last_was_alpha = curr_is_alpha
        temp.append(ch)
        i += 1
    
    if len(temp) > 0:
        if last_was_alpha:
            result.add_elem(ParsedWord("".join(temp)))
        else:
            result.add_elem(ParsedSpecialCharacters("".join(temp)))

    return result

def translate(translate_db, part):
    result = translate_db.get(part.lower())

    if result is None:
        return result

    if part.isupper():
        return result.upper()

    if part[0].isupper():
        result = result[0].upper() + result[1:]
    
    return result

def process(translate_db):
    content = sys.stdin.read()
    parsed = parse(content)
    missing = set()

    for word in parsed.words():
        translate_to = []

        for part in split_word(word):
            part_translation = translate(translate_db, part)

            if part_translation is None:
                missing.add(part.lower())
                part_translation = part

            translate_to.append(part_translation)

        translate_to = "".join(translate_to)
        parsed.translate(word, translate_to)

    final = parsed.collect()
    sys.stdout.write(final)

    if len(missing) > 0:
        for x in sorted(missing):
            sys.stderr.write(x + "\n")

def load_translate_db(fname):
    result = {}

    if not os.path.exists(fname):
        return result

    with codecs.open(fname, "r", "u8") as f:
        for line in f:
            line = line.strip()

            if len(line) == 0:
                continue

            tl_from, tl_to = (x.strip() for x in line.split("="))
            result[tl_from] = tl_to

    return result

def check_consistency():
    for original in translated_to_source.keys():
        translated = translated_to_source[original]
        assert(source_to_translated[translated] == original)

def main():
    global translated_to_source
    global source_to_translated

    if len(sys.argv) < 3:
        sys.stderr.write("Használat: %s <src nyelv> <target nyelv>\n" % sys.argv[0])
        sys.exit(1)

    source_language = sys.argv[1]
    target_language = sys.argv[2]
    source_to_translated = load_translate_db("db/%s_to_%s.txt" % (source_language, target_language))
    translated_to_source = load_translate_db("db/%s_to_%s.txt" % (target_language, source_language))
    check_consistency()
    process(source_to_translated)

main()