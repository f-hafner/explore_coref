#!/bin/bash

python msmarco.py --n_docs 5000 &> msmarco.log
# python msmarco.py --n_docs 10 --no_corefs &> msmarco_nocorefs.log