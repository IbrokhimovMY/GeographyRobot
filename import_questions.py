import pandas as pd

from database import add_user_question

def import_questions():
    questions = pd.read_excel('questions.xlsx')

    letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    for index, row in questions.iterrows():
        question = row['Savol']
        answer_a = row["A varianti (TO'G'RI)"]
        answer_b = row['B varianti']
        answer_c = row['C varianti']
        answer_d = row['D varianti']
        correct = letter_to_index[row["To'g'ri javob"]]


        add_user_question(author_id="5138960130",
                          author_name='Tester admin',
                          question=question,
                          opts=[answer_a, answer_b, answer_c, answer_d],
                          correct= correct,
                          lang= "uz",
                          )


if __name__ == '__main__':
    import_questions()


