import asyncio
import wave
import logging
import sys
from pathlib import Path
from .speechmatics_client import SpeechmaticsClient
from .database import (
    update_benchmark_result,
    update_benchmark_run_status,
    get_ground_truth,
)

# Dynamically import the evaluation engine from scripts/vendor/soniox
# We know backend is at VoiceAgent/demos/realtimeasr-en-arabic/backend
# and scripts is at VoiceAgent/demos/scripts
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.parent
VENDOR_SONIOX_DIR = PROJECT_ROOT / "scripts" / "vendor" / "soniox"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.vendor.soniox.arabic_normalizer import normalize_arabic_text
    from scripts.vendor.soniox.wer_calculator import calculate_wer
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import WER calculator: {e}")
    normalize_arabic_text = None
    calculate_wer = None

logger = logging.getLogger(__name__)


async def run_benchmark(
    run_id: int,
    language: str,
    hotwords: list,
    replacements: list,
    files: list,
    benchmark_dir: Path,
    concurrency: int = 5,
):
    """
    files is a list of tuples: (result_id, rel_path)
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def process_file(result_id: int, rel_path: str):
        async with semaphore:
            file_path = benchmark_dir / rel_path

            if not file_path.exists():
                update_benchmark_result(
                    result_id, "error", error_message="File not found"
                )
                return

            update_benchmark_result(result_id, "running")

            try:
                with wave.open(str(file_path), "rb") as wf:
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    framerate = wf.getframerate()

                    if n_channels != 1 or sampwidth != 2:
                        update_benchmark_result(
                            result_id,
                            "error",
                            error_message=f"Unsupported format: channels={n_channels}, width={sampwidth}",
                        )
                        return

                    pcm_data = wf.readframes(wf.getnframes())
            except Exception as e:
                update_benchmark_result(
                    result_id, "error", error_message=f"WAV parse error: {str(e)}"
                )
                return

            client = SpeechmaticsClient(
                language=language,
                hotwords=hotwords,
                replacements=replacements,
                sample_rate=framerate,
            )

            final_transcript_parts = []

            async def message_handler(msg):
                if msg.get("type") == "final":
                    final_transcript_parts.append(msg.get("text", ""))

            listen_task = None
            try:
                await client.connect(message_handler)

                # Streaming simulation
                # chunk size = 0.1 seconds
                chunk_duration = 0.1
                bytes_per_second = framerate * sampwidth
                chunk_size = int(bytes_per_second * chunk_duration)

                listen_task = asyncio.create_task(client.listen())

                for i in range(0, len(pcm_data), chunk_size):
                    chunk = pcm_data[i : i + chunk_size]
                    await client.send_audio(chunk)
                    await asyncio.sleep(chunk_duration)

                await client.end_stream()
                await client.wait_for_end_of_transcript()

                if listen_task and not listen_task.done():
                    listen_task.cancel()
                    try:
                        await listen_task
                    except asyncio.CancelledError:
                        pass

                await client.close()

                final_text = " ".join(final_transcript_parts).strip()

                # Evaluation logic
                ground_truth = get_ground_truth(rel_path.replace("\\", "/"))
                wer_val = None
                wer_s = None
                wer_words = None

                if ground_truth and normalize_arabic_text and calculate_wer:
                    norm_gt = normalize_arabic_text(ground_truth)
                    norm_hyp = normalize_arabic_text(final_text)
                    w, s, d, i, ref_count = calculate_wer(norm_gt, norm_hyp)
                    wer_val = w
                    wer_s = s + d + i
                    wer_words = ref_count

                update_benchmark_result(
                    result_id,
                    "completed",
                    final_transcript=final_text,
                    ground_truth=ground_truth,
                    wer=wer_val,
                    wer_errors=wer_s,
                    wer_words=wer_words,
                )

            except Exception as e:
                logger.error(f"Error during benchmark file {rel_path}: {e}")
                update_benchmark_result(result_id, "error", error_message=str(e))
                if listen_task and not listen_task.done():
                    listen_task.cancel()
                await client.close()

    try:
        tasks = [process_file(result_id, rel_path) for result_id, rel_path in files]
        await asyncio.gather(*tasks)

        update_benchmark_run_status(run_id, "completed")
    except Exception as e:
        logger.error(f"Benchmark run failed: {e}")
        update_benchmark_run_status(run_id, "failed")
