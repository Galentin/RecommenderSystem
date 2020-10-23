from gensim.models import Phrases
from gensim.models.phrases import Phraser
from gensim.corpora.dictionary import Dictionary
from gensim.models.ldamulticore import LdaMulticore as LDA
from gensim.models import CoherenceModel
from sklearn.metrics.pairwise import linear_kernel
import psycopg2
import pyLDAvis.gensim
import warnings
import WordProcessing
import pandas as pd
import config
import numpy as np

connection = psycopg2.connect(host='127.0.0.1', user='postgres', password='s2128506', dbname='Test')
cursor = connection.cursor()


def main(coursesList):
    lda = LDA.load("./best_model.lda")
    dictionary = Dictionary.load("best_model.lda.id2word")
    bigrams = Phraser.load("./bigram_model.pkl")
    trigrams = Phraser.load("./trigram_model.pkl")
    text_clean = [doc.split(' ') for doc in coursesList['description']]
    corpus = [dictionary.doc2bow(text) for text in text_clean]
    create_vector_topics(lda,corpus,dictionary,coursesList)
    courses_topic = config.matrix_courses_topic.to_numpy()

    #lda, dictionary, bigrams, trigrams = create_LDA_model(coursesList)
    #courses_topic = config.matrix_courses_topic.to_numpy()

    cursor.execute("select id from auth_group")
    id_groups = cursor.fetchall()
    for i in id_groups:
        cursor.execute("select distinct studyplan_id from students where group_id = %(id)s ", {'id': i[0]})
        studyplan_id = cursor.fetchall()
        for j in studyplan_id:
            subject_list = pd.DataFrame(columns=['id_subject', 'description'])
            subject_list = WordProcessing.word_processing(get_work_program(j[0], subject_list))
            #for k in subject_list:
            token_stud_prog = [program.split(' ') for program in subject_list['description']]
            #token_stud_prog = add_n_grams(token_stud_prog, bigrams, trigrams)
            prog_corp = [dictionary.doc2bow(program) for program in token_stud_prog]
            topic_prog = lda.get_document_topics(prog_corp)
            for l in range(0, len(topic_prog)):
                profile_student = np.zeros(config.num_lda_topic)
                dense_topic_prog = np.zeros(config.num_lda_topic)
                for m in topic_prog[l]:
                    dense_topic_prog[m[0]] += m[1]
                #mask = np.argsort(dense_topic_prog)[::-1][:1]
                #profile_student[mask] += 1
                profile_student = dense_topic_prog
                cosine_similarities = linear_kernel(profile_student.reshape(1, -1), courses_topic).flatten()
                top_courses = np.where(cosine_similarities >= 0.2)[0]
                print(subject_list.loc[l, 'id_subject'])
                #print(top_courses)
                print(coursesList.loc[top_courses, 'name':'link'])

            #cursor.execute("select id from students where group_id = %(group_id)s and studyplan_id = %(studyplan_id)s",
            #               {'group_id': i[0], 'studyplan_id': j[0]})
            #student_id = cursor.fetchall()
            #for k in student_id:
            #    cursor.execute("select subject from recommend_stud where student_id = %(id)s ", {'id': k[0]})
            #    subject_id = cursor.fetchone()[0]
            #    stud_priorities = pd.DataFrame(columns=['id_subject', 'description'])
            #    for l in range(0, len(subject_id)):
            #        stud_priorities.loc[l, :] = subject_list.loc[
            #            subject_list['id_subject'] == subject_id[l]['id']].values
            #    token_stud_prog = [program.split(' ') for program in stud_priorities['description']]
            #    token_stud_prog = add_n_grams(token_stud_prog, bigrams, trigrams)
            #    prog_corp = [dictionary.doc2bow(program) for program in token_stud_prog]
            #    topic_prog = lda.get_document_topics(prog_corp)
            #    profile_student = np.zeros(config.num_lda_topic)
            #    for l in range(0, len(topic_prog)):
            #        dense_topic_prog = np.zeros(config.num_lda_topic)
            #        for m in topic_prog[l]:
            #            #dense_topic_prog[m[0]] += m[1]
            #            profile_student[m[0]] += m[1]
            #        #mask = np.argsort(dense_topic_prog)[::-1][:1]
            #        #profile_student[mask] += 1
            #    profile_student = profile_student / (len(topic_prog))
            #    mask = np.argsort(linear_kernel(profile_student.reshape(1, -1), courses_topic).flatten())[::-1][:20]
            #    print(coursesList.loc[mask, 'name':'link'])

def create_LDA_model(coursesList):
    warnings.filterwarnings('ignore')
    text_clean = [doc.split(' ') for doc in coursesList['description']]
    bigrams, trigrams = create_n_grams(text_clean)
    text_clean = add_n_grams(text_clean, bigrams, trigrams)

    id2word = Dictionary(text_clean)
    id2word.filter_extremes(no_below=5, no_above=0.45)
    corpus = [id2word.doc2bow(text) for text in text_clean]

    num_topics = config.num_lda_topic
    lda_model = LDA(corpus=corpus,
                    id2word=id2word,
                    num_topics=num_topics,
                    random_state=42,
                    alpha='asymmetric',
                    passes=25)
    lda_model.save("./best_model.lda")
    coherence_model_c_v = CoherenceModel(model=lda_model, texts=text_clean, dictionary=id2word, coherence='c_v')
    c_v = coherence_model_c_v.get_coherence()
    term_topic_mat = lda_model.get_topics()
    aver_cosine_similarities = 0
    for i in range(0, (num_topics - 1)):
        cosine_similarities = linear_kernel(term_topic_mat[i].reshape(1, -1), term_topic_mat[i + 1:]).flatten()
        aver_cosine_similarities += sum(cosine_similarities)
    if num_topics != 1:
        aver_cosine_similarities = aver_cosine_similarities / (num_topics * (num_topics - 1) / 2)
    print(c_v)
    print(aver_cosine_similarities)

    create_vector_topics(lda_model, corpus, id2word, coursesList)

    visual_data = pyLDAvis.gensim.prepare(lda_model, corpus, id2word)
    pyLDAvis.save_html(visual_data, 'topics.html')
    return lda_model, id2word, bigrams, trigrams


def create_vector_topics(model, corpus, dictiosnary, coursesList):
    probability_doc_topics = model.get_document_topics(corpus)
    for i in range(0, len(corpus)):
        best_topic = 0
        prob_best_topic = 0
        for j in probability_doc_topics[i]:
            config.matrix_courses_topic.loc[i, j[0]] = j[1]
            if j[1] > prob_best_topic:
                best_topic = j[0]
                prob_best_topic = j[1]
        coursesList.loc[i, 'topic_id'] = best_topic
    config.matrix_courses_topic = config.matrix_courses_topic.fillna(0)
    config.matrix_courses_topic.to_csv("./source/matrix_doc_top.csv", index=False)


def create_n_grams(text):
    bigram = Phrases(text, min_count=20, threshold=10, delimiter=b' ')
    bigram_phraser = Phraser(bigram)
    bigram_phraser.save("./bigram_model.pkl")
    tokens_bigram = bigram_phraser[text]
    trigram = Phrases(tokens_bigram, min_count=10, threshold=10, delimiter=b' ')
    trigram_phraser = Phraser(trigram)
    trigram_phraser.save("./trigram_model.pkl")
    tokens_trigram = trigram_phraser[tokens_bigram]
    return tokens_bigram, tokens_trigram


def add_n_grams(text, bigrams, trigrams):
    for id in range(len(text)):
        for token in bigrams[id]:
            if token.count(' ') == 1:
                text[id].append(token)
        for token in trigrams[id]:
            if token.count(' ') == 2:
                text[id].append(token)
    return text


def get_work_program(id_studyplan, subject_list):
    index = -1
    cursor.execute("""
            with study_plan as(
                select id,name,rpd_id 
                from studyplan_programblock 
                where study_plan_id = %(id)s and rpd_id is not null
            ) 
            select distinct study_plan.id, content, number 
            from rpd_workprogramsection 
            inner join study_plan 
            on rpd_workprogramsection.work_program_id = study_plan.rpd_id 
            where number = '1.2' or number = '11.2' or title = 'Содержание и результаты обучения'""",
                   {'id': id_studyplan})
    for i in cursor.fetchall():
        if np.all(subject_list['id_subject'] != i[0]):
            if index == -1 or subject_list.loc[index, 'description'] != '':
                index += 1
            subject_list.loc[index, 'id_subject'] = i[0]
            subject_list.loc[index, 'description'] = ''
        if i[2] == '11.2':
            if 'content' in i[1]:
                subject_list.loc[index, 'description'] += i[1]['content']
        else:
            if 'sections' in i[1]:
                for k in i[1]['sections']:
                    subject_list.loc[index, 'description'] += k['name'] + '. '

    return subject_list
