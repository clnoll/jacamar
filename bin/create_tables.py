#!/usr/bin/env python

import re
from operator import itemgetter

from pandas import DataFrame


def create_tables(fp):
    family_table = {}
    genus_table = {}
    species_table = {}
    family_id = genus_id = species_id = 0
    family = None
    for line in fp:
        if is_species_line(line):
            genus, species, species_english = parse_species(line)
            if genus not in genus_table:
                genus_id += 1
                genus_table[genus] = {
                    "id": genus_id,
                    "name": genus,
                    "english_name": "",
                    "family_id": family_table[family]["id"],
                }
            assert (genus, species) not in species_table
            species_id += 1
            species_table[(genus, species)] = {
                "id": species_id,
                "name": species,
                "english_name": species_english,
                "genus_id": genus_table[genus]["id"],
            }
        else:
            family, family_english = parse_family(line)
            assert family not in family_table
            family_id += 1
            family_table[family] = {
                "id": family_id,
                "name": family,
                "english_name": family_english,
            }
    tables = family_table, genus_table, species_table
    return [sorted(table.values(), key=itemgetter("id")) for table in tables]


def is_species_line(line):
    return re.match("^\d+\t", line)


def parse_species(line):
    _, english_name, binomial = line.strip().split("\t")
    genus, name = binomial.split()
    return genus.strip(), name.strip(), english_name.strip()


def parse_family(line):
    english_name, name = line.strip().split(":")
    return name.strip(), english_name.strip()


if __name__ == "__main__":
    import sys

    [path] = sys.argv[1:]
    with open(path) as fp:
        family_table, genus_table, species_table = create_tables(fp)

    for table, columns, path in [
        (family_table, ["id", "name", "english_name"], "tables/family.tsv"),
        (genus_table, ["id", "name", "english_name", "family_id"], "tables/genus.tsv"),
        (species_table, ["id", "name", "english_name", "genus_id"], "tables/species.tsv"),
    ]:
        DataFrame.from_records(table, columns=columns).to_csv(
            path, header=False, index=False, sep="\t"
        )
