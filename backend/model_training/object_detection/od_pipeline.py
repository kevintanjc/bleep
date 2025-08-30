import argparse
import io
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml
from datasets import load_dataset
from PIL import Image
import numpy as np
import json

def export_hf_parquet_to_yolo(
    repo_id: str,
    out_root: Path,
    split_map: dict = None,  # e.g., {"train": "train", "val": "validation"}
    class_name: str = "license-plate",
):
    if split_map is None:
        split_map = {"train": "train", "val": "validation"}

    names = {0: class_name}
    for split_key, hf_split in split_map.items():
        ds = load_dataset(repo_id, split=hf_split, streaming=False)
        img_dir = out_root / split_key / "images"
        lbl_dir = out_root / split_key / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(ds):
            # row["image"] is a PIL Image or dict depending on version, normalize to PIL
            im = row["image"]
            if isinstance(im, dict) and "bytes" in im:
                im = Image.open(io.BytesIO(im["bytes"])).convert("RGB")
            w = int(row.get("width", im.width))
            h = int(row.get("height", im.height))

            stem = f"{i:07d}"
            img_path = img_dir / f"{stem}.jpg"
            im.save(img_path, quality=90)

            # objects.bbox is [[x, y, w, h], ...] in pixels
            bboxes = row["objects"]["bbox"]
            cats = row["objects"]["category"]

            lines = []
            for bb, cat in zip(bboxes, cats):
                x, y, bw, bh = map(float, bb)
                # convert to YOLO normalized cx, cy, bw, bh
                cx = (x + bw / 2.0) / w
                cy = (y + bh / 2.0) / h
                nw = bw / w
                nh = bh / h
                if nw <= 0 or nh <= 0:
                    continue
                lines.append(f"{int(cat)} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

            (lbl_dir / f"{stem}.txt").write_text("\n".join(lines))

    # write data yaml
    data_yaml = {
        "path": str(out_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "names": names,
    }
    (out_root / "license_plate.yaml").write_text(
        yaml.safe_dump(data_yaml, sort_keys=False)
    )
    return out_root / "license_plate.yaml"


# Optional training, guarded import
def _maybe_import_ultralytics():
    try:
        from ultralytics import YOLO
        return YOLO
    except Exception:
        return None

REQUIRED_COL_SETS = [
    # Common detection schema with absolute boxes
    {"image_path", "xmin", "ymin", "xmax", "ymax", "class"},
    # Alternate names
    {"file_path", "xmin", "ymin", "xmax", "ymax", "class"},
    # Already-normalized YOLO format
    {"image_path", "x_center", "y_center", "width", "height", "class", "normalized"},
]

def read_config(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_schema(df: pd.DataFrame) -> str:
    cols = set(df.columns.str.lower())
    for idx, req in enumerate(REQUIRED_COL_SETS):
        if req.issubset(cols):
            return f"s{idx}"
    # Try weak match for absolute box case with any image col guess
    image_cols = {"image_path", "file_path", "path"}
    if {"xmin", "ymin", "xmax", "ymax", "class"}.issubset(cols) and len(cols & image_cols) > 0:
        return "s_abs_generic"
    raise ValueError(f"Unsupported columns. Got {sorted(df.columns)}")

def normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    # Lowercase for uniform handling
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    schema = find_schema(df)

    # Ensure an 'image_path' column
    if "image_path" not in df.columns:
        if "file_path" in df.columns:
            df["image_path"] = df["file_path"]
        elif "path" in df.columns:
            df["image_path"] = df["path"]
        else:
            raise ValueError("No image path column found")

    # If boxes are absolute, convert to YOLO normalized later once we know image sizes.
    # If already normalized, ensure a flag
    if {"x_center", "y_center", "width", "height"}.issubset(df.columns) and "normalized" in df.columns:
        # Assume True means already in 0..1
        return df

    # Mark as not normalized yet
    df["normalized"] = False
    return df

def load_parquets(parquet_paths: List[Path]) -> pd.DataFrame:
    parts = []
    for p in parquet_paths:
        if not p.exists():
            raise FileNotFoundError(f"Missing parquet file: {p}")
        parts.append(pd.read_parquet(p))
    if not parts:
        raise ValueError("No parquet data found")
    df = pd.concat(parts, ignore_index=True)
    return df

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def yolo_box_from_abs(xmin, ymin, xmax, ymax, width, height) -> Tuple[float, float, float, float]:
    # Guard
    xmin = float(xmin)
    ymin = float(ymin)
    xmax = float(xmax)
    ymax = float(ymax)
    iw = float(width)
    ih = float(height)
    bw = max(0.0, xmax - xmin)
    bh = max(0.0, ymax - ymin)
    cx = xmin + bw / 2.0
    cy = ymin + bh / 2.0
    # Normalize
    return cx / iw, cy / ih, bw / iw, bh / ih

def read_image_size_fast(img_path: Path) -> Tuple[int, int]:
    # Pillow is simple and reliable
    from PIL import Image
    with Image.open(img_path) as im:
        w, h = im.size
    return w, h

def stratified_split_by_image(df: pd.DataFrame, seed: int, ratios=(0.7, 0.2, 0.1)) -> Dict[str, List[str]]:
    # Group by image, then random shuffle unique images
    rng = np.random.default_rng(seed)
    images = df["image_path"].astype(str).unique().tolist()
    rng.shuffle(images)

    n = len(images)
    n_train = int(round(ratios[0] * n))
    n_val = int(round(ratios[1] * n))
    n_test = n - n_train - n_val
    return {
        "train": images[:n_train],
        "val": images[n_train:n_train + n_val],
        "test": images[n_train + n_val:],
    }

def write_yolo_dataset(
    df: pd.DataFrame,
    image_root: Path,
    out_root: Path,
    class_map: Dict[str, int],
    seed: int,
    ratios=(0.7, 0.2, 0.1),
) -> Dict[str, int]:
    ensure_dir(out_root)
    splits = stratified_split_by_image(df, seed, ratios)

    # Prepare folders
    folders = {}
    for split in ["train", "val", "test"]:
        folders[split] = {
            "images": out_root / split / "images",
            "labels": out_root / split / "labels",
        }
        ensure_dir(folders[split]["images"])
        ensure_dir(folders[split]["labels"])

    # Index rows by image for efficient loop
    by_image = {img: rows for img, rows in df.groupby("image_path")}
    stats = {"train": 0, "val": 0, "test": 0}

    for split, img_list in splits.items():
        for rel_img in img_list:
            src_img = (image_root / rel_img).resolve() if not Path(rel_img).is_absolute() else Path(rel_img)
            if not src_img.exists():
                # Try fallback: if rel path already absolute-ish in parquet, keep as is
                src_img = Path(rel_img)
            if not src_img.exists():
                # Skip missing
                continue

            # Copy image
            dst_img = folders[split]["images"] / src_img.name
            if not dst_img.exists():
                shutil.copy2(src_img, dst_img)

            # Build label file
            rows = by_image.get(rel_img)
            if rows is None or len(rows) == 0:
                # no annotations, write empty file so YOLO does not crash
                (folders[split]["labels"] / (dst_img.stem + ".txt")).write_text("")
                continue

            # Determine if boxes already normalized
            normalized = bool(rows["normalized"].iloc[0]) if "normalized" in rows.columns else False

            # Get image size once if needed
            if normalized:
                w, h = None, None
            else:
                w, h = read_image_size_fast(src_img)

            lines = []
            for _, r in rows.iterrows():
                # Class id mapping
                cls_key = str(r["class"])
                if cls_key not in class_map:
                    # Try stringifying everything to map
                    if str(int(r["class"])) in class_map:
                        cls_key = str(int(r["class"]))
                    else:
                        raise ValueError(f"Class {r['class']} not in class_map")
                cls_id = class_map[cls_key]

                if normalized:
                    xc = float(r["x_center"])
                    yc = float(r["y_center"])
                    bw = float(r["width"])
                    bh = float(r["height"])
                else:
                    xc, yc, bw, bh = yolo_box_from_abs(r["xmin"], r["ymin"], r["xmax"], r["ymax"], w, h)

                # Clip to [0,1] to avoid format issues
                xc = float(np.clip(xc, 0, 1))
                yc = float(np.clip(yc, 0, 1))
                bw = float(np.clip(bw, 0, 1))
                bh = float(np.clip(bh, 0, 1))

                # Skip degenerate boxes
                if bw <= 0 or bh <= 0:
                    continue

                lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

            label_path = folders[split]["labels"] / (dst_img.stem + ".txt")
            label_path.write_text("\n".join(lines))
            stats[split] += len(lines)

    return stats

def write_yolo_data_yaml(out_root: Path, names: Dict[int, str], file_path: Path) -> None:
    content = {
        "path": str(out_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "names": {int(k): v for k, v in names.items()},
    }
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f, sort_keys=False)

def maybe_train(cfg: Dict, data_yaml_path: Path) -> None:
    train_cfg = cfg.get("train", {})
    if not bool(train_cfg.get("enabled", False)):
        print("Training disabled. Skipping YOLOv8 train step.")
        return

    YOLO = _maybe_import_ultralytics()
    if YOLO is None:
        print("Ultralytics not installed. Run: pip install ultralytics torch torchvision")
        return

    base = train_cfg.get("base", "yolov8n.pt")
    device = str(train_cfg.get("device", "0"))
    imgsz = int(train_cfg.get("imgsz", 640))
    epochs = int(train_cfg.get("epochs", 100))
    batch = int(train_cfg.get("batch", 16))
    workers = int(train_cfg.get("workers", 4))
    project = str(train_cfg.get("project", "lp-det"))
    name = str(train_cfg.get("name", "yolov8-finetune"))
    mosaic = float(train_cfg.get("mosaic", 1.0))
    mixup = float(train_cfg.get("mixup", 0.0))
    patience = int(train_cfg.get("patience", 15))

    model = YOLO(base)
    print("Starting YOLOv8 training")
    model.train(
        data=str(data_yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=workers,
        device=device,
        project=project,
        name=name,
        mosaic=mosaic,
        mixup=mixup,
        patience=patience,
        exist_ok=True,
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, required=True)
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = read_config(cfg_path)

    proj_root = Path(cfg.get("project_root", ".")).resolve()
    out_root = proj_root / cfg["data"]["output_dataset_dir"]
    out_root.mkdir(parents=True, exist_ok=True)

    source_type = cfg["data"].get("source_type", "local_parquet")

    if source_type == "hf_parquet":
        # Hugging Face parquet with embedded images and objects.bbox
        repo_id = cfg["data"].get("hf_repo_id", "jtatman/license-plate-finetuning")
        split_map = cfg["data"].get("hf_split_map", {"train": "train", "val": "validation"})
        class_name = cfg["data"].get("class_name", "license-plate")

        print(f"Exporting HF dataset {repo_id} to YOLO folder at {out_root}")
        yolo_yaml = export_hf_parquet_to_yolo(
            repo_id=repo_id,
            out_root=out_root,
            split_map=split_map,
            class_name=class_name,
        )
        print(f"Wrote YOLO data yaml to {yolo_yaml}")

        # Optional manual resplit
        force_resplit = bool(cfg["data"].get("force_resplit", False))
        if force_resplit:
            # Merge current train and val, then re-split by images
            print("Force re-splitting to 70,20,10 by image")
            # Load labels for both splits and reconstruct a small index
            def collect_split(split):
                img_dir = out_root / split / "images"
                lbl_dir = out_root / split / "labels"
                items = []
                for lbl_file in lbl_dir.glob("*.txt"):
                    items.append({"image_path": str((img_dir / (lbl_file.stem + ".jpg")).resolve())})
                return items

            merged = collect_split("train") + collect_split("val")
            df = pd.DataFrame(merged)
            ratios = tuple(cfg["data"].get("splits", [0.7, 0.2, 0.1]))
            seed = int(cfg["data"].get("seed", 1337))

            # Use existing split util if present, else simple shuffle
            images = df["image_path"].astype(str).unique().tolist()
            rng = np.random.default_rng(seed)
            rng.shuffle(images)
            n = len(images)
            n_train = int(round(ratios[0] * n))
            n_val = int(round(ratios[1] * n))
            new = {
                "train": images[:n_train],
                "val": images[n_train:n_train + n_val],
                "test": images[n_train + n_val:],
            }

            # Nuke old layout and rebuild folders
            for split in ["train", "val", "test"]:
                for sub in ["images", "labels"]:
                    p = out_root / split / sub
                    if p.exists():
                        shutil.rmtree(p)
                    p.mkdir(parents=True, exist_ok=True)

            # Reuse labels by name, copy images accordingly
            # Labels live only for original train and val
            old_lbl = {
                "train": out_root / "train" / "labels",
                "val": out_root / "val" / "labels",
            }
            old_img = {
                "train": out_root / "train" / "images",
                "val": out_root / "val" / "images",
            }

            def find_source(stem):
                if (old_lbl["train"] / f"{stem}.txt").exists():
                    return "train"
                if (old_lbl["val"] / f"{stem}.txt").exists():
                    return "val"
                return None

            for split, img_list in new.items():
                for img_path in img_list:
                    img_path = Path(img_path)
                    stem = img_path.stem
                    src_split = find_source(stem)
                    if src_split is None:
                        continue
                    # copy image
                    shutil.copy2(img_path, out_root / split / "images" / img_path.name)
                    # copy label
                    shutil.copy2(old_lbl[src_split] / f"{stem}.txt", out_root / split / "labels" / f"{stem}.txt")

            # Rewrite yaml with test
            names = {0: class_name}
            data_yaml = {
                "path": str(out_root.resolve()),
                "train": "train/images",
                "val": "val/images",
                "test": "test/images",
                "names": names,
            }
            (out_root / "license_plate.yaml").write_text(yaml.safe_dump(data_yaml, sort_keys=False))
            yolo_yaml = out_root / "license_plate.yaml"
            print(f"Rewrote YOLO yaml with test split at {yolo_yaml}")

        # Optional training
        maybe_train(cfg, yolo_yaml)
        return

    # Fallback to your original local parquet flow
    parquet_dir = proj_root / cfg["data"]["parquet_dir"]
    parquet_files = [parquet_dir / p for p in cfg["data"]["parquet_files"]]
    image_root = proj_root / cfg["data"]["image_root"]

    df = load_parquets(parquet_files)
    print(f"Total rows across parquet files: {len(df)}")

    df = normalize_schema(df)

    lower_cols = set(df.columns)
    has_abs = {"xmin", "ymin", "xmax", "ymax"}.issubset(lower_cols)
    has_norm = {"x_center", "y_center", "width", "height"}.issubset(lower_cols)

    if not (has_abs or has_norm):
        raise ValueError("Parquet must contain either absolute or normalized boxes")

    class_map_cfg = cfg["data"]["class_map"]
    df["class"] = df["class"].astype(str)

    cls_counts = df["class"].value_counts()
    print("Class counts:")
    for k, v in cls_counts.items():
        print(f"  {k}: {v}")

    ratios = tuple(cfg["data"].get("splits", [0.7, 0.2, 0.1]))
    seed = int(cfg["data"].get("seed", 1337))

    stats = write_yolo_dataset(
        df=df,
        image_root=image_root,
        out_root=out_root,
        class_map=class_map_cfg,
        seed=seed,
        ratios=ratios,
    )

    print("Written label counts by split:")
    for split, n in stats.items():
        print(f"  {split}: {n}")

    names = {int(v): k for k, v in cfg["data"]["class_map_names"].items()}
    data_yaml_path = proj_root / cfg["data"]["yolo_data_yaml"]
    data_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    write_yolo_data_yaml(out_root=out_root, names=names, file_path=data_yaml_path)
    print(f"Wrote YOLO data yaml to {data_yaml_path}")

    maybe_train(cfg, data_yaml_path)

if __name__ == "__main__":
    main()