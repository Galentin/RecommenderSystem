def analysis_num_word(list_descriptions, event):
    num_50 = 0
    num_100 = 0
    num_150 = 0
    num_else = 0
    average = 0
    for i in range(0, (list_descriptions.last_valid_index() + 1)):
        a = list_descriptions.loc[i, 'description'].split()
        average += len(a)
        if len(a) < 50:
            num_50 += 1
        elif len(a) < 100:
            num_100 += 1
        elif len(a) < 150:
            num_150 += 1
        else:
            num_else += 1

    print(event)
    print("Меньше 50 слов:", num_50)
    print("От 50 до 100 слов:", num_100)
    print("От 100 до 150 слов:", num_150)
    print("Больше 150 слов:", num_else)
    print("Среднее число слов:", average / (list_descriptions.last_valid_index() + 1), "\n")
