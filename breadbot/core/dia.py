import random
import re
import string
import Levenshtein as Leven

from breadbot.core import common

JARO_WINKLER_PERCENT = 0.98


@common.time_limit(3)
def response(db, user, in_str):
    in_str = common.que_init(in_str)
    ans = ''
    colls = db.collection_names()
    random.shuffle(colls)
    for coll in colls:
        if coll[-4:] != '_yml':
            continue
        reqs = db[coll].find_one({'tag': 'dia'})
        if not reqs:
            continue
        qas = reqs['qas']
        if not qas:
            continue
        random.shuffle(qas)
        for qa in qas:
            ques = qa['que']
            random.shuffle(ques)
            for que in ques:
                que = str(que)
                que = common.que_init(que)
                if Leven.jaro_winkler(in_str, que) > JARO_WINKLER_PERCENT:
                    ans = qa['ans']
                    if type(ans) is list:
                        ans = random.choice(ans)
                    return ans
    return ans
