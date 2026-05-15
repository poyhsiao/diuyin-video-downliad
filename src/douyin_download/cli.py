"""CLI entrypoint."""

import os
from pathlib import Path

import click

from douyin_download.core import download_video, resolve_video_id, sort_urls
from douyin_download.extractor import extract_cdn_url


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Douyin video downloader CLI."""


@main.command()
@click.argument("url")
@click.option(
    "--quality", "-q",
    type=click.Choice(["480p", "720p", "1080p"], case_sensitive=False),
    default=None,
    help="Desired video quality (default: best available)",
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: ~/Downloads)",
)
def download(url: str, quality: str | None, output: Path | None) -> None:
    """Download a Douyin video."""
    output_dir = output or Path(os.path.expanduser("~/Downloads"))
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        video_id, path = download_video(url, output_dir, quality=quality)
        click.echo(f"Downloaded: {path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("url")
def info(url: str) -> None:
    """Show video information."""
    try:
        video_id = resolve_video_id(url)
        urls = extract_cdn_url(url, wait_seconds=5)
        sorted_urls = sort_urls(urls)

        click.echo(f"Video ID: {video_id}")
        click.echo(f"Available URLs: {len(urls)}")

        if sorted_urls:
            best = sorted_urls[0]
            click.echo(f"Best quality URL: {best[:80]}...")
        else:
            click.echo("No URLs extracted")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("url")
def session(url: str) -> None:
    """Test URL resolution and extraction without downloading."""
    try:
        video_id = resolve_video_id(url)
        click.echo(f"Video ID: {video_id}")
        click.echo("URL format: valid")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
