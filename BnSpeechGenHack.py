import os
import csv
import time
import requests
import base64
import re

def get_name_ben(name):
    name = name.strip()

    pattern = r'(মোঃ)|(মোঃ)|(মোহাম্মদ)|(মোহাম্মেদ)|(মুহাম্মদ)|(মুহাম্মদ)|(মো:)|(মো)[\s]+|(শ্রী[\s]+)|[\s]+(চন্দ্র)|[\s]+(নাথ)|[\s]+(উল্লাহ)|(আলহাজ্ব)|(আঃ)|(-উর)|(এম)[\s]+|[\s]+(আল)[\s-]+|(মাওলানা)[\s]+|(মুল্লা)[\s]+|(হাজী)[\s]+|(মো\.)|(অর)[\s]+|(হাজি)[\s]+|(মিঃ)|(এম\.)|(মি\.)'
    temp_name = re.sub(pattern, '', name).strip().replace(':', '').replace('-', ' ')
    if len(temp_name) > 2:
        name = temp_name
    splited_name = name.split()
    splited_name = [x for x in splited_name if len(x)>=2]
    if len(splited_name) == 0:
        return name, name
    if len(splited_name) < 2:
        return splited_name[0].strip(), splited_name[0].strip()
    if len(splited_name) > 3:
        return splited_name[-3].strip(), splited_name[-2].strip()
    return splited_name[-2].strip(), splited_name[-1].strip()

def make_prompt(name):
    return f"প্রিয় {name} ভাই, বিজ্ঞান ও প্রযুক্তির হাত ধরে, বিশ্বের সাথে, বাংলাদেশও এগিয়ে চলেছে, উন্নয়নের এক নতুন মাত্রায়. বাংলাদেশের ব্যবসায়, প্রযুক্তির অগ্রযাত্রায়, এক যুগান্তকারী ভূমিকা পালন করে চলেছে ইউনিলিভার. আর স্মার্ট বাংলাদেশের পরিকল্পনাকে, বাস্তবে রূপ দিতে, ইউনিলিভারের পাশে থেকে, একটি গুরুত্বপূর্ণ ভূমিকা পালন করছে, আমাদের শ্রদ্ধেয়ও হোলসেলারগন. আর তার থেকেও বড়ো গুরুত্বপূর্ণ ভূমিকা পালন করছেন, আপনি. আমাদের প্রিয় {name} ভাই. ইউনিলিভার দোস্তির অগ্রযাত্রাকে, শফল করার মাধ্যমে, আমাদের হোলসেলার এর পাশাপাশি, আপনিও বাংলাদেশকে, বিশ্বের দরবারে, আরো একধাপ এগিয়ে নিয়ে চলেছেন. আর তাই আমাদের দোস্তি হোলসেলারদের পাশাপাশি, আপনার শফোলতা উদযাপন করতে, আমরা আপনাকে আমন্ত্রণ করছি, ইউনিলিভার টপ হোলসেল মিট দুই হাজার চব্বিশে.. প্রিয় {name} ভাই. আশা করছি আপনাকে পাশে পাবো, আমাদের এই বর্ণিল আয়োজনে."

def gen_speech(name, code, audio_dir):
    prompt = make_prompt(name)
    payload = {
        "audioFormat": "ogg",
        "paragraphChunks": [prompt],
        "voiceParams": {"name": "bashkar", "engine": "azure", "languageCode": "bn-IN"},
    }
    try:
        response = requests.post(
            url="https://audio.api.speechify.com/generateAudioFiles", json=payload
        )
        print(f"Response for {name}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()

            base_aud = data["audioStream"]
            format = data["format"]
            speech_marks = data["speechMarks"]
            with open(os.path.join(audio_dir, f"{name}_{code}.ogg"), "wb") as f:
                f.write(base64.b64decode(base_aud))
            return f"{name}_{code}.ogg", speech_marks
    except Exception as e:
        print(e)
    return False, False

def generate_speech(master_csv_path, output_folder):
    audio_path = os.path.join(output_folder, "audio")
    out_csv_path = os.path.join(output_folder, "speech.csv")
    os.makedirs(audio_path, exist_ok=True)
    out_csv_data = []
    unique_name_dict = {}
    with open(master_csv_path, "r", encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        master_data = list(csv_reader)
        name_list = []
        i = 0
        while i < len(master_data):
            row = master_data[i]
            code = row["CODE"]
            name_english = row["OWNER NAME (ENGLISH)"]
            name_bangla = row["OWNER NAME (BANGLA)"]
            location = row["LOCATION"]
            given_name, surname = get_name_ben(name_bangla)

            # name_list.append({"code":code, "name":given_name})
            # i += 1
            # continue

            if given_name in unique_name_dict:
                audio_file = unique_name_dict[given_name]['speech_file']
                speech_marks = unique_name_dict[given_name]['speech_marks']
            else:
                audio_file, speech_marks = gen_speech(given_name, code, audio_path)
                if not audio_file:
                    print(f"Failed to generate speech for {name_bangla}")
                    time.sleep(60)
                    continue
                unique_name_dict[given_name] = {'speech_file': audio_file, 'speech_marks': speech_marks}

            if audio_file:
                out_csv_data.append({
                    "code": code,
                    "name_english": name_english,
                    "name_bangla": name_bangla,
                    "location": location,
                    "speech_file": audio_file,
                    "speech_marks": speech_marks
                })
                i += 1
            else:
                print(f"Failed to generate speech for {name_bangla}")
                time.sleep(60)
                continue

    with open("name_list.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = ["code", "name"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(name_list)
    with open(out_csv_path, "w", newline='', encoding='utf-8') as f:
        fieldnames = ["code", "name_english", "name_bangla", "location", "speech_file", "speech_marks"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_csv_data)



if __name__ == "__main__":
    generate_speech("master_guest_list.csv", "output")