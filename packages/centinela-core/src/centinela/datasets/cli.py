"""CLI tool for managing adversarial datasets.

Usage:
    centinela-datasets list                  # List available datasets
    centinela-datasets download advbench     # Download specific dataset
    centinela-datasets download --all        # Download all datasets
    centinela-datasets stats advbench        # Show dataset statistics
    centinela-datasets clear advbench        # Clear cached dataset
    centinela-datasets validate advbench     # Verify dataset integrity
"""

import argparse
import sys
from pathlib import Path

from centinela.datasets import DatasetLoader
from centinela.datasets.advbench import AdvBenchDataset
from centinela.datasets.gandalf import GandalfDataset
from centinela.datasets.jailbreakbench import JailbreakBenchDataset


def create_loader(cache_dir: Path | None = None) -> DatasetLoader:
    """Create DatasetLoader with registered datasets."""
    if cache_dir is None:
        cache_dir = Path.home() / ".centinela" / "datasets"

    loader = DatasetLoader(cache_dir)

    loader.register_dataset("advbench", AdvBenchDataset)
    loader.register_dataset("jailbreakbench", JailbreakBenchDataset)
    loader.register_dataset("gandalf", GandalfDataset)

    return loader


def cmd_list(args: argparse.Namespace) -> None:
    """List available datasets."""
    loader = create_loader(args.cache_dir)
    datasets = loader.list_datasets()

    if not datasets:
        print("No datasets registered.")
        return

    print("Available datasets:")
    for name in datasets:
        print(f"  - {name}")


def cmd_download(args: argparse.Namespace) -> None:
    """Download datasets."""
    loader = create_loader(args.cache_dir)

    if args.all:
        datasets = loader.list_datasets()
    elif args.name:
        datasets = [args.name]
    else:
        print("Error: specify --all or a dataset name")
        sys.exit(1)

    for name in datasets:
        print(f"\nDownloading {name}...")
        try:
            dataset = loader.load_dataset(name, force_download=args.force)
            stats = dataset.get_stats()
            print(f"  ✓ {name} v{stats.version}: {stats.total_entries} entries")
            print(f"    Categories: {', '.join(c.value for c in stats.categories)}")
        except Exception as e:
            print(f"  ✗ Failed to download {name}: {e}")
            sys.exit(1)


def cmd_stats(args: argparse.Namespace) -> None:
    """Show dataset statistics."""
    loader = create_loader(args.cache_dir)

    if not args.name:
        print("Error: specify dataset name")
        sys.exit(1)

    try:
        dataset = loader.load_dataset(args.name)
        stats = dataset.get_stats()

        print(f"\nDataset: {stats.name}")
        print(f"Version: {stats.version}")
        print(f"Source: {stats.source}")
        print(f"Entries: {stats.total_entries}")
        print(f"Categories: {', '.join(c.value for c in stats.categories)}")
        if stats.license:
            print(f"License: {stats.license}")
        if stats.description:
            print(f"Description: {stats.description}")

        sample = dataset.sample(min(3, len(dataset)))
        if sample:
            print(f"\nSample entries:")
            for i, entry in enumerate(sample, 1):
                print(f"  {i}. [{entry.category.value}] {entry.prompt[:80]}...")
                print(f"     Label: {entry.label}, Severity: {entry.severity:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_clear(args: argparse.Namespace) -> None:
    """Clear cached datasets."""
    loader = create_loader(args.cache_dir)

    if args.all:
        print("Clearing all cached datasets...")
        loader.clear_cache()
        print("✓ All caches cleared.")
    elif args.name:
        print(f"Clearing cache for {args.name}...")
        loader.clear_cache(args.name)
        print(f"✓ Cache cleared for {args.name}.")
    else:
        print("Error: specify --all or a dataset name")
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Verify dataset integrity."""
    loader = create_loader(args.cache_dir)

    if not args.name:
        print("Error: specify dataset name")
        sys.exit(1)

    try:
        dataset = loader.load_dataset(args.name)
        stats = dataset.get_stats()

        print(f"\nValidating {args.name}...")
        print(f"  Entries: {stats.total_entries}")
        print(f"  Categories: {len(stats.categories)}")

        invalid = []
        for i, entry in enumerate(dataset):
            if not entry.prompt:
                invalid.append(f"Entry {i}: empty prompt")
            if entry.severity < 0.0 or entry.severity > 1.0:
                invalid.append(f"Entry {i}: invalid severity {entry.severity}")

        if invalid:
            print(f"  ✗ Found {len(invalid)} invalid entries:")
            for issue in invalid[:5]:
                print(f"    - {issue}")
            if len(invalid) > 5:
                print(f"    ... and {len(invalid) - 5} more")
            sys.exit(1)
        else:
            print(f"  ✓ All {stats.total_entries} entries valid")
    except Exception as e:
        print(f"  ✗ Validation failed: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="centinela-datasets",
        description="Manage adversarial datasets for red-team and blue-team operations",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Cache directory (default: ~/.centinela/datasets)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    list_parser = subparsers.add_parser("list", help="List available datasets")
    list_parser.set_defaults(func=cmd_list)

    download_parser = subparsers.add_parser("download", help="Download datasets")
    download_parser.add_argument("name", nargs="?", help="Dataset name")
    download_parser.add_argument("--all", action="store_true", help="Download all datasets")
    download_parser.add_argument("--force", action="store_true", help="Force re-download")
    download_parser.set_defaults(func=cmd_download)

    stats_parser = subparsers.add_parser("stats", help="Show dataset statistics")
    stats_parser.add_argument("name", nargs="?", help="Dataset name")
    stats_parser.set_defaults(func=cmd_stats)

    clear_parser = subparsers.add_parser("clear", help="Clear cached datasets")
    clear_parser.add_argument("name", nargs="?", help="Dataset name")
    clear_parser.add_argument("--all", action="store_true", help="Clear all caches")
    clear_parser.set_defaults(func=cmd_clear)

    validate_parser = subparsers.add_parser("validate", help="Verify dataset integrity")
    validate_parser.add_argument("name", nargs="?", help="Dataset name")
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
