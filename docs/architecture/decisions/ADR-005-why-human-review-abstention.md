# ADR-005: Implementation of Model Abstention & Human Review Class

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
Machine learning models forced to output a hard prediction on ambiguous or out-of-distribution inputs risk misclassifying critical industrial hazards or wildland fires.

**Decision:**  
Implement an explicit **Abstention State (`Human Review Required`)** triggered whenever maximum prediction confidence falls below a configured threshold (0.65) or top prediction probabilities conflict.

**Alternatives Considered:**  
1. **Hard Argmax Classification:** Always forcing the highest probability class regardless of magnitude.

**Trade-offs & Rationale:**  
In safety-critical disaster management and industrial monitoring, false certainty is highly dangerous. Introducing an explicit abstention state ensures human analysts are automatically alerted to ambiguous events requiring satellite optical verification or ground-truth check.
