# Context: Plagiarism Detection System - Target Comparison Feature

## Project Overview
Complete distributed plagiarism detection system using Apache Spark 3.3.0, Hadoop HDFS 3.3.1, and Docker Compose.

**Architecture:**
- 4 Docker containers: spark-master, 2 spark workers, app-client
- HDFS with NameNode + 2 DataNodes (replication factor 1)
- Streamlit web interface on port 8501
- Winnowing algorithm (k=5, window=4) for fingerprinting
- Jaccard similarity metric (threshold 70%)

## Recent Work: Adding Target Comparison Feature

### User Request
"ajoute l'option de choisir un seul fichier pour le comparer avec la toute la base de donnees"

### Implementation Summary

**1. Added `--target` Parameter**
- Modified `detect_plagiarism.py` to accept optional `--target` argument
- Enables comparing a single file against entire database instead of all-to-all comparison
- Performance improvement: O(n) vs O(n²) comparisons

**2. Key Code Changes in `src/spark_jobs/detect_plagiarism.py`**

**Lines 356-362:** Added argparse target parameter
```python
parser.add_argument('--target', type=str, default=None,
                    help='Fichier cible pour comparaison ciblée (ex: student1.py)')
```

**Lines 200-305:** Rewrote `compare_pairs()` method with conditional logic:
- **Target mode:** Filter target file, broadcast it, compare against all others
- **Standard mode:** Cartesian product for all-to-all comparison
- Both modes use inline Jaccard calculation (no object dependencies)

**Lines 124-195:** Rewrote `extract_features()` method:
- Removed broadcast of complex objects (`ast_extractor`, `winnowing_hasher`)
- Added local imports inside `extract_file_features()` function
- Recreates `ASTExtractor` and `WinnowingHasher` instances on each worker

**Lines 295, 379, 437:** Updated method signatures and calls to pass `target_file` parameter through pipeline

### Critical Bug Fixes

**Bug 1: ModuleNotFoundError on Workers**
- **Problem:** Broadcasting `self.similarity_calculator` caused `ModuleNotFoundError: No module named 'spark_jobs'` on workers
- **Solution:** Removed broadcast, implemented inline Jaccard similarity calculation
```python
# Inline Jaccard calculation (no dependencies)
set1 = set(fp1)
set2 = set(fp2)
if not set1 or not set2:
    score = 0.0
else:
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    score = intersection / union if union > 0 else 0.0
```

**Bug 2: Broadcast Deserialization Failures**
- **Problem:** Broadcasting `self.ast_extractor` and `self.winnowing_hasher` failed during pickle deserialization
- **Solution:** Import modules locally in worker functions, recreate instances
```python
def extract_file_features(file_tuple):
    # Local imports to avoid serialization issues
    import sys
    sys.path.append('/app/src')
    from spark_jobs.ast_extractor import ASTExtractor
    from spark_jobs.winnowing import WinnowingHasher
    
    ast_extractor = ASTExtractor()
    winnowing_hasher = WinnowingHasher(k=k_value, window_size=window_size)
    # ... rest of logic
```

### Testing Results

**Test 1: Target Mode - Plagiarism Detection**
```bash
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/test_target_final \
  --target plagiat1.py
```
**Result:** ✅ Detected 100% similarity between `plagiat1.py` and `plagiat2.py`

**Test 2: Target Mode - Student Verification**
```bash
--target student1.py
```
**Result:** ✅ Found 12.5% similarity with `test_file_1.py` (below threshold, no plagiarism)

### Usage Documentation Updated

Created examples in `USAGE_WITHOUT_STREAMLIT.md`:

**Example 1bis: Verify Suspect Student**
```bash
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/suspect_etudiant42 \
  --target etudiant42.py
```

**Example 4: New File vs Existing Database**
```bash
# Upload new file
docker exec spark-master hdfs dfs -put /tmp/nouveau_fichier.py hdfs://spark-master:9000/app/input/

# Compare
--target nouveau_fichier.py
```

**Example 5: Quick Email Attachment Check**
```bash
docker cp piece_jointe.py spark-master:/tmp/
docker exec spark-master hdfs dfs -put /tmp/piece_jointe.py hdfs://spark-master:9000/app/input/
--target piece_jointe.py
```

## Current System Status

**Cluster State:**
- All 4 containers: ✅ Healthy (90+ minutes uptime)
- HDFS: ✅ 10 files stored in `/app/input`
- Results: ✅ 7 analyses completed in `/app/results`

**Key Files in HDFS:**
- `example1.py`, `example2.py`, `example3.py` (reference files)
- `student1.py` through `student5.py` (student submissions)
- `plagiat1.py`, `plagiat2.py` (100% similar test files)
- `test_file_1.py`, `test_file_2.py` (additional test data)

**Recent Test Results:**
- `/app/results/test_target_final/` - plagiat1.py vs all: 100% match with plagiat2.py
- `/app/results/test_target_student1/` - student1.py vs all: ~12% similarity (no plagiarism)

## Important Code Patterns

**Archive Recreation Command:**
```bash
docker exec spark-master bash -c "cd /app/src && rm -f spark_jobs.zip && python3 -m zipfile -c spark_jobs.zip spark_jobs/*.py"
```

**HDFS Read Results:**
```bash
docker exec spark-master hdfs dfs -cat hdfs://spark-master:9000/app/results/[path]/part-*
```

## Known Limitations & Design Decisions

1. **No broadcast of complex objects:** All worker functions use local imports and recreate instances
2. **Inline similarity calculations:** Jaccard similarity implemented directly in lambda/map functions
3. **Module path management:** Each worker function adds `/app/src` to `sys.path`
4. **Archive dependency:** Must recreate `spark_jobs.zip` after any Python file changes
5. **Language detection:** Currently returns "unknown" for non-.py/.cpp/.java files (0 fingerprints)

## Next Potential Tasks

1. ⏳ Add `--target` support to Streamlit web interface (`src/client/app.py`)
2. ⏳ Test all 5 examples in `USAGE_WITHOUT_STREAMLIT.md`
3. ⏳ Performance benchmarking: target mode vs all-to-all mode
4. ⏳ Validate CLI mode with larger datasets (100+ files)
5. ⏳ Add progress indicators for long-running target comparisons

## Technical Debt

- `ast_extractor.py` uses simplified tokenization (not full tree-sitter AST)
- Encoding issues in console output (├®, ├á, ┼ô characters)
- Health check warnings suppressed with `2>/dev/null` in `entrypoint.sh`
- Optional tree-sitter dependency with `|| true` fallback

## Key Learning: PySpark Serialization

**Critical Rule:** Never broadcast objects that import custom modules. Workers cannot deserialize them due to module path issues. Instead:
- Broadcast only primitives (strings, numbers, lists, dicts)
- Import modules locally in worker functions
- Recreate class instances on each worker

This pattern solved both `ModuleNotFoundError` and pickle deserialization failures.
