# Evidence Table

| Claim | Evidence | Strength | Status |
| --- | --- | --- | --- |
| Planar screens can be rectified by a homography | projective document and screen-camera literature [3-6] | strong literature | evidence-backed |
| LK features and RANSAC support frame-to-reference motion estimation | Lucas-Kanade, Shi-Tomasi, Bouguet, robust estimation [7-10] | strong literature and code | evidence-backed |
| Temporal filtering can reduce high-frequency trajectory variation | stabilization literature [11-13] | strong literature | evidence-backed |
| Dynamic screen content can corrupt content-only tracking | task geometry and pilot observation | plausible | plausible-inference |
| The current proposed pipeline improves formal stability and geometry | formal experiment not completed | none yet | unsupported |
| Rectification suppresses moire | not measured and outside method | none | forbidden |
| Dataset contains 50 completed clips | collection incomplete | none yet | unsupported |
| Current implementation is per-frame border-guided | code audit contradicts claim | none | forbidden |

