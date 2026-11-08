# Design and statistical proof

## One fixed one-sided null

The user supplies differences `D_t` in `[-1,1]`, or ordered baseline/candidate scores in `[0,1]` whose differences are computed exactly. The intended null is `E[D_t | F_(t-1)] <= 0` at every round. The information set must include the available past used to choose observations and bets. Independence is not required by the algebra, but marginal mean zero does not imply this conditional property. The code cannot establish it from one observed sequence.

All testing choices must precede the tested stream: score definition/direction, model pair, stream, fixed-mixture bets/weights and reported process. Inspecting two reported tests does not make their union a level-alpha test. This repository returns them separately and makes no combined rejection. It does not implement multiplicity correction or a confidence sequence.

## Nonnegative betting and mixtures

For `0 <= b_t <= 1`, `D_t >= -1` implies `1+b_t*D_t >= 0`. If `b_t` is measurable before observing `D_t`,

```text
E[1+b_t*D_t | F_(t-1)] = 1+b_t*E[D_t | F_(t-1)] <= 1.
K_0 = 1
K_t = K_(t-1) * (1+b_t*D_t)
```

Since previous wealth is nonnegative and past-measurable, `E[K_t | F_(t-1)] <= K_(t-1)`. Starting at one, this is a nonnegative test supermartingale, hence an e-process. Zero is absorbing. No division by current wealth is used.

Each fixed component uses its own constant bet in `[0,1]`. With fixed positive weights summing exactly to one, `M_t = sum_j w_j*K_(j,t)` is nonnegative, starts at one and has the same conditional inequality by linearity. Components are not independently rescaled or replaced by their hindsight maximum.

The separate past-only process chooses

```text
S_(t-1) = sum_(i<t) D_i
Q_(t-1) = sum_(i<t) D_i^2
b_t = clip(S_(t-1)/(1+Q_(t-1)),0,1).
```

This is a transparent custom heuristic inside the allowed interval. It is not advertised as the optimal, Kelly, empirical-Bernstein or published variance-adaptive betting strategy. At the first round the bet is zero. Prefix tests show its next bet cannot depend on the current or future difference.

Ville's inequality gives `P(exists t: K_t >= 1/alpha) <= alpha` under the null. A bounded replay records first equality-inclusive crossing, running maximum (including initial wealth one) and `p_t=min(1,1/max_(s<=t) K_s)`. For each fixed alpha, the event `exists t: p_t<=alpha` is precisely a threshold-crossing event, so this is an anytime-valid p-value bound. It need not be a fixed-time uniform p-value. It is not a posterior probability, effect size or coverage interval. Even if later wealth falls, the ever-crossed decision remains true. An arbitrary stopping rule within this prespecified test does not justify an arbitrary choice of test, stream, model or hypothesis after data inspection.

The code returns mixture and past-only results separately. Reporting the smaller p bound without correction is outside this guarantee. Alpha never changes wealth updates, only threshold/decision reporting.

## Finite-law audit

A tree is `null` for a leaf, or exactly `{"outcomes": [...]}`. Each outcome is exactly `{"probability": rational, "difference": rational, "next": node_or_null}`. Branch probabilities are strictly positive and sum to one exactly; zero-mass branches must be omitted. Every internal node must have conditional mean at most zero. This is a requirement on the supplied law, not merely a check of its marginal average. Invalid laws fail rather than produce a validity claim.

The auditor visits every history, carries exact path mass, computes the same prefix-dependent wealth and retains:

- Each internal history's mass, conditional mean, current wealth, expected next wealth and slack `current - expected_next` for both valid processes and the invalid comparator.
- Every leaf's path, exact differences, probability, current wealth, first crossing and wealth stopped at the first crossing (or that leaf if no crossing).
- Exact sums of crossing mass, final wealth expectation and stopped wealth expectation. On variable-depth laws, stopping at a leaf is terminal. No padding creates extra evidence.

For valid processes it asserts every conditional slack nonnegative; total leaf mass one; expected final/stopped wealth at most one; and crossing probability at most alpha. These follow from the earlier algebra, but the explicit finite arithmetic is independently testable. The tree audit is exhaustive for this supplied law only and says nothing about whether real model evaluations follow it.

The invalid comparator resets wealth to one before the next round if its previous wealth was zero, then uses bet one. This spends external statistical capital. At a ruined fair-coin node its current wealth is zero, but expected next wealth is one: slack `-1`. Under eight fair flips at threshold four, it crosses on any run of two positive signs. There are 55 paths without such a run, so its crossing probability is `1-55/256=201/256`. Its expected final wealth is `9/2`, and wealth stopped at first crossing/leaf has expectation `423/128`. Optional stopping has not failed; the reset process is not the original supermartingale.

## Exact arithmetic and scope limits

The API accepts integers, exact signed decimal/fraction strings or `Fraction`, never floats/booleans. Strings have at most 160 characters with no whitespace, exponent, plus sign or nonfinite syntax. Input numerator and denominator components have at most 512 bits. Internal arithmetic is exact `Fraction` and is not truncated to those input caps; canonical output fractions can be longer. Paired-score subtraction may have larger components than either input, and is retained exactly. Convert an output back to a `Fraction` before using it as internal data; replay's public input caps still apply.

Replay/paired: 0..256 observations, 1..16 distinct mixture bets, positive weights exactly summing to one, alpha strictly between zero and one. The tree: at most eight rounds, 255 internal nodes, 256 leaves, 1..4 outcomes per internal node. Variable depths, one-child nodes, repeated difference values and zero differences are allowed. Shared internal-node objects and cycles are rejected; a law is a tree, not a DAG. String-key schema is exact. No input is normalized or clipped into range. The only clipping is the documented past-only bet selection.

CLI schema requires integer `schema_version:1`. `replay` requires differences, `paired` requires baseline/candidate, `tree` requires tree; all allow only optional bets, weights and alpha. Duplicate keys, nonfinite JSON, invalid UTF-8, unknown fields, missing files and inputs larger than 200000 bytes fail with status 2 and empty stdout. Output uses canonical exact fraction strings. The renderer alone converts wealth to float for a log2(1+wealth) axis; displayed coordinates never affect evidence calculations.

The runtime is standard-library-only Python 3.10+. This is deliberately bounded exhaustive code, not a scalable stream processor. No persistent checkpoint/resume protocol or online side effect is implemented. Replaying a prefix does not create a new independent test.

## Verification and attribution

The 34-test suite combines independent products, path enumeration, conditional-law witnesses, schema/CLI guards, full installed-wheel parity and SVG checks. The demo is a developed control, with no random seeds or measured real-model performance. The standard mathematical sources are linked in README. The Python implementation is not formally verified; formal theorem documentation is a supporting reference only. No new statistical result is claimed.
