import argparse
import json
import os
import random
import shutil
from pathlib import Path


def split_dataset(
    source_dir: str,
    train_dir: str,
    test_dir: str,
    train_ratio: float = 0.8,
    seed: int = 42,
):
    source_path = Path(source_dir).resolve()
    train_path = Path(train_dir).resolve()
    test_path = Path(test_dir).resolve()

    if not source_path.exists() or not source_path.is_dir():
        raise FileNotFoundError(f"Source dataset path not found: {source_path}")

    train_path.mkdir(parents=True, exist_ok=True)
    test_path.mkdir(parents=True, exist_ok=True)

    random.seed(seed)
    summary = {
        "source": str(source_path),
        "train": str(train_path),
        "test": str(test_path),
        "categories": {},
    }

    for category_dir in sorted(os.listdir(source_path)):
        category_src = source_path / category_dir
        if not category_src.is_dir():
            continue

        category_train = train_path / category_dir
        category_test = test_path / category_dir
        category_train.mkdir(parents=True, exist_ok=True)
        category_test.mkdir(parents=True, exist_ok=True)

        image_files = [
            f
            for f in sorted(os.listdir(category_src))
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        if not image_files:
            continue

        random.shuffle(image_files)
        split_index = int(len(image_files) * train_ratio)
        split_index = max(1, min(split_index, len(image_files) - 1))

        train_files = image_files[:split_index]
        test_files = image_files[split_index:]

        for filename in train_files:
            shutil.copy2(category_src / filename, category_train / filename)

        for filename in test_files:
            shutil.copy2(category_src / filename, category_test / filename)

        summary["categories"][category_dir] = {
            "total": len(image_files),
            "train": len(train_files),
            "test": len(test_files),
        }

    manifest_path = source_path.parent / "split_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as manifest_file:
        json.dump(summary, manifest_file, indent=2, ensure_ascii=False)

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Split Fruits_data_processed into train and test folders."
    )
    parser.add_argument(
        "--source",
        type=str,
        default="static/Fruits_data_processed",
        help="Source dataset path.",
    )
    parser.add_argument(
        "--train-dir",
        type=str,
        default="static/Fruits_data_train",
        help="Output train dataset directory.",
    )
    parser.add_argument(
        "--test-dir",
        type=str,
        default="static/Fruits_data_test",
        help="Output test dataset directory.",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.8,
        help="Train ratio (value between 0 and 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for dataset split.",
    )

    args = parser.parse_args()
    summary = split_dataset(
        source_dir=args.source,
        train_dir=args.train_dir,
        test_dir=args.test_dir,
        train_ratio=args.ratio,
        seed=args.seed,
    )

    print("Dataset split completed.")
    for category, counts in summary["categories"].items():
        print(
            f"{category}: total={counts['total']}, train={counts['train']}, test={counts['test']}"
        )
    print(
        f"Manifest written to {Path(args.source).resolve().parent / 'split_manifest.json'}"
    )


if __name__ == "__main__":
    main()
