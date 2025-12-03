import os
import psycopg2
from flask import Flask, request, jsonify, render_template, session
from course_aid.app.models.votes import Votes

def handle_votes(conn, review_id):
    '''
    Endpoint for creating/updating/deleting a vote on a review
    :param review_id: review id
    :return: JSON response with success status and updated counts
    '''

    cursor = conn.cursor()

    try:
        data = request.get_json()
        vote_type_str = data.get('vote_type')


        vote_type = 1 if vote_type_str == 'upvote' else -1

        username = session.get("user_id")

        existing_vote = Votes.check_vote(cursor, username, review_id)

        action = ""

        if existing_vote:
            existing_vote_id = existing_vote[0]
            existing_vote_type = existing_vote[1]


            if existing_vote_type == vote_type:
                Votes.delete_vote(cursor, existing_vote_id)
                action += 'removed'
            else:

                Votes.edit_vote(cursor, existing_vote_id, vote_type)
                action += 'changed'
        else:

            Votes.update_vote_id(cursor)

            Votes.create_vote(cursor, review_id, username, vote_type)
            action += 'added'

        conn.commit()

        counts = Votes.count_votes(cursor, review_id)

        cursor.close()


        return jsonify({
            'success': True,
            'action': action,
            'upvotes': counts[0] if counts[0] else 0,
            'downvotes': counts[1] if counts[1] else 0,
            'message': f'Vote {action} successfully'
        })

    except psycopg2.Error as e:
        conn.rollback()
        cursor.close()

        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500

    except Exception as e:
        conn.rollback()
        cursor.close()

        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500