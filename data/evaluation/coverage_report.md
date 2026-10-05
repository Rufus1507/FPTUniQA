# Coverage Analysis Report

**Generated:** Task 7 - Coverage Analysis
**Date:** 2024-10-02

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Questions | 151 |
| Corpus Size | 3,931 documents |
| BM25 Index | ✅ Built & Verified |

> **Note:** This analysis uses BM25 retrieval only. Dense vector retrieval (FAISS) results may differ.

## Corpus Distribution

### By Document Type
| Doc Type | Count | Percentage |
|----------|-------|------------|
| curriculum | 1,676 | 42.6% |
| admission | 658 | 16.7% |
| scholarship | 581 | 14.8% |
| general | 546 | 13.9% |
| tuition | 445 | 11.3% |
| enrollment | 25 | 0.6% |

### By Campus
| Campus | Count | Percentage |
|--------|-------|------------|
| all | 2,535 | 64.5% |
| ho_chi_minh | 691 | 17.6% |
| ha_noi | 225 | 5.7% |
| can_tho | 218 | 5.5% |
| da_nang | 131 | 3.3% |
| quy_nhon | 131 | 3.3% |

## Coverage by Category

| Category | Count | BM25 Performance |
|----------|-------|-----------------|
| dao_tao | 27 | ✅ All questions retrieve relevant docs |
| hoc_phi | 21 | ✅ All questions retrieve relevant docs |
| hoc_bong | 17 | ✅ All questions retrieve relevant docs |
| tot_nghiep | 19 | ✅ All questions retrieve relevant docs |
| ky_luat | 14 | ✅ All questions retrieve relevant docs |
| admission | 13 | ✅ All questions retrieve relevant docs |
| temporal | 18 | ✅ All questions retrieve relevant docs |
| multi_hop | 22 | ✅ All questions retrieve relevant docs |

## Data Gaps Analysis

### Identified Issues

1. **Chunk Size Too Small**
   - Current: ~217 characters average
   - Recommended: 400-500 tokens
   - Impact: May split related information across chunks

2. **Campus Distribution Imbalance**
   - 64.5% documents are "all campuses" generic
   - Campus-specific docs only 35.5%
   - Hà Nội, Cần Thơ, Đà Nẵng, Quy Nhơn have fewer docs

3. **Enrollment Documents**
   - Only 25 documents (0.6%)
   - Lowest coverage among doc types

4. **Missing Historical Data**
   - Only K22 (2026) cohort data
   - Temporal comparisons require older cohorts

## Recommendations

### High Priority
1. **No immediate crawling needed** - Corpus coverage is adequate

### Task 8 Results (Completed)
- Current chunk size: ~114 tokens (285 chars)
- Retrieval performance: 100% Recall@10
- **Conclusion: No immediate chunk optimization needed**

### Medium Priority
1. Collect historical tuition data (K20-K21) for temporal comparisons
2. Increase campus-specific documents if needed

### Low Priority
1. Review enrollment category documents (only 25)
2. Consider rebalancing corpus by campus

## Conclusion

✅ **Corpus is sufficient for current evaluation needs**
- 3,931 documents covering all major categories
- BM25 retrieval successfully finds relevant documents for all 151 questions
- No critical data gaps identified
