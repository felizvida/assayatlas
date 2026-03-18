# AssayAtlas Real-Data Training Tutorial

This tutorial is intentionally hand-held. Every lesson uses a real public dataset, a real statistical workflow, and a biomedical wet-lab framing rendered through the AssayAtlas workspace.

## How to use this tutorial

1. Start the app locally or open the deployed AssayAtlas home page.
2. Open the Workspace or the Tutorial page.
3. Work through the twenty use cases in order at least once.
4. Re-run the flows with the provided CSV files to internalize the bench-science patterns.

## Training goals

- Learn the SaaS navigation without friction.
- See what publication-grade defaults should feel like.
- Practice twenty biomedical wet-lab workflows with transparent results and publication-ready figures.
- Leave with exportable example figures and the raw input data for each lesson.
- See clearly when a workflow is built from a public proxy dataset versus a directly biomedical source.


## Use Cases


### 01. Low-Dose Mineralization Rescue Assay

**Goal:** Compare low-dose mineralization rescue between two supplement chemistries while keeping every animal visible.

**Analysis:** Welch t test + raw-point estimation plot

**Data files:** data/raw/ToothGrowth.csv

**Source:** ToothGrowth from the R datasets collection, framed here as a preclinical mineralization assay proxy.

**What to notice:** Bench scientists trust this style of view because every replicate stays visible and the efficacy call is tied to a confidence interval, not a bar chart alone.

![Screenshot](/assets/screenshots/01-two-group-supplement-comparison.png)

**Step-by-step**

1. Open Low-Dose Mineralization Rescue Assay from the Tutorial library.
2. Review the preview table and confirm the analysis is restricted to the 0.5 mg/day treatment arm in the preclinical cohort.
3. Inspect the raw-point efficacy plot before reading the test result so replicate spread stays visible.
4. Read the automatic Welch t test card and the 95% confidence interval for the treatment difference.
5. Export the figure as SVG or PNG for a lab meeting slide or a draft results section.

**Result summary:** At the low dose, the OJ formulation looks biologically more active than VC, improving mean tooth length by 5.25 units. Welch's t test is the right statistical move here because it stays reliable when group variances may differ, and the 95% confidence interval [1.72, 8.78] keeps the likely size of the rescue effect visible alongside p 0.006.

**Key metrics**

- OJ mean = 13.23
- VC mean = 7.98
- Mean difference = 5.25

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/two-group-supplement-comparison/two-group-supplement-comparison-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/01-two-group-supplement-comparison.png`

### 02. Vitamin C Dose Escalation Response

**Goal:** Show how a preclinical growth readout shifts across three dose levels in a simple dose-escalation study.

**Analysis:** One-way ANOVA + Tukey multiple comparison

**Data files:** data/raw/ToothGrowth.csv

**Source:** ToothGrowth from the R datasets collection, framed here as a three-arm dose-escalation efficacy proxy.

**What to notice:** This feels like a classic wet-lab potency check: replicate-level spread, monotonic dose behavior, and formal post-hoc comparisons in one view.

![Screenshot](/assets/screenshots/02-dose-response-overview.png)

**Step-by-step**

1. Open Vitamin C Dose Escalation Response.
2. Confirm the input file contains the full cohort so all three treatment levels remain in the analysis.
3. Inspect the dose-wise raw-point summary plot to see whether the assay response rises monotonically.
4. Read the ANOVA result and the pairwise dose-comparison card to identify where the separation appears.
5. Use the publication export preset if you need a journal-ready raster or vector figure.

**Result summary:** The dose-escalation pattern supports a biologically graded response rather than an isolated group difference: mean growth rises steadily across the three dose levels. A one-way ANOVA confirms that dose explains substantial response variance (F 67.42, p < 0.001), and Tukey follow-up contrasts are what tell you which dose steps are really driving the signal.

**Key metrics**

- Dose 0.5 mean = 10.61
- Dose 1.0 mean = 19.73
- Dose 2.0 mean = 26.10

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/dose-response-overview/dose-response-overview-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/02-dose-response-overview.png`

### 03. Three-Arm Compound Response Screen

**Goal:** Compare a control arm and two treated arms in a compact compound-response experiment.

**Analysis:** One-way ANOVA + Tukey HSD

**Data files:** data/raw/PlantGrowth.csv

**Source:** PlantGrowth from the R datasets collection, framed here as a three-arm compound-response assay proxy.

**What to notice:** This is the kind of figure wet-lab teams drop into update decks because it shows every replicate and the follow-up pairwise call without clutter.

![Screenshot](/assets/screenshots/03-grouped-mean-comparison.png)

**Step-by-step**

1. Open Three-Arm Compound Response Screen from the Tutorial list.
2. Review the preview table and verify that each treatment arm contributes the same number of replicates.
3. Inspect the dot-and-summary chart before looking at p values so the replicate structure is clear.
4. Use the Tukey card to identify which treatment separates from the control condition.
5. Add the figure to a board if you want to combine this hit-confirmation panel with orthogonal assays.

**Result summary:** This reads like a hit-confirmation screen: Treatment 2 produces the strongest growth phenotype, while the overall arm-to-arm difference is supported by the omnibus ANOVA (F 4.85, p 0.016). The important statistical trick is using Tukey-adjusted pairwise follow-up after the omnibus test so the strongest arm is identified without over-reading raw mean separation alone.

**Key metrics**

- Control mean = 5.03
- Treatment 1 mean = 4.66
- Treatment 2 mean = 5.53

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/grouped-mean-comparison/grouped-mean-comparison-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/03-grouped-mean-comparison.png`

### 04. Matrix-by-Tension Interaction Screen

**Goal:** Assess whether scaffold material and applied tension interact in a biomaterials stress assay.

**Analysis:** Two-way ANOVA with interaction

**Data files:** data/raw/warpbreaks.csv

**Source:** warpbreaks from the R datasets collection, framed here as a biomaterials tensile-stress assay proxy.

**What to notice:** Interaction plots matter in translational lab work because they separate a main effect from a context-dependent effect that changes with the assay condition.

![Screenshot](/assets/screenshots/04-factorial-experiment.png)

**Step-by-step**

1. Open Matrix-by-Tension Interaction Screen.
2. Inspect the grouped preview and note the two material classes and three mechanical settings.
3. Read the interaction plot first to understand whether the response curves stay parallel or diverge by condition.
4. Use the ANOVA panel to separate the material effect, the tension effect, and the interaction term.
5. Export the figure and the ANOVA summary if you need a methods-friendly interaction readout.

**Result summary:** The main biological story is a strong tension effect, with much weaker evidence that the material-specific response meaningfully changes across tension states. Two-way ANOVA is doing the critical work here because it separates the main effects from the interaction term, letting the team ask whether the scaffold changes the biology itself or just the overall baseline.

**Key metrics**

- Wool effect p = 0.058
- Tension effect p = < 0.001
- Interaction p = 0.021

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/factorial-experiment/factorial-experiment-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/04-factorial-experiment.png`

### 05. Matched Before/After Neuroresponse Study

**Goal:** Measure within-subject change after intervention instead of pretending paired readouts are independent.

**Analysis:** Paired t test + subject spaghetti plot

**Data files:** data/raw/sleep.csv

**Source:** sleep from the R datasets collection, framed here as a matched before-and-after neuropharmacology proxy.

**What to notice:** Paired plots are a wet-lab staple because they surface donor-to-donor heterogeneity before the statistical summary flattens it.

![Screenshot](/assets/screenshots/05-paired-before-after.png)

**Step-by-step**

1. Open Matched Before/After Neuroresponse Study.
2. Verify from the preview that every subject contributes a baseline and a post-intervention readout.
3. Inspect the paired-lines plot to see whether the direction of change is consistent donor by donor.
4. Review the paired t test and the mean paired shift from baseline.
5. Use the notes area to record whether the change looks biologically meaningful, not merely non-zero.

**Result summary:** The paired readout suggests a real within-subject neuroresponse after intervention, with subjects improving by 1.58 units on average in group 2 versus group 1. The key statistical trick is the paired t test: it uses each subject as their own control, which is biologically more faithful and usually more sensitive than pretending repeated observations are independent.

**Key metrics**

- Mean group 1 = 0.75
- Mean group 2 = 2.33
- Mean paired difference = 1.58

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/paired-before-after/paired-before-after-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/05-paired-before-after.png`

### 06. Cellular Oxygen Demand Time Course

**Goal:** Turn a short respirometry-style time course into a compact functional summary.

**Analysis:** Area-under-the-curve summary + line plot

**Data files:** data/raw/BOD.csv

**Source:** BOD from the R datasets collection, framed here as a cellular respirometry assay proxy.

**What to notice:** This is the kind of metabolic assay panel people want quickly: kinetics, endpoint, and AUC in one publication-ready card.

![Screenshot](/assets/screenshots/06-time-course-summary.png)

**Step-by-step**

1. Open Cellular Oxygen Demand Time Course.
2. Inspect the input table and confirm the measurement times increase in the correct order.
3. Review the line chart to see how quickly the assay response approaches a plateau.
4. Read the AUC and terminal-value summary card for the compact kinetic interpretation.
5. Export the panel if you need a clean metabolism figure for a progress review or manuscript draft.

**Result summary:** The time course looks like a fast metabolic activation followed by a plateau, which is often the biological question in short functional assays. Reporting both the terminal value (19.8) and the integrated exposure-like summary AUC (92.65) keeps the interpretation from depending on a single timepoint.

**Key metrics**

- Baseline = 8.3
- Final value = 19.8
- AUC = 92.65

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/time-course-summary/time-course-summary-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/06-time-course-summary.png`

### 07. Longitudinal Organoid Growth Tracking

**Goal:** Review repeated growth measurements while preserving each organoid trajectory.

**Analysis:** Subject-wise growth lines + slope summary

**Data files:** data/raw/Orange.csv

**Source:** Orange from the R datasets collection, framed here as a longitudinal organoid-growth assay proxy.

**What to notice:** Developmental and screening groups like this view because outlier trajectories and growth-rate differences stay visible instead of disappearing into a mean trace.

![Screenshot](/assets/screenshots/07-repeated-growth-curves.png)

**Step-by-step**

1. Open Longitudinal Organoid Growth Tracking.
2. Inspect the preview and confirm each organoid has measurements across multiple collection days.
3. Read the trajectory plot to compare how growth velocity differs organoid by organoid.
4. Use the slope summary to identify the fastest and slowest-growing members of the cohort.
5. Add this panel to a board if you are building a developmental or screening narrative.

**Result summary:** The longitudinal traces make it clear that not all members of the cohort follow the same growth program: Tree 4 expands fastest while Tree 3 lags behind. The useful analytic trick is preserving subject-level trajectories and summarizing them with per-subject slopes instead of collapsing everything into one average curve.

**Key metrics**

- Fastest slope = Tree 4 (0.135)
- Slowest slope = Tree 3 (0.081)
- Median circumference = 115.0

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/repeated-growth-curves/repeated-growth-curves-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/07-repeated-growth-curves.png`

### 08. Diameter-to-Volume Calibration Curve

**Goal:** Fit a calibration relationship you could use to estimate tissue mass or volume from a bench measurement.

**Analysis:** Linear regression with 95% prediction band

**Data files:** data/raw/trees.csv

**Source:** trees from the R datasets collection, framed here as an imaging-to-volume calibration proxy.

**What to notice:** Assay teams often need a calibration figure that is statistically explicit and still clean enough to live in a methods section.

![Screenshot](/assets/screenshots/08-regression-and-calibration.png)

**Step-by-step**

1. Open Diameter-to-Volume Calibration Curve.
2. Inspect the input columns and confirm the physical measurement sits on the x-axis and the calibrated readout on the y-axis.
3. Review the fitted line and uncertainty band to see whether the relationship is tight enough for use.
4. Read the slope, R-squared, and interval summary in the result card.
5. Export the SVG if you want a clean calibration figure for methods or supplemental notes.

**Result summary:** This calibration looks biologically usable because the response scales predictably with the bench-side measurement, supporting future estimation from a simple surrogate readout. The fitted slope of 5.07 and R-squared of 0.935 quantify how strong that relationship is, while the confidence band shows where prediction uncertainty remains.

**Key metrics**

- Intercept = -36.94
- Slope = 5.07
- R-squared = 0.935

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/regression-and-calibration/regression-and-calibration-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/08-regression-and-calibration.png`

### 09. Microscopy Feature Correlation Screen

**Goal:** Quickly screen relationships across multiple morphology features before deeper modeling.

**Analysis:** Pearson correlation heatmap

**Data files:** data/raw/iris.csv

**Source:** iris from the R datasets collection, framed here as a single-cell morphology feature-screen proxy.

**What to notice:** This is a practical phenotyping move: find which readouts travel together before choosing a reduced panel for follow-up experiments.

![Screenshot](/assets/screenshots/09-correlation-screen.png)

**Step-by-step**

1. Open Microscopy Feature Correlation Screen.
2. Inspect the feature preview and note that the phenotype label is excluded from the correlation matrix.
3. Read the heatmap first to spot which morphology measurements move together most strongly.
4. Use the metric card to identify the top feature pair for follow-up review.
5. Export the heatmap when you need a compact exploratory panel for collaborators.

**Result summary:** The strongest morphology relationship is between Petal.Length and Petal.Width (r = 0.96), suggesting those measurements may be tracking overlapping biology. The Pearson correlation screen is the statistical shortcut here: it quickly tells you which features are likely redundant before you commit to a larger phenotyping panel.

**Key metrics**

- Top pair = Petal.Length vs Petal.Width
- Top correlation = 0.96
- Lowest correlation = -0.43

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/correlation-screen/correlation-screen-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/09-correlation-screen.png`

### 10. Phenotype Separation PCA Map

**Goal:** Compress multiple assay features into two axes and inspect how clearly biological states separate.

**Analysis:** Principal component analysis

**Data files:** data/raw/iris.csv

**Source:** iris from the R datasets collection, framed here as a cell-state morphology PCA proxy.

**What to notice:** PCA earns its keep when it shows whether treatment states or biological classes are visibly separable without needing a statistics lecture.

![Screenshot](/assets/screenshots/10-pca-species-map.png)

**Step-by-step**

1. Open Phenotype Separation PCA Map.
2. Inspect the standardized feature list before computing the dimensionality reduction.
3. Review the scatter plot to see whether the phenotypic classes separate along the first two components.
4. Read the explained-variance card to judge how much structure is retained in the map.
5. Add the panel to a board if you want a compact unsupervised phenotyping summary.

**Result summary:** The first two principal components retain 95.8% of the total variance and already separate the phenotypic classes, suggesting a compact feature space captures much of the underlying biology. PCA is the important trick in play because it compresses correlated measurements into orthogonal axes that are much easier to inspect visually.

**Key metrics**

- PC1 variance = 73.0%
- PC2 variance = 22.9%
- Two-component total = 95.8%

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/pca-species-map/pca-species-map-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/10-pca-species-map.png`

### 11. Cell-State Distribution Shift

**Goal:** Compare full distributions, not just means, across three biological states.

**Analysis:** Violin plot + one-way ANOVA

**Data files:** data/raw/iris.csv

**Source:** iris from the R datasets collection, framed here as a cell-state size-distribution proxy.

**What to notice:** Wet-lab teams reach for violin plots when they care about heterogeneity, tail behavior, and overlap, not just a single average per group.

![Screenshot](/assets/screenshots/11-distribution-comparison.png)

**Step-by-step**

1. Open Cell-State Distribution Shift.
2. Review the state labels in the preview and confirm which measurement column is being summarized.
3. Inspect the violin plot to understand shape, spread, overlap, and tail behavior.
4. Read the ANOVA result card to decide whether the mean difference is worth formalizing further.
5. Export the figure if you need a more expressive alternative to a plain box plot.

**Result summary:** The biological states differ not only in mean sepal length but also in spread and distribution shape, which is exactly why the violin view is more informative than a bare bar chart. The one-way ANOVA formalizes the omnibus mean-difference question (F 119.26, p < 0.001), while the violin geometry keeps heterogeneity visible.

**Key metrics**

- Setosa mean = 5.01
- Versicolor mean = 5.94
- Virginica mean = 6.59

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/distribution-comparison/distribution-comparison-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/11-distribution-comparison.png`

### 12. Enzyme Inhibition Kinetics Panel

**Goal:** Fit Michaelis-Menten curves for treated and untreated enzyme conditions.

**Analysis:** Michaelis-Menten fitting

**Data files:** data/raw/Puromycin.csv

**Source:** Puromycin from the R datasets collection, already close to a classic enzyme-kinetics assay example.

**What to notice:** This is a non-negotiable biomedical workflow: raw rates, nonlinear fits, and interpretable Km and Vmax estimates on one panel.

![Screenshot](/assets/screenshots/12-enzyme-kinetics.png)

**Step-by-step**

1. Open Enzyme Inhibition Kinetics Panel.
2. Check the substrate-concentration and rate columns in the preview table.
3. Inspect the fitted Michaelis-Menten curves over the raw points for both assay conditions.
4. Read the Vmax and Km estimates and compare how the treated condition shifts the fit.
5. Export the panel if you need a fast enzyme-kinetics figure for a deck, report, or manuscript.

**Result summary:** The treated and untreated curves separate in a way that suggests the intervention is changing catalytic behavior, not merely adding noise to the assay. Nonlinear Michaelis-Menten fitting is the crucial analytic step because it estimates Vmax and Km from the full curve shape rather than from a single substrate concentration.

**Key metrics**

- treated Vmax = 212.68, Km = 0.06
- untreated Vmax = 160.28, Km = 0.05
- See the result card in the app.

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/enzyme-kinetics/enzyme-kinetics-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/12-enzyme-kinetics.png`

### 13. PK Exposure Profile After Dosing

**Goal:** Track concentration over time and summarize exposure metrics for a small PK cohort.

**Analysis:** Concentration-time summary + noncompartmental metrics

**Data files:** data/raw/Theoph.csv

**Source:** Theoph from the R datasets collection, framed here as a small-cohort pharmacokinetic assay example.

**What to notice:** Scientists expect this view to answer two questions immediately: what the curve looks like and whether exposure is changing enough to matter.

![Screenshot](/assets/screenshots/13-pharmacokinetics.png)

**Step-by-step**

1. Open PK Exposure Profile After Dosing.
2. Inspect the subject, time, and concentration columns in the preview table.
3. Review the concentration-time plot to see the shared peak-and-decay shape across the cohort.
4. Read the automatic Cmax, Tmax, and AUC summary card.
5. Export the figure or metrics table for a PK review packet or translational update.

**Result summary:** The cohort shows the classic absorption-to-elimination PK shape, and the average Cmax (8.76) and AUC (103.81) together summarize both peak exposure and total drug burden. The key statistical choice is to use simple noncompartmental metrics, which keeps the interpretation practical for early translational review without forcing a heavier compartment model.

**Key metrics**

- Mean Cmax = 8.76
- Mean AUC = 103.81
- Earliest Tmax = 0.63

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/pharmacokinetics/pharmacokinetics-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/13-pharmacokinetics.png`

### 14. Terminal Elimination Half-Life Review

**Goal:** Estimate terminal clearance behavior from concentration decay data.

**Analysis:** Semi-log elimination fit

**Data files:** data/raw/Indometh.csv

**Source:** Indometh from the R datasets collection, framed here as a small-molecule clearance proxy.

**What to notice:** The semi-log panel is valuable because it lets reviewers judge whether the reported half-life is supported by the shape of the terminal phase.

![Screenshot](/assets/screenshots/14-drug-elimination.png)

**Step-by-step**

1. Open Terminal Elimination Half-Life Review.
2. Inspect the subject-level concentration-time table before looking at the fit.
3. Read the semi-log plot to confirm the terminal phase appears approximately linear on the log scale.
4. Review the cohort half-life estimate and the subject-to-subject variability card.
5. Export the panel if you need a compact clearance appendix figure.

**Result summary:** The semi-log terminal phase suggests reasonably consistent clearance behavior across subjects, with a median half-life of 1.66 time units. The trick here is log-linear fitting of the terminal decline, which isolates elimination kinetics instead of mixing them with the absorption phase.

**Key metrics**

- Median half-life = 1.66
- Shortest half-life = 1.51
- Longest half-life = 1.87

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/drug-elimination/drug-elimination-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/14-drug-elimination.png`

### 15. Preclinical Survival Curve Comparison

**Goal:** Compare survival across control and treatment cohorts while keeping censoring visible.

**Analysis:** Kaplan-Meier + log-rank test

**Data files:** data/raw/waltons.csv

**Source:** waltons from the lifelines example datasets, framed here as a therapy-versus-control survival proxy.

**What to notice:** Kaplan-Meier plots are central in translational work because the figure itself often carries the biological story before anyone opens the statistics table.

![Screenshot](/assets/screenshots/15-survival-analysis.png)

**Step-by-step**

1. Open Preclinical Survival Curve Comparison.
2. Inspect the event-time preview and note the cohort assignment before looking at the curves.
3. Review the stepwise survival traces and the at-risk behavior over time.
4. Read the log-rank result card for the between-cohort comparison.
5. Export the plot if you need a manuscript-ready survival panel.

**Result summary:** The survival curves separate enough to support a biologically meaningful difference in event timing between cohorts, and the log-rank test quantifies that full-curve separation at p < 0.001. Keeping censor marks visible matters because survival interpretation depends on who remains under observation, not just who has already had an event.

**Key metrics**

- control median survival = 58.00
- miR-137 median survival = 26.00
- Log-rank p = < 0.001

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/survival-analysis/survival-analysis-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/15-survival-analysis.png`

### 16. Clinical Relapse Hazard Modeling

**Goal:** Move from survival curves to interpretable hazard ratios across clinically meaningful covariates.

**Analysis:** Cox proportional hazards model

**Data files:** data/raw/rossi.csv

**Source:** rossi from the lifelines example datasets, framed here as a clinical relapse-risk modeling proxy.

**What to notice:** Hazard-ratio views work best when they stay visual and legible for biologists who need the direction and scale of risk fast.

![Screenshot](/assets/screenshots/16-hazard-modeling.png)

**Step-by-step**

1. Open Clinical Relapse Hazard Modeling.
2. Inspect the covariate preview to understand which clinical predictors are available to the model.
3. Review the ranked hazard-ratio chart to see the strongest risk and protective associations.
4. Read the model card for the top coefficients and confidence intervals.
5. Use the result bundle if you want a fast model summary for collaborators or investigators.

**Result summary:** The Cox model ranks prior convictions, age, and parole-related covariates as the strongest hazard modifiers, giving investigators a prioritized view of relapse risk rather than a single average survival curve. The statistical trick is the proportional-hazards model itself, which turns time-to-event data into interpretable hazard ratios while preserving follow-up information.

**Key metrics**

- race: HR 1.37 (0.75-2.50)
- prio: HR 1.10 (1.04-1.16)
- age: HR 0.94 (0.90-0.99)

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/hazard-modeling/hazard-modeling-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/16-hazard-modeling.png`

### 17. Responder Frequency Contingency Map

**Goal:** Compare categorical outcome frequencies across cohort strata from an aggregated count table.

**Analysis:** Chi-square test + normalized heatmap

**Data files:** data/raw/Titanic.csv

**Source:** Titanic from the R datasets collection, framed here as an aggregated cohort-outcome contingency proxy.

**What to notice:** This is useful when assay or screening results arrive as summarized counts and you still need a clean figure plus a formal test.

![Screenshot](/assets/screenshots/17-contingency-explorer.png)

**Step-by-step**

1. Open Responder Frequency Contingency Map.
2. Inspect the aggregated count table and note that summarized frequencies, not individual records, drive the analysis.
3. Review the heatmap to spot which strata are enriched or depleted for the responder outcome.
4. Read the chi-square statistic and the odds-style interpretation card.
5. Export the panel if you need a clean categorical summary for a screen review or supplement.

**Result summary:** The contingency map shows a pronounced enrichment of the outcome in one cohort stratum versus the other, and the chi-square test on aggregated counts confirms that imbalance is unlikely to be sampling noise (chi-square 454.50, p < 0.001). The useful trick here is that summarized count tables can still yield a clean, valid categorical inference without reconstructing individual-level rows.

**Key metrics**

- Male survival share = 0.21
- Female survival share = 0.73
- Chi-square p = < 0.001

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/contingency-explorer/contingency-explorer-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/17-contingency-explorer.png`

### 18. Exposure-Associated Cancer Risk Model

**Goal:** Model case-control risk across exposure bins and show interpretable odds ratios.

**Analysis:** Logistic regression with odds-ratio view

**Data files:** data/raw/esoph.csv

**Source:** esoph from the R datasets collection, already a biomedical case-control dataset.

**What to notice:** Odds-ratio plots land well with biomedical teams because they let you scan effect size and interval uncertainty without reading raw coefficients.

![Screenshot](/assets/screenshots/18-logistic-risk-model.png)

**Step-by-step**

1. Open Exposure-Associated Cancer Risk Model.
2. Inspect the grouped case-control input table and note the exposure bins before looking at the model.
3. Review the odds-ratio chart to see which exposure ranges shift risk most strongly.
4. Read the model summary card and the interval labels for the leading effects.
5. Export the figure if you need a concise epidemiology or translational risk slide.

**Result summary:** The model points to alcohol and tobacco exposure bins with materially elevated odds of case status, which is the biological question investigators actually care about in exposure-associated cancer risk work. Logistic regression is doing the heavy lifting by converting grouped case-control counts into adjusted odds ratios and confidence intervals instead of leaving you with raw percentages alone.

**Key metrics**

- C(agegp)[T.65-74]: OR 41.55 (5.57-309.97)
- C(agegp)[T.75+]: OR 39.72 (4.93-319.93)
- C(agegp)[T.55-64]: OR 28.74 (3.89-212.13)

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/logistic-risk-model/logistic-risk-model-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/18-logistic-risk-model.png`

### 19. Assay Plate QC and Outlier Review

**Goal:** Run a transparent QC pass that flags outliers and missing values before downstream interpretation.

**Analysis:** IQR outlier flagging + scatter and box plot

**Data files:** data/raw/airquality.csv

**Source:** airquality from the R datasets collection, framed here as a plate-level assay QC proxy.

**What to notice:** Good QC figures reduce argument later because the exclusion logic is visible, reproducible, and tied to the raw distribution.

![Screenshot](/assets/screenshots/19-outlier-qc-review.png)

**Step-by-step**

1. Open Assay Plate QC and Outlier Review.
2. Inspect the preview table and note missing values before looking at any outlier flags.
3. Review the scatter and box plot together so both trend and spread remain visible.
4. Read the QC card to see how many measurements were flagged by the IQR rule.
5. Export the panel if you need an appendix figure documenting exclusions or review decisions.

**Result summary:** This QC pass flags 2 ozone values after removing rows with missing inputs, giving the team a concrete set of measurements that could distort downstream conclusions. The IQR rule is intentionally simple and robust: it is a transparent nonparametric screen for unusual values that does not depend on assuming a normal distribution.

**Key metrics**

- Rows with missing data = 37
- Flagged outliers = 2
- IQR bounds = [-49.9, 131.1]

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/outlier-qc-review/outlier-qc-review-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/19-outlier-qc-review.png`

### 20. Mechanism-of-Action Manuscript Board

**Goal:** Assemble multiple assay readouts into a single submission-style figure board with a bench-science narrative.

**Analysis:** Four-panel figure composition

**Data files:** data/generated/two-group-supplement-comparison.csv, data/generated/factorial-experiment.csv, data/generated/enzyme-kinetics.csv, data/generated/survival-analysis.csv

**Source:** Composite figure built from generated proxy assay panels spanning efficacy, interaction, kinetics, and survival.

**What to notice:** This is where the product has to feel like a serious publication tool: panel balance, labeling, and narrative flow should work before Illustrator ever opens.

![Screenshot](/assets/screenshots/20-publication-figure-board.png)

**Step-by-step**

1. Open Mechanism-of-Action Manuscript Board.
2. Review how the board combines efficacy, interaction, nonlinear-fit, and survival readouts into one story.
3. Inspect the shared spacing, panel labels, and caption strip to see whether the narrative hangs together.
4. Use this board as the final checkpoint before exporting a submission-ready multi-panel figure.
5. Export the board as a vector source figure or a high-resolution raster for manuscript assembly.

**Result summary:** The final board reads like a mechanism-of-action figure rather than a pile of unrelated plots: efficacy, interaction, kinetic, and survival evidence all support the same biological story. The trick here is compositional rather than inferential, using panel hierarchy, typography, and cross-panel alignment so reviewers can connect multiple analyses in one pass.

**Key metrics**

- Panel A: two-group comparison
- Panel B: factorial ANOVA interaction
- Panel C: enzyme kinetics fit

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/publication-figure-board/publication-figure-board-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/20-publication-figure-board.png`
