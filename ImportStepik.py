import requests
import json
import re
import numpy as np
from langdetect import detect


def import_courses(coursesList):
    index = 0
    if coursesList.last_valid_index() is not None:
        index = 1 + coursesList.last_valid_index()
    has_next_page = True
    page = 1

    while has_next_page:

        courses_json = requests.get("https://stepic.org/api/courses", params={'page': page, 'language': 'ru', 'is_paid': False}).json()
        has_next_page = courses_json['meta']['has_next']
        page += 1
        courses_json = courses_json['courses']

        for i in range(0, len(courses_json)):
            try:
                link = 'https://stepic.org/course/' + str(courses_json[i]['id'])
                accessibility = requests.head(link)
                if accessibility.status_code == 404:
                    continue
                name = courses_json[i]['title'].lower()
                name_split = re.search(r'\b\d-\d\b|\d+.*класс\w*|\b\d{1,2}\s\w\b', name)
                stop_words = ['ЕГЭ', 'егэ', 'лет', 'детей', 'школьников', 'старшеклассников', 'ОГЭ', 'огэ']
                mask = [courses_json[i]['title'].find(j) != -1 for j in stop_words]
                if name_split is not None or np.any(mask):
                    continue

                description = ''

                if courses_json[i]['summary'] is not None:
                    description += courses_json[i]['summary']
                if courses_json[i]['requirements'] is not None:
                    description += courses_json[i]['requirements']
                if courses_json[i]['target_audience'] is not None:
                    description += courses_json[i]['target_audience']
                if courses_json[i]['description'] is not None:
                    description += courses_json[i]['description']
                sections_url = 'https://stepik.org/api/sections?{}'.format(
                    '&'.join('ids[]={}'.format(obj_id) for obj_id in courses_json[i]['sections']))
                sections_json = requests.get(sections_url).json()
                sections_json = sections_json['sections']
                for j in range(0, len(sections_json)):
                    description += sections_json[j]['title'] + '. '
                if courses_json[i]['total_units'] != 0:
                    lessons = requests.get('https://stepic.org:443/api/lessons',
                                           params={'language': 'ru', 'course': courses_json[i]['id']}).json()
                    lessons = lessons['lessons']
                    for k in range(0, len(lessons)):
                        description += lessons[k]['title'] + '. '

                len_words = description.split()

                if len(len_words) < 50:
                    continue

                language = detect(description)

                if language != 'ru':
                    continue

                target_aud = courses_json[i]['target_audience'].lower()
                target_aud_split = re.search(r'\d+.*класс\w*|\b\d{1,2}\s\w\b|дет\w{1,2}', target_aud)
                mask = [courses_json[i]['target_audience'].find(j) != -1 for j in stop_words]
                if target_aud_split is not None or np.any(mask):
                    continue

                coursesList.loc[index, 'name'] = courses_json[i]['title']
                coursesList.loc[index, 'parameters'] = str(courses_json[i]['id'])
                coursesList.loc[index, 'link'] = link
                coursesList.loc[index, 'description'] = description

                index += 1
            except json.decoder.JSONDecodeError:
                continue

    return coursesList
