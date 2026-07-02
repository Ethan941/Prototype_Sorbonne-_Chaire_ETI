from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd


DATA_DIR = Path("/workspace/.cache")
ISOCHRONES_FILE = DATA_DIR / "isochrones_walking_15min.geojson"
CLASSIFICATION_FILE = DATA_DIR / "bpe24key_classification(2).csv"

FUNCTIONS = [
    "habiter",
    "travailler",
    "s_approvisionner",
    "etre_en_forme",
    "apprendre",
    "s_epanouir",
]

LEVELS = ["proximite", "intermediaire", "centralite", "prioritaire"]


def main() -> None:
    classification = pd.read_csv(CLASSIFICATION_FILE, sep=";", encoding="utf-8")
    classification.columns = classification.columns.str.strip()
    class_types = set(classification["typequ"].astype(str).str.strip())

    with ISOCHRONES_FILE.open(encoding="utf-8") as handle:
        data = json.load(handle)

    features = data["features"]
    props = [feature.get("properties", {}) for feature in features]

    print("=== AUDIT DONNEES HQVS ===")
    print(f"Isochrones: {len(features)}")
    print(f"Types BPE classification: {classification['typequ'].nunique()}")
    print()

    print("Fonctions sociales:")
    for col in FUNCTIONS:
        print(f"- {col}: {sum(bool(p.get(col)) for p in props)}")
    print()

    print("Niveaux de proximite:")
    for col in LEVELS:
        print(f"- {col}: {sum(bool(p.get(col)) for p in props)}")
    print()

    typequ_counter = Counter(str(p.get("typequ")) for p in props)
    matched = sum(count for typequ, count in typequ_counter.items() if typequ in class_types)
    print(f"Isochrones matchees avec la classification: {matched}/{len(features)}")
    print()

    print("Top 15 typequ:")
    for typequ, count in typequ_counter.most_common(15):
        print(f"- {typequ}: {count}")


if __name__ == "__main__":
    main()
