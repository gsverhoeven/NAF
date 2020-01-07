import argparse
import requests
import sys
import pathlib
import yaml
import logging

import session

LOG = logging.getLogger("glicko")


def load_file(filename):
    file = pathlib.Path(filename)
    if not file.is_file():
        LOG.debug("File %s not found", filename)
        return False
    return file


def upload_file(file, url, secret=False):
    LOG.debug('Connecting to %s', url)
    header = session.build_header()
    form = {'submit': 'submit'}
    if secret:
        form['top_secret'] = secret

    response = False
    with open(file.as_posix(), 'r') as csv_file:
        LOG.info('Uploading file')
        response = requests.post(url, files={'csv_file': csv_file}, headers=header, data=form)
        if not response:
            LOG.error('Problem uploading file %s %s', response.status_code, response.reason)
            LOG.debug('%s', response.text)
            return False
        LOG.info('Upload OK!')
        return response.text


def upload_rank(filename, secret=False, url='https://member.thenaf.net/glicko/import.php'):
    LOG.debug('Uploading %s to %s', filename, url)

    file = load_file(filename)
    if not file:
        LOG.error('Error loading file %s', filename)
        return False
    
    response = upload_file(file, url, secret)
    if not response:
        return False

    LOG.info('Server responded')
    LOG.info(response)

    LOG.info('Done!')
    return True


def main():
    log_format = "[%(levelname)s:%(filename)s:%(lineno)s - %(funcName)20s ] %(message)s"
    logging.basicConfig(level=logging.INFO if "--debug" not in sys.argv else logging.DEBUG, format=log_format)

    config = {'target_url': 'http://example.com/ranks.php',
              'top_secret': 'no secret'}
    if pathlib.Path('upload.yml').is_file():
        with open('upload.yml', 'r') as config_file:
            config.update(yaml.safe_load(config_file))

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--debug', action='store_true')
    arg_parser.add_argument('filename', type=str)
    arg_parser.add_argument('--target-url', default=config['target_url'], action='store_true')
    arg_parser.add_argument('--top-secret', default=config['top_secret'], action='store_true')

    arguments = arg_parser.parse_args()

    LOG.debug("Using arguments %s", arguments)
    upload_rank(filename=arguments.filename, url=arguments.target_url, secret=arguments.top_secret)


if __name__=='__main__':
    main()
