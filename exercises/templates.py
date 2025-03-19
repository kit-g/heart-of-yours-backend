from common import templates, get_json

if __name__ == '__main__':
    source = get_json('templates.json')
    for name, template in source.items():
        templates.document(name).set(template)
