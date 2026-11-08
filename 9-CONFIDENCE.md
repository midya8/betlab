# Confidence-sequence inversion with rational certificates

Version 0.3 adds `mean_evidence`, `confidence_sequence` and `confidence_demo`. This is a deliberately conservative fixed-bet family, not the paper's optimized betting strategy and not the original zero-null test with an effect size pasted onto it.

## The target and the proof

For differences `D_t in [-1,1]`, fix a number `mu` such that `E[D_t|past] <= mu` at every round. For an IID stream, its common mean is one such target. A time-varying stream needs that same upper bound at all rounds; the reported interval is not an estimate of the current mean, a moving average, or the average of arbitrary drifting conditional means. The scoring rule, stream, comparison, fixed bets/weights and alpha must be selected before testing. No data-generating assumption is verified by replaying observations.

For candidate `m in [-1,1]`, fixed `b_k in [0,1]` and positive normalized weights `w_k`, define

```text
K_(k,t)(m) = product_(i=1..t) [1 + b_k*(D_i-m)/2]
W_t(m) = sum_k w_k*K_(k,t)(m)
```

All factors are nonnegative throughout the domain. Under `E[D_t|past]<=m`, their conditional expectations are at most one. Every component, and then the fixed convex mixture, is a nonnegative supermartingale starting at one. Ville gives `P(exists t: W_t(mu)>=1/alpha)<=alpha`. Inverting the tests for each candidate does **not** require a union bound across candidate means: coverage concerns the one true fixed target `mu` and its one valid process. This does not authorize selection across models, scoring rules, streams, alphas or bet families.

Each factor is nonincreasing in `m`. Products and fixed positive sums preserve this property, so each prefix's rejected candidates form a lower interval. At a positive threshold greater than one, a crossing boundary, when present, is unique: a contributing positive-bet product is strictly decreasing where it is positive. Flat zero products and the zero-bet component cannot make wealth reach a threshold greater than one. The domain endpoints, zero-only bets and exact equalities are handled explicitly.

We intersect accepted sets across all prefixes, equivalently keeping the largest prefix boundary. This retains an earlier exclusion after wealth later falls. It is not necessary to rerun all possible candidate means, or to rely on a finite grid as if it were continuous coverage.

The new family uses effective bet `b/2`. At `m=0`, it matches the original fixed mixture with bets halved, not the original bets unchanged. The factor of two avoids a parameter singularity at either endpoint and makes global nonnegativity simple, at a cost in potential sensitivity. No optimality, variance adaptation or near-optimal width claim is made. Predictable and start-time mixtures are not included in this inversion.

## Exact arithmetic, inexact endpoints

For each prefix:

- If `W_t(-1)<1/alpha`, no candidate in the domain is rejected. Boundary convention: `[-1,-1]`, status `no_rejection`.
- If an evaluated endpoint or midpoint has wealth exactly equal to the threshold, report the exact rational boundary with status `exact`.
- Otherwise start with `lo=-1`, `hi=1`. The left witness has wealth strictly above threshold, the right strictly below. Bisect with exact rational arithmetic, retaining the appropriate witness. After `r` steps, the root lies in `[lo,hi]`, width `2/2^r`.

Each certificate retains both endpoints' mean, every component capital and mixture wealth, plus all tested midpoints, their exact wealth and comparison. No decimal threshold or numerical root solver is used. Roots are generally algebraic and are **not** claimed to be rational. Equality terminates early; it is not rounded away.

Take the maximum of prefix lower endpoints and independently the maximum of prefix upper endpoints. Their bracket encloses the running boundary with the same uncertainty bound. The lower endpoint is conservative. The reported confidence set is the **closed outer interval `[running_lower,1]`**, which includes every nonrejected candidate, possibly some rejected candidates and an exact boundary point. If the fixed target is excluded by this interval, its wealth must already have crossed. Thus simultaneous coverage is at least `1-alpha`. Including an equality point makes the interval conservative rather than changing the evidence test's equality-inclusive rejection rule.

The report distinguishes `certificate.lower/upper` for the current prefix from `running_lower/upper` and gives the prefix attaining each running witness. Prefix zero represents the initial `[-1,-1]` boundary convention. The upper side of the boundary bracket is **not** a confidence upper bound: the confidence upper endpoint is always one. No two-sided result is claimed.

## Developed controls

At alpha `1/4`, bet one:

| Sequence | Running boundary bracket | Reported confidence interval |
|---|---|---|
| 24 differences all `1/2` | `[12487/32768,1561/4096]` | `[12487/32768,1]` |
| Eight `+1`, then twelve `-1` | `[1273/2048,20369/32768]` | `[1273/2048,1]` |
| Eight `-1` | `[-1,-1]` | `[-1,1]` |

The first two use 16 bisections per nonexact prefix, so boundary uncertainty is at most `1/32768`. The reversal's current-prefix bound weakens after round eight, while its running interval does not expand. These sequences are developed numerical controls, not IID data or real-model benchmarks. A high persistent bound on a deliberately reversing sequence does not validate a common-mean interpretation of that sequence.

The coverage control is a supplied eight-round IID sign law: `P(D=+1)=3/4`, `P(D=-1)=1/4`, true mean `1/2`. All 256 paths are enumerated, with exact path probabilities, final interval/bracket, first true-mean crossing and exclusion indicators. At alpha `1/4`, both ever-exclusion probability and true-mean crossing probability are `2187/16384 <= 1/4`. The coverage enumeration uses eight bisections, separately from the 16-step display fixtures. Every conditional mixture slack is zero; final and stopped wealth expectations are both one. These witnesses come from the existing auditor applied to the explicit transformed differences `(D-mu)/2`, namely `+1/4` and `-3/4`. The complete underlying audit is retained, including its separately labeled past-only and invalid controls; only its fixed-mixture column supports this construction. This does not audit an unknown law from observed data.

## API, CLI and limits

```python
from betlab import mean_evidence, confidence_sequence

point = mean_evidence(["1/2"]*24, mean="0", bets=[1], alpha="1/4")
cs = confidence_sequence(["1/2"]*24, bets=[1], alpha="1/4", iterations=16)
print(cs["final_outer_interval"])  # ['12487/32768', '1']
```

```bash
python -m betlab confidence-demo
python -m betlab mean examples/mean-input.json
python -m betlab confidence examples/confidence-input.json
python examples/render_confidence.py --check
```

New modes require `schema_version:1` and `differences`. `mean` also requires `mean` in `[-1,1]`. Both permit optional `bets`, `weights`, `alpha`. Only `confidence` permits optional integer `iterations` in `1..32`, default 16. Unknown fields are rejected. Each new replay accepts at most 64 differences and the original at most 16 distinct bets. Empty observations are valid. Exact rational input syntax, component/string caps, floats/booleans prohibition, duplicate-key/nonfinite/UTF-8 checks and the 200,000-byte CLI input limit remain in force. Internal arithmetic is exact and can exceed input bit limits. The old replay/paired/start modes keep their own existing limits.

The tighter 64-observation cap makes repeated rational prefix inversions bounded; it is not a statistical horizon restriction in the proof. There is no service, streaming checkpoint, adaptive stopping API, online data collection or live monitor. Defaults are fixed allocations, not learned choices. The original seven CLI fixture outputs remain byte-identical. All ten complete CLI outputs match the seven-module installed wheel outside checkout.

67 tests retain all previous 51, adding 13 behavior tests and three SVG tests. They include independent products and every bracket/trial on all 81 length-four ternary streams with nonuniform mixtures; pointwise evidence at five candidate means on every such stream; exact threshold ties at the endpoint and midpoint; no-rejection/empty/zero-bet/domain controls; reversal retention, prefix-only behavior, permuted paired weights, nested refinement and full 64-observation/32-bisection/16-bet capacity without mutation or RNG use. All 256 coverage paths are independently re-enumerated for exact mass, first crossing, final/stopped expectations and implication from exclusion to rejection. CLI fixtures and negative schema cases are tested. The new SVG checks 92 coordinates, seven cells, full compressed report metadata, hidden-leaf tampering and byte-exact reproduction. The two older SVGs remain unchanged.

## Attribution and nonclaims

This is an implementation of established testing-by-betting and confidence-set inversion. The primary [Waudby-Smith/Ramdas paper](https://academic.oup.com/jrsssb/article/86/1/1/7043257) develops bounded-mean betting and confidence sequences. [FormalSLT's theorem documentation](https://robby955.github.io/FormalSLT/FormalSLT/AnytimeValid/BettingCS.html) states the nonnegative predictable-factor and conditional-upper-mean result; our Python code is not formally verified. [Clerico](https://arxiv.org/html/2412.02640) discusses coin-betting admissibility for bounded-mean testing and estimation. Those optimality results are not imported here.

No new theorem, optimized betting method, causal effect, current drifting mean, two-sided interval, post-hoc model-selection correction, production reliability or general test-power advantage is claimed. Rational brackets certify computation within the stated model; they do not certify that the data satisfy the model.
