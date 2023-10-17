import os
import json
import base64
import shutil
import urllib.request


def download_js(jsLink, path):
    """Download js map file from js link

    Args:
        jsLink (str): js map file links
    """
    try:
        if not jsLink.endswith('.js.map'):
            return
        if not os.path.exists(path):
            os.makedirs(path)
        with urllib.request.urlopen(jsLink, timeout=10) as response:
            with open(f'{path}/{jsLink.split("/")[-1]}', 'wb') as f:
                f.write(response.read())
    except urllib.error.URLError as e:
        print(f"Failed to download {jsLink}: {e}")


def makedir(path):
    try:
        os.makedirs(path)
    except Exception as e:
        print(f"Failed to make dir {path}: {e}")


def unpack_js(js_path, path):
    """Unpack js map file

    Args:
        jsLink (str): js map file links
    """
    list_js = os.listdir(js_path)
    list_js = [js for js in list_js if js.endswith('.js.map')]
    ignore_folders = ['node_modules']
    for js in list_js:
        with open(f'{js_path}/{js}', 'r') as f:
            js_map = json.load(f)
        sources = js_map.get('sources', [])
        sourcesContent = js_map.get('sourcesContent', [])
        for name, content in zip(sources, sourcesContent):
            dest_file = f'{path}/{name}'
            if any(folder in dest_file for folder in ignore_folders):
                continue
            dest_file = dest_file.replace('../', '')
            # create all the folders if not exist
            if not os.path.exists(os.path.dirname(dest_file)):
                os.makedirs(os.path.dirname(dest_file))
            # write file
            with open(dest_file, 'w') as f:
                # write a signiture to the file
                if dest_file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    f.write(
                        '// unpacked by map2code https://github.com/chapimenge3/map2code\n\n')
                f.write(content)


def create_zip(path):
    """Create zip file from folder

    Args:
        path (str): path to folder
    """
    shutil.make_archive(path, 'zip', path)


def lambda_handler(event, context):
    httpmethod = event['requestContext']['http']['method']
    if httpmethod.lower() != 'post':
        return {
            'statusCode': 400,
            'body': json.dumps('Method not allowed')
        }
    isBase64Encoded = event['isBase64Encoded']
    if isBase64Encoded:
        body = base64.b64decode(event['body']).decode('utf-8')
    else:
        body = event['body']

    body = json.loads(body)

    jsLinks = body.get('jsLinks', [])
    jsLinks = [jsLink for jsLink in jsLinks if jsLink.startswith(
        'http') and jsLink.endswith('.js.map')]
    if len(jsLinks) > 5 or len(jsLinks) == 0:
        return {
            'statusCode': 400,
            'body': json.dumps('Too many js links' if len(jsLinks) > 5 else 'No js links')
        }

    js_path = '/tmp'
    for jsLink in jsLinks:
        download_js(jsLink, js_path)

    domain = jsLinks[0].split('/')[2]
    # create folder for unpacked js map files
    main_path = f'/tmp/{domain}'
    makedir(main_path)
    unpack_js(js_path, main_path)
    create_zip(main_path)

    with open(f'{main_path}.zip', 'rb') as f:
        zip_file = f.read()

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/zip',
            'Content-Disposition': f'attachment; filename="{domain}.zip"'
        },
        'body': base64.b64encode(zip_file).decode('utf-8'),
        'isBase64Encoded': True
    }
