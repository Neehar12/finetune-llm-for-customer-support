"""Frozen prompt + generation contract — the single source of truth.

The assignment is graded partly on an *identical* prompt template across
train -> eval -> serving -> README. To guarantee that, every stage imports the
constants here instead of re-declaring them. Changing anything in this file
changes the contract everywhere at once, which is exactly what we want.

Contract:
  - system role  = SYSTEM_PROMPT (fixed)
  - user role    = the raw customer message (the dataset `instruction`)
  - assistant    = the support reply (the dataset `response`)

Qwen3 is a hybrid-reasoning model. For a customer-support assistant we want
direct replies and predictable latency, so we run it with thinking disabled
(THINK = False). The Bitext reference responses are themselves direct (no
reasoning traces), so this also matches what the fine-tune will be trained on.
"""

# ---------------------------------------------------------------------------
# The frozen system prompt. Kept general so it holds up on the graders' own
# held-out queries, not just our test split.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a customer support assistant for an online business. "
    "A customer has sent you a message. Respond directly to the customer in a "
    "helpful, professional, and empathetic tone. Understand what they need, "
    "give accurate information, and clearly explain any steps required to "
    "resolve their request. Keep the response focused and concise."
)

# Qwen3 thinking mode. False = direct answers (no <think> traces).
THINK = False

# Deterministic, reproducible generation. Identical for base and fine-tuned
# models so the only variable in the comparison is the model weights.
GEN_OPTIONS = {
    "temperature": 0.0,   # greedy decoding
    "top_p": 1.0,
    "seed": 42,
    "num_predict": 512,   # max new tokens
}


def build_chat_messages(instruction: str) -> list[dict]:
    """Return the chat-format messages for a single customer query.

    This is the exact structure fed to the model at eval and serving time, and
    the structure the fine-tuning data is rendered into via the tokenizer's
    chat template.
    """
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": instruction},
    ]
