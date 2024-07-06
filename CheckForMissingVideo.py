import os
import csv

from requests import get

def check_for_missing_videos(master_csv_path, video_folder_path):
    generated_video_dict = {}
    for root, dirs, files in os.walk(video_folder_path):
            for file in files:
                if file.endswith(".mp4"):
                    generated_video_dict[file.split('.')[0].strip()] = os.path.join(root, file)

    missing_videos = []
    found_videos = []
    with open(master_csv_path, 'r', encoding='utf-8') as master_csv:
        csv_reader = csv.DictReader(master_csv)
        for row in csv_reader:
            if row['Cleaned_names'].strip() not in generated_video_dict:
                missing_videos.append(row)
                continue
            row['Video_path'] = generated_video_dict[row['Cleaned_names'].strip()]
            found_videos.append(row)

    with open('missing_videos.csv', 'w', newline='', encoding='utf-8') as missing_csv:
        csv_writer = csv.DictWriter(missing_csv, fieldnames=missing_videos[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(missing_videos)

    with open('found_videos.csv', 'w', newline='', encoding='utf-8') as found_csv:
        csv_writer = csv.DictWriter(found_csv, fieldnames=found_videos[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(found_videos)