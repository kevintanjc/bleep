from typing import List, Optional, Dict, Tuple, Any
import json
import os
import numpy as np

from presidio_analyzer import AnalyzerEngine, RecognizerResult, EntityRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

_ONNXR_AVAILABLE = True
try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
except Exception:
    _ONNXR_AVAILABLE = False

# Constants
LABEL_MAP = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION", "MISC": "NRP"}
REQ_TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json")


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


def _load_id2label(labels_path: Optional[str], cfg_path: Optional[str]) -> Dict[int, str]:
    # labels.txt preferred
    if labels_path and os.path.isfile(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            labels = [ln.strip() for ln in f if ln.strip()]
        return {i: lab for i, lab in enumerate(labels)}
    # fallback to config.json id2label
    if cfg_path and os.path.isfile(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return {int(k): v for k, v in (cfg.get("id2label") or {}).items()}
        except Exception:
            return {}
    return {}


class DistilBertOnnxRecognizer(EntityRecognizer):
    """
    DistilBERT NER using a local ONNX model.
    Supports PERSON, ORGANIZATION, LOCATION, NRP.
    """

    def __init__(
        self,
        onnx_path: str,
        tokenizer_path: Optional[str] = None,
        model_id_fallback: str = "dslim/distilbert-base-NER",
        labels_path: Optional[str] = None,
        config_path: Optional[str] = None,
        supported_entities: Optional[List[str]] = None,
        score_threshold: float = 0.60,
        device: int = -1,
        max_length: int = 256,
        allow_download: bool = True,
    ):
        if not _ONNXR_AVAILABLE:
            raise RuntimeError("onnxruntime or transformers not available")

        if supported_entities is None:
            supported_entities = ["PERSON", "ORGANIZATION", "LOCATION", "NRP"]
        super().__init__(supported_entities=supported_entities, name=f"distilbert_onnx::{os.path.basename(onnx_path)}")

        self.sess = None
        self.input_names: List[str] = []
        self.input_dtypes: Dict[str, Any] = {}
        self.output_name: Optional[str] = None

        self.score_threshold = score_threshold
        self.max_length = max_length
        self.group2presidio = LABEL_MAP

        if not os.path.isfile(onnx_path) or not onnx_path.lower().endswith(".onnx"):
            raise FileNotFoundError(f"Invalid ONNX model path: {onnx_path}")

        # Resolve tokenizer
        target_tok = tokenizer_path or model_id_fallback
        tok_kwargs: Dict[str, Any] = {}
        if not allow_download:
            tok_kwargs["local_files_only"] = True
            if os.path.isdir(target_tok):
                missing = [
                    p for p in REQ_TOKENIZER_FILES
                    if not os.path.isfile(os.path.join(target_tok, p)) or os.path.getsize(os.path.join(target_tok, p)) == 0
                ]
                if missing:
                    raise RuntimeError(f"TOKENIZER_PATH missing or empty: {missing} in {target_tok}")
            elif os.path.sep in target_tok:
                raise RuntimeError(f"TOKENIZER_PATH directory not found: {target_tok}")

        self.tokenizer = AutoTokenizer.from_pretrained(target_tok, **tok_kwargs)

        # ONNX session
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        so.inter_op_num_threads = 1
        so.intra_op_num_threads = max(1, (os.cpu_count() or 4) - 1)
        providers = ["CPUExecutionProvider"] if device == -1 else ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self.sess = ort.InferenceSession(onnx_path, sess_options=so, providers=providers)

        # Model I/O
        inputs = self.sess.get_inputs()
        self.input_names = [i.name for i in inputs]
        self.input_dtypes = {
            i.name: (np.int64 if "int64" in i.type else np.int32 if "int32" in i.type else None) for i in inputs
        }
        self.output_name = self.sess.get_outputs()[0].name

        # Labels
        self.id2label = _load_id2label(labels_path, config_path) or {
            i: lab for i, lab in enumerate(["O", "B-MISC", "I-MISC", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC"])
        }

    def _to_inputs(self, enc: Dict[str, Any]) -> Dict[str, np.ndarray]:
        out: Dict[str, np.ndarray] = {}
        for name in self.input_names:
            if name in enc:
                arr = enc[name]
                want = self.input_dtypes.get(name) or arr.dtype
                out[name] = arr.astype(want, copy=False) if arr.dtype != want else arr
            elif name == "token_type_ids":
                base = enc["input_ids"]
                want = self.input_dtypes.get(name) or base.dtype
                out[name] = np.zeros_like(base, dtype=want)
        return out

    def _aggregate(
        self, ids: np.ndarray, scores: np.ndarray, offsets: List[Tuple[int, int]]
    ) -> List[Tuple[str, int, int, float]]:
        res: List[Tuple[str, int, int, float]] = []
        curr_group: Optional[str] = None
        start = last_end = 0
        sum_score = 0.0
        count = 0

        def flush():
            if curr_group is not None and count:
                res.append((curr_group, start, last_end, sum_score / count))

        for i, lab_id in enumerate(ids):
            label = self.id2label.get(int(lab_id), "O")
            s, e = offsets[i]
            if s == e:
                continue
            if label == "O":
                flush()
                curr_group = None
                sum_score = 0.0
                count = 0
                continue
            prefix, group = (label.split("-", 1) + [""])[:2] if "-" in label else ("B", label)
            if curr_group == group and prefix in ("I", "B"):
                sum_score += float(scores[i])
                count += 1
                last_end = e
            else:
                flush()
                curr_group = group
                start = s
                last_end = e
                sum_score = float(scores[i])
                count = 1
        flush()
        return res

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        if not text or not entities or self.sess is None:
            return []

        enc = self.tokenizer(
            text,
            return_tensors="np",
            return_offsets_mapping=True,
            truncation=True,
            max_length=self.max_length,
        )
        offsets = [tuple(map(int, o)) for o in enc.pop("offset_mapping")[0]]
        ort_inputs = self._to_inputs(enc)

        logits = self.sess.run([self.output_name], ort_inputs)[0]  # [1, seq_len, num_labels]
        probs = _softmax(logits, axis=-1)
        ids = probs.argmax(axis=-1)[0]
        conf = probs.max(axis=-1)[0]

        spans = self._aggregate(ids=ids, scores=conf, offsets=offsets)

        out: List[RecognizerResult] = []
        for group, s, e, score in spans:
            mapped = self.group2presidio.get(group)
            if mapped and mapped in entities and score >= self.score_threshold:
                out.append(RecognizerResult(entity_type=mapped, start=int(s), end=int(e), score=float(score)))
        return out


def build_analyzer(spacy_model: str = "en_core_web_lg", use_distilbert: bool = True) -> AnalyzerEngine:
    nlp_conf = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": spacy_model}]}
    provider = NlpEngineProvider(nlp_configuration=nlp_conf)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

    if use_distilbert:
        try:
            db = DistilBertOnnxRecognizer(
                onnx_path=os.getenv("ONNX_MODEL_PATH"),
                tokenizer_path=os.getenv("TOKENIZER_PATH"),
                labels_path=os.getenv("NER_LABELS_PATH"),
                config_path=os.getenv("NER_CONFIG_PATH"),
                score_threshold=0.60,
                device=int(os.getenv("HF_NER_DEVICE", "-1")),
                max_length=int(os.getenv("HF_MAX_LEN", "256")),
                allow_download=os.getenv("HF_ALLOW_DOWNLOAD", "true").lower() == "true",
            )
            analyzer.registry.add_recognizer(db)
        except Exception:
                import traceback
                print("[DistilBERT ONNX] init failed:\n" + traceback.format_exc())
    return analyzer