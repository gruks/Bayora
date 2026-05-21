# Phase 3: Evaluation Engine - Research

**Researched:** 2026-05-16
**Domain:** AI safety classification, multi-seed evaluation, safety metrics
**Confidence:** MEDIUM

## Summary

Phase 3 builds the blue-agent evaluation engine: a safety classifier trained on HH-RLHF and ToxiGen datasets, a 50+ metric scoring system, and multi-seed evaluation with confidence intervals. The HuggingFace ecosystem (transformers + datasets + Trainer API) is the standard stack for classifier training. DistilBERT is the recommended base model — it balances accuracy and inference latency for production use. For the 50+ metrics, LLM-Guard (Protect AI) provides 30+ pre-built scanners covering toxicity, bias, PII, injection, and more; the remaining metrics can be implemented as custom scorers. Multi-seed evaluation uses BCa bootstrap confidence intervals with paired evaluation design.

**Primary recommendation:** Use HuggingFace `transformers` + `Trainer` API for fine-tuning DistilBERT on HH-RLHF (harmless-base) and ToxiGen datasets. Use LLM-Guard as the foundation for the 50+ metric scoring system. Use scipy for BCa bootstrap confidence intervals.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `transformers` | >=4.51 | Fine-tuning text classifiers (DistilBERT/RoBERTa) | Industry standard for HF model training; Trainer API handles distributed training, mixed precision, checkpointing |
| `datasets` | >=3.0 | Load HH-RLHF and ToxiGen datasets | Native HF dataset loading with streaming, caching, and preprocessing |
| `torch` | >=2.4 | Deep learning backend for transformers | Required by transformers; GPU acceleration for training |
| `llm-guard` | >=0.3.16 | 30+ pre-built safety scanners (toxicity, bias, PII, injection, etc.) | MIT-licensed, production-ready, ONNX-optimized, maintained by Protect AI |
| `scikit-learn` | >=1.5 | Classical ML baselines, metric computation, train/test splits | Standard ML toolkit; TF-IDF + LogisticRegression as fast baseline |
| `scipy` | >=1.14 | BCa bootstrap confidence intervals, statistical tests | `scipy.stats.bootstrap` with BCa method is the standard for non-parametric CIs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `evaluate` (HF) | >=0.4 | Load accuracy, F1, precision, recall metrics during training | Paired with Trainer for compute_metrics callback |
| `pydantic` | >=2.0 (existing) | Frozen response types for scoring results | Already used in centinela-core for LLM types |
| `numpy` | >=2.0 | Numerical operations, array manipulation | Underlying array library for scipy/sklearn |
| `onnxruntime` | >=1.18 | Accelerated inference for deployed classifiers | Production inference speedup (5-10x vs raw transformers) |
| `structlog` | >=24 (existing) | Structured logging for evaluation runs | Already in llm-guard dependency chain |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| transformers Trainer | PyTorch native training loop | More control but significantly more boilerplate; Trainer handles gradient accumulation, mixed precision, checkpointing automatically |
| DistilBERT | BERT-base / RoBERTa-base | +2-3% accuracy but 40% slower inference and 2x parameters; DistilBERT is 97% of BERT performance at 60% speed |
| LLM-Guard | NVIDIA NeMo Guardrails | NeMo is more complex (Colang state machines), better for conversational guardrails; LLM-Guard is simpler for batch scoring |
| scipy bootstrap | Custom percentile bootstrap | BCa corrects for bias and skewness; critical when k (seeds) is small |

**Installation (to add to blue-agent/pyproject.toml):**
```bash
uv add --package blue-agent transformers datasets torch scikit-learn scipy llm-guard evaluate
```

## Architecture Patterns

### Recommended Project Structure
```
services/blue-agent/src/blue_agent/
├── classifiers/              # Safety classifier models
│   ├── __init__.py
│   ├── base.py               # Abstract SafetyClassifier interface
│   ├── hh_rlhf_classifier.py # HH-RLHF trained classifier
│   ├── toxigen_classifier.py # ToxiGen trained classifier
│   └── ensemble.py           # Combined classifier output
├── metrics/                  # Safety metric scorers
│   ├── __init__.py
│   ├── registry.py           # Metric registry (50+ metrics)
│   ├── categories/           # Metric categories
│   │   ├── toxicity.py       # Toxicity scores
│   │   ├── bias.py           # Bias detection
│   │   ├── harmfulness.py    # Harm content detection
│   │   ├── privacy.py        # PII/secret detection
│   │   ├── injection.py      # Prompt injection detection
│   │   └── quality.py        # Quality metrics (relevance, coherence)
│   └── base.py               # Abstract MetricScorer interface
├── evaluation/               # Multi-seed evaluation engine
│   ├── __init__.py
│   ├── runner.py             # Multi-seed evaluation orchestrator
│   ├── statistics.py         # BCa bootstrap, confidence intervals
│   └── results.py            # EvaluationResult pydantic model
├── isolation.py              # Prompt-stripping enforcement layer
└── main.py                   # Service entry point

services/blue-agent/tests/
├── test_classifiers.py
├── test_metrics.py
├── test_evaluation.py
└── test_isolation.py
```

### Pattern 1: Classifier Interface (Strategy Pattern)
**What:** Abstract base class for safety classifiers with a uniform `classify(text) -> ClassificationResult` interface
**When to use:** Every classifier (HH-RLHF, ToxiGen, ensemble) implements this interface
**Example:**
```python
# Source: transformers pipeline pattern + pydantic frozen models (project convention)
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

class ClassificationResult(BaseModel, frozen=True):
    label: str  # "safe" | "harm"
    confidence: float = Field(ge=0.0, le=1.0)
    model_source: str  # "hh_rlhf" | "toxigen" | "ensemble"

class SafetyClassifier(ABC):
    @abstractmethod
    def classify(self, response_text: str) -> ClassificationResult:
        """Classify a model response as safe or harmful."""
        ...
```

### Pattern 2: Isolation Layer (Mediator Pattern)
**What:** The orchestrator strips prompts before forwarding responses to blue-agent. Blue-agent's interface accepts ONLY `response_text`, never `prompt`.
**When to use:** Enforced at the API boundary — blue-agent's public methods must not accept prompt parameters
**Example:**
```python
# Source: BLUE-04 requirement — blue-agent receives only model response
class BlueAgentEvaluator:
    def evaluate_response(self, response: str) -> EvaluationResult:
        """
        Evaluate ONLY the model response.
        The original prompt is NEVER accessible here — enforced by interface design.
        The orchestrator strips prompts before calling this method.
        """
        classification = self.classifier.classify(response)
        scores = self.metric_registry.score(response)
        return EvaluationResult(
            classification=classification,
            metric_scores=scores,
        )
```

### Pattern 3: Multi-Seed Evaluation with BCa Bootstrap
**What:** Run evaluation across multiple random seeds, compute per-seed metrics, then use BCa bootstrap for confidence intervals
**When to use:** Every evaluation run; minimum 3 seeds recommended
**Example:**
```python
# Source: scipy.stats.bootstrap documentation
from scipy.stats import bootstrap
import numpy as np

def compute_confidence_intervals(
    per_seed_scores: list[float],
    confidence_level: float = 0.95,
    n_resamples: int = 10000,
) -> tuple[float, float]:
    """Compute BCa bootstrap confidence interval for per-seed scores."""
    result = bootstrap(
        (np.array(per_seed_scores),),
        statistic=np.mean,
        confidence_level=confidence_level,
        method="BCa",
        n_resamples=n_resamples,
    )
    return result.confidence_interval.low, result.confidence_interval.high
```

### Anti-Patterns to Avoid
- **Embedding prompts in blue-agent interface:** Violates BLUE-04 isolation. The blue-agent must NEVER receive the original adversarial prompt.
- **Single-run evaluation without error bars:** Point estimates without confidence intervals are misleading. Always report CIs.
- **Training classifiers from scratch:** HH-RLHF and ToxiGen are preference/toxicity datasets — fine-tune pretrained models, don't train from random weights.
- **Using temperature variation for seed diversity:** Temperature changes model behavior, not evaluation randomness. Seeds should control evaluation ordering/sampling, not the model's generation.
- **Unpaired t-tests for small k:** With 3-5 seeds, unpaired t-tests produce false positives. Use paired BCa bootstrap + permutation tests.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Text classifier training | Custom PyTorch training loop | `transformers.Trainer` API | Handles gradient accumulation, mixed precision, distributed training, checkpointing, eval callbacks |
| Dataset loading/preprocessing | Custom JSON/CSV parsers | `datasets.load_dataset()` | Handles streaming, caching, tokenization batching, train/test splits |
| Toxicity/bias/PII scanning | Custom regex + keyword lists | `llm-guard` scanners | 30+ production-tested scanners with ONNX optimization, maintained by Protect AI |
| Bootstrap confidence intervals | Manual percentile bootstrap | `scipy.stats.bootstrap(method="BCa")` | BCa corrects for bias and skewness; critical for small sample sizes |
| Metric computation | Manual accuracy/F1 formulas | `evaluate` library or `sklearn.metrics` | Standardized, tested, supports batch computation |
| Model inference optimization | Custom ONNX export pipeline | `optimum` library or llm-guard's built-in ONNX | Handles graph optimization, quantization, device placement |

**Key insight:** Safety evaluation has well-established tooling. The value is in orchestration (multi-seed runs, metric aggregation, isolation enforcement), not in building individual components from scratch.

## Common Pitfalls

### Pitfall 1: ToxiGen Data Access Requires HuggingFace Form
**What goes wrong:** ToxiGen dataset (`toxigen/toxigen-data`) requires filling out a HuggingFace access form before downloading. CI/CD pipelines will fail without pre-approved HF token.
**Why it happens:** Microsoft gated the dataset to track usage and ensure responsible research use.
**How to avoid:** Pre-approve HF token in CI secrets. Document the access request process. Consider caching the dataset in the repo or artifact registry.
**Warning signs:** `datasets` library raises `DatasetGenerationError` or authentication error during CI.

### Pitfall 2: HH-RLHF Format Is Preference Pairs, Not Labels
**What goes wrong:** HH-RLHF contains `(chosen, rejected)` pairs, not `(text, label)` rows. Direct use as classification training data requires transformation.
**Why it happens:** The dataset is designed for reward model training, not binary classification.
**How to avoid:** Extract the `chosen` response as "safe" and `rejected` response as "harm" to create binary labels. Use the `harmless-base` subset specifically. Validate label quality — some "rejected" responses may be merely less helpful, not harmful.
**Warning signs:** Classifier achieves ~50% accuracy (random) on validation set.

### Pitfall 3: LLM-Guard Python Version Constraint
**What goes wrong:** `llm-guard` v0.3.16 requires `Python <3.13,>=3.10`. If the project uses Python 3.12 (as specified in blue-agent/pyproject.toml), this is compatible. But future upgrades may break.
**Why it happens:** LLM-Guard pins specific versions of `transformers` (4.51.3) and other dependencies.
**How to avoid:** Pin `llm-guard>=0.3.16,<0.4.0` in dependencies. Test compatibility before upgrading.
**Warning signs:** `uv sync` fails with dependency resolution conflicts.

### Pitfall 4: GPU Requirement for Training
**What goes wrong:** Fine-tuning DistilBERT on CPU takes hours. Development without GPU access blocks iteration.
**Why it happens:** Transformer models require significant compute for fine-tuning.
**How to avoid:** Use Google Colab free tier for training runs. Export trained models to HF Hub or local artifact store. Blue-agent service only needs inference (runs on CPU with ONNX).
**Warning signs:** Training ETA > 4 hours on available hardware.

### Pitfall 5: Dataset Licensing Ambiguity
**What goes wrong:** ToxiGen code is MIT-licensed, but the dataset itself uses CDLA-Permissive-2.0. HH-RLHF is MIT-licensed. Both allow commercial use, but ToxiGen's README states "intended for research purposes only."
**Why it happens:** Research datasets often have ambiguous commercial-use language.
**How to avoid:** Both licenses (MIT and CDLA-Permissive-2.0) explicitly allow commercial use. The "research purposes only" statement in ToxiGen's README is aspirational, not a license restriction. Document license compliance in the project.
**Warning signs:** Legal review flags dataset usage.

### Pitfall 6: Over-Refusal (False Positives)
**What goes wrong:** Safety classifiers trained on HH-RLHF/ToxiGen may over-classify benign responses as harmful, especially for responses mentioning minority groups (ToxiGen's focus).
**Why it happens:** ToxiGen is specifically designed to detect implicit toxicity around 13 minority groups, which can create bias toward flagging any mention of these groups.
**How to avoid:** Use an ensemble of HH-RLHF (general harmlessness) and ToxiGen (implicit hate speech) classifiers. Calibrate thresholds using a held-out validation set. Report both precision and recall, not just accuracy.
**Warning signs:** High harm classification rate (>30%) on benign benchmark responses.

### Pitfall 7: Confidence Interval Width with Small k
**What goes wrong:** With only 3 seeds, BCa bootstrap CIs are very wide. The permutation test is deliberately conservative (minimum p-value = 0.25 with k=3).
**Why it happens:** Small sample sizes limit statistical power.
**How to avoid:** Use minimum 5 seeds for meaningful CIs. Report the number of seeds alongside CIs. Consider the paired evaluation design (same seeds across model variants) for variance reduction.
**Warning signs:** CI spans >20 percentage points; all permutation p-values >= 0.25.

## Code Examples

### Fine-tuning DistilBERT on HH-RLHF
```python
# Source: HuggingFace course chapter 3 + HH-RLHF dataset format
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

# Load HH-RLHF harmless-base subset
dataset = load_dataset("Anthropic/hh-rlhf", data_dir="harmless-base")

# Convert preference pairs to binary classification
def convert_to_labels(example):
    return {
        "text": example["chosen"],
        "label": 1,  # chosen = safe
    }

def convert_to_labels_rejected(example):
    return {
        "text": example["rejected"],
        "label": 0,  # rejected = potentially harmful
    }

safe_ds = dataset["train"].map(convert_to_labels, remove_columns=dataset["train"].column_names)
harm_ds = dataset["train"].map(convert_to_labels_rejected, remove_columns=dataset["train"].column_names)

# Combine and split
from datasets import concatenate_datasets
combined = concatenate_datasets([safe_ds, harm_ds])
split = combined.train_test_split(test_size=0.1, seed=42)

tokenizer = AutoTokenizer.from_pretrained("distilbert/distilbert-base-uncased")

def tokenize(examples):
    return tokenizer(examples["text"], truncation=True, max_length=512)

tokenized = split.map(tokenize, batched=True)

model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert/distilbert-base-uncased",
    num_labels=2,
    id2label={0: "harm", 1: "safe"},
    label2id={"harm": 0, "safe": 1},
)

training_args = TrainingArguments(
    output_dir="./hh-rlhf-classifier",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["test"],
    tokenizer=tokenizer,
)

trainer.train()
```

### Using LLM-Guard for Safety Scanning
```python
# Source: llm-guard documentation (protectai.github.io/llm-guard)
from llm_guard import output_scanners
from llm_guard.output_scanners import Toxicity, Bias, NoRefusal, FactualConsistency, Sensitive

scanners = [
    Toxicity(threshold=0.5),
    Bias(threshold=0.5),
    NoRefusal(threshold=0.5),
    FactualConsistency(minimum_score=0.7),
    Sensitive(threshold=0.5),
]

def scan_response(response: str) -> dict:
    results = {}
    for scanner in scanners:
        sanitized, is_valid, risk_score = scanner.scan(response)
        results[scanner.__class__.__name__] = {
            "valid": is_valid,
            "risk_score": risk_score,
        }
    return results
```

### Multi-Seed Evaluation with BCa CIs
```python
# Source: scipy.stats.bootstrap documentation + arXiv:2511.19794
import numpy as np
from scipy.stats import bootstrap

def evaluate_with_confidence(
    evaluator,
    test_samples: list[str],
    seeds: list[int],
    confidence_level: float = 0.95,
) -> dict:
    per_seed_scores = []

    for seed in seeds:
        np.random.seed(seed)
        # Run evaluation with this seed
        scores = [evaluator.score(sample) for sample in test_samples]
        per_seed_scores.append(np.mean(scores))

    # BCa bootstrap confidence interval
    result = bootstrap(
        (np.array(per_seed_scores),),
        statistic=np.mean,
        confidence_level=confidence_level,
        method="BCa",
        n_resamples=10000,
    )

    return {
        "mean": float(np.mean(per_seed_scores)),
        "std": float(np.std(per_seed_scores)),
        "ci_low": result.confidence_interval.low,
        "ci_high": result.confidence_interval.high,
        "per_seed": per_seed_scores,
        "n_seeds": len(seeds),
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rule-based toxicity (keyword lists) | Transformer-based classifiers (DistilBERT, RoBERTa) | 2020+ | 15-25% improvement on implicit toxicity detection |
| Single-run evals | Multi-seed + BCa bootstrap CIs | 2024+ | Prevents false claims of significance for <2pp gains |
| Manual metric implementation | LLM-Guard + evaluate library | 2023+ | 30+ pre-built scanners, ONNX-optimized |
| Zero-shot LLM-as-judge | Fine-tuned classifiers on domain data | 2024+ | Lower cost, deterministic, auditable |
| Unpaired t-tests for seed comparison | Paired BCa + permutation tests | 2025+ | Conservative decision rule prevents over-claiming |

**Deprecated/outdated:**
- **Pass@k for safety evaluation:** Being replaced by posterior-based Bayesian frameworks with credible intervals (arXiv:2510.04265)
- **Chatbot Arena-style bootstrap with fixed reference:** Incorrect for per-model CIs; use all-pairs paired method instead (arXiv:2512.21326)
- **Training classifiers from scratch on HH-RLHF:** Fine-tuning pretrained models is standard; training from random weights is wasteful

## Open Questions

1. **Which HH-RLHF subset to use for training?**
   - What we know: `harmless-base` contains harmlessness preference pairs. `helpful-base`, `helpful-online`, `helpful-rejection-sampled` contain helpfulness pairs.
   - What's unclear: Whether to include red-teaming transcripts (`red-team-attempts`) as additional harmful examples. These are full conversation transcripts, not single responses.
   - Recommendation: Start with `harmless-base` only. Red-teaming transcripts require different preprocessing (extract only the model's response, not the full dialogue).

2. **How to reach 50+ metrics?**
   - What we know: LLM-Guard provides ~30 scanners (14 prompt + 17 output). The requirement is 50+ core metrics.
   - What's unclear: Which additional metrics to implement. Candidates include: calibration scores, robustness to paraphrasing, consistency across seeds, category-specific breakdowns.
   - Recommendation: Use LLM-Guard scanners as the base (~30), add statistical metrics (mean, variance, CI width per category), add derived metrics (cross-classifier agreement, over-refusal rate), and add category-level breakdowns to reach 50+.

3. **ToxiGen access in CI/CD?**
   - What we know: ToxiGen requires filling out a HuggingFace access form. The form approval may take time.
   - What's unclear: How long approval takes and whether automated CI can access it.
   - Recommendation: Request access immediately. Cache the dataset as a build artifact. Provide a fallback mock dataset for CI runs without HF access.

4. **GPU availability for training?**
   - What we know: Fine-tuning DistilBERT requires GPU for reasonable training times.
   - What's unclear: Whether the project has GPU resources available.
   - Recommendation: Use Google Colab free tier for initial training. Export models to ONNX for CPU inference in the blue-agent service.

## Sources

### Primary (HIGH confidence)
- `Anthropic/hh-rlhf` (HuggingFace) — Dataset format, license (MIT), subsets
- `toxigen/toxigen-data` (HuggingFace) — Dataset structure, access requirements, CDLA-Permissive-2.0 license
- `microsoft/TOXIGEN` (GitHub) — LICENSE.txt (MIT + CDLA-Permissive-2.0), pretrained checkpoints
- HuggingFace Transformers docs — Trainer API, text classification task, pipeline usage
- `protectai/llm-guard` (GitHub) — Scanner list, MIT license, Python version constraints, ONNX support
- `scipy.stats.bootstrap` docs — BCa method implementation

### Secondary (MEDIUM confidence)
- arXiv:2511.19794 — Paired BCa bootstrap + permutation test protocol for small-k evaluation
- arXiv:2506.11094 — Comprehensive survey on LLM safety evaluation (four-dimensional taxonomy)
- arXiv:2512.21326 — All-pairs paired method for LLM evaluation noise analysis
- arXiv:2402.04249 — HarmBench standardized red teaming evaluation framework
- arXiv:2406.16746 — Holistic safety evaluation methodology
- HuggingFace Course Chapter 3 — Fine-tuning with Trainer API
- 4Geeks blog (2025-11-20) — Classical vs Transformer text classification comparison

### Tertiary (LOW confidence)
- arXiv:2501.18243 — Statistical multi-metric evaluation framework (abstract only, not fully verified)
- arXiv:2510.04265 — Bayesian framework replacing Pass@k (needs verification for safety eval applicability)
- GuardBench paper (EMNLP 2024) — 40-dataset guardrail benchmark (useful for metric inspiration)
- Crucible Benchmark — Multi-track safety evaluation design (commercial, limited access)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — HuggingFace transformers + LLM-Guard + scipy is the established ecosystem for this problem
- Architecture patterns: HIGH — Strategy pattern for classifiers, mediator for isolation, BCa bootstrap for statistics are well-established
- Pitfalls: MEDIUM — Dataset-specific pitfalls (HH-RLHF format, ToxiGen access) verified from official sources; some pitfalls (over-refusal, GPU requirements) based on general ML experience
- 50+ metrics definition: MEDIUM — LLM-Guard provides ~30; reaching 50+ requires custom metric design that needs validation

**Research date:** 2026-05-16
**Valid until:** 2026-08-16 (3 months — transformer ecosystem moves fast, but core patterns are stable)
