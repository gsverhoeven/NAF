import h5py
import pandas as pd
import string


def cleanup(x):         
    if isinstance(x, float):
        return "Unknown"
    y = x.lower()
    y = y.rstrip()
    return string.capwords(y)


def read_hdf5(hf, ix, prefix):

    coaches = list(hf["coaches"].keys())
    race_ids = hf["race_ids"][:].astype("<U19")

    # create 2 data frames, coach by race id
    df_mu = pd.DataFrame(index=coaches, columns=race_ids)
    df_mu.index.name = "coach"
    df_phi = pd.DataFrame(index=coaches, columns=race_ids)
    df_phi.index.name = "coach"

    # loop through all coaches, grab most recent mu/phi
    for pid in coaches:
           
        df_mu.loc[pid] = hf["coaches"][pid]["mu"][ix]
        df_phi.loc[pid] = hf["coaches"][pid]["phi"][ix]

    # melt both dataframes to long form
    mu_melt = df_mu.reset_index().melt(var_name="race", id_vars="coach", value_name=prefix + "_mu")
    phi_melt = df_phi.reset_index().melt(var_name="race", id_vars="coach", value_name=prefix + "_phi")

    # merge mu and phi and create rating
    df_out = pd.merge(mu_melt, phi_melt, on=["coach", "race"])
    df_out[prefix + "_rating"] = (df_out[prefix + "_mu"] - (PHI_PENALTY * df_out[prefix + "_phi"]))

    return df_out

PHI_PENALTY = snakemake.params.phi_penalty
coach_info = pd.read_csv(snakemake.input.csv)
coach_info["nation"] = coach_info.nation.apply(cleanup).replace(
    "United States Of America", "USA")
coach_info = coach_info[["naf_number", "naf_name", "nation"]].drop_duplicates()

with h5py.File(snakemake.input.hdf5, "r") as fh:

    curr_df = read_hdf5(fh, 0, "curr")
    last_df = read_hdf5(fh, 1, "last")
    
    rank_df = pd.merge(curr_df, last_df, on=["coach", "race"])

    # merge with existing coach info.
    merged = pd.merge(rank_df, coach_info, how="left", left_on=["coach"], right_on=["naf_name"])
    merged = merged.dropna(subset=["curr_rating"]).sort_values("curr_rating", ascending=False)
    merged.reset_index(inplace=True, drop=True)
    merged.index = merged.index.values + 1
    merged.to_csv(snakemake.output.csv, float_format='%.1f')
