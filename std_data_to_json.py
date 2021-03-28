import json
import sys
import csv

data_folder = "example_data/"

solution_folder = "example_solution/"

all_c = data_folder+"all-exam-course.in"

st = data_folder+"regist-studentid.in"

sctble = solution_folder+"graph-coloring-solution-deg.txt"

all_courses_set = set()
with open(all_c,"r",encoding="utf-8-sig") as all_exam:
    all_courses_list = list(csv.reader(all_exam,delimiter=" "))
    for i in all_courses_list:
        all_courses_set.add(i[0])

with open(st,"r",encoding="utf-8-sig") as regist:
    regist_std = list(csv.reader(regist,delimiter=" "))

with open(sctble,"r",encoding="utf-8-sig") as table:
    sched_table = dict(csv.reader(table,delimiter=" "))

summary_regist = {}
for std in regist_std:
    std_id = std[0]
    courses = std[1:]
    summary_regist[std_id] = courses

data_json = []
for k, v in summary_regist.items():
    std_id = k
    timetable_dict = {}
    for course in v:
        course_slot = sched_table.get(course,"99")
        if course_slot not in timetable_dict.keys():
            timetable_dict[course_slot] = [course]
        else:
            timetable_dict[course_slot].append(course)
    if "99" in timetable_dict.keys():
        timetable_dict.pop("99")
    timetable_dict["student_id"] = std_id
    data_json.append(timetable_dict)
    
print(data_json[:10])
with open('student_timetable.json', 'w') as outfile:
    json.dump(data_json, outfile)