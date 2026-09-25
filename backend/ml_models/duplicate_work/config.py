from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
FEATURES_DIR = DATA_DIR / "features"
MODELS_DIR = BASE_DIR / "models" / "duplicate_work"
OUTPUTS_DIR = DATA_DIR / "model_outputs" / "duplicate_work"
REPORTS_DIR = DATA_DIR / "reports"

# Inputs
CANDIDATE_PAIRS_PATH = FEATURES_DIR / "duplicate" / "duplicate_candidate_pairs.parquet"
CANONICAL_WORKS_PATH = FEATURES_DIR / "shared" / "canonical_works.parquet"

# Outputs
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SCORES_OUTPUT_PATH = OUTPUTS_DIR / "duplicate_scores.parquet"
REVIEW_OUTPUT_PATH = OUTPUTS_DIR / "duplicate_review.parquet"
EMBEDDINGS_CACHE_PATH = MODELS_DIR / "embeddings_cache.npz"
METADATA_PATH = MODELS_DIR / "global_model_metadata.json"
REPORT_PATH = REPORTS_DIR / "model2_duplicate_work_report.md"

# Model Configuration
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_BATCH_SIZE = 256
PAIR_CHUNK_SIZE = 100000

# Scoring Weights
WEIGHT_SEMANTIC = 0.65
WEIGHT_STRUCTURAL = 0.35

# Structural Sub-Weights
WEIGHT_STRUCT_AMOUNT = 0.35
WEIGHT_STRUCT_DATE = 0.35
WEIGHT_STRUCT_CONST = 0.15
WEIGHT_STRUCT_MP = 0.15

# Parameters
DATE_PROXIMITY_DECAY_DAYS = 30.0
THRESHOLD_HIGH = 0.85
THRESHOLD_REVIEW = 0.70
SHORT_DESC_WORD_THRESHOLD = 5
GENERIC_DESC_FREQ_THRESHOLD = 50
