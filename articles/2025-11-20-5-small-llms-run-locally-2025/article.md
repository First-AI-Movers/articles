---
title: "The 5 Small LLMs You Can Run Locally On Your Computer Today"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://www.firstaimovers.com/p/5-small-llms-run-locally-2025"
published_date: "2025-11-20"
license: "CC BY 4.0"
---
Your API bills are climbing, latency is killing customer experience, and your compliance team just flagged another data-transfer issue. It's time to bring AI home—small language models (SLMs) running on your own hardware can solve focused problems faster, cheaper, and without uploading your data anywhere.

Here's why this matters now: the latest small models from late 2024 and 2025 deliver near-flagship accuracy while fitting on consumer GPUs and even laptop CPUs. \[Quantization]\(), \[pruning]\(), and \[distillation]\() techniques compress them further so they run on the devices you already own. The tradeoff isn't quality anymore—it's choosing the right model for your task.

If this topic speaks to you, let’s turn it into outcomes.
Workshops & audits 👉 \[book here]\()

Three key insights for practitioners
\- Model size vs. activated parameters: Larger isn't always better. \[Qwen 3's 8B]\()-parameter model matches the performance of older 14B models thanks to better training data and architecture improvements. A well-trained 7B model at Q4 quantization beats a poorly quantized 13B model every time.

\- Quantization changes the game: Running at Q4 (4-bit precision) cuts memory by ~75% with minimal accuracy loss—under 2% on most benchmarks. Q5 preserves even more quality when precision matters. This is the difference between "won't fit" and "runs smoothly" on your i7 laptop or RTX 4070.

\- Hardware pairing dictates success: Match model size and quant level to your hardware tier. A 7B model at Q4 runs comfortably on 8GB VRAM; 8B models need 10-12GB; 32B models require 24GB+ or CPU offloading. Know your limits before you download.

The Top 5 Models—Match Your Use Case

1\. \[Qwen]\() 3 8B-Instruct (8.2B parameters) — The default pick for multilingual workflows
\- Best for: Multilingual support, tool use, RAG-first apps, general assistant tasks

\- Runs on: i7/i9 CPU (16GB+ RAM) at Q4; RTX 4070/4080 (12GB+ VRAM) at Q5

\- Quant sweet spot: Q4 or Q5 for balanced speed and accuracy

\- Why it wins: Qwen 3 8B performs on par with Qwen 2.5 14B, especially on STEM and coding tasks. It handles 32K context natively (extensible to 128K) and supports seamless switching between thinking mode (deep reasoning) and non-thinking mode (fast responses). As we've covered at \[First AI Movers]\(), small models trained on high-quality data can punch above their weight class.

\- Limits: Struggles with extremely long reasoning chains without scaffolding. Pair with \[RAG workflows]\() for document-heavy tasks.

2- Meta \[Llama 3.3 70B]\()-Instruct (70B parameters) — Maximum accuracy when hardware allows
\- Best for: Complex reasoning, code generation, generalist assistant where correctness trumps speed

\- Runs on: Dual RTX 3090 (48GB combined) or single A100 (80GB) at Q4; high-end i9 CPU (128GB+ RAM) with slow inference

\- Quant sweet spot: Q4 maintains 86% MMLU accuracy (vs. 86% at full precision); Q5 closes the gap further

\- Why it's here: Llama 3.3 70B matches Llama 3.1 405B performance on many benchmarks while using far fewer resources. At Q4 quantization, it delivers 80%+ MMLU accuracy—better than most smaller models at any precision. The 70B architecture is more resilient to quantization than smaller models, making it the go-to when you need flagship-level outputs locally.

\- Limits: High memory requirements; first-token latency on CPUs can exceed 10 seconds. Best suited for batch processing or cloud-bursting for complex queries.

3- \[Mistral 7B]\()-Instruct v0.3 (7.3B parameters) — Speed demon for interactive tasks
\- Best for: Chat UIs, coding copilot, real-time customer support, anything latency-sensitive

\- Runs on: i5/i7 CPU (8GB+ RAM) at Q4; RTX 3060 (6GB VRAM) at Q5

\- Quant sweet spot: Q4 for speed; Q5 if code accuracy dips

\- Why it's fast: Mistral uses \[Grouped Query Attention]\() (GQA) and \[Sliding Window Attention]\() (SWA) to decode tokens faster with lower memory overhead. It handles 32K context and supports function calling out of the box. Snappy decoding and compact outputs make it ideal for workflows where users expect instant responses.

\- Limits: Weaker on long multi-hop reasoning and edge-case math. Use for tasks with clear, short prompts.

4- Microsoft\[ Phi-3 Small 7B]\()-Instruct (7B parameters) — Grounded reasoning on a budget
\- Best for: RAG apps, education, structured Q&A, scenarios requiring high factual accuracy

\- Runs on: i5 CPU (8GB+ RAM) at Q4; entry-level GPUs (6GB VRAM)

\- Quant sweet spot: Q4; upgrade to Q5 if hallucinations appear in retrieval tasks

\- Why it's underrated: Phi-3 Small punches above its parameter count on grounded tasks. It's designed to work with external knowledge bases and stays on-topic better than most 7B models. Pair it with a \[retrieval-augmented generation pipeline]\() and it becomes a reliable policy assistant or domain-specific Q&A engine.

\- Limits: Open-ended knowledge without retrieval can trigger hallucinations. Always provide context.

5- Google \[Gemma 2 9B]\()-Instruct (9B parameters) — Enterprise-safe summarization
\- Best for: Compliance-friendly summarization, customer response helpers, policy-aware answering

\- Runs on: i7 CPU (12GB+ RAM) at Q4; RTX 4060 (8GB VRAM) at Q5

\- Quant sweet spot: Q4 for most tasks; Q5 for critical policy work

\- Why choose it: Gemma 2 delivers predictable tone, solid summarization, and good refusal behavior—critical when outputs face regulatory scrutiny. It's optimized for \[energy-efficient edge deployment]\(), making it a strong pick for always-on assistants in field devices or kiosks.

\- Limits: Weaker on edge-case coding and advanced math. Don't use it for technical deep dives.

How Quantization Works—And Why Q4 Is the Sweet Spot
\[Quantization]\() reduces the numerical precision of model weights from 16-bit (FP16) or 32-bit (FP32) down to 4-bit (Q4) or 8-bit (Q8). Q4 is the Goldilocks zone: it cuts memory by ~75%, accelerates inference by 2-3×, and typically drops accuracy by less than 2% on well-trained models. Q5 adds a bit more precision for tasks that require nuance (like code generation or policy analysis), while Q6 achieves full-precision quality at the cost of speed.

\[Quantization-Aware Training]\() (QAT) fine-tunes the model to achieve greater accuracy with fewer bits, further closing the quality gap. Most practitioners start with Post-Training Quantization (PTQ)—quantize a pre-trained model, calibrate with real examples, and test. If quality drops on sensitive tasks, move to QAT or keep a few critical layers at higher precision.

Limits & How to Work Around Them
Small LLMs still miss tricky logic jumps and long multi-step plans. Here's how to compensate:

\- Prompt scaffolding: Break complex queries into smaller, sequential steps. Instead of "analyze this 50-page contract," ask "summarize key obligations," then "flag non-standard clauses," then "compare to template".

\- Retrieval-augmented generation (\[RAG]\()): Fetch relevant docs first, then ask the model to reason over them. This keeps outputs grounded and reduces hallucinations.

\- Function calling: Let the LLM decide when to call a calculator, database, or API—not how to compute. This offloads deterministic logic to reliable tools.

\- Hybrid deployment: Run the small model locally for 80-90% of queries; burst to a cloud model (e.g., GPT-4x or Claude) for rare, complex cases. Track and learn from escalations.

These constraints force you to ship faster and spend less—a feature, not a bug.

Your Move
Pick one workflow where cloud costs or latency block progress—field service, retail kiosks, compliance Q&A, coding copilot. Deploy one of the five models above locally: benchmark speed, accuracy, and cost savings. One proven win unlocks broader adoption across your team.

The clever play isn't chasing the biggest model—it's running the right model in the right place with the right precision.

---

My Open Tabs
" width="100%">
---
Looking for more great writing in your inbox? 👉 \[Discover the newsletters busy professionals love to read. ]\()

For services or sponsorships, email \[Dr. Hernani Costa]\() at \[info at firstaimovers dot com]\()

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://www.firstaimovers.com/p/5-small-llms-run-locally-2025) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*