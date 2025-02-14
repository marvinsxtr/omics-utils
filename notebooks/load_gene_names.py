# %%
import pandas as pd
import numpy as np

# Gene set from Geneformer and scCello
# Downloaded from https://github.com/DeepGraphLearning/scCello/tree/main/data/token_vocabulary

vocab_1 = pd.read_csv("vocab_id2name.csv")
vocab_2 = pd.read_csv("vocab_ids_notFoundName.csv", header=None)
all_genes = np.concat((vocab_2.values.squeeze(), vocab_1["id"].values))
unique_genes = np.unique(all_genes)

pd.DataFrame(unique_genes).to_csv("../data/gene_vocabulary.csv", index=False, header=None)
# %%
