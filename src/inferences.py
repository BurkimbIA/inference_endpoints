

import os
import re
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer


class MistralTranslator:
    """
    Wrapper around a Mistral-Instruct-based model fine-tuned for French↔Mooré translation.
    """
    def __init__(self, model_id: str, hf_token_env: str = "HF_TOKEN"):
        hf_token = os.environ.get(hf_token_env)
        if hf_token is None:
            raise ValueError(f"Please set the environment variable {hf_token_env} with your HuggingFace token.")
        self.model = AutoPeftModelForCausalLM.from_pretrained(
            model_id,
            token=hf_token,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.prompt_template = (
            """
<s>

You are an expert Moore translator. Translate the provided {src_name} text to {tgt_name}.
The Moore alphabet is: a, ã, b, d, e, ẽ, ɛ, f, g, h, i, ĩ, ɩ, k, l, m, n, o, õ, p, r, s, t, u, ũ, ʋ, v, w, y, z.
Based on source language ({src_name}), provide the {tgt_name} text.
[INST]
### {src_name}: 
{text}
[/INST]

### {tgt_name}:
"""
        )

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        lang_map = {"fra_Latn": "French", "moor_Latn": "Moore"}
        src_name = lang_map.get(src_lang, src_lang)
        tgt_name = lang_map.get(tgt_lang, tgt_lang)
        prompt = self.prompt_template.format(src_name=src_name, tgt_name=tgt_name, text=text)
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = self.model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=512,
            do_sample=False
        )
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        pattern = rf"### {tgt_name}:\s*(.+)"
        match = re.search(pattern, decoded, re.DOTALL)
        return match.group(1).strip() if match else decoded



import re
import os
import sys
import typing as tp
import unicodedata

import torch
from sacremoses import MosesPunctNormalizer
from transformers import AutoModelForSeq2SeqLM, NllbTokenizer

from huggingface_hub import login
auth_token = os.getenv('HF_TOKEN')
login(token=auth_token)

MODELS_URLS = {
            "V0.3(NLLB)": "burkimbia/BIA-NLLB-600M-david_5_epocks",
            "V0.5(NLLB)": "burkimbia/BIA-NLLB-1.3B-david_7_epocks",
        }

class TextPreprocessor:
    """
    Mimic the text preprocessing made for the NLLB model.
    This code is adapted from the Stopes repo of the NLLB team:
    https://github.com/facebookresearch/stopes/blob/main/stopes/pipelines/monolingual/monolingual_line_processor.py#L214
    """

    def __init__(self, lang="fr"):
        self.mpn = MosesPunctNormalizer(lang=lang)
        self.mpn.substitutions = [
            (re.compile(r), sub) for r, sub in self.mpn.substitutions
        ]

    def __call__(self, text: str) -> str:
        clean = self.mpn.normalize(text)
        clean = unicodedata.normalize("NFKC", clean)
        clean = clean[0].lower() + clean[1:]
        return clean


def fix_tokenizer(tokenizer, new_lang):
    """
    Ajoute un nouveau token de langue au tokenizer et met à jour les mappings d’identifiants.
    - Ajoute le token spécial s'il n'existe pas déjà.
    - Initialise ou met à jour `lang_code_to_id` et `id_to_lang_code` en utilisant `getattr` pour éviter les vérifications répétitives.
    """
    if new_lang not in tokenizer.additional_special_tokens:
        tokenizer.add_special_tokens({'additional_special_tokens': [new_lang]})

    tokenizer.lang_code_to_id = getattr(tokenizer, 'lang_code_to_id', {})
    tokenizer.id_to_lang_code = getattr(tokenizer, 'id_to_lang_code', {})

    if new_lang not in tokenizer.lang_code_to_id:
        new_lang_id = tokenizer.convert_tokens_to_ids(new_lang)
        tokenizer.lang_code_to_id[new_lang] = new_lang_id
        tokenizer.id_to_lang_code[new_lang_id] = new_lang

    return tokenizer



class NLLBTranslator:
    def __init__(self, model_name:str):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODELS_URLS[model_name]).to(device)
        if torch.cuda.is_available():
            self.model.cuda()
        self.tokenizer = NllbTokenizer.from_pretrained(MODELS_URLS[model_name])
        self.tokenizer = fix_tokenizer(self.tokenizer, "moor_Latn")

        self.preprocessor = TextPreprocessor()

    def translate(self, text, src_lang='moor_Latn', tgt_lang='fr_Latn', a=32, b=3, max_input_length=1024, num_beams=5, **kwargs):
        self.tokenizer.src_lang = src_lang
        self.tokenizer.tgt_lang = tgt_lang
        text_clean = self.preprocessor(text)

        inputs = self.tokenizer(text_clean, return_tensors='pt', padding=True, truncation=True, max_length=max_input_length)

        result = self.model.generate(
            **inputs.to(self.model.device),
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt_lang),
            max_new_tokens=int(a + b * inputs.input_ids.shape[1]),
            num_beams=num_beams,
            no_repeat_ngram_size=3,
            repetition_penalty=1.2,
            length_penalty=1.0,
            early_stopping=True,
            **kwargs
        )
        output = self.tokenizer.batch_decode(result, skip_special_tokens=True)[0]
        if text.endswith('?') or text.endswith('!'):
            output += text[-1]  # Ajouter le dernier caractère  (soit "?" ou "!")


        return output.capitalize(