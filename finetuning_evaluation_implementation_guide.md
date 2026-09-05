# Fine-Tuning an LLM with an 80/10/10 Split and Task-Level Evaluation

## Goal

This document describes an implementation plan for fine-tuning a base LLM on customer-support data using an 80/10/10 train/validation/test split. It also describes how to:

- Track validation loss during training
- Measure actual customer-support task performance
- Establish a benchmark for the base model
- Evaluate checkpoints during fine-tuning
- Select the best fine-tuned model
- Avoid data leakage and test-set contamination

The implementation should be reproducible and should compare the base model and fine-tuned checkpoints fairly.

---

# 1. Dataset Split

Split the cleaned dataset into:

| Split | Percentage | Purpose |
|---|---:|---|
| Training | 80% | Used to update model weights |
| Validation | 10% | Used to monitor training and select checkpoints |
| Test | 10% | Used only for final unbiased evaluation |

For example, with 10,000 examples:

- Training: 8,000
- Validation: 1,000
- Test: 1,000

## Important rules

### Training set

The model learns from this data and sees it repeatedly during fine-tuning.

### Validation set

The model does not train on this data. Use it to:

- Calculate validation loss
- Track actual task performance during fine-tuning
- Compare checkpoints
- Select the best model
- Configure early stopping and other training decisions

### Test set

Keep this completely untouched until the final evaluation.

Do not use test results to:

- Choose epochs
- Choose checkpoints
- Tune hyperparameters
- Modify prompts
- Modify the training process

The test set should answer the final question:

> Does the selected fine-tuned model actually perform better than the base model on unseen data?

---

# 2. Clean the Data Before Splitting

Before performing the 80/10/10 split:

- Remove exact duplicates
- Detect and remove near-duplicates
- Normalize formatting
- Remove malformed conversations
- Standardize the instruction/response structure

Be particularly careful about semantic duplicates.

For example, these should not end up in different splits:

- Train: "I was charged twice for my subscription."
- Test: "My card was charged two times for the same subscription."

This can cause data leakage and artificially inflate evaluation performance.

A recommended order is:

1. Clean
2. Normalize
3. Deduplicate / semantic deduplicate
4. Group related or duplicate conversations if necessary
5. Split into train/validation/test

---

# 3. What Happens During Fine-Tuning?

The training loop should conceptually look like:

Base Model
    |
    v
Train on Training Set
    |
    v
Epoch completes
    |
    +--> Calculate validation loss on validation set
    |
    +--> Evaluate task-level performance on fixed validation benchmark
    |
    +--> Save checkpoint and metrics
    |
    v
Next epoch

An epoch is one complete pass through the training dataset.

For example:

- Epoch 1: model sees all training examples once
- Epoch 2: model sees all training examples again
- Epoch 3: model sees them again

The model should save checkpoints regularly, preferably at least once per epoch for this project.

---

# 4. Validation Loss

Track:

- Training loss
- Validation loss

Example:

| Epoch | Training Loss | Validation Loss |
|---|---:|---:|
| 1 | 1.20 | 1.10 |
| 2 | 0.85 | 0.82 |
| 3 | 0.60 | 0.65 |
| 4 | 0.42 | 0.67 |
| 5 | 0.30 | 0.75 |

In this example:

- Training loss keeps decreasing
- Validation loss improves until Epoch 3
- Validation loss begins increasing afterward

This is a potential sign of overfitting.

However, do NOT automatically assume that the checkpoint with the lowest validation loss is the best customer-support model.

Validation loss is a supporting metric. Actual task performance should also be measured.

---

# 5. Define "Actual Task Performance"

For a customer-support model, define what a good answer means.

The evaluation should answer:

1. Did the model understand the customer's issue?
2. Is the response correct?
3. Does the response resolve or meaningfully advance the issue?
4. Does the response hallucinate unsupported information?
5. Is the response clear, helpful, and professionally written?

Recommended metrics:

| Metric | Question |
|---|---|
| Issue Understanding | Did the model correctly understand what the customer needs? |
| Correctness | Is the information provided correct? |
| Resolution Quality | Does the response solve or appropriately advance the problem? |
| Hallucination Rate | Did the model invent unsupported information? |
| Support Quality | Is the response clear, helpful, professional, and appropriate? |

---

# 6. Metric Rubrics

## 6.1 Issue Understanding

Score from 1 to 5.

| Score | Meaning |
|---:|---|
| 5 | Fully understands the customer's issue and intent |
| 4 | Understands the main issue with minor omissions |
| 3 | Partially understands the issue |
| 2 | Significant misunderstanding |
| 1 | Completely misunderstands the issue |

## 6.2 Correctness

Score from 1 to 5.

| Score | Meaning |
|---:|---|
| 5 | Fully correct |
| 4 | Mostly correct, minor issues |
| 3 | Partially correct |
| 2 | Major incorrect information |
| 1 | Completely incorrect |

## 6.3 Resolution Quality

Score from 1 to 5.

| Score | Meaning |
|---:|---|
| 5 | Fully resolves the issue or gives the correct next steps |
| 4 | Mostly helpful, minor missing information |
| 3 | Somewhat helpful |
| 2 | Barely advances resolution |
| 1 | Does not help resolve the issue |

## 6.4 Hallucination

Use a binary metric:

- Yes
- No

Then calculate:

Hallucination Rate = (number of responses containing hallucinations / total responses) * 100

A hallucination should mean factual information, policies, actions, guarantees, or claims unsupported by the reference answer or available context.

## 6.5 Support Quality

Score from 1 to 5 based on:

- Clarity
- Helpfulness
- Professional tone
- Appropriate customer-support behavior
- Conciseness where appropriate

---

# 7. Use LLM-as-a-Judge

Manual human evaluation is valuable but can be expensive and slow after every epoch.

A practical implementation is to use a strong evaluator model as an LLM judge.

For each evaluation example, provide:

- Customer question
- Reference answer
- Model-generated answer
- Evaluation rubric

The evaluator should return structured JSON.

Example:

{
  "issue_understanding": 5,
  "correctness": 4,
  "resolution_quality": 5,
  "hallucination": false,
  "support_quality": 4,
  "reason": "The response correctly understands the issue and provides appropriate next steps."
}

The implementation should validate that the evaluator output is valid JSON.

Prefer structured outputs or JSON schema enforcement if available.

---

# 8. Example Judge Prompt

Use a prompt conceptually similar to:

You are evaluating a customer support assistant.

Customer Query:
{customer_query}

Reference Answer:
{reference_answer}

Generated Answer:
{generated_answer}

Evaluate the generated answer on the following criteria.

1. Issue Understanding (1-5):
Did the response correctly understand the customer's problem?

2. Correctness (1-5):
Is the information in the response correct based on the reference answer and available context?

3. Resolution Quality (1-5):
Does the response solve the customer's problem or provide appropriate next steps?

4. Hallucination (Yes/No):
Does the response contain factual information, policies, actions, or guarantees unsupported by the reference answer or available context?

5. Support Quality (1-5):
Is the response clear, helpful, professional, and appropriate?

Return ONLY valid JSON.

The implementation may improve this prompt, but the evaluation rubric should remain fixed across experiments.

---

# 9. Reference Answers Are Not the Only Valid Answers

Do not use exact string matching as the primary evaluation method.

For example:

Reference answer:

"Please contact billing support and provide your transaction ID."

Generated answer:

"Please send us your transaction ID and account email so we can investigate the duplicate charge."

These responses use different wording but may both be useful.

Therefore, metrics such as exact match, BLEU, or ROUGE should not be the primary indicators of customer-support quality.

The evaluation should focus on:

- Correctness
- Resolution
- Helpfulness
- Groundedness
- Hallucination

rather than wording similarity alone.

---

# 10. Create a Fixed Validation Benchmark

Do not necessarily run expensive generation + LLM judging on the entire validation set after every epoch.

Instead, create a fixed representative benchmark subset.

For example:

Validation set: 1,000 examples
Task evaluation benchmark: 50-200 representative examples

A good starting point is around 100 examples.

Each benchmark item should contain:

{
  "id": "example_001",
  "customer_query": "I was charged twice for my subscription.",
  "reference_response": "Sorry about that. Please provide...",
  "category": "billing"
}

The benchmark should represent important categories in the dataset.

Example:

| Category | Example Count |
|---|---:|
| Billing | 20 |
| Account issues | 20 |
| Technical issues | 20 |
| Refunds | 15 |
| General questions | 15 |
| Edge cases | 10 |

The exact categories should be derived from the actual dataset.

## Critical requirement

Freeze this benchmark before comparing models.

Every checkpoint must be evaluated using the exact same benchmark examples.

---

# 11. Establish the Base Model Benchmark

The base model benchmark must be created BEFORE fine-tuning.

Use the same fixed validation benchmark.

For every benchmark example:

Customer Question
    +
Same System Prompt
    |
    v
Base Model
    |
    v
Generated Response
    |
    v
LLM Judge
    |
    v
Scores

Aggregate the results.

Example baseline:

| Model | Understanding | Correctness | Resolution | Support Quality | Hallucination |
|---|---:|---:|---:|---:|---:|
| Base Model | 3.1 | 2.9 | 2.7 | 3.5 | 18% |

This becomes the baseline against which every fine-tuned checkpoint is compared.

---

# 12. Fair Comparison Requirements

The base model and all fine-tuned checkpoints must use:

- The same benchmark questions
- The same system prompt
- The same input formatting
- The same generation parameters
- The same evaluator model
- The same evaluator prompt
- The same scoring rubric

The only intended difference should be the model weights.

For example, if the model input format is:

System:
You are a helpful customer support assistant.

User:
{customer question}

Assistant:

Then use this same structure for:

- Base model
- Epoch 1 checkpoint
- Epoch 2 checkpoint
- Epoch 3 checkpoint
- Final selected model

---

# 13. Generation Settings

Use fixed generation settings to make results reproducible.

For example:

generation_config = {
    "max_new_tokens": 256,
    "do_sample": False
}

For deterministic generation, use greedy decoding or another fixed deterministic decoding strategy.

Avoid changing generation parameters between checkpoints.

Record all generation settings as part of the experiment metadata.

---

# 14. Evaluation During Fine-Tuning

After each epoch, or at each selected checkpoint:

1. Calculate validation loss on the full validation set.
2. Load the checkpoint.
3. Generate responses for the fixed validation benchmark.
4. Evaluate generated responses using the fixed LLM judge.
5. Aggregate metrics.
6. Save results.

The result may look like:

| Model | Val Loss | Understanding | Correctness | Resolution | Support Quality | Hallucination |
|---|---:|---:|---:|---:|---:|---:|
| Base | - | 3.1 | 2.9 | 2.7 | 3.5 | 18% |
| Epoch 1 | 0.92 | 3.8 | 3.7 | 3.6 | 3.9 | 12% |
| Epoch 2 | 0.71 | 4.3 | 4.1 | 4.0 | 4.2 | 8% |
| Epoch 3 | 0.63 | 4.5 | 4.4 | 4.4 | 4.5 | 5% |
| Epoch 4 | 0.64 | 4.4 | 4.2 | 4.1 | 4.4 | 7% |

---

# 15. Choosing the Best Checkpoint

Do not select the best checkpoint solely by minimum validation loss.

Use a decision framework.

Recommended priority:

Primary:
- Resolution Quality

Secondary:
- Correctness
- Hallucination Rate

Supporting:
- Validation Loss
- Issue Understanding
- Support Quality

Example:

| Epoch | Val Loss | Resolution | Correctness | Hallucination |
|---:|---:|---:|---:|---:|
| 2 | 0.68 | 4.1 | 4.2 | 7% |
| 3 | 0.62 | 4.3 | 4.4 | 6% |
| 4 | 0.63 | 4.6 | 4.6 | 3% |
| 5 | 0.69 | 4.3 | 4.2 | 7% |

In this example, Epoch 4 may be selected even though Epoch 3 has slightly lower validation loss.

The objective is to build a better customer-support model, not merely minimize cross-entropy loss.

---

# 16. Early Stopping

Use a maximum number of epochs and optionally early stopping.

For example:

- Maximum epochs: 5-10
- Evaluate every epoch
- Save checkpoints every epoch
- Early stopping patience: 2-3 evaluations

Example:

Epoch 1 -> Validation loss improves
Epoch 2 -> Validation loss improves
Epoch 3 -> Validation loss improves
Epoch 4 -> No improvement
Epoch 5 -> No improvement
Epoch 6 -> No improvement

With patience = 3, training may stop after the third non-improving evaluation.

However, checkpoint selection should also consider task-level metrics.

The implementation should preserve all evaluation results so that the final selection can be justified.

---

# 17. Final Test Evaluation

Once the best checkpoint is selected using ONLY the validation data, perform the final evaluation on the untouched test set.

Compare:

Base Model
vs
Selected Fine-Tuned Model

Use the same evaluation pipeline.

Do NOT compare every epoch on the test set.

The test evaluation should be run only after model selection.

Example:

| Model | Understanding | Correctness | Resolution | Support Quality | Hallucination |
|---|---:|---:|---:|---:|---:|
| Base Model | 3.0 | 2.8 | 2.6 | 3.4 | 19% |
| Fine-Tuned Model | 4.5 | 4.4 | 4.3 | 4.6 | 4% |

This is the strongest evidence that fine-tuning improved the model on unseen examples.

---

# 18. Recommended Overall Architecture

                         TRAINING DATA
                               |
                               v
                        Fine-Tune Model
                               |
                        Save Checkpoints
                               |
               +---------------+---------------+
               |                               |
               v                               v
      Full Validation Set            Fixed Validation Benchmark
               |                               |
               v                               v
        Validation Loss                 Generate Responses
                                               |
                                               v
                                         LLM-as-a-Judge
                                               |
                                               v
                                        Task-Level Metrics
                                               |
                               +---------------+
                               |
                               v
                         Select Best Checkpoint
                               |
                               v
                     UNTOUCHED TEST SET EVALUATION
                               |
                      +--------+--------+
                      v                 v
                  Base Model       Best Fine-Tuned
                      |                 |
                      +--------+--------+
                               |
                               v
                         Final Comparison

---

# 19. Suggested Implementation Components

The implementation should ideally be modular.

## data/

Responsible for:

- Loading dataset
- Cleaning
- Normalization
- Exact deduplication
- Semantic/near-duplicate detection if implemented
- Train/validation/test splitting
- Saving split metadata and random seed

## training/

Responsible for:

- Loading base model
- Tokenization
- Fine-tuning
- Checkpoint saving
- Training and validation loss logging
- Early stopping

## evaluation/

Responsible for:

- Loading benchmark
- Running generation
- Calling the LLM judge
- Parsing structured evaluation results
- Calculating aggregate metrics
- Saving per-example results

## experiments/

Responsible for:

- Recording configuration
- Base model benchmark
- Per-checkpoint metrics
- Generation parameters
- Random seeds
- Model/checkpoint identifiers

## reporting/

Responsible for:

- Producing comparison tables
- Plotting validation loss
- Plotting task metrics by epoch/checkpoint
- Comparing base model versus final fine-tuned model

---

# 20. Recommended Output Files

Suggested experiment structure:

experiment/
    config.json
    data_split_metadata.json

    base_model/
        generations.jsonl
        evaluation_results.jsonl
        aggregate_metrics.json

    checkpoints/
        epoch_1/
            generations.jsonl
            evaluation_results.jsonl
            aggregate_metrics.json

        epoch_2/
            generations.jsonl
            evaluation_results.jsonl
            aggregate_metrics.json

        epoch_3/
            generations.jsonl
            evaluation_results.jsonl
            aggregate_metrics.json

    final_test/
        base_model_results.jsonl
        fine_tuned_results.jsonl
        comparison.json

    metrics/
        training_metrics.json
        validation_task_metrics.json

---

# 21. Suggested Aggregate Metrics

For each model/checkpoint, calculate:

{
  "model_id": "...",
  "checkpoint": "...",
  "validation_loss": 0.63,
  "issue_understanding_mean": 4.5,
  "correctness_mean": 4.4,
  "resolution_quality_mean": 4.4,
  "support_quality_mean": 4.5,
  "hallucination_rate": 0.05,
  "num_evaluated": 100
}

Also preserve individual example-level scores for later error analysis.

---

# 22. Error Analysis

Do not rely only on averages.

Store per-example results so the system can identify:

- Categories where the model improved
- Categories where it regressed
- Frequent hallucination patterns
- Common misunderstanding patterns
- Examples where the fine-tuned model is worse than the base model

Potential analysis:

| Category | Base Resolution | Fine-Tuned Resolution | Change |
|---|---:|---:|---:|
| Billing | 2.8 | 4.5 | +1.7 |
| Account | 3.2 | 4.1 | +0.9 |
| Technical | 2.6 | 4.3 | +1.7 |
| Refunds | 3.1 | 4.0 | +0.9 |

This makes the evaluation much more informative.

---

# 23. Recommended Final Workflow

## Phase 1: Prepare data

1. Clean data
2. Normalize data
3. Deduplicate and check near duplicates
4. Create 80/10/10 train/validation/test split
5. Freeze the split

## Phase 2: Build evaluation benchmark

1. Select 50-200 representative examples from the validation set
2. Preserve category coverage
3. Freeze the benchmark

## Phase 3: Benchmark base model

1. Use fixed system prompt
2. Use fixed generation settings
3. Generate answers for the validation benchmark
4. Run LLM-as-a-Judge
5. Save aggregate and per-example metrics

## Phase 4: Fine-tune

For each epoch/checkpoint:

1. Train on training split
2. Calculate validation loss on full validation split
3. Generate answers for fixed validation benchmark
4. Run LLM judge
5. Save metrics and checkpoint

## Phase 5: Select best model

Select using:

- Resolution Quality
- Correctness
- Hallucination Rate
- Validation Loss

Do not use the test set for this decision.

## Phase 6: Final evaluation

On the untouched test set:

1. Run base model
2. Run selected fine-tuned model
3. Use identical prompts and generation settings
4. Evaluate both using the same judge
5. Report final comparison

---

# 24. Key Principles

1. The test set must remain untouched until final evaluation.
2. Every checkpoint must be evaluated on the same fixed validation benchmark.
3. The base model benchmark must be generated before fine-tuning.
4. Base and fine-tuned models must use identical prompts and generation settings.
5. Validation loss alone should not determine the best customer-support model.
6. Task-level metrics should reflect the actual objective of the system.
7. Preserve per-example results for error analysis.
8. Use reproducible random seeds and save all experiment configurations.
9. Avoid data leakage, especially from duplicate and semantically similar support conversations across splits.
10. Final evaluation should compare the base model against the selected fine-tuned model on unseen test data.

---

# Desired End Result

The final experiment should be able to support a conclusion such as:

"Although Epoch 3 achieved the lowest validation loss, Epoch 4 achieved the highest customer-support resolution and correctness scores while producing the lowest hallucination rate on the fixed validation benchmark. Therefore, Epoch 4 was selected as the final checkpoint. On the untouched test set, the selected fine-tuned model significantly outperformed the base model across correctness, resolution quality, and hallucination rate."

This is the target implementation and evaluation methodology.
