# -*- coding: utf-8 -*-
import os
import pandas as pd
import datetime
import chardet

PATH_SRT = "data/ПРГРМ-001655.srt"
TIMECODE_TO_MEDIA = "data/ПРГРМ-001655.xls"

time_codes = pd.read_excel(TIMECODE_TO_MEDIA, header=None)

# исправляем названия столбцов
time_codes.columns = time_codes.loc[1, :]

# устраняем первые ненужные строки
time_codes = time_codes.loc[2:, ["Хронометраж", "КТК"]]
try:
    time_codes['КТК'] = time_codes["КТК"].map(lambda x: datetime.datetime.strptime(x, "%M:%S.%f"))
except:
    time_codes['КТК'] = time_codes['КТК'].map(lambda h: '00:'+h if len(h) < 9 else h)
    time_codes['КТК'] = time_codes["КТК"].map(lambda x: datetime.datetime.strptime(x, "%H:%M:%S.%f"))
print(time_codes)

# открываем файл .srt разделяем строки и формируем строки для таблицы
with open(PATH_SRT, 'rb') as f:
    ENCODING = chardet.detect(f.read())["encoding"]

if not '16-LE' in ENCODING:
    print(f'CHANGE ENCODING FROM {ENCODING} to {"UTF-16-LE"}')
    with open(PATH_SRT, 'r', encoding=ENCODING) as f:
        content = f.read()
    with open(PATH_SRT, 'w', encoding="UTF-16-LE") as f:
        f.write(content)

with open(PATH_SRT, 'r', encoding="UTF-16-LE") as f:
    srt = f.read().replace("\n\n", "\n").split("\n")
    idx, rows = 0, []
    while idx < len(srt) - 1:
        rows.append(srt[idx:idx+3])
        idx += 3

# создаем таблицу из субтитров
srt = pd.DataFrame(columns=["part", "time", "text"],
                    data=rows)

print(srt.head())
# начало и окончание субтитра преобразуем к формату datetime
srt["start"] = srt["time"].map(lambda x: datetime.datetime.strptime(x.split(" --> ")[0], "%H:%M:%S,%f"))
srt["end"] = srt["time"].map(lambda x: datetime.datetime.strptime(x.split(" --> ")[1], "%H:%M:%S,%f"))

# фильтруем нужную часть и склеиваем нужные части для формирования новых субтитров
# первая часть отдельно
part_first = srt.loc[srt['start'] < time_codes['КТК'].values[0], :]\
        .assign(full=lambda row: row['part'] + "\n" + row['time'] + "\n" + row['text'])

if not os.path.exists(PATH_SRT[:-4] + "_1_RUS.srt"):
    with open(PATH_SRT[:-4] + "_1_RUS.srt", 'w', encoding='utf-16') as f:
        f.write("\n\n".join(part_first["full"].values))
        print(f"File {f.name} is done!")
else:
    print(f"File {PATH_SRT[:-4] + '_1_RUS.srt'} already exists.")

for num_part in range(time_codes.shape[0] - 1):
    filename = PATH_SRT[:-4] + f"_{num_part + 2}_RUS.srt"
    if not os.path.exists(filename):
        filter_time_1 = srt['start'] >=  time_codes['КТК'].values[num_part]
        filter_time_2 = srt['start'] <  time_codes['КТК'].values[num_part + 1]
        temp = srt.loc[filter_time_1 & filter_time_2, :]\
                .assign(start_new=lambda row: (row["start"] - time_codes['КТК'].values[num_part] + datetime.datetime(1970, 1, 1)).dt.strftime("%H:%M:%S.%f"))\
                .assign(end_new=lambda row: (row["end"] - time_codes['КТК'].values[num_part] + datetime.datetime(1970, 1, 1)).dt.strftime("%H:%M:%S.%f"))\
                .assign(time_new=lambda row: row["start_new"].map(lambda s: s[:-3]) + " --> " + row["end_new"].map(lambda s: s[:-3]))

        temp['part_new'] = [str(i) for i in range(1, temp.shape[0]+1)]
        temp['full'] = (temp['part_new'] + "\n" + temp['time_new'] + "\n").str.replace('.', ',') + temp['text'] + "\n\n"


        with open(PATH_SRT[:-4] + f"_{num_part + 2}_RUS.srt", 'w', encoding='utf-16-le') as f:
            # склеиваем субтитры
            f.write("".join(temp["full"].values))
            print(f"File {f.name} is done!")
    else:
        print(f"File {filename} already exists.")
