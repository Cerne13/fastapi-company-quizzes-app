import csv
import os

from app.schemas.quiz_schemas import RedisQuizResults


def write_to_csv(results: RedisQuizResults, filename):
    path = os.path.abspath(os.path.dirname(__file__))
    filename = filename
    file_path = os.path.join(path, filename)

    with open(file_path, 'w', newline='') as csv_file:
        fieldnames = ['user_id', 'quiz_id', 'question_text', 'user_answer', 'is_correct']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results.results:
            user_id = result.user_id
            quiz_id = result.quiz_id
            questions = result.questions

            for question in questions:
                writer.writerow({
                    'user_id': user_id,
                    'quiz_id': quiz_id,
                    'question_text': question.question_text,
                    'user_answer': question.user_answer,
                    'is_correct': question.is_correct
                })

    return f'Data written to {file_path} successfully.'
