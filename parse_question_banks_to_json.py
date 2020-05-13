# -*- coding: UTF-8 -*-
import re
from pathlib import Path

import json


def parseQuestionsFromTxt(questionBanksI):
    questionBanksI = questionBanksI.replace('（', '(')
    questionBanksI = questionBanksI.replace('）', ')')
    questionBanksI = re.sub(r'((?<=[^(\[]) )|( (?=[^)\]]))', '', questionBanksI)
    questionBanksI = re.sub(r'(?<![^\n]\n)\( \)', '', questionBanksI)
    questionBanksI = re.sub(r'((?<=[^0-9])\.)|(\.(?=[^0-9]))', '', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'[^\u4e00-\u9fa5. ()\[\]a-zA-Z0-9\n]', '', questionBanksI)
    questionBanksI = re.sub(r'(?<=[^\n]\n)([ABCDEFG])', r'`\1`', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'(?<=\n\n)[0-9]+\.?', '', questionBanksI)
    questionBanksI = re.sub(r'^[0-9]+\.?', '', questionBanksI)
    questionBanksI = re.sub(r'(?<=[^\n]\n)[(\[]([Xx ])[)\]]', r'`\1`', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'(参考)?答案?(?P<answer>[ABCDEFG对错]+)$', r'`!\g<answer>`!', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'(参考)?答案?(?P<answer>[对错])$', r'`!\g<answer>`!', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'\((?P<answer>[ABCDEFG]+)\)', r'`!\g<answer>`!', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'[\[\]()]', '', questionBanksI)
    questionBanksI = re.sub('\n{3,}', '\n\n', questionBanksI)
    questionBanksI = re.sub('\n+$', '', questionBanksI)
    questionsBanksDict = {}

    questionBanksII = questionBanksI.split('\n\n')
    for questionBank in questionBanksII:
        question = None  # 题目
        options = None  # 选项
        answers = None  # 答案
        lines = questionBank.split('\n')
        searchAnswerInFirst = re.findall(r'`!(.+?)`!', lines[0])
        searchAnswerInLast = re.search(r'`!(.+?)`!', lines[-1])
        if len(searchAnswerInFirst) != 0:
            question = re.sub(r'`!.+?`!', '', lines[0])
            answers = []
            for answer in searchAnswerInFirst:
                for char in answer:
                    answers.append(char)
        else:
            question = lines[0]
            if searchAnswerInLast is not None:
                answers = searchAnswerInLast.group(1)
        if searchAnswerInLast is not None:
            options = lines[1:-1]
        else:
            options = lines[1:]
        nextQuestionBank = False
        # 纠正错误分割的题目
        for index, option in enumerate(options):
            searchIndex = re.search(r'^`(ABCDEFG)`', option)
            if searchIndex is not None and ord(option[0]) + 17 != index + 48:
                questionBanksII.append(questionBank.replace('\n{}'.format(option), option))
                nextQuestionBank = True
                break
        if nextQuestionBank:
            continue
        if answers is None:
            answers = []
            for indexI, optionI in enumerate(options):
                searchIndexI = re.search(r'^`(.)`', optionI)
                if searchIndexI is not None:
                    if searchIndexI.group(1) != ' ':
                        answers.append(str(indexI))  # 0, 1, 2
        if len(answers) == 0:
            answers.append('2')
        for indexII, optionII in enumerate(options):
            options[indexII] = re.sub(r'^`.`', '', optionII)
        if answers == '对':
            answers = ['0']
        elif answers == '错':
            answers = ['1']
        elif re.search(r'[0-9]', answers[0]) is None:
            # ord('0') - ord('A') = 17
            answers = [chr(ord(i) - 17) for i in answers]
        options.sort()  # 保证统一
        # {'题目_选项': ['0', '1', '2']}
        questionsBanksDict['_'.join((question, *options))] = answers

    return questionsBanksDict


def parseQuestionsFromHtml(questions):
    questions = re.split(r'<div style=".+?" class="cls_003"><span class="cls_003">'
                         r'[0-9]+</span><span[\n\s]+?class="cls_002">、', questions)
    del questions[0]
    del questions[-1]
    questions = {}
    for question in questions:
        # 答案标签 class
        answers = re.findall(r'<span[\n\s]+class="cls_005">(.+?)</span>'
                             r'([\n\s]*<span[\n\s]+class="cls_007">(.+?)</span>)?', question)
        # 合并
        answers = [answer[0] + answer[2] for answer in answers]
        # 移除空白填空
        question = re.sub(r'<span[\n\s]+class="cls_00[57]">.+?</span>', '', question)
        question = re.sub(r'<.+?>', '', question, flags=re.S)
        # 只保留汉字,数字,字母等字符, 适用于填空题
        question = re.sub(r'[^\u4e00-\u9fa5.a-zA-Z0-9]', '', question)
        questions[question] = answers
    return questions


questionBanks = {}
for file in Path('Question-Banks').iterdir():
    with file.open('r', encoding='UTF-8') as stream:
        if file.suffix == '.html':
            questionBanks = {**questionBanks, **parseQuestionsFromHtml(stream.read())}
        else:
            questionBanks = {**questionBanks, **parseQuestionsFromTxt(stream.read())}
path = Path('Question-Banks.json')
path.touch()
with path.open('r+', encoding='UTF-8') as file:
    content = file.read()
    if content == '':
        questionBanksO = {'collected': {}}
    else:
        questionBanksO = json.loads(content)
    questionBanksO['parsed'] = questionBanks
    file.truncate(0)
    json.dump(questionBanksO, file, indent=4, ensure_ascii=False)
