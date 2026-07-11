# Canopy outstanding issues

1. give user option to reset cascor model back to original (no hidden nodes)
    - i.e., reset training, vs reset model

2. training metric plots should accuracy in addition to loss

3. training metrics plots need to be reevaluated for the following requirements:
    - readability of the overall metrics display
    - visibility and clarity of the individual metric plots
    - color schemes for trend lines and backgrounds
    - effective scaling for clarity and for avoiding overlapping line graphs

4. consider the following fields to include in the training metrics plots:
    - loss
    - accuracy
    - f1 score
    - precision
    - recall
    - roc auc
    - confusion matrix
    - feature importance
    - shap values
    - permutation importance
    - partial dependence plots
    - calibration curve
    - roc curve
    - precision-recall curve
    - lift curve
    - gain curve
    - cumulative gain curve
    - cumulative lift curve
    - cumulative gain curve

5. workers tab should display both local and remote workers

6. dataset view tab left menu should update to reflect current dataset
    - dataset view tab -> left menu -> dataset parameters module -> current dataset section -> spiral sub-section
    - what is currently the spiral sub-section should be appropriately named and displaying relvant parameters for the currently selected dataset.
      - i.e., if xor dataset is selected, the left menu should NOT be displaying a "spiral" sub-section with number and rotation meta parameters
      - it should be displaying relevant read-only and/or editable metaparameter values

---
