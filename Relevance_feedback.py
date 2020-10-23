from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import psycopg2
import numpy as np
import WordProcessing


connection = psycopg2.connect(host='127.0.0.1', user='postgres', password='s2128506', dbname='Test')
cursor = connection.cursor()


def main(coursesList):
    create_tables()

    tf = TfidfVectorizer(analyzer='word',min_df=5, max_df=0.5, ngram_range=(1, 3))
    tfidf_courses = tf.fit_transform(coursesList['description'].values.astype('U'))

    cursor.execute("select id from auth_group")
    id_groups = cursor.fetchall()
    for i in id_groups:
        cursor.execute("select distinct studyplan_id from students where group_id = %(id)s ", {'id': i[0]})
        studyplan_id = cursor.fetchall()
        for j in studyplan_id:
            subject_list = pd.DataFrame(columns=['id_subject', 'description'])
            subject_list = WordProcessing.word_processing(get_work_program(j[0], subject_list))
            tfidf_priorities = tf.transform(subject_list['description'])
            dense = tfidf_priorities.todense()
            denselist = dense.tolist()
            for l in range(0, len(denselist)):
                cosine_similarities = linear_kernel(dense[l], tfidf_courses).flatten()
                #top_courses = np.argsort(cosine_similarities)[::-1][:3]
                top_courses = np.where(cosine_similarities >= 0.2)[0]
                cursor.execute("INSERT INTO studyplan_programblock_recommend (studyplan_programblock_id, courses) VALUES (%(id)s, %(courses)s)", {'id': subject_list.loc[l, 'id_subject'], 'courses': (coursesList.loc[top_courses, 'name':'link']).to_json(orient='records', force_ascii=False)})
                print(subject_list.loc[l, 'id_subject'])
                print(coursesList.loc[top_courses, 'name':'link'])
            connection.commit()


def create_tables():
    cursor.execute("""DROP TABLE IF EXISTS studyplan_programblock_recommend""")
    cursor.execute("""
    CREATE TABLE studyplan_programblock_recommend(
        studyplan_programblock_id INT NOT NULL,
        courses JSON 
    );
    ALTER TABLE studyplan_programblock_recommend
        ADD FOREIGN KEY (studyplan_programblock_id) REFERENCES studyplan_programblock(id)
    ;""")
    connection.commit()


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
        where number = '1.2' or number = '11.2' or title = 'Содержание и результаты обучения'""", {'id': id_studyplan})
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
