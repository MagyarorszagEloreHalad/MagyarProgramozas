#!/usr/bin/env python3
import sys
import glob
import os
import os.path
import codecs
import subprocess
import re

source_to_target = {}
target_to_source = {}

def read_file(fname):
    words = set()

    with codecs.open(fname, "r", "u8") as f:
        for line in f:
            line = line.strip()

            if len(line) == 0:
                continue

            words.add(line.lower())

    return sorted(list(words))

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

def translate_new(word, source_language, target_language):
    result     = subprocess.run(["trans", "-brief", "-source", source_language, "-target", target_language, word], capture_output = True)
    translated = result.stdout.decode("u8", "ignore").strip()
    translated = "".join(re.findall("(\\w+)", translated))
    translated = translated.lower()

    # no overwrites
    while translated in source_to_target:
        translated += translated[-1]

    assert(translated[0].upper() != translated[0])
    return translated

def write_file_line(fname, line):
    with codecs.open(fname, "a+", "u8") as f:
        f.write(line + "\n")

def main():
    global target_to_source
    global source_to_target

    if len(sys.argv) < 3:
        sys.stderr.write("Használat: %s <src nyelv> <target nyelv>\n" % sys.argv[0])
        sys.exit(1)

    source_language = sys.argv[1]
    target_language = sys.argv[2]
    source_to_target = load_translate_db("db/%s_to_%s.txt" % (source_language, target_language))
    target_to_source = load_translate_db("db/%s_to_%s.txt" % (target_language, source_language))

    words = set(sys.stdin.read().split("\n"))
    words = set((word for word in words if len(word) > 0))
    words = set((word.lower() for word in words))

    # filter existing
    words = set((word for word in words if word not in source_to_target))

    for word in words:
        translated = translate_new(word, source_language, target_language)
        source_to_target[translated] = word
        print("%s -> %s" % (word, translated))
        write_file_line("db/%s_to_%s.txt" % (source_language, target_language), "%s = %s" % (word, translated))
        write_file_line("db/%s_to_%s.txt" % (target_language, source_language), "%s = %s" % (translated, word))

main()