# Prespecified start-time mixtures

Version 0.2 adds `start_mixture`, `audit_starts` and `starts_demo`. This is a finite allocation of one unit of initial statistical capital over fixed start times, not permission to reset the same test until it succeeds.

## Construction and proof

Choose distinct deterministic starts `s_j` and positive weights `a_j` summing exactly to one before the tested stream. Also choose fixed bets `b_k` in `[0,1]` and positive weights `w_k` summing to one, as in the original mixture. Define

```text
K_(j,k,t) = 1                                      for t < s_j
K_(j,k,t) = product_(i=s_j..t) (1+b_k*D_i)          for t >= s_j
M_t = sum_j a_j * sum_k w_k*K_(j,k,t).
```

Every component is a nonnegative supermartingale under `E[D_t|past] <= 0`, `D_t in [-1,1]`: its bet is zero before its fixed start and `b_k` thereafter. Fixed convex mixing preserves the conditional inequality and `M_0=1`. Therefore Ville's inequality controls `P(ever M_t>=1/alpha)<=alpha` for **this one prespecified statistic**. The code reports first equality-inclusive crossing and the running-maximum reciprocal p-value bound exactly.

Before a start, its internal capital is one, and its weighted contribution is its preallocated budget. The complete sum includes the unstarted reserve `sum_(s_j>t) a_j`. This reserve is carried, not injected at activation. A component that reaches zero stays zero forever. No observed loss or threshold crossing changes the schedule or reallocates budget. Future starts after the observed prefix remain valid constant-one components. With the single start `[1]`, the statistic and decision are exactly the original fixed-bet mixture.

This can make a delayed-signal fixture more sensitive after early losses, but it spends part of its starting capital on other times. It is not uniformly more powerful. No active-component maximum, hindsight start selection, adaptive schedule, automatic reset, effect-size estimate or change-time estimate is supplied. Reporting an alarm if either the original statistic or this new statistic crosses at alpha is not automatically an alpha-level combined test. Choose one before testing or provide a separate correction, which this project does not implement.

## Developed controls

For eight `-1`, eight `+1`, then eight `-1`, use bet one, starts `[1,9,17]` and weights `[1/3,1/3,1/3]`, alpha `1/4`. The single process from round one is ruined by the first difference and never crosses. The allocated mixture first reaches threshold four at round 12. At round 16 its wealth is `257/3`, including `1/3` unstarted reserve. At round 17 all its active components are ruined, leaving final wealth zero. Its earlier crossing remains recorded. This is a developed deterministic sequence, not evidence of general detection performance or the true time of a change.

For the full fair-coin eight-round null tree, use bet one and starts `[1,3,5,9]`, each weight `1/4`. The round-nine component has not started at any leaf. Every node's scheduled-mixture conditional slack is zero. All 256 paths give exact crossing probability `5/32` at alpha `1/4`, with final and stopped wealth expectations both one. The original invalid free-refill comparator crosses with probability `201/256`; it is not part of this mixture.

For the six-round negative-drift tree with positive-sign probability `1/3`, the same schedule yields crossing probability `17/729`, expected final wealth `1261/2916` and expected stopped wealth `683/1458`. The future weight remains `1/4`. The node audit checks every conditional expectation, not just final expectations or a Monte Carlo estimate.

## Schema and reports

`start_mixture(differences, starts, *, start_weights=None, bets=None, weights=None, alpha="1/20")` accepts the original exact difference and bet schema. `starts` must have 1..16 distinct integer entries in 1..256, never booleans. Optional `start_weights` must be positive exact rationals matching starts and summing exactly to one; omitted weights are uniform. Starts and their weights are sorted together into canonical order. A future-only schedule has wealth one throughout the observed prefix. Empty observations are valid. Replay still has at most 256 observations and 16 distinct bets, for at most 256 start/bet cells per round. Existing exact-input component/string caps remain unchanged; internal arithmetic is not rounded.

Each trace row retains the observed difference, started/unstarted budgets, and every component's start, weight, active flag, per-bet wealth, local fixed-bet mixture and weighted contribution. The complete wealth is their sum. No per-component p-value is selected as the test result.

`audit_starts(tree, starts, ...)` first applies the existing full finite-law validation and returns that unchanged original audit in `base_audit` (apart from canonical rational-string zero for an empty crossing sum). It then enumerates scheduled-mixture current/next expectations and slack at every internal history, plus exact leaf masses, final wealth, first crossing and stopped wealth. Its summary sums all leaf crossing mass and final/stopped expectations. Variable-depth trees and future starts are handled without padding. The existing depth-eight, 255-node, 256-leaf and four-outcome bounds still apply. The law, not the observed data, must satisfy the conditional null at every node.

CLI commands:

```bash
python -m betlab starts-demo
python -m betlab starts examples/starts-input.json
python -m betlab starts-tree examples/starts-tree-input.json
python examples/render_starts.py --check
```

`starts` requires `schema_version:1`, `differences` and `starts`; `starts-tree` requires `schema_version:1`, `tree` and `starts`. Each permits only optional `start_weights`, `bets`, `weights` and `alpha`. Unknown fields and the original invalid-number/duplicate-key/nonfinite/UTF-8/size cases fail with status two and empty stdout. Start weights are not accepted by the original modes.

## Verification and boundaries

51 tests retain all initial 34 and add 14 behavior tests plus three SVG tests. New references independently multiply all suffix products on all 243 length-five ternary sequences, with nonuniform start and bet weights; enumerate all 256 fair sign paths for crossing/final/stopped expectations; reconstruct each node expectation from its children; check negative drift, all-future schedules, exact equality, permanent ruin, unstarted reserve, unsorted paired weights, variable-depth/four-way laws, invalid laws/schedules and the full 256-observation/16-start/16-bet capacity. Original four CLI fixture outputs remain byte-identical. All seven complete CLI JSON outputs match the six-module installed wheel outside checkout.

The second figure checks all 50 plotted coordinates, nine values/metadata and hidden-witness tampering, with complete compressed JSON and exact regeneration. The original figure is unchanged and still regenerates exactly.

The start-mixture idea is established. [Shin, Ramdas and Rinaldo, E-detectors](https://nejsds.nestat.org/journal/NEJSDS/article/59/file/pdf), especially Remark 2.7, distinguishes summable initial allocations controlling ever-false-alarm probability from raw Shiryaev-Roberts/CUSUM sums with average-run-length guarantees. [Nonconform's implementation documentation](https://oliverhennhoefer.github.io/nonconform/user_guide/exchangeability_martingales/) also explains why a weighted restart mixture retains future reserve and why ARL is not a lifetime probability bound. BetLab implements neither that library's infinite harmonic prior nor a general e-detector. Its proof is the finite convex-mixture argument above and the original [bounded-mean betting](https://academic.oup.com/jrsssb/article/86/1/1/7043257) construction.

No new theorem, infinite-horizon restart service, ARL detector, data-driven start selection, online checkpoint/resume, change-point localization, model-selection correction, production monitoring or real-model performance guarantee is claimed. The exact tree audit concerns the supplied law only.
