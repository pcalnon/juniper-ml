# Lane A3 — digit-level comparison: my fresh run vs the 2026-10-04 evidence

- mine: `reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun`
- ref: `reports/2026-10-04_recurrence-equities-cv-matrix`

Classes: EXACT = bitwise-equal floats; DIGITS(k) = agree to k significant digits (k ≥ 3); CLASS = same sign and within 10×; NO = neither; MISSING = absent on one side.

## Replay (HTTP `POST /v1/crossval`)

| label | fold | metric | mine | ref | class | rel |
| --- | --- | --- | --- | --- | --- | --- |
| eh-rff | 0 | train_metrics.r2 | 0.18425734696545304 | 0.18425734696545304 | EXACT | 0.0 |
| eh-rff | 0 | train_metrics.rmse | 0.01565221327473285 | 0.01565221327473285 | EXACT | 0.0 |
| eh-rff | 0 | eval_metrics.r2 | -0.08027410347435637 | -0.08027410347435637 | EXACT | 0.0 |
| eh-rff | 0 | eval_metrics.rmse | 0.011767970562964492 | 0.011767970562964492 | EXACT | 0.0 |
| eh-rff | 1 | train_metrics.r2 | 0.16043227273595284 | 0.16043227273595284 | EXACT | 0.0 |
| eh-rff | 1 | train_metrics.rmse | 0.013460732356581883 | 0.013460732356581883 | EXACT | 0.0 |
| eh-rff | 1 | eval_metrics.r2 | -0.050026437320272565 | -0.050026437320272565 | EXACT | 0.0 |
| eh-rff | 1 | eval_metrics.rmse | 0.01380346406800385 | 0.01380346406800385 | EXACT | 0.0 |
| eh-rff | 2 | train_metrics.r2 | 0.1391709396666495 | 0.1391709396666495 | EXACT | 0.0 |
| eh-rff | 2 | train_metrics.rmse | 0.013266063744700409 | 0.013266063744700409 | EXACT | 0.0 |
| eh-rff | 2 | eval_metrics.r2 | -0.1019728052541875 | -0.1019728052541875 | EXACT | 0.0 |
| eh-rff | 2 | eval_metrics.rmse | 0.02061861754805457 | 0.02061861754805457 | EXACT | 0.0 |
| eh-rff | 3 | train_metrics.r2 | 0.1261839639360519 | 0.1261839639360519 | EXACT | 0.0 |
| eh-rff | 3 | train_metrics.rmse | 0.014764961945880553 | 0.014764961945880553 | EXACT | 0.0 |
| eh-rff | 3 | eval_metrics.r2 | -0.0855859667520531 | -0.0855859667520531 | EXACT | 0.0 |
| eh-rff | 3 | eval_metrics.rmse | 0.028824350270245432 | 0.028824350270245432 | EXACT | 0.0 |
| eh-rff | 4 | train_metrics.r2 | 0.12388855137480626 | 0.12388855137480626 | EXACT | 0.0 |
| eh-rff | 4 | train_metrics.rmse | 0.017613371057945866 | 0.017613371057945866 | EXACT | 0.0 |
| eh-rff | 4 | eval_metrics.r2 | -0.2584455292757877 | -0.2584455292757877 | EXACT | 0.0 |
| eh-rff | 4 | eval_metrics.rmse | 0.017836298407318436 | 0.017836298407318436 | EXACT | 0.0 |
| eh-rff | agg | eval_aggregate.r2 | -0.11526096841533144 | -0.11526096841533144 | EXACT | 0.0 |
| eh-rff | agg | eval_std.r2 | 0.07353723443032745 | 0.07353723443032745 | EXACT | 0.0 |
| eh-rff | agg | eval_aggregate.rmse | 0.018570140171317355 | 0.018570140171317355 | EXACT | 0.0 |
| eh-rff | agg | eval_std.rmse | 0.005981209250732683 | 0.005981209250732683 | EXACT | 0.0 |
| eh-rff | agg | eval_aggregate.mae | 0.013371934065211014 | 0.013371934065211014 | EXACT | 0.0 |
| eh-rff | agg | eval_std.mae | 0.004151768887388219 | 0.004151768887388219 | EXACT | 0.0 |
| service-defaults | 0 | train_metrics.r2 | 0.4532378241225371 | 0.4532378241225371 | EXACT | 0.0 |
| service-defaults | 0 | train_metrics.rmse | 0.012814403736882314 | 0.012814403736882314 | EXACT | 0.0 |
| service-defaults | 0 | eval_metrics.r2 | -93606.2421298088 | -93606.2421298088 | EXACT | 0.0 |
| service-defaults | 0 | eval_metrics.rmse | 3.464091188469113 | 3.464091188469113 | EXACT | 0.0 |
| service-defaults | 1 | train_metrics.r2 | 0.32241383452526007 | 0.32241383452526007 | EXACT | 0.0 |
| service-defaults | 1 | train_metrics.rmse | 0.012092694636052063 | 0.012092694636052063 | EXACT | 0.0 |
| service-defaults | 1 | eval_metrics.r2 | -798.4669029752575 | -798.4669029752575 | EXACT | 0.0 |
| service-defaults | 1 | eval_metrics.rmse | 0.38088004235480577 | 0.38088004235480577 | EXACT | 0.0 |
| service-defaults | 2 | train_metrics.r2 | 0.24871053755659267 | 0.24871053755659267 | EXACT | 0.0 |
| service-defaults | 2 | train_metrics.rmse | 0.01239330873360751 | 0.01239330873360751 | EXACT | 0.0 |
| service-defaults | 2 | eval_metrics.r2 | -3.696331338492504 | -3.696331338492504 | EXACT | 0.0 |
| service-defaults | 2 | eval_metrics.rmse | 0.042565081520498815 | 0.042565081520498815 | EXACT | 0.0 |
| service-defaults | 3 | train_metrics.r2 | 0.18360537545455657 | 0.18360537545455657 | EXACT | 0.0 |
| service-defaults | 3 | train_metrics.rmse | 0.01427159112874352 | 0.01427159112874352 | EXACT | 0.0 |
| service-defaults | 3 | eval_metrics.r2 | -75.61767366018817 | -75.61767366018817 | EXACT | 0.0 |
| service-defaults | 3 | eval_metrics.rmse | 0.2421541392443082 | 0.2421541392443082 | EXACT | 0.0 |
| service-defaults | 4 | train_metrics.r2 | 0.13530373960772168 | 0.13530373960772168 | EXACT | 0.0 |
| service-defaults | 4 | train_metrics.rmse | 0.017498249192114096 | 0.017498249192114096 | EXACT | 0.0 |
| service-defaults | 4 | eval_metrics.r2 | -7239.1656160853 | -7239.1656160853 | EXACT | 0.0 |
| service-defaults | 4 | eval_metrics.rmse | 1.3528877638467969 | 1.3528877638467969 | EXACT | 0.0 |
| service-defaults | agg | eval_aggregate.r2 | -20344.637730773607 | -20344.637730773607 | EXACT | 0.0 |
| service-defaults | agg | eval_std.r2 | 36730.52121489702 | 36730.52121489702 | EXACT | 0.0 |
| service-defaults | agg | eval_aggregate.rmse | 1.0965156430871044 | 1.0965156430871044 | EXACT | 0.0 |
| service-defaults | agg | eval_std.rmse | 1.2668086126881442 | 1.2668086126881442 | EXACT | 0.0 |
| service-defaults | agg | eval_aggregate.mae | 0.9169037872275736 | 0.9169037872275736 | EXACT | 0.0 |
| service-defaults | agg | eval_std.mae | 1.075346808183454 | 1.075346808183454 | EXACT | 0.0 |

## Matrix (24 cells, in-process)

| cell (readout/ridge/normalize/theta) | agg r² mine | agg r² ref | agg class | per-fold eval r² class (0..4) | worst fold rel | train r² class | θ class | γ class | ridge-resolved mine / ref | mem-z class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linear|0.0|off|fold-resolved | -20344.6 | -20344.6 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|0.0|off|configured | -20344.6 | -20344.6 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|1.0|off|fold-resolved | -2063.68 | -2063.68 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|1.0|off|configured | -2063.68 | -2063.68 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|gcv|off|fold-resolved | -246.89 | -246.89 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1000.0 / 1000.0 / 85.54672535565685 / 60.20894493336138 / 1000.0 vs 1000.0 / 1000.0 / 85.54672535565685 / 60.20894493336138 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|gcv|off|configured | -246.89 | -246.89 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1000.0 / 1000.0 / 85.54672535565685 / 60.20894493336138 / 1000.0 vs 1000.0 / 1000.0 / 85.54672535565685 / 60.20894493336138 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|0.0|off|fold-resolved | -1986.28 | -1986.28 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|0.0|off|configured | -1986.28 | -1986.28 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|1.0|off|fold-resolved | -0.115261 | -0.115261 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|1.0|off|configured | -0.115261 | -0.115261 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|gcv|off|fold-resolved | -0.0145435 | -0.0145435 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1000.0 / 495.353520895918 / 60.20894493336138 / 1000.0 / 1000.0 vs 1000.0 / 495.353520895918 / 60.20894493336138 / 1000.0 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|gcv|off|configured | -0.0145435 | -0.0145435 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1000.0 / 495.353520895918 / 60.20894493336138 / 1000.0 / 1000.0 vs 1000.0 / 495.353520895918 / 60.20894493336138 / 1000.0 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|0.0|on|fold-resolved | -4.28939e+12 | -4.28939e+12 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|0.0|on|configured | -4.28939e+12 | -4.28939e+12 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|1.0|on|fold-resolved | -4.52303 | -4.52303 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|1.0|on|configured | -4.52303 | -4.52303 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|gcv|on|fold-resolved | -0.0147398 | -0.0147398 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1000.0 / 1000.0 / 1000.0 / 1000.0 / 1000.0 vs 1000.0 / 1000.0 / 1000.0 / 1000.0 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| linear|gcv|on|configured | -0.0147398 | -0.0147398 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | MISSING / MISSING / MISSING / MISSING / MISSING | 1000.0 / 1000.0 / 1000.0 / 1000.0 / 1000.0 vs 1000.0 / 1000.0 / 1000.0 / 1000.0 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|0.0|on|fold-resolved | -3196.64 | -3196.64 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|0.0|on|configured | -3196.64 | -3196.64 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 vs 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|1.0|on|fold-resolved | -0.142375 | -0.142375 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|1.0|on|configured | -0.142375 | -0.142375 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 vs 1.0 / 1.0 / 1.0 / 1.0 / 1.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|gcv|on|fold-resolved | -0.0134155 | -0.0134155 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1000.0 / 1000.0 / 495.353520895918 / 1000.0 / 1000.0 vs 1000.0 / 1000.0 / 495.353520895918 / 1000.0 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |
| rff|gcv|on|configured | -0.0134155 | -0.0134155 | EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 0.00e+00 | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | EXACT / EXACT / EXACT / EXACT / EXACT | 1000.0 / 1000.0 / 495.353520895918 / 1000.0 / 1000.0 vs 1000.0 / 1000.0 / 495.353520895918 / 1000.0 / 1000.0 | EXACT / EXACT / EXACT / EXACT / EXACT |

GCV folds at the grid ceiling (λ = 1000.0): mine 30/40, ref 30/40.

Aggregate eval r² relative difference by readout/ridge (the §2.4 prediction: ridge 0 moves, RFF ridge 1 stable):
- linear/0.0: n=4 max rel=0.000e+00 all_exact=True
- linear/1.0: n=4 max rel=0.000e+00 all_exact=True
- linear/gcv: n=4 max rel=0.000e+00 all_exact=True
- rff/0.0: n=4 max rel=0.000e+00 all_exact=True
- rff/1.0: n=4 max rel=0.000e+00 all_exact=True
- rff/gcv: n=4 max rel=0.000e+00 all_exact=True

## Linear-design conditioning (per fold)

| artifact | fold | n_train | rank mine/ref | cond mine | cond ref | cond class | ‖coef‖ mine / ref (class) | amp p99 train mine/ref (class) | amp p99 eval mine/ref (class) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| normalize=False | 0 | 281 | 113/113 | 8.62e+32 | 8.62e+32 | EXACT | 0.16 / 0.16 (EXACT) | 0.331 / 0.331 (EXACT) | 2.65e+04 / 2.65e+04 (EXACT) |
| normalize=False | 1 | 564 | 149/149 | 2.41e+31 | 2.41e+31 | EXACT | 0.103 / 0.103 (EXACT) | 10.5 / 10.5 (EXACT) | 2.54e+03 / 2.54e+03 (EXACT) |
| normalize=False | 2 | 847 | 159/159 | 2.52e+31 | 2.52e+31 | EXACT | 0.0622 / 0.0622 (EXACT) | 0.0556 / 0.0556 (EXACT) | 0.872 / 0.872 (EXACT) |
| normalize=False | 3 | 1130 | 160/160 | 1.31e+31 | 1.31e+31 | EXACT | 0.0472 / 0.0472 (EXACT) | 6.42e-14 / 6.42e-14 (EXACT) | 454 / 454 (EXACT) |
| normalize=False | 4 | 1413 | 161/161 | 1.54e+22 | 1.54e+22 | EXACT | 0.0263 / 0.0263 (EXACT) | 2.14e-05 / 2.14e-05 (EXACT) | 0.00279 / 0.00279 (EXACT) |
| normalize=True | 0 | 281 | 210/210 | 1.75e+24 | 1.75e+24 | EXACT | 6.56e+06 / 6.56e+06 (EXACT) | 5.6e-07 / 5.6e-07 (EXACT) | 0.0989 / 0.0989 (EXACT) |
| normalize=True | 1 | 564 | 210/210 | 3.37e+22 | 3.37e+22 | EXACT | 5.9e+03 / 5.9e+03 (EXACT) | 3.85e-05 / 3.85e-05 (EXACT) | 0.0218 / 0.0218 (EXACT) |
| normalize=True | 2 | 847 | 210/210 | 2.15e+21 | 2.15e+21 | EXACT | 55.5 / 55.5 (EXACT) | 0.000138 / 0.000138 (EXACT) | 0.000796 / 0.000796 (EXACT) |
| normalize=True | 3 | 1130 | 210/210 | 1.22e+21 | 1.22e+21 | EXACT | 44 / 44 (EXACT) | 0.00018 / 0.00018 (EXACT) | 4.53e+13 / 4.53e+13 (EXACT) |
| normalize=True | 4 | 1413 | 226/226 | 1.11e+20 | 1.11e+20 | EXACT | 20.6 / 20.6 (EXACT) | 0.00072 / 0.00072 (EXACT) | 0.109 / 0.109 (EXACT) |

## Matrix datasets record

- normalize=False: dataset_id EXACT (equities_seq-6.0.0-15505731cba5b86d); n_full 1698 vs 1698 (EXACT); folds equal True; theta_cfg 91.0 vs 91.0; last-step std lists equal True; meta checksum mine c02004e1708e489aea48aa0a985b2eb797ee190d340080ea547dcf363bfed261 ref c02004e1708e489aea48aa0a985b2eb797ee190d340080ea547dcf363bfed261
  - last-step std mine: 4.040e+01, 4.090e+01, 3.992e+01, 4.044e+01, 6.705e+07, 4.310e+01, 2.257e+01, 4.431e+09, 7.936e+11, 3.815e-04, 2.211e-02, 9.704e-02, 8.176e+01, 7.600e+01, 2.665e+01
  - last-step std ref:  4.040e+01, 4.090e+01, 3.992e+01, 4.044e+01, 6.705e+07, 4.310e+01, 2.257e+01, 4.431e+09, 7.936e+11, 3.815e-04, 2.211e-02, 9.704e-02, 8.176e+01, 7.600e+01, 2.665e+01
- normalize=True: dataset_id EXACT (equities_seq-6.0.0-fa3aae11ac374c94); n_full 1698 vs 1698 (EXACT); folds equal True; theta_cfg 91.0 vs 91.0; last-step std lists equal True; meta checksum mine 97e778900093da01fdf8aa9cdbe8258843b34215df2223058ab758864463a8ae ref 97e778900093da01fdf8aa9cdbe8258843b34215df2223058ab758864463a8ae
  - last-step std mine: 4.454e-01, 4.470e-01, 4.541e-01, 4.429e-01, 1.111e-01, 4.980e-01, 8.231e-01, 2.788e+00, 2.184e+00, 0.000e+00, 1.078e-01, 9.704e-02, 3.257e-01, 3.028e-01, 2.747e-01
  - last-step std ref:  4.454e-01, 4.470e-01, 4.541e-01, 4.429e-01, 1.111e-01, 4.980e-01, 8.231e-01, 2.788e+00, 2.184e+00, 0.000e+00, 1.078e-01, 9.704e-02, 3.257e-01, 3.028e-01, 2.747e-01

