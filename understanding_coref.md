
## Key questions
1. What does `with_coref` do?
2. Why do we consider to get rid of it/why is it deemed expensive?
3. How to test the efficiency gains from omitting the call to `with_coref`?


### "Pseudo"code
```python
def with_coref(dataset):
    for data_name, content in dataset.items(): 
            # dataset.keys = ['1 EU)', '2 Rare)', '3 China)', '4 China)' ... ]
            # what are these data names?
        content['1 EU)'] # list of mentions (based on what? an article?)
        content['1 EU)'][0] # first mention. dictionary with keys ('mention', 'candidates', ..., 'sentence')
        # where do these data names come from? `mentions_dataset` in efficiency_test.py does not have the same keys..?
        for cur_m in content: # iterate through the mentions
            coref = find_coref(cur_m, content) # check if the current mention occurs in another mention
            if coref is not None: # continue only if the mention is a (co?)reference to another mention (exact terminology used here? see example below)
                cur_cands = {}
                cur_cands = ... # get candidates and probabilities from all coreferences, summing up the probabilities 
                cur_m['candidates'] = cur_cands
```

## What does `with_coref` do?
- for a given mention `cur_m`, it looks for coreferences in the content (by calling `__find_coref`). The content are all mentions in a "content".
    - for all mentions in the content (what is this? same document??)
        - a mention `m` is a coreference for mention `cur_m` if it contains the string `cur_m` as a separate word (ie, `cur_m` is not part of a bigger word).
    - each item in the dict is one "content", but what is it exactly? and what do the keys refer to? when are these dictionary keys generated, and what do they refer to?  
- if there are coreferences,
    - take the candidate entities for all coreferences and add their probabilities across all coreferences
    - this constitutes the new preference list for the mention.
    - the candidate entities for the referring mention itself are discarded altogether.


### Terminology and example
A coreference is a substring of another mention, and is detected as a named entity. 
Example: 

    This sentence is about Jimi Hendrix. The music of Hendrix is popular.

Here, the second mention "Hendrix" refers to the entity "Jimi Hendrix" in the preceding sentence. 
Just in terms of terminology, what is the coreference here? I think "Hendrix" a coreference to "Jimi Hendrix", but not sure. 
After the mention detection, we have candidate entities for both "Jimi Hendrix" and "Jimi". If we call `with_coref`, the candidates for "Jimi" will be replaced by the candidates of "Jimi Hendrix". 



## Where in REL is `with_coref` used?
- the method is defined in `TrainingEvaluationDatasets`. 
- the `load` method includes a call to `with_coref`. 
    - the data are loaded and already contain candidates. when the training data sets are loaded, the candidates are processed with the `with_coref` function
    - we process the candidates with coref because...?
- the `predict` method of the  `EntityDisambiguation` class calls `with_coref`
    - Thus, the disambiguation of the candidate entities is done after resolving coreferences
    - Because the way `with_coref` is defined, when `EntityDisambiguation` is instantiated, a `TrainingEvaluationDatasets` instance is also assigned:
        `self.coref = TrainingEvaluationDatasets(base_url, wiki_version, use_corefs)`


## Questions 
- Why is it deemed expensive?
    - Because `with_coref` has quadratic time complexity in the number of mentions?  
        - For each mention, we check whether the mention occurs in any of the other mentions (see function `__find_mention()`)
        - How do we then test the efficiency properly? How can we vary the size of the context? (What is context exactly?)
    - Other reason?
- Why is it defined/used in the TrainingEvaluationDatasets class? 
    - To compare predictions of entities (disambiguation step) with and without coreferences? 
- What are the pros and cons of resolving coreferences?
    - Better disambiguation of candidates, as long as the coreferences are true coreferences



## Timing
- Once I know what to time exactly, do so without other processes running



# Log

## 7/12/22
- the timing and prediction output from `predictions, timing = model.predict(mentions_dataset)` are not comparable
    - reason: in `get_data_items()`, if there are more than 100 mentions in a document, they are added separately in groups of 100 to the `data` object. This means that `len(data)` can be larger than the number of input documents. this does not matter for the prediction output because in the `__predict()` method, the predictions are stored in a dictionary where the keys are the document names. the multiple arrays of predictions are then just appended to the same item in the dictionary in the order they appear
    - but this change is not reflected in the timings, because the timings are just stored in a list
    - therefore, a document
- also, the timing from `model.predict` does *not* include the time spent on `with_coref` -- only the time for actual prediction is measured.
    - to change this, I am not sure it would be necessary to change the location of when `with_coref` is executed?
    - but the timing of `model.predict()` in efficiency_test *should* take care of this right? b/c with_coref is included in the call there
    - therefore, I should find out how to change the size of the input document for `predict`, ie, change `mentions_dataset`. can I just stack them on top of each other? 
- Chris
    - focus on the time complexity
    - increase length of documents? how? stack them on top of each other?
- Note the overall timing depends on two factors: $t_{disambiguate} + t_{coref}$
    - suppose the first term grows linearly in the number of mentions
    - it is possible that for small values, $t_{disambiguate} > t_{coref}$. Then, quadratic time is less visible when looking at "total" time
    - but for ever larger mentions, the second term will become more dominant
- what I did 
    - from the mention list, create datasets that repeat the mentions 2, 5, 10, 50, 100 times
    - run the entity disambiguation code for each data set, record the timing
    - plot the time as a function of the number of mentions 

## 8/12/22
- next steps 
    - write clean code for coref as well as for efficiency test
        - store the predictions as well as the timings
        - keep as is, or stack the full mentions dataset on top of each other?
            - it seems more straightforward the way it is now?
    - make clean notebook / sure everything runs / explain clearly what I did, make pdf report for Faegheh
    - write down the thing about the timing above? should this be an issue/changed (at least the timing)
    - talk to Chris/Stef about it 
    - think: should the # of mentions be increased in a different way? what is the consequence of what I am doing now?
    - natural way to increase number of mentions? ie use original dataset?
        - comparing predictions would then be easier, which we cannot do at the moment.
        - can I just increase the number of documents?
            - `with_coref` runs separately for each document. So increasing the number of documents is only useful for testing effectiveness and efficiency if there are more long documents.
            - presumably the number of mentions in the training data set would indicate the number of mentions to be detected? 
    - the number of mentions in the training datasets is at most 288 -- as the graph in the notebook shows, this is not large enough to see the timing difference in action
        - so I see no other option than the "stacking" of mentions to show the efficiency difference
        - we can still compare the predictive performance with and without coref for the different datasets and their number of mentions. anyway it would be good to do this for all datasets 

Plan
- code: 
    - tidy stacking/timing
    - add option for evaluating dataset
    - store predictions measure for all data sets, with and without coref 
- write/document
    - profiling for two simple examples: overhead of the other functions; need for large number of mentions to see non-linearity in action 
    - show the non-linearity as in the notebook
    - discuss predictions with and without coref -- check Erik's code?


