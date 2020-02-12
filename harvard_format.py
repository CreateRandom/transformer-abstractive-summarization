import argparse
import os
import re
import pickle as pkl
from nltk import word_tokenize, sent_tokenize

# import stanfordnlp

# nlp = stanfordnlp.Pipeline(processors='tokenize', lang='en', use_gpu=False)
# def stanford_tokenize(text):
#     # tackle the case of they said.' --> they said . '
#     text = re.sub('\'\.','\' .',text)
#
#
#     doc = nlp(text)
#     tokens = []
#     for i, sentence in enumerate(doc.sentences):
#         for token in sentence.tokens:
#             # match = re.match('(\'|\'\')([^s])', token.text)
#             # if match:
#             #     tokens.extend(match.groups())
#             # else:
#             tokens.append(token.text)
#     return tokens

def nltk_tokenize(text):
    # tackle the case of they said.' --> they said . '
    text = re.sub(r'\'\.',r'\' .',text)

    text = re.sub(r'^\'(\w)',r'\' \1 .',text)
    text = re.sub(r' \'(\w)', r" ' \1", text)

    sents = text.split('\n')
    all_tokens = []
    for sent in sents:
        sent_tokens = word_tokenize(sent, language='english')
        if sent_tokens:
            if sent_tokens[-1] is not '.' and sent_tokens[-1] is not '…' and sent_tokens[-1] is not '\'':
                sent_tokens.append('.')
            all_tokens.extend(sent_tokens)


    return all_tokens

def main(args):
    id_to_story_mapping = {}
    count = 0
    paths = [args.dailymail, args.cnn]
    story_lines = []
    highlight_lines = []
    for path in paths:
        for file in os.listdir(path):
            print(file.rstrip('.story'))
            id_to_story_mapping[count] = file.rstrip('.story')
            count = count + 1
            with open(os.path.join(path, file)) as f:
                lines = f.readlines()
                story, highlights = extract_story_and_highlights(lines)
                story = story.lower()
                story_tokens = nltk_tokenize(story)
                story_tokens = clean_tokens(story_tokens)
                # merge to single-line string
                story_line = ' '.join(story_tokens)
                story_lines.append(story_line)
                # merge the highlights?
                hl_lines = []
                for highlight in highlights:
                    highlight = highlight.lower()
                    hl_tokens = nltk_tokenize(highlight)
                    hl_tokens = clean_tokens(hl_tokens)
                    hl_line = ' '.join(hl_tokens)
                #    hl_line = wrap_in_tag(hl_line,'t')
                    hl_lines.append(hl_line)
                highlight_line = ' '.join(hl_lines)
                if not highlight_line:
                    highlight_line = '\n'
                highlight_lines.append(highlight_line)

    src_path = os.path.join(args.export_path, 'test.txt.src')
    tgt_path = os.path.join(args.export_path, 'test.txt.tgt.tagged')

    with open(src_path, 'w') as f:
        f.write('\n'.join(story_lines))

    with open(tgt_path, 'w') as f:
        f.write('\n'.join(highlight_lines))

    pkl_path = os.path.join(args.export_path, 'id_to_story_dict.pkl')

    with open(pkl_path, 'wb') as f:
        pkl.dump(id_to_story_mapping,f)


def clean_tokens(tokens):
    single_open = False
    double_open = False
    new_tokens = []

    for token in tokens:
        new_token, single_open, double_open = clean_token(token, single_open, double_open)
        new_tokens.append(new_token)
    return new_tokens

mapping = dict(zip('( ) [ ] { }'.split(), '-lrb- -rrb- -lsb- -rsb- -lcb- -rcb-'.split(), ))

# TODO implement this
def clean_token(token, single_open, double_open):
    if token in mapping:
        return mapping[token], single_open, double_open


    if token is '\'':
        to_return = '`' if not single_open else token
        return to_return, not single_open, double_open
    if token is '\"':
        to_return = '``' if not double_open else '\'\''
        return to_return, single_open, not double_open

    return token, single_open, double_open

def wrap_in_tag(text, tag):
    return '<' + tag + '>' + text + '</' + tag + '>'

def extract_story_and_highlights(lines):

    story = None
    highlights = None

    # find first highlight (if any)
    try:
        highlight_start = lines.index('@highlight\n')
    except ValueError:
        highlight_start = len(lines)

    story_lines = lines[:highlight_start]
    story_lines = [x for x in story_lines if x != '\n']
    # TODO think about xa0 character
    story = ''.join(story_lines)

    highlight_lines = lines[highlight_start:]
    highlight_lines = [x for x in highlight_lines if x != '\n' and x != '@highlight\n']

    return story, highlight_lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('cnn', metavar='cnn', type=str)
    parser.add_argument('dailymail', metavar='dm', type=str)
    parser.add_argument('export_path', type=str)
    args = parser.parse_args()
    print(args)
    main(args)
