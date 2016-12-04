import gensim
import logging
import re
import pickle
import itertools
import dicttoxml
from xml.dom.minidom import parseString


def generate_similarities(words, n, _model):
    result = {}
    for word in words:
        result[word] = _model.most_similar(word, topn=n)
    return result


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def refresh_cache(words, n, _model):
    cache = generate_similarities(words, n, _model)
    save_obj(cache, 'cache')


informations = {
    'personal': {
        'name': '',
        'last_name': '',
        'gender': '',
        'address': '',
        'postal_code': '',
        'phone': '',
        'email': '',
    },
    'education': [],
    'experience': '',
    'award': '',
    'interests': '',
    'skills': ''
}

education = {
    'graduation_school': '',
    'degree': '',
    'major': ''
}


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
model = gensim.models.Word2Vec.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)

blocks = {key: [] for key in informations.keys()}
current = 'personal'

# refresh_cache(blocks.keys(), 15, model)

tops = load_obj('cache')
keys = list(blocks.keys())

all_tops = []
for x in keys:
    all_tops.extend([first for first, secound in tops[x]])

# stage 1
with open('resume.txt', 'r') as file:
    for line in file:
        line = line.rstrip()
        first, *rest = line.split(' ')
        first = first.lower()
        if first in blocks.keys():
            if len(line.split(' ')) < 4 and not line.split(' ')[-1][-1] == '.':
                current = first
        else:
            for key in keys:
                if first in [_first for _first, _secound in tops[key]]:
                    current = key
            if line not in blocks[current] and line.lower() not in all_tops:
                blocks[current].append(line)

# stage 2
email_pattern = re.compile(r'[^@]+@[^@]+\.[^@]+')
postal_code_pattern = re.compile(r'\d\d\-\d\d\d')
phone_pattern = re.compile(r'\d\d\d\-\d\d\d\-\d\d\d')

blocks['personal'] = list(itertools.chain(*[item.split() for item in blocks['personal']]))
to_delete = []
for value in blocks['personal']:
    if re.match(email_pattern, value):
        informations['personal']['email'] = value
        to_delete.append(value)
    elif re.match(postal_code_pattern, value):
        informations['personal']['postal_code'] = value
        to_delete.append(value)
    elif re.match(phone_pattern, value):
        informations['personal']['phone'] = value
        to_delete.append(value)

for x in to_delete:
    blocks['personal'].remove(x)
to_delete.clear()

for index, value in enumerate(blocks['personal']):
    man_score = model.similarity(value, "John")
    woman_score = model.similarity(value, "Catherine")
    if man_score > 0.5 or woman_score > 0.5:
        informations['personal']['name'] = value
        informations['personal']['last_name'] = blocks['personal'][index + 1]
        to_delete.extend([value, blocks['personal'][index + 1]])
        if man_score >= woman_score:
            informations['personal']['gender'] = 'male'
        else:
            informations['personal']['gender'] = 'female'
        break

for x in to_delete:
    blocks['personal'].remove(x)

informations['personal']['address'] = ' '.join([item for item in blocks['personal']])
informations['experience'] = ' '.join([item for item in blocks['experience']])
informations['award'] = ' '.join([item for item in blocks['award']])
informations['interests'] = ' '.join([item for item in blocks['interests']])
informations['skills'] = ' '.join([item for item in blocks['skills']])

values = list(itertools.chain(*[words.split() for words in blocks['education']]))
for value in values:
    value = value.rstrip()
for index, value in enumerate(values):
    if value == 'degree':
        education['degree'] = values[index - 1]
    elif value == 'of':
        _iter = 1
        education['graduation_school'] = 'of'
        while values[index - _iter][0].isupper():
            education['graduation_school'] = values[index - _iter] + ' ' + education['graduation_school']
            _iter += 1
        _iter = 1
        while values[index + _iter][0].isupper():
            education['graduation_school'] = education['graduation_school'] + ' ' + values[index + _iter]
            _iter += 1
    elif value == 'in':
        _iter = 1
        while not values[index + _iter][-1] == '.':
            education['major'] += ' ' + values[index + _iter]
            _iter += 1
        education['major'] += ' ' + values[index + _iter][:-1]
        informations['education'].append(education)
        education = {
            'graduation_school': '',
            'degree': '',
            'major': ''
        }


# save informations to xml
xml = dicttoxml.dicttoxml(informations, custom_root="Person")
dom = parseString(xml)
with open('result.xml', 'w') as xml_file:
    xml_file.write(dom.toprettyxml())



