import pandas as pd
from pathlib import Path


HERE = Path(__file__).resolve().parent
EDU_PATH = HERE / "Education2023.csv"
UNEMP_PATH = HERE / "Unemployment2023.csv"
POV_PATH = HERE / "Poverty2023.csv"


edu = pd.read_csv(EDU_PATH, encoding="latin1")
unemp = pd.read_csv(UNEMP_PATH, encoding="latin1")
pov = pd.read_csv(POV_PATH, encoding="latin1")


edu_targets = [
    "Percent of adults who are not high school graduates, 2019-23",
    "Percent of adults who are high school graduates (or equivalent), 2019-23",
    "Percent of adults completing some college or associate degree, 2019-23",
    "Percent of adults with a bachelor's degree or higher, 2019-23",
]

unemp_targets = [
    "Civilian_labor_force_2023",
    "Employed_2023",
    "Unemployed_2023",
    "Unemployment_rate_2023",
    "Median_Household_Income_2022",
]

pov_targets = [
    "PCTPOVALL_2023",
    "POVALL_2023",
]


edu["fips"] = edu["FIPS Code"].astype("Int64")
unemp["fips"] = unemp["FIPS_Code"].astype("Int64")
pov["fips"] = pov["FIPS_Code"].astype("Int64")

edu["fips5"] = edu["fips"].astype(str).str.zfill(5)
unemp["fips5"] = unemp["fips"].astype(str).str.zfill(5)
pov["fips5"] = pov["fips"].astype(str).str.zfill(5)


def is_county(fips_series: pd.Series) -> pd.Series:
    f = fips_series.fillna(-1).astype(int)
    return (f >= 1000) & ((f % 1000) != 0)


edu = edu[is_county(edu["fips"])].copy()
unemp = unemp[is_county(unemp["fips"])].copy()
pov = pov[is_county(pov["fips"])].copy()


edu_f = edu[edu["Attribute"].isin(edu_targets)].copy()
unemp_f = unemp[unemp["Attribute"].isin(unemp_targets)].copy()
pov_f = pov[pov["Attribute"].isin(pov_targets)].copy()


edu_w = (
    edu_f.pivot_table(index=["fips5"], columns="Attribute", values="Value", aggfunc="first")
    .reset_index()
)

unemp_w = (
    unemp_f.pivot_table(
        index=["fips5", "State", "Area_Name"], columns="Attribute", values="Value", aggfunc="first"
    )
    .reset_index()
    .rename(columns={"Area_Name": "Area name"})
)

pov_w = (
    pov_f.pivot_table(
        index=["fips5", "Stabr", "Area_Name"], columns="Attribute", values="Value", aggfunc="first"
    )
    .reset_index()
    .rename(columns={"Stabr": "State", "Area_Name": "Area name"})
)


edu_w = edu_w.rename(columns={
    "Percent of adults who are not high school graduates, 2019-23": "edu_not_hs_pct_2019_23",
    "Percent of adults who are high school graduates (or equivalent), 2019-23": "edu_hs_grad_pct_2019_23",
    "Percent of adults completing some college or associate degree, 2019-23": "edu_some_college_pct_2019_23",
    "Percent of adults with a bachelor's degree or higher, 2019-23": "edu_bachelors_plus_pct_2019_23",
})

unemp_w = unemp_w.rename(columns={
    "Civilian_labor_force_2023": "labor_force_2023",
    "Employed_2023": "employed_2023",
    "Unemployed_2023": "unemployed_2023",
    "Unemployment_rate_2023": "unemployment_rate_2023",
    "Median_Household_Income_2022": "median_household_income_2022",
})

pov_w = pov_w.rename(columns={
    "PCTPOVALL_2023": "poverty_rate_2023",
    "POVALL_2023": "poverty_count_2023",
})


merged = pd.merge(unemp_w, edu_w, on="fips5", how="inner")
merged = pd.merge(
    merged,
    pov_w[["fips5", "poverty_rate_2023", "poverty_count_2023"]],
    on="fips5",
    how="inner",
)


pct_cols = [
    "edu_not_hs_pct_2019_23",
    "edu_hs_grad_pct_2019_23",
    "edu_some_college_pct_2019_23",
    "edu_bachelors_plus_pct_2019_23",
]
for c in pct_cols + ["unemployment_rate_2023", "poverty_rate_2023"]:
    merged[c] = pd.to_numeric(merged[c], errors="coerce")
merged["edu_pct_sum_2019_23"] = merged[pct_cols].sum(axis=1)


OUT_PATH = HERE / "merged_county_edu_unemp_poverty.csv"
merged.to_csv(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(merged))
print("Columns:", list(merged.columns))
print("Education % sum stats:\n", merged["edu_pct_sum_2019_23"].describe())