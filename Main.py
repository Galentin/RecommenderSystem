import ImportOpenEdu
import ImportStepik
import Select_topic_LDA
import Analysis
import Relevance_feedback
import WordProcessing
import pandas as pd
import sys
import LDA

if __name__ == '__main__':
    coursesList = pd.DataFrame(columns=['parameters', 'year', 'name', 'link', 'description', 'topic_id'])
    coursesList.index.name = "id"

    if len(sys.argv) > 1:
        if sys.argv[1] == "update":
            coursesList = ImportOpenEdu.import_courses(coursesList)
            coursesList = ImportStepik.import_courses(coursesList)
            coursesList.to_csv("./source/base_courses.csv")

            # for analysis quantity words in description before preprocessing
            Analysis.analysis_num_word(coursesList, "Исходные данные:")

            coursesList = WordProcessing.word_processing(coursesList)
            coursesList.to_csv("./source/finish_version.csv")
    else:

        #coursesList = pd.read_csv("./source/finish_version.csv").set_index('id')
        #print(coursesList)
        coursesList = pd.read_csv("./source/testing.csv").set_index('id')
        print(coursesList)

    #LDA.main(coursesList)
    Relevance_feedback.main(coursesList)
