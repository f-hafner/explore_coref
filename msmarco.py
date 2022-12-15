
import json 
import time 
import flair
import torch
from flair.models import SequenceTagger
import argparse
import pickle 
import gzip 
import time 

from REL.entity_disambiguation import EntityDisambiguation
from REL.mention_detection import MentionDetection


base_url = "/home/flavio/projects/rel20/data"
wiki_version = "wiki_2019"
datapath = "../data/msmarco/"

parser = argparse.ArgumentParser()
parser.add_argument( 
    "--no_corefs",
    action="store_true",
    help="use function with_coref()?", 
    default=False)
parser.add_argument( 
    "--n_docs",
    type=int,
    help="number of documents to process", 
    default=10)
args = parser.parse_args()
print(f"args.no_corefs is {args.no_corefs}")



config = {
    "mode": "eval",
    "model_path": "{}/{}/generated/model".format(base_url, wiki_version),
}

# ## Read ms marco data 
start = time.time()

with gzip.open(f"{datapath}msmarco_doc_00_5k.gz", "r") as file:
    data = file.readlines()

data = [json.loads(d) for d in data ]


# ## Bring into shape for REL
docids = [doc['docid'] for doc in data]
assert len(docids) == len(set(docids)), "docids are not unique"
docids_to_keep = docids[0:min(len(docids), args.n_docs)]
n_docs_eff = len(docids_to_keep)

data_input = {doc["docid"]: [doc['body'] , []] for doc in data if doc['docid'] in docids_to_keep}

assert len(data_input) == len(docids_to_keep)

# ## Run REL

flair.device = torch.device("cpu")

mention_detection = MentionDetection(base_url, wiki_version)
tagger_ner = SequenceTagger.load("ner-fast")

mentions_dataset, n_mentions = mention_detection.find_mentions(data_input, tagger_ner)

n_mentions_per_doc = {url: len(mentions_dataset[url]) for url in docids_to_keep}


model = EntityDisambiguation(base_url, wiki_version, config, no_corefs=args.no_corefs)
predictions, timing = model.predict(mentions_dataset)


# ## Save outputs 
output = {
    "md": mentions_dataset,
    "ed": predictions
}
filename = f"output_md_ed_{n_docs_eff}_docs"
filename = f"{datapath}predictions/{filename}"

if args.no_corefs:
    filename = f"{filename}_nocoref"


with open(f"{filename}.pickle", "wb") as f:
    pickle.dump(output, f, protocol=pickle.HIGHEST_PROTOCOL)

end = time.time()

print(f"Done in {(end-start)/60} minutes")

# TODO
    # save the identified mentions and the predictions, even though the mentions should not change 
    # think about a good way to compare the output from the disambiguation in the two steps -- 

# is this too big? -- 3.5M for only 10 documents
    # 1.5gb for all documents... -- for one condition (coref yes/no)
    # perhaps leave it for now, easier to investigate differences in the predictions 

