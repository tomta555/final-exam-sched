import sys
import csv
import ast
import os
import math

conflicts = {}
course_slot = {}
exam_table = sys.argv[1]

TOTAL_SLOTS = 42

data_path = "data"

# output folder path
penalty_file_path  = "penalty_report"

# student regist file path
regist_path = data_path+"/regist.in"

# student enrolled courses file path
st_courses_path = data_path+"/enrolled-courses.in"

# all exam courses file path
all_courses_path = data_path+"/all-exam-course.in"

# conflicts file path
conflicts_path  = data_path+"/conflicts.in"

# courses by faculty folder path
fa_course_path  = data_path+"/exam-courses-faculty"

# capacity file path
capacity_path  = data_path+"/faculty-capacity.in"

penalty_file = "solution_penalty.txt"

student_enrolled_courses = set()
course_total_enroll = {}
MAX_CAPACITY = {
    "01": 0,
    "02": 0,
    "03": 0,
    "04": 0,
    "05": 0,
    "06": 0,
    "07": 0,
    "08": 0,
    "09": 0,
    "10": 0,
    "11": 0,
    "12": 0,
    "13": 0,
    "14": 0,
    "15": 0,
    "16": 0,
    "17": 0,
    "18": 0,
    "19": 0,
    "20": 0,
    "21": 0,
    "RB": 0,
    "99": math.inf
}

SLOT_CAPACITY = { s:MAX_CAPACITY.copy() for s in range(TOTAL_SLOTS) }
with open(exam_table, "r", encoding="utf-8-sig") as read_exam_slot:
    for i in read_exam_slot:
        course, slot = i.strip().split(" ")
        course_slot[course] = int(slot)


with open(regist_path, "r", encoding="utf-8-sig") as regist:
    STUDENTS = list(csv.reader(regist, delimiter=" "))


with open(st_courses_path, "r", encoding="utf-8-sig") as courses:
    for row in courses:
        student_enrolled_courses.add(row.split()[0])
        course_total_enroll[row.split()[0]] = int(row.split()[1])

# Read capacity

with open(capacity_path, "r", encoding="utf-8-sig") as capa:
    for row in capa:
        MAX_CAPACITY[row.split()[0]] = int(row.split()[1])

COURSE_FACULTY = {}

for file in os.listdir(fa_course_path):
    with open(os.path.join(fa_course_path, file), "r", encoding="utf-8-sig") as courses:
        for row in courses:
            COURSE_FACULTY[row.rstrip("\n")] = file.replace(".in", "")

exam_courses = set()
with open(all_courses_path, "r", encoding="utf-8-sig") as courses:
    for c in courses:
        cs = c.rstrip("\n")
        exam_courses.add(cs)

all_courses = set()
for c in student_enrolled_courses:
    x = c
    if len(c) > 6:
        x = c[:-4]
    if x in exam_courses:
        all_courses.add(c)

COURSE_LIST = list(all_courses)
COURSE_LIST.sort()

TOTAL_COURSES = len(COURSE_LIST)


def remove_no_slot(student):
    """
    Input: Individual student regist Ex. [261216,261497]
    Remove course with no exam slot from student
    """
    global COURSE_LIST
    return [slot for slot in student if slot in COURSE_LIST]


def remove_no_exam(students):
    """
    Input: Student regists Ex. [[261216,261497],[],[261498],...]
    Remove student who has no exam -> []
    """
    return [courses for courses in students if courses]


def get_slot(course_list, student):
    """
    Return students who has at least one exam slot
    """
    student_slot = []
    for s in student:  # s = all enroll course Ex. [001101, 001102]
        s_remove_noslot = remove_no_slot(s)
        # Remove student that don't have any exam
        student_slot.append(s_remove_noslot)
    return remove_no_exam(student_slot)


# 1 over seat 250
# 2 overlap 10000
# 3 consecutive_a (0800,1200) 78
# 4 consecutive_b (1200,1530) 78
# 5 consecutive_c (0800,1530) 38
# 6 consecutive_d (1530,0800) 29
# 7 wait3day 12
# 7 first_slot 12


def pen_first_slot(first_slot):
    return 1 if first_slot > 9 else 0  # No exam more than 3 days


def pen_wait3day(s1, s2):  # No exam more than 3 days
    return 1 if abs(s1 // 3 - s2 // 3) > 3 else 0


def pen_overlap(s1, s2):  # 2 exams in 1 slot
    return 1 if abs(s1 - s2) == 0 else 0


def pen_consecutive_a(s1, s2):
    if abs(s1 - s2) == 1:  # Consecutive exam
        return 1 if s1 % 3 == 0 else 0  # Exam 8.00 then 12.00 on the same day
    return 0


def pen_consecutive_b(s1, s2):
    if abs(s1 - s2) == 1:  # Consecutive exam
        return 1 if s1 % 3 == 1 else 0  # Exam 12.00 then 15.30 on the same day
    return 0


def pen_consecutive_c(s1, s2):
    if abs(s1 - s2) == 2:  # Consecutive exam
        return 1 if s1 // 3 == s2 // 3 else 0  # Exam 8.00 then 15.30 on the same day
    return 0


def pen_consecutive_d(s1, s2):
    if abs(s1 - s2) == 1:  # Consecutive exam
        return 1 if s1 // 3 != s2 // 3 else 0  # Exam 15.30 then 8.00 on next day
    return 0


def penalty_count(student,student_courses):
    sc_sorted_rmdup = {}
    global conflicts
    for i in range(len(student_courses)):
        sc_sorted_rmdup[student_courses[i]] = student[i]
    sc_sorted = sorted(student_courses, key=lambda x: sc_sorted_rmdup[x])
    student.sort()

    pen_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    count = pen_first_slot(student[0])
    pen_count[7] += count

    for i in range(len(student) - 1):
        count = pen_overlap(student[i], student[i + 1])
        if count == 1:
            if str(sc_sorted[i]) + " " + str(sc_sorted[i + 1]) in conflicts:
                conflicts[str(sc_sorted[i]) + " " + str(sc_sorted[i + 1])] += 1
            else:
                conflicts[str(sc_sorted[i]) + " " + str(sc_sorted[i + 1])] = 1
        pen_count[2] += count
        count = pen_consecutive_a(student[i], student[i + 1])
        pen_count[3] += count
        count = pen_consecutive_b(student[i], student[i + 1])
        pen_count[4] += count
        count = pen_consecutive_c(student[i], student[i + 1])
        pen_count[5] += count
        count = pen_consecutive_d(student[i], student[i + 1])
        pen_count[6] += count
        count = pen_wait3day(student[i], student[i + 1])
        pen_count[7] += count
    # calc slot[i], slot[i+2]
    for i in range(len(student_slot)-2):
        count = pen_consecutive_c(student_slot[i], student_slot[i + 2])
        pen_count[5] += count
    return pen_count


def penalty_calc(pen_count):
    pen_value = {1: 0, 2: 10000, 3: 78, 4: 78, 5: 38, 6: 29, 7: 12}
    penalty = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    for i in range(1, 8):
        penalty[i] = pen_value[i] * pen_count[i]
    return penalty


def calc_table(solution):
    table = {}
    for k, v in solution.items():
        if v not in table:
            table[v] = [k]
        else:
            table[v].append(k)
    return table


def linear_pen(x):
    return 500 * (x - 80)


def expo_pen(x):
    return (500 * (x - 80)) + (2**(2*((x / 10) - 1))) - (2**18)

def calc_capacity_penalty_v1(fa, slot, total_std_in_course, max_capacity):
    capacity_penalty = 0
    fa_penalty = 0
    rb_penalty = 0
    used_rb_capa = SLOT_CAPACITY[slot]["RB"]
    used_fa_capa = SLOT_CAPACITY[slot][fa]
    max_rb_capa = max_capacity["RB"]
    max_fa_capa = max_capacity[fa]
    max80_rb_capa = (max_rb_capa * 80) // 100
    max80_fa_capa = (max_fa_capa * 80) // 100 
    this_used_rb_capa = 0
    this_used_fa_capa = 0
    rb80_remain = max80_rb_capa - used_rb_capa
    fa80_remain = max80_fa_capa - used_fa_capa
    rb80_100 = max_rb_capa - max80_rb_capa
    fa80_100 = max_fa_capa - max80_fa_capa
    d = False
    if total_std_in_course > fa80_remain:
        remain_std = total_std_in_course - fa80_remain
        if remain_std > rb80_remain:
            remain_std = remain_std - rb80_remain
            if remain_std > fa80_100:
                remain_std = remain_std - fa80_100
                # over fa80 -> over rb80 -> over fa100 -> over rb100 -> overflow fa100
                if remain_std > rb80_100:
                    remain_std = remain_std - rb80_100
                    overflow_percent = ((remain_std + max_fa_capa) / max_fa_capa) * 100
                    this_used_fa_capa = fa80_remain + fa80_100
                    this_used_rb_capa = rb80_remain + rb80_100
                    fa_penalty = expo_pen(overflow_percent)
                    rb_penalty = linear_pen(100)
                # over fa80 -> over rb80 -> over fa100 -> fit in rb80-100
                else:
                    over80_rb = ((max80_rb_capa + remain_std) / max_rb_capa) * 100
                    this_used_fa_capa = fa80_remain + fa80_100
                    this_used_rb_capa = rb80_remain + remain_std
                    fa_penalty = linear_pen(100)
                    rb_penalty = linear_pen(over80_rb)

            # over fa80 -> over rb80 -> fit in fa80-100
            else:
                over80_fa = ((max80_fa_capa + remain_std) / max_fa_capa) * 100
                this_used_fa_capa = fa80_remain + remain_std
                this_used_rb_capa = rb80_remain
                fa_penalty = linear_pen(over80_fa)
        # over fa80 -> fit in rb80
        else:
            this_used_fa_capa = fa80_remain
            this_used_rb_capa = remain_std
    # fit in fa80        
    else:
        this_used_fa_capa = total_std_in_course
    capacity_penalty = fa_penalty + rb_penalty

    return capacity_penalty, this_used_fa_capa, this_used_rb_capa

def calc_capacity_penalty_for_eng(fa, slot, total_std_in_course, max_capacity):
    fa_for_eng = ["02","03","04","05","06","08","15","16","18","19","20"]
    fa_for_eng = sorted(fa_for_eng, key = lambda fa : max_capacity[fa], reverse=True)
    available_fa = ["01","RB"] + fa_for_eng
    this_used_fa_capa = {}
    penalty = 0
    remain = total_std_in_course
    for fa in available_fa:
        used_fa_capa = SLOT_CAPACITY[slot][fa]
        max80_fa_capa = (max_capacity[fa] * 80) // 100
    
        # penalty for eng in same slot
        if used_fa_capa == max80_fa_capa:
            penalty += 1

        fa80_remain = max80_fa_capa - used_fa_capa
        if remain > fa80_remain:
            this_used_fa_capa[fa] = fa80_remain
            remain = remain - fa80_remain
        else:
            this_used_fa_capa[fa] = remain
            remain = 0
            break
    
    if remain > 0:
        for fa in available_fa:
            max_fa_capa = max_capacity[fa]
            max80_fa_capa = (max_fa_capa * 80) // 100
            fa80_100 = max_fa_capa - max80_fa_capa
            if remain > fa80_100:
                this_used_fa_capa[fa] += fa80_100
                remain = remain - fa80_100
                penalty += linear_pen(100)
            else:
                this_used_fa_capa[fa] += remain
                over80_percent = ((remain + max80_fa_capa) / max_fa_capa) * 100
                penalty += linear_pen(over80_percent)
                remain = 0
                break
    if remain > 0:
        max_01_capa = max_capacity["01"]
        overflow_percent = ((remain + max_01_capa) / max_01_capa) * 100
        penalty += expo_pen(overflow_percent)
    return penalty, this_used_fa_capa


def pen_capacity(solution, max_capacity, course_faculty, course_total_enroll):
    global SLOT_CAPACITY
    slot_penalty_count = 0
    capacity_penalty = { i:0 for i in range(TOTAL_SLOTS)}
    capacity_penalty_detail = {}
    for n, slot in solution.items():
        node_n = n
        if len(n) > 6:
            node_n = n[:-4]
        course_fa = course_faculty.get(node_n,"99")
        total_std_in_course = course_total_enroll[n]
        used_capa = {}
        if node_n == "001101" or node_n == "001102" or node_n == "001201":
            capa_pen, all_used_capa = calc_capacity_penalty_for_eng(course_fa, slot ,total_std_in_course,max_capacity)
            used_capa[slot] = all_used_capa
        else:
            capa_pen, used_fa, used_rb = calc_capacity_penalty_v1(course_fa, slot, total_std_in_course, max_capacity)

            if node_n == "140104":
                capa_pen = 0
                used_fa = 0
                used_rb = 0
            used_capa[slot] = {}
            used_capa[slot]["fa"] = used_fa
            used_capa[slot]["RB"] = used_rb
        capacity_penalty[slot] += capa_pen

        if capa_pen > 0:
            if slot not in capacity_penalty_detail.keys():
                capacity_penalty_detail[slot] = {"faculty_id":[course_fa],"course_id":[node_n]}
            else:
                capacity_penalty_detail[slot]["faculty_id"].append(course_fa)
                capacity_penalty_detail[slot]["course_id"].append(node_n)

        if node_n == "001101" or node_n == "001102" or node_n == "001201":
            for fa, capa in used_capa[slot].items():
                SLOT_CAPACITY[slot][fa] += capa
        else:
            SLOT_CAPACITY[slot][course_fa] += used_capa[slot]["fa"]
            SLOT_CAPACITY[slot]["RB"] += used_capa[slot]["RB"]
 
    for slot in range(TOTAL_SLOTS):
        if capacity_penalty[slot] > 0:
            slot_penalty_count += 1
    return capacity_penalty_detail,capacity_penalty, slot_penalty_count

def get_reg_exam_solution(course_slot, course_list):
    solution = {}
    for c in course_list:
        solution[c] = course_slot[c]
    return solution

total_penalty = 0
penalties = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
penalties_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

STUDENT_CLEAN = get_slot(COURSE_LIST, STUDENTS)
STUDENT_DUP_COUNT = {str(s): STUDENT_CLEAN.count(s) for s in STUDENT_CLEAN}
# For each student
for s, count in STUDENT_DUP_COUNT.items():
    student_slot = []
    student_courses = []
    # Convert course-code to exam-slot
    for key in ast.literal_eval(s):
        student_slot.append(course_slot[key])
        student_courses.append(key)

    pen_count = penalty_count(student_slot,student_courses)
    # Multiply duplicate student count with pen_count
    pen_count.update((k, v * count) for k, v in pen_count.items())

    pen_calc = penalty_calc(pen_count)

    for i in range(1, 8):
        penalties[i] += pen_calc[i]
        penalties_count[i] += pen_count[i]

reg_exam = get_reg_exam_solution(course_slot,COURSE_LIST)
capa_detail, slot_penalty, pencapa_count = pen_capacity(reg_exam, MAX_CAPACITY, COURSE_FACULTY, course_total_enroll)
exceed_capacity_penalty = sum(slot_penalty.values()) //1
penalties[1] += exceed_capacity_penalty
penalties_count[1] += pencapa_count

with open(penalty_file_path+penalty_file, "a") as p_file:
    p_file.write("name:" + exam_table +"\n")
    p_file.write("total courses:          "+str(TOTAL_COURSES)+"\n")
    p_file.write("student having an exam: "+str(len(STUDENT_CLEAN))+"\n")
    p_file.write("total_penalty:          "+str(sum(penalties.values()))+"\n")
    p_file.write("penalty:       "+str(penalties)+"\n")
    p_file.write("penalty_count: "+str(penalties_count)+"\n")
    if len(conflicts) > 0:
        p_file.write("exceed_capa:  "+str(capa_detail)+"\n")
        p_file.write("conflicts:    "+str(conflicts)+"\n\n")
    else:
        p_file.write("exceed_capa:  "+str(capa_detail)+"\n\n")

if not os.path.exists(penalty_file_path):
    os.makedirs(penalty_file_path)
    
with open(penalty_file_path+"/pen_result_csv.csv","a") as res_csv:
    res_csv.write(exam_table+"\n")
    pen_str = ","
    for i in range(len(penalties_count.keys())):
        pen_str += str(penalties_count[i+1])+","
    res_csv.write(pen_str+str(sum(penalties_count.values()))+"\n")
    pen_str = ","
    for i in range(len(penalties.keys())):
        pen_str += str(penalties[i+1])+","
    res_csv.write(pen_str+str(sum(penalties.values()))+"\n")
