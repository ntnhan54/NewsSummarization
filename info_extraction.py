from underthesea import ner, word_tokenize, pos_tag
import re
from collections import Counter
import jsonlines
def get_team_name_set(dir):
    team_name_set = []
    with jsonlines.open(dir) as f:
        for line in f:
            ms = line["match_summary"]
            team_name_set.append(ms["players"]["team1"])
            team_name_set.append(ms["players"]["team2"])
    return set(team_name_set)
            

    
def get_team_names(corpus, team_name_set):
    all_token = []

    for text in corpus:
        tagged_sentence = pos_tag(text)
        names = []
        for i, comp in enumerate(tagged_sentence):
            if comp[1] == "Np":
                if i - 1 >= 0 and tagged_sentence[i - 1][1] == "Np":
                    names[-1] = names[-1] + " " + comp[0]
                else:
                    names.append(comp[0])
        all_token.extend(names[:])

    team_name = []
    top10 = Counter(all_token).most_common(10)
    for a in top10:
        if a[0] in team_name_set:
            for i, t in enumerate(team_name):
                if a[0].lower() in t.lower():
                    break
                elif t.lower() in a[0].lower():
                    team_name[i] = a[0]
                    break
            else:
                team_name.append(a[0])
                
        if len(team_name) == 2:
            break

    for a in top10:
        if len(team_name) == 2:
            break
        if a[0] not in team_name:
            team_name.append(a[0])

    return team_name

def get_result(corpus):
    res = "0-0"  
    sum_res = 0

    result_filter = re.compile(r" (\d-\d) |^(\d-\d) | (\d-\d)$")
    for text in corpus:
        candidate_res = result_filter.findall(text)
        for candidate in candidate_res:
            r = candidate[0] + candidate[1] + candidate[2]
            if len(r) == 0:
                pass
            sr = sum([int(x) for x in r.split("-")])
            if sr > sum_res:
                sum_res = sr
                res = r
    return res


def process_goal_info(text):
    res = {}
    # time_filter = re.compile(r"(\d?\d phút sau)|phút (\d?\d\+?\d)|(\d?\d\+?\d)'")
    time_filter = re.compile(r"(\d?\d phút sau)|phút (\d?\d\+?\d)|(\d?\d\+?\d)|(phút thứ \d+)")
    res["time"] = list(map(lambda x : [a for a in x if a != ""][0], time_filter.findall(text.lower())))
    

    tagged_sentence = ner(text)
    names = []
    for i, comp in enumerate(tagged_sentence):
        if comp[1] == "Np" and comp[3] == "B-PER":
            names.append(comp[0])
            j = i + 1
            while j < len(tagged_sentence) and tagged_sentence[j][3] == "I-PER":
                names[-1] = names[-1] + " " + tagged_sentence[j][0]
                j += 1
    res["names"] = names
    return res

def process_match_info(text):  
    res = {}  
    tagged_sentence = pos_tag(text)
    names = []
    for i, comp in enumerate(tagged_sentence):
        if comp[1] == "Np":
            if i - 1 >= 0 and tagged_sentence[i - 1][1] == "Np":
                names[-1] = names[-1] + " " + comp[0]
            else:
                names.append(comp[0])
    res["names"] = names
    return res

def process_match_result(text):  
    res = {}  
    result_filter = re.compile(r"\d-\d")
    result = result_filter.findall(text.replace(" ", ""))
    res["result"] = result
    return res

def process_card_info(text):
    res = {}  
    # time_filter = re.compile(r"(\d?\d phút sau)|phút (\d?\d\+?\d)|(\d?\d\+?\d)'")
    time_filter = re.compile(r"(\d?\d phút sau)|phút (\d?\d\+?\d)|(\d?\d\+?\d)|(phút thứ \d+)")
    res["time"] = list(map(lambda x : [a for a in x if a != ""][0], time_filter.findall(text.lower())))
    
    tagged_sentence = ner(text)
    names = []
    for i, comp in enumerate(tagged_sentence):
        if comp[1] == "Np" and comp[3] == "B-PER":
            names.append(comp[0])
            j = i + 1
            while j < len(tagged_sentence) and tagged_sentence[j][3] == "I-PER":
                names[-1] = names[-1] + " " + tagged_sentence[j][0]
                j += 1
    res["names"] = names
    return res

def process_subtitutions(text):
    res = {}  
    # time_filter = re.compile(r"(\d?\d phút sau)|phút (\d?\d\+?\d)|(\d?\d\+?\d)'")
    time_filter = re.compile(r"(\d?\d phút sau)|phút (\d?\d\+?\d)|(\d?\d\+?\d)|(phút thứ \d+)")
    res["time"] = list(map(lambda x : [a for a in x if a != ""][0], time_filter.findall(text.lower())))

    tagged_sentence = ner(text)
    names = []
    for i, comp in enumerate(tagged_sentence):
        if comp[1] == "Np" and comp[3] == "B-PER":
            names.append(comp[0])
            j = i + 1
            while j < len(tagged_sentence) and tagged_sentence[j][3] == "I-PER":
                names[-1] = names[-1] + " " + tagged_sentence[j][0]
                j += 1
    res["names"] = names
    return res