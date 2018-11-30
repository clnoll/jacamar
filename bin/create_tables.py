#!/usr/bin/env python
import os
import re
import sys
from functools import partial
from operator import itemgetter

from clint.textui import colored
from pandas import DataFrame

red = partial(colored.red, bold=True)

ORDER_TABLE = [
    {"id": 1, "name": "Tinamiformes", "english_name": "Tinamous"},
    {"id": 2, "name": "Craciformes", "english_name": "Guans, Curassows, Chachalacas"},
    {"id": 3, "name": "Galliformes", "english_name": "Pheasants, Quails, Grouse, etc"},
    {"id": 4, "name": "Columbiformes", "english_name": "Doves, Pigeons"},
    {"id": 5, "name": "Cuculiformes", "english_name": "Cuckoos"},
    {"id": 6, "name": "Caprimulgiformes", "english_name": "Nightjars"},
    {"id": 7, "name": "Apodiformes", "english_name": "Swifts, Hummingbirds"},
    {"id": 8, "name": "Accipitriformes", "english_name": "Hawks"},
    {"id": 9, "name": "Strigiformes", "english_name": "Owls"},
    {"id": 10, "name": "Trogoniformes", "english_name": "Trogons"},
    {"id": 11, "name": "Coraciiformes", "english_name": "Motmots, Kingfishers"},
    {"id": 12, "name": "Galbuliformes", "english_name": "Jacamars"},
    {"id": 13, "name": "Piciformes", "english_name": "Woodpeckers"},
    {"id": 14, "name": "Falconiformes", "english_name": "Falcons"},
    {"id": 15, "name": "Psittaciformes", "english_name": "Parrots"},
    {"id": 16, "name": "Passeriformes", "english_name": "Passerines"},
]

FAMILY_DATA = {
    "Tinamidae": {"order_id": 1, "weight": 800},
    "Cracidae": {"order_id": 2, "weight": 1000},
    "Odontophoridae": {"order_id": 3, "weight": 300},
    "Columbidae": {"order_id": 4, "weight": 400},
    "Cuculidae": {"order_id": 5, "weight": 115},
    "Caprimulgidae": {"order_id": 6, "weight": 60},
    "Steatornithidae": {"order_id": 6, "weight": 60},
    "Apodidae": {"order_id": 7, "weight": 25},
    "Trochilidae": {"order_id": 7, "weight": 5},
    "Cathartidae": {"order_id": 8, "weight": 1400},
    "Accipitridae": {"order_id": 8, "weight": 800},
    "Strigidae": {"order_id": 9, "weight": 500},
    "Trogonidae": {"order_id": 10, "weight": 85},
    "Momotidae": {"order_id": 11, "weight": 77},
    "Alcedinidae": {"order_id": 11, "weight": 90},
    "Bucconidae": {"order_id": 12, "weight": 27},
    "Galbulidae": {"order_id": 12, "weight": 28},
    "Ramphastidae": {"order_id": 13, "weight": 280},
    "Picidae": {"order_id": 13, "weight": 90},
    "Falconidae": {"order_id": 14, "weight": 200},
    "Psittacidae": {"order_id": 15, "weight": 150},
    "Thamnophilidae": {"order_id": 16, "weight": 25},
    "Grallariidae": {"order_id": 16, "weight": 50},
    "Rhinocryptidae": {"order_id": 16, "weight": 15},
    "Furnariidae": {"order_id": 16, "weight": 30},
    "Tyrannidae": {"order_id": 16, "weight": 25},
    "Cotingidae": {"order_id": 16, "weight": 60},
    "Pipridae": {"order_id": 16, "weight": 15},
    "Tityridae": {"order_id": 16, "weight": 25},
    "Vireonidae": {"order_id": 16, "weight": 17},
    "Corvidae": {"order_id": 16, "weight": 90},
    "Hirundinidae": {"order_id": 16, "weight": 15},
    "Troglodytidae": {"order_id": 16, "weight": 10},
    "Polioptilidae": {"order_id": 16, "weight": 7},
    "Turdidae": {"order_id": 16, "weight": 60},
    "Fringillidae": {"order_id": 16, "weight": 30},
    "Rhodinocichlidae": {"order_id": 16, "weight": 30},
    "Passerellidae": {"order_id": 16, "weight": 25},
    "Icteridae": {"order_id": 16, "weight": 80},
    "Parulidae": {"order_id": 16, "weight": 11},
    "Cardinalidae": {"order_id": 16, "weight": 30},
    "Thraupidae": {"order_id": 16, "weight": 25},
}


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
            family_table[family].update(FAMILY_DATA[family])

    tables = [family_table, genus_table, species_table]
    tables = [sorted(table.values(), key=itemgetter("id")) for table in tables]
    return [ORDER_TABLE] + tables


def create_recording_table(dir, species_table):
    recording_table = []
    recordings = list(
        filter(
            bool,
            (parse_recording_file_name(file) for file in os.listdir(dir) if file.endswith(".mp3")),
        )
    )
    recording_id = 0
    for species in species_table:
        species_recordings = match_species_recordings(species["english_name"], recordings)
        if species_recordings:
            for recording in species_recordings:
                recording_id += 1
                recording_table.append(
                    {
                        "id": recording_id,
                        "path": os.path.join(dir, recording["file"]),
                        "type": recording["type"].lower(),
                        "species_id": species["id"],
                    }
                )
        else:
            error(f"Failed to find recordings for: {species['english_name']}")

    return recording_table


def parse_recording_file_name(file):
    # E.g. "2326 1 Dusky-chested Flycatcher 1 Song.mp3"
    regexp = r"""
    ^
    \d+
    \s+
    \d+
    \s+
    (?P<english_name>[a-zA-Z- ']+)
    \s+
    \d+
    \s+
    (?P<type>[^.]+)
    \.mp3$
    """
    match = re.match(regexp, file, re.VERBOSE)
    if not match:
        error(f"Failed to parse file name: {file}")
        return None
    recording = match.groupdict()
    recording["file"] = file
    return recording


def match_species_recordings(english_name, recordings):
    canonicalized_english_name = canonicalize_name(english_name)
    return [
        r for r in recordings if canonicalize_name(r["english_name"]) == canonicalized_english_name
    ]


def canonicalize_name(name):
    return name.lower().replace("-", " ")


def is_species_line(line):
    return re.match("^\d+\t", line)


def parse_species(line):
    _, english_name, binomial = line.strip().split("\t")
    genus, name = binomial.split()
    return genus.strip(), name.strip(), english_name.strip()


def parse_family(line):
    english_name, name = line.strip().split(":")
    return name.strip(), english_name.strip()


def error(msg):
    print(red(msg), file=sys.stderr)


if __name__ == "__main__":
    [checklist_file, recordings_dir] = sys.argv[1:]
    with open(checklist_file) as fp:
        order_table, family_table, genus_table, species_table = create_tables(fp)

    recording_table = create_recording_table(recordings_dir, species_table)

    for table, columns, path in [
        (order_table, ["id", "name", "english_name"], "tables/order.tsv"),
        (family_table, ["id", "name", "english_name", "order_id", "weight"], "tables/family.tsv"),
        (genus_table, ["id", "name", "english_name", "family_id"], "tables/genus.tsv"),
        (species_table, ["id", "name", "english_name", "genus_id"], "tables/species.tsv"),
        (recording_table, ["id", "path", "species_id", "type"], "tables/recording.tsv"),
    ]:
        DataFrame.from_records(table, columns=columns).to_csv(
            path, header=False, index=False, sep="\t"
        )
