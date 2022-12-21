
import os 
import pickle 
import evaluate_predictions
import re 

datapath = "../data/"
path_efficiencytest = f"{datapath}efficiency_test/"
path_profiling = f"{path_efficiencytest}profile/"
msmarcopath = f"{datapath}msmarco/"
name_aida_dataset = "aida_testB"

# load single data set 
files = os.listdir(f"{path_efficiencytest}/predictions")
predictions = {}

for f in files:
    with open(f"{path_efficiencytest}/predictions/{f}", "rb") as file:
        f = re.sub(".pickle", "", f)
        predictions[f] = pickle.load(file)


# Subset predicted to those that are coreferences
n_documents = [50, 500] 
predictions_for_coreferences = {}

for n in n_documents:
    iteration_name = f"{name_aida_dataset}_{n}"
    iteration_name_nocoref = f"{iteration_name}_nocoref"

    predictions_coref = predictions[iteration_name]["predictions"]
    predictions_nocoref = predictions[iteration_name_nocoref]["predictions"]

    predicted_entities_coref = {}
    predicted_entities_nocoref = {}
    for docname, mentions_coref, mentions_nocoref in zip(predictions_coref.keys(), predictions_coref.values(), predictions_nocoref.values()):
        n_mentions = len(mentions_coref)
        # only keep the mentions that are labelled as coreferences. since we only have this information for the iteration where with_coref is used,
            # use the index of the mention list to subset
        prediction_coref = [mentions_coref[i] for i in range(n_mentions) if mentions_coref[i]['is_coref'] == 1]
        prediction_nocoref = [mentions_nocoref[i] for i in range(n_mentions) if mentions_coref[i]['is_coref'] == 1]
        
        predicted_entities_coref[docname] = prediction_coref 
        predicted_entities_nocoref[docname] = prediction_nocoref
    
    predictions_for_coreferences[iteration_name] = predicted_entities_coref
    predictions_for_coreferences[iteration_name_nocoref] = predicted_entities_nocoref


# Evaluate predictions. The adjustment for the gold entities is made in evaluate_predictions.evaluate()
for version, d in predictions_for_coreferences.items():
    # this only works for the aida test data sets 
    if "aida_test" in version:
        print(f"Evaluating predictions for {version}")
        evaluate_predictions.evaluate(d, coref_only=True)


# more generally it would be good to know which types of gold entities 
    # make a dict with gold entities and count how often they are missed (and their coreference)
    # this would require a function like with_coref that connects coreferring mentions and their coreferences
    # first ask Faegheh whether this is something worth doing 
    # for now, collect the missed entities in a separate object and return it from compare_and_count_entities()
# what does "--NME--" mean for the gold entities? 
