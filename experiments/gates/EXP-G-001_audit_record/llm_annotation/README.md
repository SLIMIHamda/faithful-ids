# LLM annotation of extractor_audit_batch_v1

Six self-contained prompt files (`chunk_01.md` … `chunk_06.md`, 25 items each,
150 total). Same blindness as `annotator.html`: no extractor output or SHAP
signs are present anywhere in these files.

## How to use

1. Start a FRESH conversation per chunk (no shared context, no mention of the
   project, hypotheses, or other chunks).
2. Paste the entire chunk file as the message.
3. Save the model's fenced JSONL output to:
       responses/<model_name>/chunk_NN.jsonl
   (e.g. `responses/gpt-5/chunk_01.jsonl`) — content of the code block only.
4. Validate/merge:  python validate_llm_annotations.py responses/<model_name>
   Fix anything it flags (usually a truncated last line → ask the model to
   continue from the missing item, in the same conversation).

One model = one annotator. Multiple models give inter-annotator agreement, but
LLM annotators are a COMPLEMENT to the human pass, not a substitute — the audit
protocol's blind-human reading remains the primary evidence.
