#!/usr/bin/env python3
"""
tts_minimax.py — Convert text file to audio using MiniMax async TTS API.

Usage:
    python tts_minimax.py --input script.txt --output podcast.mp3 --voice_id male-qn-qingse
    python tts_minimax.py --input script.txt --voice_id female-shaonv --format flac

Environment:
    MINIMAX_API_KEY  — MiniMax API key (required)
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time

import requests


class TeeLogger:
    """Write to both stdout/stderr and a log file."""

    def __init__(self, log_path: str):
        self.log_file = open(log_path, "a", encoding="utf-8")
        self.log_file.write(f"\n{'='*60}\n")
        self.log_file.write(f"Run started: {datetime.datetime.now().isoformat()}\n")
        self.log_file.write(f"{'='*60}\n")

    def log(self, msg: str, *, error: bool = False):
        stream = sys.stderr if error else sys.stdout
        print(msg, file=stream)
        self.log_file.write(msg + "\n")
        self.log_file.flush()

    def close(self):
        self.log_file.close()


logger: TeeLogger | None = None

API_BASE = "https://api.minimaxi.com/v1"
MODEL = "speech-2.8-turbo"
MAX_TEXT_LENGTH = 50000
POLL_INTERVAL = 5  # seconds
POLL_MAX_RETRIES = 360  # 30 minutes max wait


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def create_task(
    api_key: str,
    text: str,
    voice_id: str,
    audio_format: str = "mp3",
    speed: float = 1.0,
) -> str:
    """Submit async TTS task. Returns task_id."""
    payload = {
        "model": MODEL,
        "text": text,
        "language_boost": "auto",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": 1,
            "pitch": 0,
        },
        "audio_setting": {
            "audio_sample_rate": 32000,
            "bitrate": 128000,
            "format": audio_format,
            "channel": 1,
        },
    }

    resp = requests.post(
        f"{API_BASE}/t2a_async_v2",
        headers=_headers(api_key),
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()

    status_code = data.get("base_resp", {}).get("status_code", -1)
    if status_code != 0:
        msg = data.get("base_resp", {}).get("status_msg", "unknown error")
        logger.log(f"ERROR: Task creation failed [{status_code}]: {msg}", error=True)
        sys.exit(1)

    task_id = data["task_id"]
    chars = data.get("usage_characters", 0)
    logger.log(f"Task created: {task_id} ({chars} billable characters)")
    return task_id


def poll_task(api_key: str, task_id: str) -> int:
    """Poll until task completes. Returns file_id."""
    for i in range(POLL_MAX_RETRIES):
        resp = requests.get(
            f"{API_BASE}/query/t2a_async_query_v2",
            params={"task_id": task_id},
            headers=_headers(api_key),
        )
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", "").lower()
        if status == "success":
            file_id = data["file_id"]
            logger.log(f"Task completed. file_id: {file_id}")
            return file_id
        elif status in ("failed", "expired"):
            msg = data.get("base_resp", {}).get("status_msg", "")
            logger.log(f"ERROR: Task {status}: {msg}", error=True)
            sys.exit(1)

        # Still processing
        if i % 6 == 0:
            logger.log(f"  Processing... ({i * POLL_INTERVAL}s elapsed)")
        time.sleep(POLL_INTERVAL)

    logger.log("ERROR: Polling timed out.", error=True)
    sys.exit(1)


def download_audio(api_key: str, file_id: int, output_path: str):
    """Download audio file using file_id."""
    resp = requests.get(
        f"{API_BASE}/files/retrieve_content",
        params={"file_id": file_id},
        headers=_headers(api_key),
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    size_mb = len(resp.content) / (1024 * 1024)
    logger.log(f"Audio saved: {output_path} ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="MiniMax async TTS: text → audio")
    parser.add_argument("--input", required=True, help="Input text file path")
    parser.add_argument("--output", help="Output audio file path (default: input with audio extension)")
    parser.add_argument("--voice_id", required=True, help="MiniMax voice ID")
    parser.add_argument("--format", default="mp3", choices=["mp3", "pcm", "flac"], help="Audio format (default: mp3)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed 0.5-2.0 (default: 1.0)")
    args = parser.parse_args()

    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # Read input text
    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("ERROR: Input file is empty.", file=sys.stderr)
        sys.exit(1)

    # Default output path
    output_path = args.output
    if not output_path:
        base = os.path.splitext(args.input)[0]
        output_path = f"{base}.{args.format}"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Initialize logger — writes to .log file next to the output audio
    global logger
    log_path = os.path.splitext(output_path)[0] + ".log"
    logger = TeeLogger(log_path)

    if len(text) > MAX_TEXT_LENGTH:
        logger.log(f"WARNING: Text is {len(text)} chars (max {MAX_TEXT_LENGTH}). It will be truncated.")
        text = text[:MAX_TEXT_LENGTH]

    logger.log(f"Input: {args.input} ({len(text)} chars)")
    logger.log(f"Voice: {args.voice_id}, Speed: {args.speed}, Format: {args.format}")
    logger.log(f"Model: {MODEL}")
    logger.log(f"Output: {output_path}")

    # Run async TTS pipeline
    task_id = create_task(api_key, text, args.voice_id, args.format, args.speed)
    file_id = poll_task(api_key, task_id)
    download_audio(api_key, file_id, output_path)

    logger.log("Done.")
    logger.close()


if __name__ == "__main__":
    main()
