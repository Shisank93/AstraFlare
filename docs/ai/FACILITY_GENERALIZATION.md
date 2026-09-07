# AstraFlare Facility Generalization & Held-Out Partitioning

## 1. Objective
Facility generalization tests whether the AstraFlare model generalizes to industrial sites unseen during training, preventing spatial auto-correlation leakage across thermal detection clusters.

## 2. FacilityGroupSplitter Protocol
The `FacilityGroupSplitter` partitions dataset observations according to industrial site identity (`nearest_industrial_name` within 3,000m) or spatial cell grid ($\sim 3.3\text{ km}$):

- **Train Facilities $\cap$ Test Facilities = $\emptyset$** (Zero Overlap).
- **Fallback Handling**: Unnamed facilities or wildland regions outside named site buffers are partitioned by spatial cell ID (`cell_y_x`).

## 3. Empirical Verification Results

```text
Total Dataset Records: 8,786
Train Partition Records: 7,691 (87.5%)
Test Partition Records: 1,095 (12.5%)

Train Facility Groups: 14 facilities
Test Facility Groups: 3 facilities
Train/Test Facility Overlap: 0 (PASS)
```

## 4. Evaluation Experiments
1. **Experiment A (Weak Rule Fidelity)**: Tests model fidelity against weak supervision rules.
2. **Experiment B (Independent Event Generalization)**: Evaluates performance against independently verified external ground truth.
3. **Experiment C (Facility Held-Out)**: Evaluates model generalization on strictly held-out industrial facilities.
