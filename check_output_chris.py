

import pandas as pd 

datapath = "../data/msmarco/"

d = pd.read_parquet(f"{datapath}msmarco_doc_md_00_5k.parquet")



n_mentions = d.groupby('identifier').size().reset_index(name="count")

large_docs = n_mentions.loc[n_mentions['count'] > 2000, :]

# save subset of data for trying out stuff
keep_docids = ["msmarco_doc_00_0", "msmarco_doc_00_4806"]
d_subset = d.loc[d['identifier'].isin(keep_docids), :]

d_subset.to_parquet(f"{datapath}msmarco_md_subset.parquet")


# this is the output from large_docs
# 155   msmarco_doc_00_13707723   3957
# 160   msmarco_doc_00_13953003   2315
# 192    msmarco_doc_00_1494588   2353
# 1518  msmarco_doc_00_22560563   3165
# 2361  msmarco_doc_00_28953614  15109
# 2996  msmarco_doc_00_33635656   2242
# 3620    msmarco_doc_00_399588   5866