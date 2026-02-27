# Geographic Data Availability

## Summary Table

| Category | ZIP | Metro (CBSA) |
|---|---|---|
| ZHVI | ✅ | ✅ |
| ZORI | ✅ | ✅ |
| ZHVF (forecast) | ✅ (when available) | ✅ (when available) |
| Flip dynamics (inventory, price cuts, sale-to-list, heat, pending) | ❌ | ✅ |

## Implications

LTR analysis is natively ZIP-level because both home values (ZHVI) and rents (ZORI) are available at ZIP granularity. This enables direct ZIP screening for yield and growth.

Flip dynamics are metro-level only. Inventory pressure, pricing behavior, and market-speed indicators should be ranked at CBSA level first, then narrowed to ZIPs by applying ZIP-level proxy filters (for example ZHVI price bands and optional positive ZHVF).

In practical terms:
- Use `rank_metros_for_flip` to decide which metros look favorable for flips.
- Use `select_zips_within_metro_for_flip` to pick ZIPs inside those metros that fit your buy box.
- Do not treat ZIP-level flip dynamics as directly observed Zillow Research signals because they are not published at ZIP level.

## ZIP -> Metro Mapping

ZIP to metro mapping should be sourced from HUD USPS ZIP-CBSA crosswalk files. A single ZIP can map to multiple CBSAs, so the pipeline resolves to one CBSA by selecting the row with the highest residential ratio (`res_ratio`).

If a ZIP has no CBSA mapping, LTR outputs remain available while flip outputs must return `null` with `flip_null_reason="metro_mapping_unavailable"`.
