"""The LLM-as-a-judge rubric and prompt.

Adapted from the rubric in `finetuning_evaluation_implementation_guide.md`
(sections 6-8). This rubric is FROZEN: base model, every fine-tuned checkpoint,
and the final test comparison are all scored with this exact prompt so that the
only variable is the model being judged.

Note on `{{placeholders}}`: the Bitext reference responses contain template
variables like {{Order Number}} or {{Customer Support Hours}}. These are
placeholders, not facts. The judge is told to treat them as such and NOT to
count a model's failure to reproduce them (or its use of a generic equivalent)
as a hallucination or an error.
"""

JUDGE_SYSTEM = (
    "You are a meticulous evaluator of customer-support assistant replies. "
    "You are given the customer's message, a reference answer, and a candidate "
    "answer produced by a model. You score the candidate answer against a fixed "
    "rubric and return only the structured verdict requested. Be calibrated and "
    "consistent: the reference answer is one valid way to respond, not the only "
    "one — reward correct, helpful, well-grounded answers even when their wording "
    "differs from the reference.\n\n"
    "The reference answer may contain template placeholders in double curly "
    "braces, e.g. {{Order Number}} or {{Customer Support Hours}}. These are "
    "variables, not real values. Do NOT penalize the candidate for omitting them, "
    "for phrasing them differently, or for using a generic equivalent, and do NOT "
    "treat their presence or absence as a hallucination."
)

JUDGE_TEMPLATE = """Evaluate the candidate answer.

# Customer message
{instruction}

# Reference answer
{reference_response}

# Candidate answer
{generated_response}

# Rubric
Score each dimension:

1. issue_understanding (1-5): Did the candidate correctly understand what the
   customer needs? 5 = fully understands intent; 3 = partial; 1 = misunderstands.

2. correctness (1-5): Is the information provided correct given the reference and
   ordinary customer-support knowledge? 5 = fully correct; 3 = partially; 1 = wrong.

3. resolution_quality (1-5): Does the answer resolve the issue or give the correct
   next steps? 5 = fully resolves / correct next steps; 3 = somewhat helpful;
   1 = does not help.

4. hallucination (true/false): Does the candidate invent factual information,
   policies, actions, or guarantees unsupported by the reference or reasonable
   support context? Template placeholders do not count. true = it hallucinates.

5. support_quality (1-5): Is the answer clear, helpful, professional in tone, and
   appropriately concise? 5 = excellent; 3 = mediocre; 1 = poor.

Also give a one-sentence `reason` justifying the scores."""


def build_judge_user_message(instruction: str, reference_response: str,
                             generated_response: str) -> str:
    return JUDGE_TEMPLATE.format(
        instruction=instruction,
        reference_response=reference_response,
        generated_response=generated_response,
    )
