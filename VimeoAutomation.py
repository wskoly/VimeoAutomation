from requests import get
import vimeo
import os
import csv
import logging
import json

logging.basicConfig(
    filename="vimeo.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

FOLDER_IDS = {"CHITTAGONG": "21407340"}
CONFIG = {}
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Create a new Vimeo object
vClient = vimeo.VimeoClient(
    token=CONFIG["token"], key=CONFIG["client_id_key"], secret=CONFIG["secret"]
)


def k_print(*args, **kwargs):
    if "log_level" in kwargs:
        if kwargs["log_level"] == "info":
            logging.info(args)
        elif kwargs["log_level"] == "error":
            logging.error(args)
        kwargs.pop("log_level")
    # print('\r',*args, **kwargs, end='\r')
    print(*args, **kwargs)


def upload_video(video_path, video_title, video_description):
    video_uri = vClient.upload(
        video_path, data={"name": video_title, "description": video_description}
    )
    vClient.get(video_uri, params={"fields": "link"})
    return video_uri


def generate_title_and_description(data: dict):
    title = f"{data['CODE']} - {data['OWNER NAME (ENGLISH)']}"
    description = ""
    for key, value in data.items():
        description += f"{key}: {value}\n"
    return title, description


def upload_multiple_videos(master_csv_path, video_dir, *args, **kwargs):
    not_uploaded_count = 0
    proccessed_count = 0
    backend_data = []
    video_uris = []
    with open(master_csv_path, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            if "location" in kwargs:
                if (
                    kwargs["location"].strip().upper()
                    != row["LOCATION"].strip().upper()
                ):
                    continue
            proccessed_count += 1
            code = row["CODE"].strip()
            video_path = os.path.join(video_dir, code + ".mp4")
            name_english = row["OWNER NAME (ENGLISH)"].strip()
            name_bangla = row["OWNER NAME (BANGLA)"].strip()
            location = row["LOCATION"].strip()
            if os.path.exists(video_path):
                video_title, video_description = generate_title_and_description(row)
                # k_print(title, description)
                k_print(f"Uploading {video_path} with title {video_title}")
                video_uri = upload_video(video_path, video_title, video_description)
                video_uris.append(video_uri)
                vimeo_url = f"https://vimeo.com/{str(video_uri).split('/')[-1]}"
                k_print(
                    f"Uploaded {video_title} with URI {video_uri}", log_level="info"
                )
                backend_data.append(
                    {
                        "code": code,
                        "name_english": name_english,
                        "name_bangla": name_bangla,
                        "location": location,
                        "video_url": vimeo_url,
                    }
                )
            else:
                k_print(f"Video {code} not found at {video_path}", log_level="error")
                not_uploaded_count += 1

        k_print(
            f"Proccessed {proccessed_count} rows. {not_uploaded_count} videos not found",
            log_level="info",
        )
    os.system("cls")
    with open("backend_data.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["code", "name_english", "name_bangla", "location", "video_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in backend_data:
            writer.writerow(data)
        k_print("Backend data written to backend_data.csv", log_level="info")
    # print(video_uris)
    # res = vClient.put('/me/projects/21389077/videos', data={'uris': ", ".join(video_uris)})
    # print(res.json())


def get_master_csv_data(master_csv_path, filter_location=None):
    data_dict = []
    with open(master_csv_path, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            if filter_location and filter_location.strip().upper() != row["LOCATION"].strip().upper():
                continue
            data_dict.append(row)
    return data_dict


def get_videos_info(*args, **kwargs):
    matched_output_dir = kwargs.get(
        "matched_output_dir", os.path.join(os.getcwd(), "outputs", "matched_videos")
    )
    unmatched_output_dir = kwargs.get(
        "unmatched_output_dir", os.path.join(os.getcwd(), "outputs", "unmatched_videos")
    )

    os.makedirs(matched_output_dir, exist_ok=True)
    os.makedirs(unmatched_output_dir, exist_ok=True)
    master_csv_path = kwargs.get("master_csv_path", None)
    location = kwargs.get("location", None)
    if not master_csv_path or not location:
        k_print(
            f"Master CSV path and location are required kwargs: master_csv_path, location",
            log_level="error",
        )
        return

    master_data = get_master_csv_data(master_csv_path, filter_location=location)
    uri = f"/me/projects/{FOLDER_IDS[location.upper()]}/videos"
    res = vClient.get(f"{uri}?per_page=100")
    if res.status_code != 200:
        k_print(f"Failed to get videos for location: {location}", log_level="error")
        return
    res_json = res.json()
    total_videos = res_json["total"]

    next_page = res_json["paging"]["next"]
    data = res_json["data"]
    while next_page:
        res = vClient.get(next_page)
        res_json = res.json()
        data += res_json["data"]
        next_page = res_json["paging"]["next"]
    k_print(
        f"Total Videos: {total_videos} - Scrapped Total Videos: {len(data)} for location: {kwargs['location']}",
        log_level="info",
    )
    if len(data) != total_videos:
        k_print(
            f"Total video and Scrapped videos mismatched for location: {kwargs['location']}",
            log_level="error",
        )
        return
    matched_csv_data = []
    unmatched_csv_data = []
    for video in data:
        name, video_url = video["name"], video["link"]
        matched_data = [
            d
            for d in master_data
            if name.strip() in d["OWNER NAME (BANGLA)"].strip()
            and d["LOCATION"].strip().upper() == kwargs["location"].strip().upper()
        ]
        if matched_data:
            for el in matched_data:
                data = {
                    "code": el["CODE"],
                    "name_english": el["OWNER NAME (ENGLISH)"],
                    "name_bangla": el["OWNER NAME (BANGLA)"],
                    "location": el["LOCATION"],
                    "vimeo_url": video_url,
                }
                matched_csv_data.append(data)
                master_data.remove(el)
        else:
            unmatched_csv_data.append({"video_title": name, "video_url": video_url})

    k_print(
        f"Matched Videos: {len(matched_csv_data)} - Unmatched Videos: {len(unmatched_csv_data)} for location: {kwargs['location']}",
        log_level="info",
    )

    k_print(f"Remaining master data: {len(master_data)}", log_level="info")
    with open(
        os.path.join(matched_output_dir, f"{location}_matched.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fieldnames = ["code", "name_english", "name_bangla", "location", "video_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in matched_csv_data:
            writer.writerow(data)
        k_print(f"Matched data written to {location}_matched.csv", log_level="info")
    with open(
        os.path.join(unmatched_output_dir, f"{location}_unmatched.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fieldnames = ["video_title", "video_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in unmatched_csv_data:
            writer.writerow(data)
        k_print(f"Unmatched data written to {location}_unmatched.csv", log_level="info")

    with open(
        os.path.join(matched_output_dir, f"{location}_remaining.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fieldnames = master_data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in master_data:
            writer.writerow(data)
        k_print(f"Remaining data written to {location}_remaining.csv", log_level="info")


if __name__ == "__main__":
    master_csv_path = (
        r"F:\KOLY\Others\ExperimetalProj\UniDostiQrGen\master_guest_list.csv"
    )
    video_path = r"F:\KOLY\Others\ExperimetalProj\UniDostiQrGen\videos"

    # upload_multiple_videos(master_csv_path, video_path)
    # res = vClient.post('/me/projects', data={'name': 'koly'})
    # res = vClient.get('/me/projects/21393145')
    # res = vClient.put('/me/projects/21393145/videos/973000088')
    # print(res.status_code, res.text)

    get_videos_info(location="CHITTAGONG", master_csv_path=master_csv_path)
