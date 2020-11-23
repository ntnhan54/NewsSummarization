# -*- coding: utf-8 -*-
"""Copy_of_tag_classification (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BCsR8HeNO88iFJpY9ef8JirNtZACsVL3

### Download
"""
"""### Code"""
from info_extraction import *
from sys import argv

import json 

import numpy as np

from transformers import TFRobertaForSequenceClassification, AutoTokenizer, RobertaConfig
from underthesea import sent_tokenize
from fairseq.data import Dictionary
from fairseq.data.encoders.fastbpe import fastBPE

from torch import nn

import torch
from transformers import *
from torch.utils.data import DataLoader
from transformers import RobertaForSequenceClassification, AdamW
import torch.nn.functional as F
import jsonlines

MAX_SEQUENCE_LENGTH = 256

vocab = Dictionary()
vocab.add_from_file("/content/PhoBERT_base_transformers/dict.txt")

class BPE():
    bpe_codes = '/content/PhoBERT_base_transformers'

args = BPE()
bpe = fastBPE(args)

def convert_lines(train, vocab = vocab, bpe = bpe, max_sequence_length = MAX_SEQUENCE_LENGTH):
    outputs = np.zeros((len(train), max_sequence_length))
    
    cls_id = 0
    eos_id = 2
    pad_id = 1

    # for idx, line in tqdm(enumerate(train), total=len(train)): 
    for idx, line in enumerate(train):     
        
        subwords = bpe.encode('<s> '+ line+' </s>')       
        
        input_ids = vocab.encode_line(subwords, append_eos=False, add_if_not_exist=False).long().tolist()
        if len(input_ids) > max_sequence_length: 
            input_ids = input_ids[:max_sequence_length] 
            input_ids[-1] = eos_id
        else:
            input_ids = input_ids + [pad_id, ]*(max_sequence_length - len(input_ids))
        outputs[idx,:] = np.array(input_ids)
    
    return outputs

class RobertaForAIViVN(BertPreTrainedModel):
  #  config_class = RobertaConfig
  #  pretrained_model_archive_map = ROBERTA_PRETRAINED_MODEL_ARCHIVE_MAP
    base_model_prefix = "roberta"
    def __init__(self, config):
        super(RobertaForAIViVN, self).__init__(config)
        self.num_labels = config.num_labels
        self.roberta = RobertaModel(config)
        self.qa_outputs = nn.Linear(4*config.hidden_size, self.num_labels)
        self.init_weights()

    def forward(self, input_ids, attention_mask=None, token_type_ids=None, position_ids=None, head_mask=None,
                start_positions=None, end_positions=None):

        outputs = self.roberta(input_ids,
                            attention_mask=attention_mask,
#                            token_type_ids=token_type_ids,
                            position_ids=position_ids,
                            head_mask=head_mask)

        cls_output = torch.cat((outputs[2][-1][:,0, ...],outputs[2][-2][:,0, ...], outputs[2][-3][:,0, ...], outputs[2][-4][:,0, ...]),-1)
        logits = self.qa_outputs(cls_output)
        return logits

# Load model

config = RobertaConfig.from_pretrained(
    "/content/PhoBERT_base_transformers/config.json",
    output_hidden_states=True,
    num_labels=6,
    add_pooling_layer=False   
)
# myRobertaForTokenClassification
# RobertaForAIViVN
model = RobertaForAIViVN.from_pretrained("/content/PhoBERT_base_transformers/model.bin", config=config)

device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

# Creating optimizer and lr schedulers
param_optimizer = list(model.named_parameters())
no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']
optimizer_grouped_parameters = [
    {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)], 'weight_decay': 0.01},
    {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
]

optim = AdamW(optimizer_grouped_parameters, 4e-5, correct_bias=False)  # To reproduce BertAdam specific behavior set correct_bias=False
avg_loss = 0

if torch.cuda.device_count():
    print(f"Training using {torch.cuda.device_count()} gpus")
    model = nn.DataParallel(model)
    tsfm = model.module.roberta
else:
    tsfm = model.roberta

for child in tsfm.children():
        for param in child.parameters():
            if not param.requires_grad:
                print("whoopsies")
            param.requires_grad = False


def get_annotation(text, model):
    text_encoding = convert_lines([text])
    input = torch.tensor(text_encoding)
    y_pred = model(input.long(), input > 0).tolist()
    return (np.array(y_pred) > 0).astype(int).reshape(-1)

# tags = ["goal_info", "match_info", "match_result", "card_info", "substitution", 'penalty']

# team_name_set = get_team_name_set('train.jsonl')

def origin_to_summary(corpus, team_name_set, model):
    summary = {
        "players": { "team1":"", "team2":"" },
        "score_board": { "score1":"0", "score2":"0" },
        "score_list": [],
        "card_list": [],
        "substitution_list": []
    }
    
    team_name = get_team_names(corpus, team_name_set)
    summary["players"] = {"team1" : team_name[0], "team2" : team_name[1]}

    res = get_result(corpus)
    res_split = res.split("-")
    summary["score_board"] = {"score1" : res_split[0], "score2" : res_split[1]}
    
    for text in corpus:
        annotation = get_annotation(text, model)
        if annotation[0] == 1 or annotation[-1] == 1:
            #do something
            goal = { "player_name":"", "time":"", "team":"" }

            res = process_goal_info(text)

            if summary["players"]["team1"] in res["names"]:
                goal["team"] = summary["players"]["team1"]
            else:
                goal["team"] = summary["players"]["team2"]

            if len(res["time"]) != 0:
                goal["time"] = res["time"][0]
            
            for name in res["names"]:
                if name != summary["players"]["team1"] and name != summary["players"]["team2"]:
                    goal["player_name"] = name
                    break
            if goal["player_name"] != "" or goal["time"] != "":
                summary["score_list"].append(goal)
        if annotation[1] == 1:
            #do something
            # print(tags[1],process_match_info(text))
            pass
        if annotation[2] == 1:
            #do something
            # print(e.text)
            # res = process_match_result(text)
            # if len(res["result"]) != 0:
            #     split = res["result"][0].split("-")
            #     if len(split) == 2:
            #         if int(split[0]) + int(split[1]) > int(summary["score_board"]["score1"]) + int(summary["score_board"]["score2"]):
            #             summary["score_board"] = {"score1" : split[0], "score2" : split[1]}
            pass
        if annotation[3] == 1:
            #do something
            card = { "player_name":"", "time":"", "team":"" }

            res = process_card_info(text, team_name_set)

            if summary["players"]["team1"] in res["names"]:
                card["team"] = summary["players"]["team1"]
            else:
                card["team"] = summary["players"]["team2"]

            if len(res["time"]) != 0:
                card["time"] = res["time"][0]
            
            for name in res["names"]:
                if name != summary["players"]["team1"] and name != summary["players"]["team2"]:
                    card["player_name"] = name
                    break
            
            summary["card_list"].append(card)
        if annotation[4] == 1:
            #do something
            sub = { "player_in":"", "time":"", "player_out":"" }

            res = process_subtitutions(text, team_name_set)

            if len(res["time"]) != 0:
                sub["time"] = res["time"][0]
            
            for name in res["names"]:
                if name != summary["players"]["team1"] and name != summary["players"]["team2"]:
                    sub["player_in"] = name
                    break

            for name in res["names"]:
                if name != summary["players"]["team1"] and name != summary["players"]["team2"] and name != sub["player_in"]:
                    sub["player_out"] = name
                    break
            summary["substitution_list"].append(sub)
            pass
    return summary

if __name__ == "__main__":
    # Load model
    modelDir = argv[1]
    test_dir = argv[2]
    output_dir = argv[3]


    config = RobertaConfig.from_pretrained(
        "/content/PhoBERT_base_transformers/config.json",
        output_hidden_states=True,
        num_labels=6,
        add_pooling_layer=False   
    )
    # myRobertaForTokenClassification
    # RobertaForAIViVN
    model = RobertaForAIViVN.from_pretrained("/content/PhoBERT_base_transformers/model.bin", config=config)
    model = torch.load(modelDir)
    
    team_name_set = get_team_name_set('train.jsonl')

    jsonlist= []
    with jsonlines.open(test_dir) as f:
        for line in f:
            sequence = []
            sequence_doc = []
            lb_list = []
            # Original Doc
            od = line['original_doc']
            for k in od['_source']['body']:
                sequence_doc = sequence_doc + sent_tokenize(k['text'])
            res = origin_to_summary(sequence_doc,team_name_set, model = model)
            jsonlist.append({"test_id" : line["test_id"], "match_summary" : res})

    with jsonlines.open(output_dir, mode='w') as writer:
        writer.write_all(jsonlist)
