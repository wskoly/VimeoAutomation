import vimeo
import os
import csv
import logging
import json

logging.basicConfig(filename='vimeo.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CONFIG = {}
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Create a new Vimeo object
vClient = vimeo.VimeoClient(
    token=CONFIG['token'],
    key=CONFIG['client_id_key'],
    secret=CONFIG['secret']
)

def k_print(*args, **kwargs):
    if 'log_level' in kwargs:
        if kwargs['log_level'] == 'info':
            logging.info(args)
        elif kwargs['log_level'] == 'error':
            logging.error(args)
        kwargs.pop('log_level')
    print('\r',*args, **kwargs, end='\r')



def upload_video(video_path, video_title, video_description):
    video_uri = vClient.upload(video_path, data = {'name': video_title, 'description':video_description})
    vClient.get(video_uri, params={'fields': 'link'})
    return video_uri

def generate_title_and_description(data:dict):
    title = f"{data['CODE']} - {data['OWNER NAME (ENGLISH)']}"
    description = ""
    for key, value in data.items():
        description += f"{key}: {value}\n"
    return title, description

def upload_multiple_videos(master_csv_path, video_dir):
    not_uploaded_count = 0
    proccessed_count = 0
    backend_data = []
    video_uris = []
    total_rows = sum(1 for line in open(master_csv_path, 'r', encoding='utf-8'))
    with open(master_csv_path, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            proccessed_count += 1
            k_print(f'Processing {proccessed_count}/{total_rows}')
            code = row['CODE'].strip()
            video_path = os.path.join(video_dir, code + '.mp4')
            name_english = row['OWNER NAME (ENGLISH)'].strip()
            name_bangla = row['OWNER NAME (BANGLA)'].strip()
            location = row['LOCATION'].strip()
            if os.path.exists(video_path):
                video_title, video_description = generate_title_and_description(row)
                # k_print(title, description)
                k_print(f'Uploading {video_path} with title {video_title}')
                video_uri = upload_video(video_path, video_title, video_description)
                video_uris.append(video_uri)
                vimeo_url = f"https://vimeo.com/{str(video_uri).split('/')[-1]}"
                k_print(f'Uploaded {video_title} with URI {video_uri}', log_level='info')
                backend_data.append({
                    'code': code,
                    'name_english': name_english,
                    'name_bangla': name_bangla,
                    'location': location,
                    'video_url': vimeo_url
                })
            else:
                k_print(f'Video {code} not found at {video_path}', log_level='error')
                not_uploaded_count += 1

        k_print(f'Proccessed {proccessed_count} rows. {not_uploaded_count} videos not found', log_level='info')
    os.system('cls')
    with open('backend_data.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['code', 'name_english', 'name_bangla', 'location', 'video_url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in backend_data:
            writer.writerow(data)
        k_print('Backend data written to backend_data.csv', log_level='info')
    print(video_uris)
    res = vClient.put('/me/projects/21389077/videos', data={'uris': ", ".join(video_uris)})
    print(res.json())

if __name__ == '__main__':
    master_csv_path = r"F:\KOLY\Others\ExperimetalProj\UniDostiQrGen\master_guest_list.csv"
    video_path = r"F:\KOLY\Others\ExperimetalProj\UniDostiQrGen\videos"

    upload_multiple_videos(master_csv_path, video_path)
