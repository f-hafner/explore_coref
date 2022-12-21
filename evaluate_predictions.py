import re

UNUSED = -1

def get_gold_data(doc):
    #GOLD_DATA_FILE = "./data/generic/test_datasets/AIDA/AIDA-YAGO2-dataset.tsv"
    GOLD_DATA_FILE = "/home/flavio/projects/rel20/data/generic/test_datasets/AIDA/AIDA-YAGO2-dataset.tsv"
    entities = []

    in_file = open(GOLD_DATA_FILE, "r")
    for line in in_file:
        if re.search(f"^-DOCSTART- \({doc} ", line):
            break
    for line in in_file:
        if re.search(f"^-DOCSTART- ", line):
            break
        fields = line.strip().split("\t")
        if len(fields) > 3:
            if fields[1] == "B":
                entities.append([fields[2], fields[3]])
    return entities


def md_match(gold_entities, predicted_entities, predicted_links, gold_i, predicted_i):
    return gold_entities[gold_i][0].lower() == predicted_entities[predicted_i][0].lower()


def el_match(gold_entities, predicted_entities, predicted_links, gold_i, predicted_i):
    return(gold_entities[gold_i][0].lower() == predicted_entities[predicted_i][0].lower() and # the same mentions
           gold_entities[gold_i][1].lower() == predicted_entities[predicted_i][1].lower()) # the same linked entity 


def find_correct_els(gold_entities, predicted_entities, gold_links, predicted_links):
    for gold_i in range(0, len(gold_entities)): #gold_i is the mention indicator for gold mentions
        if gold_links[gold_i] == UNUSED:
            for predicted_i in range(0, len(predicted_entities)): # predicted_i is the mention indicator for the predicted entities 
                # what are predicted_links, what are predicted_entities? 
                if (predicted_links[predicted_i] == UNUSED and  # what does this condition measure? 
                    el_match(gold_entities, predicted_entities, predicted_links, gold_i, predicted_i)):
                    # the following two lines link together the ith gold entity with ith predictd entity. 
                    gold_links[gold_i] = predicted_i # this means that gold entity gold_i is identified by the predicted entity predicted_i
                    predicted_links[predicted_i] = gold_i # this means the predicted_i-th entity refers to the gold entity gold_i
                # after this step, the identified mentions that are correctly linked to entities have -1 replaced with the gold mention id.
                # the other mentions remain -1
    return gold_links, predicted_links


def find_correct_mds(gold_entities, predicted_entities, gold_links, predicted_links):
    for gold_i in range(0, len(gold_entities)):
        if gold_links[gold_i] == UNUSED:
            for predicted_i in range(0, len(predicted_entities)):
                if (predicted_links[predicted_i] == UNUSED and 
                    md_match(gold_entities, predicted_entities, predicted_links, gold_i, predicted_i)):
                    gold_links[gold_i] = predicted_i
                    predicted_links[predicted_i] = gold_i
                # after this step, predicted_links[i] == -1 means that the identified mention was not a gold mention
                # if it is not -1, it means that the mention was correclty detected, but not necessarily correclty linked.
    return gold_links, predicted_links



def compare_entities(gold_entities, predicted_entities):
    gold_links = len(gold_entities) * [UNUSED] # generate a list of [UNUSED]. here we could condition only on entities being coreferences. how to do this? -- need to drop non-coreferences from the input list. but how does this work for the gold entities?
    predicted_links = len(predicted_entities) * [UNUSED] # we start with -1 for all predicted links 
    # here we "iterate": check EL and only then MD. 
    gold_links, predicted_links = find_correct_els(gold_entities, predicted_entities, gold_links, predicted_links)
    gold_links, predicted_links = find_correct_mds(gold_entities, predicted_entities, gold_links, predicted_links)
    return gold_links, predicted_links


def count_entities(gold_entities, predicted_entities, gold_links, predicted_links):
    correct = 0
    wrong_md = 0
    wrong_el = 0
    missed = 0
    missed_gold_entities = []
    # predicted_links: assigns the id of gold_links to each detected mention 
    # gold_links: for each gold entity, indicates if it has not been found (gold_link = -1), and if found, which mention
    for predicted_i in range(0, len(predicted_links)): 
        if predicted_links[predicted_i] == UNUSED: 
            wrong_md += 1 # false positive mention (?)
        elif predicted_entities[predicted_i][1] == gold_entities[predicted_links[predicted_i]][1]:
            correct += 1 # correctly identified mention, correct link 
        else:
            wrong_el += 1 # correctly identified mention but wrong link 
    for gold_i in range(0, len(gold_links)): # missed = not detected in MD? ie, false negative in MD
        if gold_links[gold_i] == UNUSED:
            # print(f"gold entity missed: {gold_entities[gold_i]}") # also need the coreference here... 
            missed_gold_entities.append(gold_entities[gold_i])
            missed += 1
    return correct, wrong_md, wrong_el, missed, missed_gold_entities


def compare_and_count_entities(gold_entities, predicted_entities):
    gold_links, predicted_links = compare_entities(gold_entities, predicted_entities)
    return count_entities(gold_entities, predicted_entities, gold_links, predicted_links)


def compute_md_scores(correct_all, wrong_md_all, wrong_el_all, missed_all):
    if correct_all + wrong_el_all > 0:
        precision_md = 100*(correct_all + wrong_el_all) / (correct_all + wrong_el_all + wrong_md_all)
        recall_md = 100*(correct_all + wrong_el_all) / (correct_all + wrong_el_all + missed_all)
        f1_md = 2 * precision_md * recall_md / ( precision_md + recall_md )
    else:
        precision_md = 0
        recall_md = 0
        f1_md = 0
    return precision_md, recall_md, f1_md


def compute_el_scores(correct_all, wrong_md_all, wrong_el_all, missed_all):
    if correct_all > 0: 
        # wrong_el_all = detected mention, but wrong link
        # wrong_md_all = number of false positive mentions
        # missed_all = false negative mentions (linking not relevant, since mention not detected in the first place)
        # correct_all = mention correctly detected and correctly linked 
        # do I understand correctly that this EL score is after both EL and MD, ie, not conditional on detected mentions?  
            # so the problem is that if we drop the mentions that are not coreferences from the gold list, we change the goal posts.
            # and so the wrong_md_all and missed_all can change as well -- worse, missed_all will go to 0! 
            # so we cannot compare recall to the recall from the full sample. 
            # but can we still compare recall from the EL with and without coref?
                # missed_all will become 0 for both 
        # so predictions: if I change the sample to only mentions that are coreferences,
            # then precision with coref should stay the same as for the full sample (current output from Erik). and so we can compare the precision without coref to the full sample precision
            # but recall with coref will not stay the same for the new sample. we can still compare recall between with_coref and not, and any variation in it will stem from changes in linked entities
        # try to make a drawing of this! 
        # instead chat gpt tells me to keep the ground truth the same. but then I will mechanically have lower recall??
        precision_el = 100 * correct_all / (correct_all + wrong_md_all + wrong_el_all) 
        recall_el = 100 * correct_all / (correct_all + wrong_el_all + missed_all) 
        f1_el = 2 * precision_el * recall_el / ( precision_el + recall_el )
    else:
        precision_el = 0.0
        recall_el = 0
        f1_el = 0
    return precision_el, recall_el, f1_el


def print_scores(correct_all, wrong_md_all, wrong_el_all, missed_all):
    precision_md, recall_md, f1_md = compute_md_scores(correct_all, wrong_md_all, wrong_el_all, missed_all)
    precision_el, recall_el, f1_el = compute_el_scores(correct_all, wrong_md_all, wrong_el_all, missed_all)
    print("Results: PMD RMD FMD PEL REL FEL: ", end="")
    print(f"{precision_md:0.1f}% {recall_md:0.1f}% {f1_md:0.1f}% | ",end="")
    print(f"{precision_el:0.1f}% {recall_el:0.1f}% {f1_el:0.1f}%")
    return precision_md, recall_md, f1_md, precision_el, recall_el, f1_el


def evaluate(predictions, coref_only = False):
    """Evaluate predictions against gold entities.
    
    Parameters
    ----------
    coref_only: Restrict the set of gold entities to coreferences.
    """
    correct_all = 0
    wrong_md_all = 0
    wrong_el_all = 0
    missed_all = 0
    missed_gold_all = []
    for doc in predictions:
        gold_entities = get_gold_data(doc)
        if coref_only:
            # change the ground truth: only entities which we would identify as coreferences in REL
            corefs = [find_coref(m, gold_entities, verbose=False) for m in gold_entities]
            coref_gold_ids = [i for i in range(len(corefs)) if len(corefs[i]) > 0]
            gold_entities = [gold_entities[i] for i in coref_gold_ids]
        predicted_entities = []
        for mention in predictions[doc]:
            predicted_entities.append([mention["mention"], mention["prediction"]])
        # predicted_entities and gold_entities are both a list of lists. each list is one mention with the string mention and the linked entity
        correct, wrong_md, wrong_el, missed, missed_gold = compare_and_count_entities(gold_entities, predicted_entities)
        # return here an additional object: the missed coreferences
        correct_all += correct
        wrong_md_all += wrong_md
        wrong_el_all += wrong_el
        missed_all += missed
        missed_gold_all += missed_gold
    print_scores(correct_all, wrong_md_all, wrong_el_all, missed_all)
    if coref_only:
        return missed_gold_all



def find_coref(mention, mentlist, verbose=False):
    "re-implement __find_coref from REL"

    coref = []
    cur_m = mention[0].lower() 
    cur_m_entity = mention[1] # entity of the current mention
    for m in mentlist:
        entity = m[1]
        m = m[0].lower()
        if cur_m == m:
            continue 
        start_pos = m.find(cur_m)
        if start_pos == -1:
            continue 
        end_pos = start_pos + len(cur_m) - 1

        if (entity == cur_m_entity) and (start_pos == 0 or m[start_pos - 1] == " "):
            #  need to check the following sequentially:
            #  because gold mentions are not surrounded by text, end_pos+1 can be larger 
            #  than len(m), which would result in an error with the original code
            if end_pos == len(m) - 1:
                if verbose:
                    print(f"{cur_m} is a coref for {m} ")
                coref.append(m)
            elif m[end_pos + 1] == " ":
                if verbose:
                    print(f"{cur_m} is a coref for {m} ")
                coref.append(m)
            else:
                continue
    return coref 
