"""Shared model/tokenizer loading, used by train.py and generate_base.py.

Keeping this in one place guarantees the base reference (no adapter) and the
training run load the base identically — same precision (fp16 for LoRA, 4-bit
NF4 for QLoRA), so the fp16 per-epoch selection compares like with like.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import config


def load_tokenizer():
    tok = AutoTokenizer.from_pretrained(config.BASE_MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok


def load_base_model(for_training):
    """Load the base model. QLoRA -> 4-bit NF4; LoRA -> fp16."""
    kwargs = dict(trust_remote_code=True, device_map="auto")
    if config.USE_QLORA:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
    else:
        kwargs["torch_dtype"] = torch.float16
    model = AutoModelForCausalLM.from_pretrained(config.BASE_MODEL, **kwargs)
    if for_training and config.USE_QLORA:
        from peft import prepare_model_for_kbit_training
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    return model
