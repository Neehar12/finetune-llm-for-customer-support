# Serving benchmark — `cs-tuned` (Q4_K_M, Ollama)

Hardware: local Mac (Apple Metal). n=40 prompts sampled across the test split. Timings from Ollama's own duration fields.

## Single-stream latency & throughput

| metric | value |
|---|---|
| n | 40 |
| latency_ms_p50 | 1229.7 |
| latency_ms_p95 | 2621.3 |
| latency_ms_mean | 1493.6 |
| decode_tps_mean | 94.4 |
| prefill_tps_mean | 2890.7 |
| output_tokens_mean | 130.6 |

## Throughput vs concurrency

| concurrency | wall (s) | req/s | system decode tok/s |
|---|---|---|---|
| 1 | 59.9 | 0.67 | 87.2 |
| 2 | 58.6 | 0.68 | 89.1 |
| 4 | 58.7 | 0.68 | 88.9 |

> Concurrency scaling depends on `OLLAMA_NUM_PARALLEL` (default lets Ollama pick based on memory). Q4_K_M 1.7B is small, so a few parallel slots fit.
