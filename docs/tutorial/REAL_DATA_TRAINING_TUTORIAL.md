# AssayAtlas Real-Data Training Tutorial

This tutorial is intentionally hand-held. Every lesson uses real data, a real statistical workflow, and a real output rendered by the AssayAtlas workspace.

## How to use this tutorial

1. Start the app locally or open the deployed AssayAtlas home page.
2. Open the Workspace or the Tutorial page.
3. Work through the twenty use cases in order at least once.
4. Re-run the flows with the provided CSV files to internalize the patterns.

## Training goals

- Learn the SaaS navigation without friction.
- See what publication-grade defaults should feel like.
- Practice the twenty most meaningful Prism-style workflows with transparent results.
- Leave with exportable example figures and the raw input data for each lesson.


## Use Cases


### 01. Two-Group Supplement Comparison

**Goal:** Compare low-dose tooth growth by supplement and show every replicate.

**Analysis:** Welch t test + raw-point estimation plot

**Data files:** data/raw/ToothGrowth.csv

**Source:** ToothGrowth from the R datasets collection.

**What to notice:** Prism users love being able to see raw points and the conclusion on one screen. This example keeps every animal visible while still surfacing the statistical decision.

![Screenshot](/assets/screenshots/01-two-group-supplement-comparison.png)

**Step-by-step**

1. Open the Workspace and choose Two-Group Supplement Comparison.
2. Review the input file preview and confirm the dose filter is 0.5 mg/day.
3. Inspect the raw-point plot to make sure the replicate spread is visible before statistics.
4. Read the automatic Welch t test result card and confidence interval.
5. Export the figure as SVG or PNG from the figure actions menu.

**Result summary:** Low-dose OJ produced a mean tooth length 5.25 units higher than VC, with Welch t 3.17 and p 0.006.

**Key metrics**

- OJ mean = 13.23
- VC mean = 7.98
- Mean difference = 5.25

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/two-group-supplement-comparison/two-group-supplement-comparison-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/01-two-group-supplement-comparison.png`

### 02. Dose-Response Overview

**Goal:** Show how growth changes across three vitamin C dose levels.

**Analysis:** One-way ANOVA + Tukey multiple comparison

**Data files:** data/raw/ToothGrowth.csv

**Source:** ToothGrowth from the R datasets collection.

**What to notice:** This workflow is common in assay exploration: a quick sanity check on monotonic dose behavior plus a formal omnibus test.

![Screenshot](/assets/screenshots/02-dose-response-overview.png)

**Step-by-step**

1. Open the Dose-Response Overview example.
2. Confirm the input file contains the full ToothGrowth table, not the low-dose subset.
3. Inspect the dose-wise raw-point summary plot and the dose means.
4. Read the ANOVA result and the pairwise dose comparison card.
5. Use the export preset if you need a journal-ready PNG.

**Result summary:** Dose explains a strong share of the growth variance (F 67.42, p < 0.001).

**Key metrics**

- Dose 0.5 mean = 10.61
- Dose 1.0 mean = 19.73
- Dose 2.0 mean = 26.10

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/dose-response-overview/dose-response-overview-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/02-dose-response-overview.png`

### 03. Grouped Mean Comparison

**Goal:** Compare plant weight across a control and two treatment groups.

**Analysis:** One-way ANOVA + Tukey HSD

**Data files:** data/raw/PlantGrowth.csv

**Source:** PlantGrowth from the R datasets collection.

**What to notice:** The dot-plus-summary view is one of the most loved Prism patterns because it keeps the data honest while still looking publication-ready.

![Screenshot](/assets/screenshots/03-grouped-mean-comparison.png)

**Step-by-step**

1. Open Grouped Mean Comparison from the left rail.
2. Review the three-group preview table and verify there are ten replicates per arm.
3. Inspect the polished dot-and-summary chart before looking at p values.
4. Use the Tukey table to identify which treatment differs from control.
5. Add the figure to a board if you want to combine it with other results.

**Result summary:** Treatment groups differ overall (F 4.85, p 0.016), with Treatment 2 showing the highest mean weight.

**Key metrics**

- Control mean = 5.03
- Treatment 1 mean = 4.66
- Treatment 2 mean = 5.53

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/grouped-mean-comparison/grouped-mean-comparison-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/03-grouped-mean-comparison.png`

### 04. Factorial Experiment

**Goal:** Analyze a classic 2x3 factorial experiment with interaction effects.

**Analysis:** Two-way ANOVA with interaction

**Data files:** data/raw/warpbreaks.csv

**Source:** warpbreaks from the R datasets collection.

**What to notice:** Many Prism users value how fast they can go from a factorial table to an interpretable graph. The interaction plot is the center of gravity here.

![Screenshot](/assets/screenshots/04-factorial-experiment.png)

**Step-by-step**

1. Open Factorial Experiment.
2. Inspect the grouped preview and note the two wool types and three tension settings.
3. Read the interaction plot first to understand the shape of the effect.
4. Use the ANOVA table to see whether wool, tension, and their interaction matter.
5. Export the figure and include the ANOVA table in your report bundle.

**Result summary:** Tension dominates the response, while the wool-by-tension interaction is comparatively small in this classic factorial example.

**Key metrics**

- Wool effect p = 0.058
- Tension effect p = < 0.001
- Interaction p = 0.021

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/factorial-experiment/factorial-experiment-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/04-factorial-experiment.png`

### 05. Paired Before-and-After Study

**Goal:** Show within-subject change instead of treating repeated observations as independent.

**Analysis:** Paired t test + subject spaghetti plot

**Data files:** data/raw/sleep.csv

**Source:** sleep from the R datasets collection.

**What to notice:** This is a classic Prism-style win: the graph makes the pairing obvious before the statistics speak.

![Screenshot](/assets/screenshots/05-paired-before-after.png)

**Step-by-step**

1. Open Paired Before-and-After Study.
2. Verify that every subject appears in both conditions in the preview panel.
3. Inspect the spaghetti plot to see whether the direction of change is consistent by subject.
4. Review the paired t test and the mean paired difference.
5. Use the notes panel to capture whether the result is biologically meaningful, not just statistically non-zero.

**Result summary:** Subjects improved by 1.58 more units on average in group 2 than group 1, with paired t 4.06 and p 0.003.

**Key metrics**

- Mean group 1 = 0.75
- Mean group 2 = 2.33
- Mean paired difference = 1.58

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/paired-before-after/paired-before-after-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/05-paired-before-after.png`

### 06. Time-Course Summary

**Goal:** Turn a small time-course table into a compact kinetic summary.

**Analysis:** Area-under-the-curve summary + line plot

**Data files:** data/raw/BOD.csv

**Source:** BOD from the R datasets collection.

**What to notice:** Even basic time-course screens feel better when the graph and one-number summary live together. That fast feedback loop is part of the Prism appeal.

![Screenshot](/assets/screenshots/06-time-course-summary.png)

**Step-by-step**

1. Open Time-Course Summary.
2. Inspect the input table and confirm that time increases monotonically.
3. Review the line chart to see the saturation shape of the response.
4. Read the computed AUC and final-value summary card.
5. Export the figure if you need a quick panel for a methods update or internal review.

**Result summary:** The BOD time course reaches 19.8 at the final timepoint, with an AUC of 92.65.

**Key metrics**

- Baseline = 8.3
- Final value = 19.8
- AUC = 92.65

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/time-course-summary/time-course-summary-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/06-time-course-summary.png`

### 07. Repeated Growth Curves

**Goal:** Review repeated measures without collapsing away subject identity.

**Analysis:** Subject-wise growth lines + slope summary

**Data files:** data/raw/Orange.csv

**Source:** Orange from the R datasets collection.

**What to notice:** Researchers love when repeated-measures data stay visually intact instead of being flattened into a single average line.

![Screenshot](/assets/screenshots/07-repeated-growth-curves.png)

**Step-by-step**

1. Open Repeated Growth Curves.
2. Inspect the preview to see age and circumference recorded for multiple trees.
3. Read the line chart to compare each tree trajectory over time.
4. Use the slope summary card to identify the fastest and slowest growers.
5. Add this view to a multi-panel board if you are telling a developmental story.

**Result summary:** Tree 4 shows the steepest growth trend, while Tree 3 is the slowest-growing trajectory in the cohort.

**Key metrics**

- Fastest slope = Tree 4 (0.135)
- Slowest slope = Tree 3 (0.081)
- Median circumference = 115.0

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/repeated-growth-curves/repeated-growth-curves-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/07-repeated-growth-curves.png`

### 08. Regression and Calibration

**Goal:** Fit a simple calibration-style relationship and show the uncertainty band.

**Analysis:** Linear regression with 95% prediction band

**Data files:** data/raw/trees.csv

**Source:** trees from the R datasets collection.

**What to notice:** Prism users often pick the tool because regression results and the fitted graphic arrive together without friction.

![Screenshot](/assets/screenshots/08-regression-and-calibration.png)

**Step-by-step**

1. Open Regression and Calibration.
2. Inspect the input columns and make sure the predictor is on the x-axis and the response on the y-axis.
3. Review the regression line and the 95% prediction band.
4. Read the slope, R-squared, and prediction summary.
5. Use the exported SVG if you need to polish labels further for a manuscript.

**Result summary:** Tree volume rises by about 5.07 units per girth unit, with R-squared 0.935.

**Key metrics**

- Intercept = -36.94
- Slope = 5.07
- R-squared = 0.935

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/regression-and-calibration/regression-and-calibration-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/08-regression-and-calibration.png`

### 09. Correlation Screen

**Goal:** Quickly screen relationships across several numeric features.

**Analysis:** Pearson correlation heatmap

**Data files:** data/raw/iris.csv

**Source:** iris from the R datasets collection.

**What to notice:** This is the kind of multivariate glance people like because it is informative in seconds and visually neat enough to share.

![Screenshot](/assets/screenshots/09-correlation-screen.png)

**Step-by-step**

1. Open Correlation Screen.
2. Inspect the feature preview and note that the species label is excluded from the correlation matrix.
3. Read the heatmap first to spot the strongest positive and negative relationships.
4. Use the metric card to identify the top correlation pair.
5. Export the heatmap when you need a compact exploratory panel for collaborators.

**Result summary:** The strongest relationship is between Petal.Length and Petal.Width with correlation 0.96.

**Key metrics**

- Top pair = Petal.Length vs Petal.Width
- Top correlation = 0.96
- Lowest correlation = -0.43

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/correlation-screen/correlation-screen-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/09-correlation-screen.png`

### 10. PCA Species Map

**Goal:** Reduce four measurements into two axes and show class separation.

**Analysis:** Principal component analysis

**Data files:** data/raw/iris.csv

**Source:** iris from the R datasets collection.

**What to notice:** Users often praise Prism when advanced-looking plots remain approachable. PCA is a good test of that principle.

![Screenshot](/assets/screenshots/10-pca-species-map.png)

**Step-by-step**

1. Open PCA Species Map.
2. Inspect the standardized feature list before computing PCA.
3. Review the biplot-style scatter to see how the species separate across the first two components.
4. Read the explained-variance card to understand how much of the structure is retained.
5. Add the plot to a board if you need a compact dimensionality-reduction panel.

**Result summary:** The first two principal components retain 95.8% of the variance and visibly separate the species.

**Key metrics**

- PC1 variance = 73.0%
- PC2 variance = 22.9%
- Two-component total = 95.8%

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/pca-species-map/pca-species-map-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/10-pca-species-map.png`

### 11. Distribution Comparison

**Goal:** Compare full distributions, not just means, across three species.

**Analysis:** Violin plot + one-way ANOVA

**Data files:** data/raw/iris.csv

**Source:** iris from the R datasets collection.

**What to notice:** Polished distribution plots are part of Prism's charm, especially when they default to something more expressive than a bare bar chart.

![Screenshot](/assets/screenshots/11-distribution-comparison.png)

**Step-by-step**

1. Open Distribution Comparison.
2. Review the species labels in the preview and confirm the measurement column is sepal length.
3. Inspect the violin plot to understand shape, spread, and overlap.
4. Read the ANOVA result card to decide whether the mean difference is large enough to formalize.
5. Export the figure if you need a more modern alternative to a plain box plot.

**Result summary:** Sepal length differs strongly by species (F 119.26, p < 0.001), and the violin view makes the distribution shape easy to see.

**Key metrics**

- Setosa mean = 5.01
- Versicolor mean = 5.94
- Virginica mean = 6.59

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/distribution-comparison/distribution-comparison-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/11-distribution-comparison.png`

### 12. Enzyme Kinetics

**Goal:** Fit enzyme-rate curves for treated and untreated conditions.

**Analysis:** Michaelis-Menten fitting

**Data files:** data/raw/Puromycin.csv

**Source:** Puromycin from the R datasets collection.

**What to notice:** Nonlinear regression is one of Prism's signature strengths, so this use case is a must-win for the alternative.

![Screenshot](/assets/screenshots/12-enzyme-kinetics.png)

**Step-by-step**

1. Open Enzyme Kinetics.
2. Check the concentration and rate columns in the preview table.
3. Inspect the fitted Michaelis-Menten curves over the raw points.
4. Read the Vmax and Km estimates for each condition.
5. Export the panel if you need a fast enzyme-kinetics figure for a slide or report.

**Result summary:** Michaelis-Menten fitting separates the treated and untreated enzyme kinetics clearly, with distinct Vmax and Km estimates.

**Key metrics**

- treated Vmax = 212.68, Km = 0.06
- untreated Vmax = 160.28, Km = 0.05
- See the result card in the app.

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/enzyme-kinetics/enzyme-kinetics-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/12-enzyme-kinetics.png`

### 13. Pharmacokinetic Exposure

**Goal:** Track drug concentration over time and summarize exposure metrics.

**Analysis:** Concentration-time summary + noncompartmental metrics

**Data files:** data/raw/Theoph.csv

**Source:** Theoph from the R datasets collection.

**What to notice:** A Prism alternative needs credible PK workflows even when the math is relatively basic, because the audience often thinks in curves first.

![Screenshot](/assets/screenshots/13-pharmacokinetics.png)

**Step-by-step**

1. Open Pharmacokinetic Exposure.
2. Inspect the subject, time, and concentration columns in the preview.
3. Review the concentration-time plot to see the shared peak-and-decay shape.
4. Read the automatic Cmax, Tmax, and AUC summary card.
5. Export the figure or the metrics table for your PK review packet.

**Result summary:** Across subjects, mean Cmax is 8.76 and mean AUC is 103.81, with the expected peak-and-decay concentration pattern.

**Key metrics**

- Mean Cmax = 8.76
- Mean AUC = 103.81
- Earliest Tmax = 0.63

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/pharmacokinetics/pharmacokinetics-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/13-pharmacokinetics.png`

### 14. Drug Elimination Half-Life

**Goal:** Estimate elimination behavior from concentration decay data.

**Analysis:** Semi-log elimination fit

**Data files:** data/raw/Indometh.csv

**Source:** Indometh from the R datasets collection.

**What to notice:** This is a deliberately practical workflow: scientists care about the answer and the shape of the decay at the same time.

![Screenshot](/assets/screenshots/14-drug-elimination.png)

**Step-by-step**

1. Open Drug Elimination Half-Life.
2. Inspect the subject-level concentration-time table.
3. Read the semi-log plot to confirm the terminal phase looks approximately linear on the log scale.
4. Review the median half-life estimate and subject variability.
5. Export the panel if you need a compact PK appendix figure.

**Result summary:** The fitted terminal phase yields a median half-life of 1.66 time units across subjects.

**Key metrics**

- Median half-life = 1.66
- Shortest half-life = 1.51
- Longest half-life = 1.87

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/drug-elimination/drug-elimination-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/14-drug-elimination.png`

### 15. Kaplan-Meier Survival Analysis

**Goal:** Compare survival curves across two groups and keep censoring visible.

**Analysis:** Kaplan-Meier + log-rank test

**Data files:** data/raw/waltons.csv

**Source:** waltons from the lifelines example datasets.

**What to notice:** Survival workflows are one of the places where users especially value an opinionated, graph-first tool.

![Screenshot](/assets/screenshots/15-survival-analysis.png)

**Step-by-step**

1. Open Kaplan-Meier Survival Analysis.
2. Inspect the event-time preview and note the group assignment.
3. Review the stepwise survival curves and at-risk behavior.
4. Read the log-rank result card for the between-group comparison.
5. Export the plot if you need a manuscript-ready survival panel.

**Result summary:** The two survival curves separate clearly, with log-rank p < 0.001.

**Key metrics**

- control median survival = 58.00
- miR-137 median survival = 26.00
- Log-rank p = < 0.001

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/survival-analysis/survival-analysis-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/15-survival-analysis.png`

### 16. Hazard Modeling

**Goal:** Move from a survival curve to interpretable hazard ratios.

**Analysis:** Cox proportional hazards model

**Data files:** data/raw/rossi.csv

**Source:** rossi from the lifelines example datasets.

**What to notice:** Prism is loved for common analyses that stay readable. The Cox view should feel serious but never opaque.

![Screenshot](/assets/screenshots/16-hazard-modeling.png)

**Step-by-step**

1. Open Hazard Modeling.
2. Inspect the covariate preview to understand the available predictors.
3. Review the ranked hazard-ratio chart to see the strongest associations.
4. Read the model card for the top coefficients and confidence intervals.
5. Use the result bundle if you want a quick model summary for collaborators.

**Result summary:** Prior convictions, age, and parole-related covariates emerge as the most influential terms in the Cox model.

**Key metrics**

- race: HR 1.37 (0.75-2.50)
- prio: HR 1.10 (1.04-1.16)
- age: HR 0.94 (0.90-0.99)

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/hazard-modeling/hazard-modeling-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/16-hazard-modeling.png`

### 17. Contingency Explorer

**Goal:** Compare survival rates by sex in the Titanic passenger data.

**Analysis:** Chi-square test + normalized heatmap

**Data files:** data/raw/Titanic.csv

**Source:** Titanic from the R datasets collection.

**What to notice:** Users love when categorical summaries are both readable and visually polished, especially when counts come in aggregated form.

![Screenshot](/assets/screenshots/17-contingency-explorer.png)

**Step-by-step**

1. Open Contingency Explorer.
2. Inspect the aggregated count table and note that counts, not individual rows, drive the analysis.
3. Review the heatmap to spot the asymmetry between women and men.
4. Read the chi-square statistic and odds-style interpretation card.
5. Export the panel if you need a compact categorical analysis figure.

**Result summary:** Sex and survival are strongly associated in the aggregated Titanic counts (chi-square 454.50, p < 0.001).

**Key metrics**

- Male survival share = 0.21
- Female survival share = 0.73
- Chi-square p = < 0.001

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/contingency-explorer/contingency-explorer-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/17-contingency-explorer.png`

### 18. Logistic Risk Model

**Goal:** Model esophageal cancer risk from alcohol and tobacco categories.

**Analysis:** Logistic regression with odds-ratio view

**Data files:** data/raw/esoph.csv

**Source:** esoph from the R datasets collection.

**What to notice:** This is the type of result that becomes much more trustworthy when the model output is paired with a clean, understandable visualization.

![Screenshot](/assets/screenshots/18-logistic-risk-model.png)

**Step-by-step**

1. Open Logistic Risk Model.
2. Inspect the grouped case-control input table.
3. Review the odds-ratio chart to see which exposure bins shift the risk most strongly.
4. Read the model summary card and the confidence interval labels.
5. Export the figure if you need a concise risk-factor slide.

**Result summary:** The fitted logistic model highlights several alcohol and tobacco categories with materially elevated odds ratios relative to baseline exposure groups.

**Key metrics**

- C(agegp)[T.65-74]: OR 41.55 (5.57-309.97)
- C(agegp)[T.75+]: OR 39.72 (4.93-319.93)
- C(agegp)[T.55-64]: OR 28.74 (3.89-212.13)

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/logistic-risk-model/logistic-risk-model-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/18-logistic-risk-model.png`

### 19. Outlier QC Review

**Goal:** Show how a QC workflow can stay visual without hiding the statistics.

**Analysis:** IQR outlier flagging + scatter and box plot

**Data files:** data/raw/airquality.csv

**Source:** airquality from the R datasets collection.

**What to notice:** Polished QC views reduce arguments later because the data-cleaning logic is visible, not hidden in a script.

![Screenshot](/assets/screenshots/19-outlier-qc-review.png)

**Step-by-step**

1. Open Outlier QC Review.
2. Inspect the preview and note the missing values before looking at the outlier flags.
3. Review the scatter plot and box plot together to understand both trend and spread.
4. Read the QC card to see how many values were flagged by the IQR rule.
5. Export the panel if you need an appendix figure documenting exclusions or review decisions.

**Result summary:** The IQR rule flags 2 ozone values after removing rows with missing Ozone or Temperature.

**Key metrics**

- Rows with missing data = 37
- Flagged outliers = 2
- IQR bounds = [-49.9, 131.1]

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/outlier-qc-review/outlier-qc-review-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/19-outlier-qc-review.png`

### 20. Publication Figure Board

**Goal:** Combine several analyses into one clean, manuscript-style board.

**Analysis:** Four-panel figure composition

**Data files:** data/generated/two-group-supplement-comparison.csv, data/generated/factorial-experiment.csv, data/generated/enzyme-kinetics.csv, data/generated/survival-analysis.csv

**Source:** Composite figure built from previously generated analysis panels.

**What to notice:** This is where the product has to exceed Prism: excellent single figures are not enough if the final board still feels clumsy.

![Screenshot](/assets/screenshots/20-publication-figure-board.png)

**Step-by-step**

1. Open Publication Figure Board.
2. Review how the board combines comparison, factorial, nonlinear, and survival panels.
3. Inspect the shared spacing, panel labels, and caption strip to see how the narrative hangs together.
4. Use this as the final checkpoint before exporting a submission-ready multi-panel figure.
5. Export the board as a high-resolution PNG for docs or as a source figure for later refinement.

**Result summary:** The figure board combines comparison, factorial, nonlinear, and survival panels into one consistent manuscript-style composition.

**Key metrics**

- Panel A: two-group comparison
- Panel B: factorial ANOVA interaction
- Panel C: enzyme kinetics fit

**Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

**Bundle:** `data/generated/publication/publication-figure-board/publication-figure-board-publication-bundle.zip`

**Figure asset:** `app/static/generated/charts/20-publication-figure-board.png`
