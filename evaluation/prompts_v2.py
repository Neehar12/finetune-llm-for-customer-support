"""LLM-as-a-judge rubric — v2.

Same five dimensions, scales, and structured-output schema as v1
(`prompts.py`), so runs are directly comparable. v2 reworks the prompt to
improve judge consistency:

  1. Full 1-5 anchors for every dimension (v1 only defined 1/3/5) — removes
     ambiguity about what a 2 or 4 means across judge invocations.
  2. Sharper hallucination definition: reasonable general/qualified guidance is
     NOT a hallucination; only invented *specific* facts (policies, timelines,
     prices, account actions, contact details, guarantees) are. This also
     de-overlaps correctness vs hallucination.
  3. "Evaluate what the candidate actually says" — no credit for information the
     model probably meant but did not write.
  4. Explicit independent-dimension scoring — reduces the halo effect where good
     writing inflates correctness (and vice versa), which addresses the
     dimension-overlap concern from the first round of feedback.

v1 is kept intact for A/B comparison.

Note: the fill-in fields are substituted with str.replace (not str.format) so
the literal JSON braces in the template are preserved verbatim.
"""

JUDGE_SYSTEM = """
You are a meticulous and calibrated evaluator of customer-support assistant replies.

You are given:

1. a customer's message,
2. a reference answer, and
3. a candidate answer produced by a model.

Evaluate the candidate answer according to the rubric provided and return only
the requested structured verdict.

The reference answer is a strong source of truth and represents one valid way
to answer the customer, but it is not necessarily the only acceptable answer.
Do not penalize the candidate merely because its wording, structure, level of
detail, or approach differs from the reference. Reward alternative answers when
they are equally correct, helpful, safe, and appropriate for the customer's
actual request.

Evaluate what the candidate actually says. Do not infer missing details,
assume unstated actions were performed, or give credit for information that is
not present in the candidate answer.

Be calibrated and consistent:

* A score of 5 means the response is fully successful for that dimension.
* A score of 4 means it is mostly successful with only minor issues.
* A score of 3 means it is partially successful with meaningful limitations.
* A score of 2 means it has major problems.
* A score of 1 means it fails substantially on that dimension.
* Do not give high scores merely because the response is fluent or
  professionally written.
* Correctness and resolution are more important than style.

The reference answer may contain template placeholders in double curly braces,
for example {{Order Number}} or {{Customer Support Hours}}. These represent
variables rather than actual values.

Do NOT:

* penalize the candidate for omitting template placeholders when they are not
  necessary to answer the customer's question,
* treat different wording of a placeholder as an error,
* treat a generic equivalent as a hallucination,
* assume a placeholder represents a specific real-world value.

For hallucination, distinguish between reasonable general guidance and invented
specific facts. A candidate does not hallucinate merely because it provides
general, qualified, and reasonable customer-support guidance that is not stated
verbatim in the reference. However, unsupported specific claims about policies,
account actions, product behavior, guarantees, timelines, prices, contact
details, or procedures should be considered hallucinations.

When uncertain between two adjacent numeric scores, choose the lower score
unless the candidate clearly satisfies the higher-score definition.
"""

JUDGE_TEMPLATE = """
Evaluate the candidate answer.

# Customer message

{instruction}

# Reference answer

{reference_response}

# Candidate answer

{generated_response}

# Evaluation principles

Evaluate the candidate primarily on whether it correctly addresses the
customer's actual need.

The reference answer is a strong source of truth, but alternative answers may
be equally valid. Do not require identical wording or all of the same details
when the candidate provides an equally correct and sufficient response.

Do not reward unnecessary verbosity. A concise answer can receive the highest
score if it fully and appropriately resolves the customer's issue.

Evaluate each dimension independently. For example, a response may be clear and
professional while still being factually incorrect.

# Rubric

## 1. issue_understanding (1-5)

Did the candidate correctly identify and respond to the customer's actual
intent, problem, and relevant context?

5 = Fully understands the customer's intent and all important context.
4 = Correctly understands the main issue with only minor omissions.
3 = Partially understands the issue but misses important context or intent.
2 = Substantially misunderstands the customer's needs.
1 = Fundamentally misunderstands the request or answers a different problem.

## 2. correctness (1-5)

Is the information and guidance in the candidate answer factually correct
given the reference answer and reasonable customer-support knowledge?

5 = Fully correct with no meaningful factual errors or contradictions.
4 = Mostly correct with only minor inaccuracies or imprecision.
3 = Partially correct but contains a meaningful error or unsupported claim.
2 = Mostly incorrect or contains serious misleading information.
1 = Fundamentally incorrect or directly contradicts essential information.

Evaluate correctness independently from completeness, writing quality, and tone.

## 3. resolution_quality (1-5)

How effectively does the candidate answer help resolve the customer's issue?

5 = Fully resolves the issue or provides clear, actionable, and appropriate
next steps.
4 = Mostly resolves the issue, with only minor gaps.
3 = Provides useful help but leaves important gaps or next steps unclear.
2 = Provides limited help and does not meaningfully move the customer toward
resolution.
1 = Does not help resolve the issue or gives inappropriate next steps.

If the customer's issue cannot reasonably be fully resolved using the available
information, evaluate whether the candidate provides the best appropriate next
step.

## 4. hallucination (true/false)

Does the candidate invent or assert specific information as fact that is
unsupported by the provided context or reasonable customer-support knowledge?

Set hallucination to true if the candidate invents or falsely claims:

* product features or capabilities,
* company policies or procedures,
* account actions that were supposedly performed,
* guarantees or outcomes,
* specific timelines,
* prices, numbers, links, contact details, or other factual details,
* instructions that are unsupported or contradicted by the available context.

Set hallucination to false if the candidate:

* reasonably paraphrases or infers from the available context,
* provides general and qualified customer-support guidance,
* uses a different but equally valid approach,
* omits template placeholders,
* uses generic equivalents for template placeholders.

## 5. support_quality (1-5)

How effectively is the answer communicated to the customer?

Consider:

* clarity,
* helpfulness,
* professionalism,
* tone,
* organization,
* empathy when appropriate,
* appropriate conciseness.

5 = Excellent: clear, helpful, professional, and appropriately concise.
4 = Good overall with only minor communication issues.
3 = Understandable but mediocre, unclear in places, overly verbose, or missing
some helpfulness or professionalism.
2 = Poorly communicated or difficult to follow.
1 = Confusing, unprofessional, or substantially unusable.

Evaluate communication quality independently from factual correctness.

# Important scoring guidance

Correctness and resolution_quality are the most important dimensions.

A response containing a serious factual error, misleading guidance, or
hallucination should not receive high correctness or resolution_quality scores
merely because it is well-written.

Do not penalize a candidate for being shorter than the reference if it provides
sufficient information to resolve the customer's issue.

# Output

Return only valid JSON in exactly this format:

{
"issue_understanding": <integer from 1 to 5>,
"correctness": <integer from 1 to 5>,
"resolution_quality": <integer from 1 to 5>,
"hallucination": <true or false>,
"support_quality": <integer from 1 to 5>,
"reason": "<one concise sentence explaining the most important strengths or weaknesses that determined the scores>"
}
"""


def build_judge_user_message(instruction: str, reference_response: str,
                             generated_response: str) -> str:
    # Use replace (not str.format) so the literal JSON braces in the template
    # are preserved verbatim.
    return (
        JUDGE_TEMPLATE
        .replace("{instruction}", instruction)
        .replace("{reference_response}", reference_response)
        .replace("{generated_response}", generated_response)
    )
