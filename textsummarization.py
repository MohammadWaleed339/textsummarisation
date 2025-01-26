# -*- coding: utf-8 -*-
"""textsummarization.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17_4h4Q8OCzbMWRkgES1p-K4-o41ZVLNU
"""

!pip install -U accelerate
!pip install -U bertviz
!pip install -U umap-learn
!pip install -U sentencepiece
!pip install py7zr
!pip install -U datasets

from datasets import load_dataset
dataset = load_dataset('cnn_dailymail', "3.0.0")

dataset['train'][1]['highlights']

from transformers import pipeline

pipe = pipeline('text-generation', model = "gpt2-medium" )

dataset['train'][1]["article"][:2000]
input_text = dataset['train'][1]["article"][:2000]
query = input_text + "\nTL;DR:\n"
pipe_out = pipe(query, max_length = 512, clean_up_tokenization_spaces=True)

pipe_out[0]['generated_text'][len(query):]

summaries = {}
summaries['gpt2-medium-380M'] = pipe_out[0]['generated_text'][len(query):]

# T-5 transformers is used
pipe = pipeline('summarization', model ='t5-base')

pipe_out = pipe(input_text)

summaries['t5-base-223M'] = pipe_out[0]['summary_text']

# Using Bart by facebook
pipe = pipeline('summarization', model = 'facebook/bart-large-cnn')
pipe_out = pipe(input_text)

summaries['bart-large-cnn-400M'] = pipe_out[0]['summary_text']

# Using google transformers
pipe = pipeline('summarization', model = 'google/pegasus-cnn_dailymail')

pipe_out = pipe(input_text)

summaries['pegasus-cnn-568M'] = pipe_out[0]['summary_text']

for model in summaries :
    print(model.upper())
    print(summaries[model])
    print("")

from datasets import load_dataset
from transformers import pipeline

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

device = 'gpu'
model_ckpt = 'facebook/bart-large-cnn'
tokenizer =  AutoTokenizer.from_pretrained(model_ckpt)
model =  AutoModelForSeq2SeqLM.from_pretrained(model_ckpt)

samsum = load_dataset('samsum')
samsum

samsum['train'][0]

dialogue_len = [len(x['dialogue'].split()) for x in samsum['train']]
summary_len = [len(x['summary'].split()) for x in samsum['train']]

import pandas as pd
data = pd.DataFrame([dialogue_len, summary_len]).T
data.colums = ['Dialogue length', 'Summary_length']
data.hist(figsize = (15,5))

# lets build data collator

def get_feature(batch):

    encodings = tokenizer(batch['dialogue'],
                         text_target = batch['summary'],
                          max_length = 1024,
                          truncation = True)

    encodings = {'input_ids': encodings['input_ids'],
            'attention_mask': encodings['attention_mask'],
                     'labels': encodings['labels']
                }

    return encodings

samsum_pt = samsum.map(get_feature, batched = True)
samsum_pt

columns = ['input_ids', 'labels', 'attention_mask']
samsum_pt.set_format(type = 'torch', columns = columns)

from transformers import DataCollatorForSeq2Seq
data_collator = DataCollatorForSeq2Seq(tokenizer, model = model)

from transformers import TrainingArguments, Trainer
training_args = TrainingArguments(
                                 output_dir = 'bart_samsum',
                                 num_train_epochs=1,
                                 warmup_steps=500,
                                 per_device_train_batch_size=4,
                                 weight_decay=0.01,
                                 logging_steps=10,
                                 evaluation_strategy='steps',
                                 eval_steps=500,
                                 save_steps=1e6,
                                 gradient_accumulation_steps=16
                                 )

trainer = Trainer(model = model,
                  args = training_args,
                  tokenizer = tokenizer,
                  data_collator = data_collator,
                  train_dataset = samsum_pt['train'],
                  eval_dataset = samsum_pt['validation'])

trainer.train()

trainer.save_model('Coder_one_2nd_project')

# Custome dialogue prediction

pipe = pipeline('summarization', model = 'Coder_one_2nd_project')
gen_kwargs = {"length_penalty": 0.8,
                   "num_beams":8,
                  "max_length":128}
custome_dialogue = """
Aria, a curious girl, discovers the magical Enchanted Forest, home to mystical creatures and the wise dragon Eldrin. The forest faces
a threat from the evil sorcerer Malakar, who seeks to drain its magic. With the help of Eldrin, Aria embarks on a quest to find three
ancient relics to defeat Malakar. Along the way, she makes new friends and overcomes challenges. Aria ultimately defeats Malakar,
restoring the forest's magic.
The creatures celebrate her bravery, and Aria continues her adventures in the Enchanted Forest, filled with wonder and friendship.

"""

print(pipe(custome_dialogue, **gen_kwargs))

from google.colab import drive
drive.mount('/content/drive')