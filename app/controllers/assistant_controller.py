import os
from flask import request, jsonify, render_template
from app.models.assistant import AssistantRoles
import asyncio
import re


assistant_roles = AssistantRoles()



class IntentClassifier:


    @staticmethod
    def classify(user_query: str) -> str:

        query_lower = user_query.lower()


        pattern = r'(?:Professor |Prof\. |Prof |Dr\. |Dr )?[A-Z][a-z]+\s+[A-Z][a-z]+'
        professor_names = re.findall(pattern, user_query)

        comparison_keywords = ['compare', 'vs', 'versus', 'between', 'difference']
        has_comparison_keyword = any(keyword in query_lower for keyword in comparison_keywords)

        if has_comparison_keyword and len(professor_names) >= 2:
            print(f"[Intent Classifier] COMPARE detected: {professor_names}")
            return 'compare'


        curriculum_keywords = [
            'recommend courses', 'suggest courses', 'curriculum',
            'courses for', 'courses in', 'learning path',
            'what courses', 'which courses', 'study plan',
            'field of'
        ]


        field_indicators = [
            'machine learning', 'data science', 'artificial intelligence',
            'databases', 'software engineering', 'web development',
            'cybersecurity', 'algorithms', 'networking', 'ai', 'ml',
            'computer science', 'programming'
        ]

        has_curriculum_keyword = any(keyword in query_lower for keyword in curriculum_keywords)
        mentions_field = any(field in query_lower for field in field_indicators)

        if has_curriculum_keyword or mentions_field:
            print(f"[Intent Classifier] CURRICULUM detected")
            return 'curriculum'


        print(f"[Intent Classifier] QNA detected (default)")
        return 'qna'


def get_assistant():

    return render_template("assistant.html")


def answer_question(conn):

    try:

        cursor = conn.cursor()

        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                'error': 'No message provided'
            }), 400

        user_message = data['message'].strip()

        if not user_message:
            return jsonify({
                'error': 'Message cannot be empty'
            }), 400


        intent_hint = data.get('intent_hint', None)


        print(f"\n{'=' * 60}")
        print(f"[USER QUERY]: {user_message}")
        if intent_hint:
            print(f"[INTENT HINT from frontend]: {intent_hint}")
        print(f"{'=' * 60}")


        if intent_hint and intent_hint in ['compare', 'curriculum', 'qna']:
            intent = intent_hint
            print(f"[USING HINT]: {intent}")
        else:
            intent = IntentClassifier.classify(user_message)
            print(f"[CLASSIFIED INTENT]: {intent}")


        if intent == 'compare':
            print("[ROUTING TO]: compare_two_professors")
            response = asyncio.run(assistant_roles.compare_two_professors(cursor,user_message))

        elif intent == 'curriculum':
            print("[ROUTING TO]: recommend_curriculum")
            response = asyncio.run(assistant_roles.recommend_curriculum(cursor,user_message))

        else:
            print("[ROUTING TO]: QnA")
            response = asyncio.run(assistant_roles.QnA(cursor,user_message))


        return jsonify({
            'response': response,
            'intent': intent
        }), 200

    except Exception as e:
        print(f"[ERROR in answer_question]: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'An error occurred processing your request',
            'details': str(e)
        }), 500




