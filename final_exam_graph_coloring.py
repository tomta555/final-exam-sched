import os
import sys
import csv
import random
import time
import itertools
import ast
import math
import networkx as nx

OPTION = sys.argv[1]

outout_file_postfix = OPTION

# Valid slot 
TOTAL_SLOTS = 42

data_path = "example_data"
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

# output folder path
out_folder_path  = "example_solution/"

START_TIME = time.time() 
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

SLOTS = [slot for slot in range(TOTAL_SLOTS)]
SLOT_CAPACITY = { s:MAX_CAPACITY.copy() for s in range(TOTAL_SLOTS) }

capacity_penalty_value_slot = {}
# Read all student enroll courses
with open(regist_path, "r", encoding="utf-8-sig") as reg:
    STUDENTS = list(csv.reader(reg, delimiter=" "))

# Read all courses that students enroll with student count
std_en_courses_set = set()
STD_ENROLL_COURSES = {}
with open(st_courses_path, "r", encoding="utf-8-sig") as courses:
    for row in courses:
        std_en_courses_set.add(row.split()[0])
        STD_ENROLL_COURSES[row.split()[0]] = int(row.split()[1])

# Read all exam courses from file
exam_courses = set()
with open(all_courses_path, "r", encoding="utf-8-sig") as courses:
    for c in courses:
        cs = c.rstrip("\n")
        exam_courses.add(cs)

# Read capacity from file
with open(capacity_path , "r", encoding="utf-8-sig") as capa:
    for row in capa:
        MAX_CAPACITY[row.split()[0]] = int(row.split()[1])

# Read course from each faculty from file
COURSE_FACULTY = {} # {"001101":"01",}
for file in os.listdir(fa_course_path):
    with open(os.path.join(fa_course_path , file), "r", encoding="utf-8-sig") as courses:
        for row in courses:
            COURSE_FACULTY[row.rstrip("\n")] = file.replace(".in", "")

# get intersection of courses from regist and from faculty
all_courses = set()
for c in std_en_courses_set:
    x = c
    if len(c) > 6:
        x = c[:-4]
    if x in exam_courses:
        all_courses.add(c)

COURSE_LIST = list(all_courses)
COURSE_LIST.sort()

TOTAL_COURSES = len(COURSE_LIST)

with open(conflicts_path, "r", encoding="utf-8-sig") as conflicts:
    CONFLICTS = list(csv.reader(conflicts, delimiter=" "))

CONFLICT_DICT = {}
for con in CONFLICTS:
    CONFLICT_DICT[con[0] + "_" + con[1]] = int(con[2])
# create graph and add nodes
G = nx.Graph()
G.add_nodes_from(COURSE_LIST)
gNode = list(G.nodes)

NODE_SUM_CONFLICTS = {}

for node in CONFLICTS:
    # add edges for each node if node exists
    if node[0] in gNode and node[1] in gNode:
        G.add_edge(node[0], node[1])

    # get sum of edge weights
    if node[0] not in NODE_SUM_CONFLICTS.keys():
        NODE_SUM_CONFLICTS[node[0]] = int(node[2])
    else:
        NODE_SUM_CONFLICTS[node[0]] += int(node[2])
    if node[1] not in NODE_SUM_CONFLICTS.keys():
        NODE_SUM_CONFLICTS[node[1]] = int(node[2])
    else:
        NODE_SUM_CONFLICTS[node[1]] += int(node[2])

# create subgraph from connected components of graph G
SG = [
    G.subgraph(c).copy()
    for c in sorted(nx.connected_components(G), key=len, reverse=True)
]

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


def linear_pen(x):
    return 500 * (x - 80)


def expo_pen(x):
    return (500 * (x - 80)) + (2**(2*((x / 10) - 1))) - (2**18)


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


def calc_each_penalty(pen_count):
    pen_value = {1: 0, 2: 10000, 3: 78, 4: 78, 5: 38, 6: 29, 7: 12}
    penalty = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    for i in range(1, 8):
        penalty[i] = pen_value[i] * pen_count[i]
    return penalty


def create_table(solution):
    table = {}
    for k, v in solution.items():
        if int(v) not in table:
            table[int(v)] = [k]
        else:
            table[int(v)].append(k)
    return table


def count_penalty2(solution, start_slot, end_slot):
    timetable = create_table(solution)
    pen_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
    for slot in range(start_slot, end_slot + 1):
        if slot in timetable.keys():
            courses = timetable[slot]
        else:
            continue
        courses_set = set(courses)
        course_to_remove = set()
        for c in courses:
            neighbor_set = set(G.neighbors(c))
            neighbor_in_currslot = neighbor_set.intersection(courses_set)
            neighbor_in_currslot = neighbor_in_currslot.difference(course_to_remove)
            course_to_remove.add(c)
            overlap_count = 0
            for n in neighbor_in_currslot:
                if c + "_" + n != n + "_" + c:
                    overlap_count += CONFLICT_DICT.get(c + "_" + n, 0)
                    overlap_count += CONFLICT_DICT.get(n + "_" + c, 0)
                else:
                    overlap_count += CONFLICT_DICT.get(c + "_" + n, 0)
            pen_count[2] += overlap_count
            if slot % 3 == 0:
                consecutive_a_count = 0
                if slot + 1 in timetable.keys():
                    neighbor_in_nextslot = neighbor_set.intersection(
                        timetable[slot + 1]
                    )
                    for n in neighbor_in_nextslot:
                        consecutive_a_count += CONFLICT_DICT.get(c + "_" + n, 0)
                        consecutive_a_count += CONFLICT_DICT.get(n + "_" + c, 0)
                pen_count[3] += consecutive_a_count

                consecutive_c_count = 0
                if slot + 2 in timetable.keys():
                    neighbor_in_next2slot = neighbor_set.intersection(
                        timetable[slot + 2]
                    )
                    for n in neighbor_in_next2slot:
                        consecutive_c_count += CONFLICT_DICT.get(c + "_" + n, 0)
                        consecutive_c_count += CONFLICT_DICT.get(n + "_" + c, 0)
                pen_count[5] += consecutive_c_count
            elif slot % 3 == 1:
                consecutive_b_count = 0
                if slot + 1 in timetable.keys():
                    neighbor_in_nextslot = neighbor_set.intersection(
                        timetable[slot + 1]
                    )
                    for n in neighbor_in_nextslot:
                        consecutive_b_count += CONFLICT_DICT.get(c + "_" + n, 0)
                        consecutive_b_count += CONFLICT_DICT.get(n + "_" + c, 0)
                pen_count[4] += consecutive_b_count
            elif slot % 3 == 2 and slot != TOTAL_SLOTS - 1:
                consecutive_d_count = 0
                if slot + 1 in timetable.keys():
                    neighbor_in_nextslot = neighbor_set.intersection(
                        timetable[slot + 1]
                    )
                    for n in neighbor_in_nextslot:
                        consecutive_d_count += CONFLICT_DICT.get(c + "_" + n, 0)
                        consecutive_d_count += CONFLICT_DICT.get(n + "_" + c, 0)
                pen_count[6] += consecutive_d_count
    return pen_count




STUDENT_CLEAN = get_slot(COURSE_LIST, STUDENTS)
STUDENT_DUP_COUNT = {str(s): STUDENT_CLEAN.count(s) for s in STUDENT_CLEAN}


# print("Total courses:", TOTAL_COURSES)
# print("Total students:", len(STUDENTS))
# print("Total students having an exam:", len(STUDENT_CLEAN))
# print("--- Clean data time %s seconds ---" % ((time.time() - START_TIME)))


class Schedule(object):
    """
    Class representing Schedule
    """

    def __init__(self, solution):
        self.solution = solution
        # self.wait_count = self.count_wait_penalty()
        self.penalty_count = count_penalty2(self.solution, 0, 41)
        self.wait_count = self.count_all_wait_penalty()
        self.penalty_count[7] = self.wait_count
        self.penalty_value = calc_each_penalty(self.penalty_count)
        self.penalty_value[1] = sum(capacity_penalty_value_slot.values())
        self.penalty_count[1] = sum(x > 0 for x in capacity_penalty_value_slot.values())
        self.total_penalty = self.calc_total_penalty(self.penalty_value)

    @classmethod
    def create_sorted_node(self, g, option):
        """
        Return tuple of nodes sort by degree -> number of student enrolled -> number of conflicts
        """
        global STD_ENROLL_COURSES, NODE_SUM_CONFLICTS
        g_tuple = []

        if option == "-std":
            for i in list(g.degree):
                course = i[0]
                degree = i[1]
                g_tuple.append(
                    (STD_ENROLL_COURSES[course], degree, NODE_SUM_CONFLICTS.get(course, 0), course)
                )
        if option == "-deg":
            for i in list(g.degree):
                course = i[0]
                degree = i[1]
                g_tuple.append(
                    (degree, STD_ENROLL_COURSES[course], NODE_SUM_CONFLICTS.get(course, 0), course)
                )

        return sorted(g_tuple, reverse=True)

    @classmethod    
    def sort_nodes_neighbor(self, neighbors, nodes_tuple):

        nodes = []
        for n in neighbors:
            for i in range(len(nodes_tuple)):
                if nodes_tuple[i][3] == n:
                    nodes.append(nodes_tuple[i])

        sorted_nodes = sorted(nodes, reverse=True)
        ret_node = [n[3] for n in sorted_nodes]
        return ret_node



    @classmethod
    def create_schedule(self):
        """
        Find schedule by graph coloring
        """
        global SLOT_CAPACITY, capacity_penalty_value_slot
        solution = {}
        option1 = OPTION[:4]
        option2 = OPTION[4:]

        for g in SG:

            sorted_nodes = self.create_sorted_node(g,option1)

            if option2 == "-bfs":
                root = sorted_nodes[0][3]
                edges = nx.bfs_edges(
                    g,
                    root,
                    sort_neighbors=lambda neighbors: self.sort_nodes_neighbor(neighbors,sorted_nodes)
                )
                nodes_seq = [root] + [v for u, v in edges]
            else:
                nodes_seq = [node for deg, std_en, conf, node in sorted_nodes]

            for n in nodes_seq:
                slots = set([slot for slot in range(TOTAL_SLOTS)])
                color = set([solution[c] for c in set(g.neighbors(n)) if c in solution.keys()])
                slots = slots.difference(color)
                
                node_n = n
                if len(n) > 6:
                    node_n = n[:-4]

                course_fa = COURSE_FACULTY.get(node_n,"99")
                total_std_in_course = STD_ENROLL_COURSES[n]
                used_capa = {}
                capacity_penalty = {}
                slot_penalty = {}

                for s in SLOTS:
                    solution[n] = s
                    if s % 3 == 0 and s != 0:
                        penalty_count = count_penalty2(solution, s - 1, s + 2)
                    elif s % 3 == 1:
                        penalty_count = count_penalty2(solution, s - 1, s + 1)
                    elif s % 3 == 2 and s != TOTAL_SLOTS-1:
                        penalty_count = count_penalty2(solution, s - 2, s + 1)
                    elif s == 0:
                        penalty_count = count_penalty2(solution, s, s + 2)
                    elif s == TOTAL_SLOTS-1:
                        penalty_count = count_penalty2(solution, s - 2, s)
                    
                    if node_n == "001101" or node_n == "001102" or node_n == "001201":
                        capa_pen, all_used_capa = calc_capacity_penalty_for_eng(course_fa, s ,total_std_in_course,MAX_CAPACITY)
                        used_capa[s] = all_used_capa
                    else:
                        capa_pen, used_fa, used_rb = calc_capacity_penalty_v1(course_fa, s, total_std_in_course, MAX_CAPACITY)
                        # Exclude CITIZENSHIP course -> online exam
                        if node_n == "140104":
                            capa_pen = 0
                            used_fa = 0
                            used_rb = 0
                        
                        used_capa[s] = {}
                        used_capa[s]["fa"] = used_fa
                        used_capa[s]["RB"] = used_rb
                    capacity_penalty[s] = capa_pen

                    penalty_value = sum(calc_each_penalty(penalty_count).values())
                    penalty_value += capacity_penalty[s]
                    slot_penalty[s] = penalty_value

                if slots:
                    for k in color:
                        slot_penalty.pop(k, None)

                lowest_pen_tuple = min(slot_penalty.items(), key=lambda x: x[1])
                lowest_pen = lowest_pen_tuple[1]

                lowest_pen_slot = [
                    k for k, v in slot_penalty.items() if v == lowest_pen
                ]
                slot_sorted = sorted(lowest_pen_slot, key=lambda slot: ((slot+2)%3, slot//3))
                solution[n] = slot_sorted[0]

                if node_n == "001101" or node_n == "001102" or node_n == "001201":
                    for fa, capa in used_capa[slot_sorted[0]].items():
                        SLOT_CAPACITY[slot_sorted[0]][fa] += capa
                else:
                    SLOT_CAPACITY[slot_sorted[0]][course_fa] += used_capa[slot_sorted[0]]["fa"]
                    SLOT_CAPACITY[slot_sorted[0]]["RB"] += used_capa[slot_sorted[0]]["RB"]

                if capacity_penalty[slot_sorted[0]] > 0:
                    if slot_sorted[0] not in capacity_penalty_value_slot.keys():
                        capacity_penalty_value_slot[slot_sorted[0]] = capacity_penalty[slot_sorted[0]]
                    else:
                        capacity_penalty_value_slot[slot_sorted[0]] += capacity_penalty[slot_sorted[0]]
        return solution

    # TODO Add fuction descriptions

    def pen_first_slot(self, first_slot):
        return 1 if first_slot > 9 else 0  # No exam more than 3 days

    def pen_wait3day(self, s1, s2):  # No exam more than 3 days
        return 1 if abs(s1 // 3 - s2 // 3) > 3 else 0

    def count_wait_penalty(self, student_slot):

        student_slot.sort()
        wait_count = 0

        count = self.pen_first_slot(student_slot[0])
        wait_count += count

        for i in range(len(student_slot) - 1):
            count = self.pen_wait3day(student_slot[i], student_slot[i + 1])
            wait_count += count

        return wait_count

    def count_all_wait_penalty(self):

        global STUDENT_DUP_COUNT

        # penalties = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
        total_wait_count = 0

        # For each student
        for s, st_count in STUDENT_DUP_COUNT.items():

            student_slot = []

            # Convert course-code to exam-slot
            for key in ast.literal_eval(s):
                student_slot.append(self.solution[key])

            wait_count = self.count_wait_penalty(student_slot)
            # Multiply duplicate student count with pen_count
            wait_count *= st_count
            total_wait_count += wait_count
        return total_wait_count

    def calc_total_penalty(self, pen_calc):
        """
        Calculate fittness score
        """

        total_penalty = sum(pen_calc.values())

        return total_penalty


def main():
    sol = Schedule.create_schedule()
    schedule = Schedule(sol)

    print("Total penalty of solution:", schedule.total_penalty)
    print("Each penalty value of solution:")
    for k, v in schedule.penalty_value.items():
        print(str(int(k)) + ": " + str(v))
    print("Each penalty count of solution:")
    for k, v in schedule.penalty_count.items():
        print(str(int(k)) + ": " + str(v))

    with open(out_folder_path +"graph-coloring-solution"+outout_file_postfix+".txt",
        "a",
        encoding="utf-8-sig",
    ) as ch:
        for k in sorted(schedule.solution.keys()):
            ch.write(str(k) + " " + str(schedule.solution[k]) + "\n")
    
    print("Solution saved to "+out_folder_path+"graph-coloring-solution"+outout_file_postfix+"-"+str(TOTAL_SLOTS)+".txt ...")
    print("--- Execution time %s seconds ---" % ((time.time() - START_TIME)))


if __name__ == "__main__":
    main()
