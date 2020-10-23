import re
import Analysis
from nltk.corpus import stopwords as nltk_stopwords
import pymorphy2


first_block_stop_words = ['который', 'твой', 'сих', 'свой', 'твоя', 'этими', 'слишком', 'нами', 'всему', 'будь', 'саму',
                          'чаще', 'ваше', 'сами', 'наш', 'затем', 'еще', 'самих', 'наши', 'тут', 'каждое', 'мочь',
                          'весь', 'этим', 'наша', 'своих', 'оба', 'зато', 'те', 'этих', 'вся', 'ваш', 'такая', 'теми',
                          'ею', 'которая', 'нередко', 'каждая', 'также', 'чему', 'собой', 'самими', 'нем', 'вами', 'ими',
                          'откуда', 'такие', 'тому', 'та', 'очень', 'сама', 'нему', 'оно', 'этому', 'кому', 'тобой',
                          'таки', 'твоё', 'каждые', 'твои', 'мой', 'нею', 'самим', 'ваши', 'ваша', 'кем', 'мои', 'однако',
                          'сразу', 'свое', 'ними', 'всё', 'неё', 'тех', 'хотя', 'всем', 'тобою', 'тебе', 'одной', 'другие', 'эта',
                          'само', 'эта', 'буду', 'самой', 'моё', 'своей', 'такое', 'всею', 'будут', 'своего', 'кого',
                          'свои', 'мог', 'нам', 'особенно', 'её', 'самому', 'наше', 'кроме', 'вообще', 'вон', 'мною',
                          'никто', 'это', 'либо', 'какой', 'именно', 'некоторый', '–', '-']

secondary_block_stop_words = ['понятие', 'задача', 'работа', 'модуль', 'задание', 'тема', 'знание', 'основной', 'лекция',
                              'решение', 'тест', 'урок', 'вариант', 'другой', 'stepik', 'каждый', 'поэтому', 'данный', 'курс',
                              'course', 'lesson', 'общий', 'org', 'иметь', 'например', 'какой', 'часть', 'тест', 'test',
                              'короче', 'вопрос', 'пример', 'примерный', 'билет', 'зачет', 'экзамен', 'зачёт', 'экзаменационный', 'контрольный', 'nbsp']


def word_processing(list_descriptions):
    stop_words = nltk_stopwords.words('russian') + nltk_stopwords.words('english') + first_block_stop_words + secondary_block_stop_words

    morph = pymorphy2.MorphAnalyzer()

    for i in range(0, (list_descriptions.last_valid_index() + 1)):

        # convert string to lowercase
        list_descriptions.loc[i, 'description'] = list_descriptions.loc[i, 'description'].lower()

        # delete html tags
        list_descriptions.loc[i, 'description'] = re.sub(r'\<[^>]*\>', ' ', list_descriptions.loc[i, 'description'])
        list_descriptions.loc[i, 'description'] = re.sub(r'&[a-zA-Z]*', ' ', list_descriptions.loc[i, 'description'])

        # delete punctuation marks
        list_descriptions.loc[i, 'description'] = re.sub(r'[\r\t\n\.,«»\/#!\$%\^&\*;:"{}№=_`~()\?\+]', ' ', list_descriptions.loc[i, 'description'])

        # delete number and tags
        list_descriptions.loc[i, 'description'] = re.sub(r'(?:\s\d+\b|&\w+)', ' ', list_descriptions.loc[i, 'description'])

        # delete single characters
        list_descriptions.loc[i, 'description'] = re.sub(r'\b[а-яА-я]\b', ' ', list_descriptions.loc[i, 'description'])

        # lemmetize words
        lemmas = (morph.parse(j)[0].normal_form for j in list_descriptions.loc[i, 'description'].split())

        # delete stop words
        list_descriptions.loc[i, 'description'] = ' '.join(j for j in lemmas if j not in stop_words)


    Analysis.analysis_num_word(list_descriptions, "После первичной чистки (удаление стоп-слов и лемматизация)")

    return list_descriptions
