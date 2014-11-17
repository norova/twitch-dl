'''
    twitch-dl - Easily download broadcast videos from Twitch.tv
    Copyright (C) 2014 Ryan Cain <ryan@yourfirefly.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import re
import os
import string
import requests
import json
import argparse

BASE_URL = 'https://api.twitch.tv'

def download_file(url, local_filename, cur_part, num_parts):
    chunk_size = 1024
    cur_length = 0

    r = requests.head(url)
    file_size = int(r.headers['Content-Length']) / float(pow(1024, 2))
    if r.headers['Content-Type'] != 'video/x-flv':
        raise Exception("Incorrect Content-Type ({0}) for {1}".format(headers['Content-Type'], url))

    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if not chunk: # filter out keep-alive new chunks
                continue
            f.write(chunk)
            f.flush()
            cur_length += chunk_size
            sys.stdout.write("\rDownloading {0}/{1}: {2:.2f}/{3:.2f}MB ({4:.1f}%)".format(cur_part, num_parts, cur_length / float(pow(1024, 2)), file_size, ((cur_length / float(pow(1024, 2))) / file_size) * 100))

    print('...complete!')

def download_broadcast(id_):
    """ Download all video parts for broadcast 'id_' """

    pattern = "{base}/api/videos/a{id_}"
    url = pattern.format(base=BASE_URL, id_=id_)
    r = requests.get(url)
    if r.status_code != 200:
        print("\n*** ERROR ***\n\nTwitch.tv API returned status code {0}.".format(r.status_code))
        r = r.json()
        print("Error: {0}\nMessage: {1}".format(r['error'], r['message']))
        raw_input('\nPress any key to exit...')
        sys.exit()

    try:
        j = r.json()
    except ValueError as e:
        print("API did not return valid JSON: {}".format(e))
        print("{}".format(r.text))
        raw_input('\nPress any key to exit...')
        sys.exit()

    savepath = "{userprofile}\Desktop\{channel}_{id_}".format(userprofile=os.environ['USERPROFILE'],channel=j['channel'], id_=id_)
    print("Save path set to: {0}".format(savepath))
    try:
        os.makedirs(savepath)
    except OSError:
        if not os.path.isdir(savepath):
            raise

    print ("Found {0} parts for broadcast ID {1} on channel '{2}'".format(len(j['chunks']['live']), id_, j['channel']))
    for nr, chunk in enumerate(j['chunks']['live']):
        video_url = chunk['url']
        ext = os.path.splitext(video_url)[1]
        filename = "{0}/{1}_{2:0>2}{3}".format(savepath, id_, nr, ext)
        download_file(video_url, filename, nr+1, len(j['chunks']['live']))

    print("Finished downloading broadcast ID {0} on channel '{1}'".format(id_, j['channel']))

if __name__=="__main__":
    # Specify CA so the py2exe-created executable knows which CAs to use for SSL
    os.environ['REQUESTS_CA_BUNDLE'] = "cacert.pem"

    # Print license
    print('twitch-dl - Copyright (C) 2014 Ryan Cain <ryan@yourfirefly.com>\n')
    print('This program comes with ABSOLUTELY NO WARRANTY.')
    print('This is free software, and you are welcome to redistribute it')
    print('under certain conditions; see LICENSE.txt file for details.\n')

    # Initialize argument parser, prompt for broadcast_id if not specified via command
    parser = argparse.ArgumentParser()
    parser.add_argument('broadcast_id', nargs='?', help='ID of Twitch broadcast to download', type=int)
    args = parser.parse_args()

    if args.broadcast_id is None:
        try:
            args.broadcast_id = int(input('Twitch broadcast ID: '))
        except:
            print('Invalid Twitch broadcast ID')
            raw_input('\nPress any key to exit...')
            sys.exit()

    if (args.broadcast_id < 1) or (args.broadcast_id > 999999999999):
        print("{0} is not a valid Twitch broadcast ID".format(args.broadcast_id))
        raw_input('\nPress any key to exit...')
        sys.exit()

    # Start downloading the broadcast files
    download_broadcast(args.broadcast_id)
