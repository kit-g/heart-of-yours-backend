from firebase_admin import credentials, firestore, auth, initialize_app
from firebase_admin.auth import UserNotFoundError

cred = credentials.Certificate('firebase.json')
initialize_app(cred)
db = firestore.client()


def delete_account(user_id: str):
    try:
        auth.delete_user(user_id)
        print(f'Deleted user {user_id} from Firebase Auth')
    except UserNotFoundError:
        pass
    except Exception as e:
        print(f'Error deleting user {user_id} from Firebase Auth: {e}')

    try:
        db.collection('users').document(user_id).delete()
        print(f'Deleted Firestore document for user {user_id}')
    except Exception as e:
        print(f'Error deleting user {user_id} from Firestore: {e}')


def handler(event: dict, context) -> dict:
    print(event)

    match event:
        case {
            'Event': 'AccountDeletion',
            'Payload': {'user_id': user_id},
        }:
            delete_account(user_id)

    try:
        return {'statusCode': 200}
    except Exception as e:
        print(f'{context.function_name}: {type(e)} - {e}')
        raise e
