def handler(event: dict, context) -> dict:
    print(event)

    try:
        return {
            'statusCode': 200,
            'body': {},
        }
    except Exception as e:
        print(f'{context.function_name}: {type(e)} - {e}')
        raise e
