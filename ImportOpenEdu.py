import requests
import json
import numpy as np
import re
from langdetect import detect

def import_courses(coursesList):
    next_page = "https://courses.openedu.ru/api/courses/v1/courses/"
    course_url = "https://openedu.ru/api/courses/export/"
    index = 0

    while next_page is not None:

        courses_json = requests.get(next_page).json()
        next_page = courses_json['pagination']['next']
        courses_json = courses_json['results']

        # add courses from one page
        for i in range(0, len(courses_json)):

            # remove duplicates of different years
            if np.all(coursesList['parameters'] != (courses_json[i]['org'] + courses_json[i]['number'])):
                try:
                    name = courses_json[i]['name'].lower()
                    name_split = re.search(r'\b\d-\d\b|\d+.*класс\w*|\b\d{1,2}\s\w\b', name)
                    stop_words = ['ЕГЭ', 'егэ', 'лет', 'детей', 'школьников', 'старшеклассников', 'ОГЭ', 'огэ']
                    mask = [courses_json[i]['name'].find(j) != -1 for j in stop_words]
                    if name_split is not None or np.any(mask):
                        continue
                    course = requests.get((course_url + courses_json[i]['org'] + '/'
                                           + courses_json[i]['number'] + '?format=json')).json()
                    if 'external_url' not in course:
                        continue
                    accessibility = requests.head(course['external_url'])
                    if accessibility.status_code == 404:
                        continue
                    if course['language'] != 'ru':
                        continue

                    description = ''

                    if course['description'] is not None:
                        description += course['description']
                    if course['results'] is not None:
                        description += (course['results'])
                    if course['competences'] is not None:
                        description += course['competences']
                    if course['content'] is not None:
                        description += course['content']

                    len_words = description.split()

                    if len(len_words) < 50:
                        continue

                    language = detect(description)

                    if language != 'ru':
                        continue

                    coursesList.loc[index, 'link'] = course['external_url']
                    coursesList.loc[index, 'parameters'] = courses_json[i]['org'] + courses_json[i]['number']
                    coursesList.loc[index, 'name'] = courses_json[i]['name']
                    coursesList.loc[index, 'description'] = description
                    coursesList.loc[index, 'year'] = courses_json[i]['start']

                    index += 1
                except json.decoder.JSONDecodeError:
                    continue
            else:
                j = coursesList.parameters[
                    coursesList.parameters == courses_json[i]['org'] + courses_json[i]['number']].index.tolist()[0]
                if coursesList.loc[j, 'year'] < courses_json[i]['start']:
                    coursesList.loc[j, 'year'] = courses_json[i]['start']
                    coursesList.loc[j, 'name'] = courses_json[i]['name']
    return coursesList
