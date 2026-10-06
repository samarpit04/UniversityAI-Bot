import csv
import json
from pathlib import Path
from core.database import (
    init_db, get_connection, insert_source_document
)

# University Documents
DOCUMENTS = [
    {
        "doc_id": "ACAD-REG-2024",
        "title": "NSUT Academic Regulations and Ordinances for B.Tech",
        "issuer": "Office of the Dean (Academics)",
        "authority_level": 1,
        "doc_type": "regulation",
        "version": "3.1",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "supersedes": "ACAD-REG-2021#7.2",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "provenance": "NSUT Academic Council Portal",
        "retrieved_on": "2026-10-05",
        "synthetic": "N",
        "content": """
Netaji Subhas University of Technology (NSUT) - Academic Regulations (B.Tech)

Section 8: Grading and Promotion
8.1 Passing Marks: A student must obtain a minimum of 40% aggregate marks (combined internal and end-semester external) in a theory course to obtain a PASS grade (Letter grade P or higher). Marks strictly below 40% receive an 'F' (Fail) grade.
8.2 Maximum Backlogs: A student is promoted to the next academic year provided they do not carry more than 4 active backlogs from previous semesters.

Section 11: Attendance and Detention
11.1 Students of the programme are expected to attend every lecture, tutorial and practical class scheduled for them.
11.2 Minimum Attendance Requirement: The students must have a minimum attendance of 75% of the total number of classes including lectures, tutorials and practicals, held in a subject till MSE/ESE in order to be eligible to appear in the MSE/ESE for that subject.
11.3 Medical & Authorized Activities Relaxation: The Dean Academics may allow relaxation in the minimum requirement of attendance upto 10% for reasons to be recorded. This relaxation may be granted on the production of documents showing that the student was either busy in any authorized activities or was absent due to medical/other genuine reasons. The student should submit these documents to the HoD, within seven days of resuming the studies. Certificates submitted later will not be considered.
11.4 Exceptional Relaxation: Under exceptional circumstances, the Dean Academics may further relax the minimum attendance up to 5% on recommendation of a committee comprising of Dean Student Welfare, Dean of Faculty and HoD of the respective department.
11.5 Relaxation Limit: Relaxation in attendance maybe granted for a maximum of 2 times during the duration of the programme.
11.6 Absolute Minimum Floor: A student shall not be permitted to appear in the MSE/ESE if his/her attendance till MSE/ESE is below 60% after relaxation given in clauses 11.3 and 11.4.
11.7 Detention and FD Grade: Students who are not allowed to appear in the ESE due to shortage of attendance shall be awarded 'FD' (Failed due to Detention) grade. Such students shall have to register again for that course in subsequent years/summer semester to pass the course. They are strictly prohibited from appearing in the supplementary examination for that course.
11.8 Elective Re-registration: A student can register again for a different elective course in subsequent years/summer semester and pass the elective course.
11.9 Count of Attendance: The attendance shall be counted from the date of start of academic session. For first year students, attendance shall be counted from the date of the start of academic session or actual date of admission, whichever is later.
"""
    },
    {
        "doc_id": "NSUT-ATT-2026-09",
        "title": "Notification Regarding Attendance (Strict Compliance for Mid/End Sem)",
        "issuer": "Assistant Registrar, Academics",
        "authority_level": 2,
        "doc_type": "circular",
        "version": "1.0",
        "effective_from": "2026-09-15",
        "effective_to": "",
        "supersedes": "",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "provenance": "F.No. 220(312)/ShortAtt/2026-27/Acad/NSIT/1005",
        "retrieved_on": "2026-10-05",
        "synthetic": "N",
        "content": """
NETAJI SUBHAS UNIVERSITY OF TECHNOLOGY (NSUT)
Azad Hind Fauj Marg, Sector-3, Dwarka, New Delhi-110078
F.No. 220(312)/ShortAtt/2026-27/Acad/NSIT/1005 Dated: 15/9/26

NOTIFICATION REGARDING ATTENDANCE
All students of the University are hereby directed to visit the CUMS portal through their respective Login IDs and regularly check their attendance status, which is being updated daily.

Students are hereby informed that if their attendance is less than 75%, they shall be detained from appearing in the upcoming End-Semester Examination. Students are advised to ensure that they maintain the required attendance well before the Mid-Semester Examination, as there shall be no shortage of attendance condonation at the Mid-Semester Examination. They will not claim any attendance relaxation during End Semester Examination.

The current attendance status is available on the CUMS portal. In case of any discrepancy, students should immediately contact the concerned Faculty Member/Course Instructor. If required, the concerned HOD may also be contacted for necessary clarification/updation.

Students are further informed that the attendance portal shall be locked on or before the Mid-Semester Examination, and no correction/alteration in attendance shall be entertained thereafter. There shall be strict compliance with the Academic Rules and Regulations of NSUT.
"""
    },
    {
        "doc_id": "NSUT-UFM-2024",
        "title": "NSUT: Dealing With Unfair Means and Examination Conduct Rules",
        "issuer": "Controller of Examinations (CoE)",
        "authority_level": 1,
        "doc_type": "regulation",
        "version": "2.0",
        "effective_from": "2024-08-01",
        "effective_to": "",
        "supersedes": "",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "provenance": "NSUT Examination Division Ordinance",
        "retrieved_on": "2026-10-05",
        "synthetic": "N",
        "content": """
NSUT: DEALING WITH UNFAIR MEANS
Table: Punishment details for the use of unfair means in University examinations

Part A: Minor Infractions (Disobedience, writing on question paper, talking)
- Offence 1-9: Doesn't follow instructions, talks after caution, writing on question paper, indecent words.
- Punishment:
  * Mid Semester: Written warning issued by CoE not to repeat in future.
  * End Semester: Written warning not to repeat. If repeated, cancellation of examination of concerned paper, deemed to have secured zero mark in paper cancelled.

Part B: Possession of unauthorised material / chits without copying / unauthorised gadgets
- Offence 1-5: Found in possession of relevant notes/chits, reveals identity, brings electronic gadgets (except non-programmable scientific calculator), attempts to bribe.
- Punishment:
  * Mid Semester: Theory examination of concerned paper cancelled and deemed to have secured Zero marks in concerned paper only.
  * End Semester: Cancellation of examination of concerned paper, declared result on remaining papers, deemed zero mark.

Part C: Actual Copying / Electronic gadgets / Exchange of answer books
- Offence 1: Examinee copied from exam material, scribbled on chits/body/desk, or found in possession of mobile-phone, smart watch, pen with voice recording, Bluetooth/wi-fi devices.
- Offence 2-9: Exchange of answer book, tearing answer book, destroying chits.
- Punishment:
  * Mid Semester: Theory examination of concerned paper cancelled, deemed to have secured zero marks in concerned paper.
  * End Semester: Cancellation of concerned paper with zero marks. In addition, punishment may be extended to cancellation of the entire examination in that semester at the discretion of the Standing UFM Committee.

Part D: Obstruction, impersonation, swallowing chits
- Offence: Threatening invigilator, bringing answer book from outside, impersonation, swallowing notes.
- Punishment: Cancellation of the entire examination taken by the examinee during that semester (both semesters for End Semester).

Part E: Weapons, Violence, Gross Misbehaviour
- Offence 1-2: Possesses Gun, Revolver, Knife, or physical force/threat to examination staff.
- Punishment: Cancellation of entire examination taken during the year (both semesters) and further debarring from appearing at any examination of the University for a span of one year (12 months).

Part F: Supplementary Paper Unfair Means
- Found with bulk material or cheating in supplementary paper:
- Punishment: Cancellation of examination of supplementary paper, zero marks, and will not be allowed to appear in the paper for the next one year.
"""
    },
    {
        "doc_id": "ACAD-CIRCULAR-2026-08",
        "title": "Circular on Supplementary Examination Eligibility & Re-appear Norms",
        "issuer": "Office of the Dean (Academics)",
        "authority_level": 2,
        "doc_type": "circular",
        "version": "1.2",
        "effective_from": "2026-08-01",
        "effective_to": "",
        "supersedes": "ACAD-REG-2024#7.2",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "provenance": "Dean Academics Official Circular",
        "retrieved_on": "2026-10-05",
        "synthetic": "N",
        "content": """
OFFICE OF THE DEAN (ACADEMICS) - NSUT
Circular No. NSUT/ACAD/2026/08 Dated: 01/08/2026

Sub: Supplementary Examination and Improvement Guidelines - Supersession of Clause 7.2

1. Explicit Supersession: This circular explicitly supersedes Clause 7.2 of the Academic Regulations (ACAD-REG-2024).
2. Supplementary Eligibility: A student who obtained grade 'F' in a regular semester examination is eligible to appear in the supplementary examination held in the immediate subsequent break, PROVIDED the student has not been detained under Clause 11.7 ('FD' grade).
3. Attendance requirement for supplementary: No separate attendance is required to appear for the supplementary examination once eligible. However, a student detained ('FD' grade) cannot clear the course via supplementary examination under any circumstance; they must re-register in regular/summer semester.
"""
    },
    {
        "doc_id": "DEPT-FAQ-2026-09",
        "title": "Department Student FAQ on Attendance Rules",
        "issuer": "Department Student Helpdesk",
        "authority_level": 4,
        "doc_type": "faq",
        "version": "1.0",
        "effective_from": "2026-09-15",
        "effective_to": "",
        "supersedes": "",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "provenance": "Student Council Notice Board & FAQ Forum",
        "retrieved_on": "2026-10-05",
        "synthetic": "Y",
        "content": """
DEPARTMENT OF COMPUTER SCIENCE - STUDENT FAQ (September 2026)

Q: What is the minimum attendance required for appearing in exams?
A: Generally 65% is enough if you submit medical certificates to the department representative before the end of semester.

Note: This FAQ is informal guidance provided by student representatives. (Informational Level 4 document).
"""
    },
    {
        "doc_id": "PLACEMENT-POL-2024",
        "title": "NSUT Campus Placement Policy & Eligibility Norms",
        "issuer": "Training and Placement Cell (T&P)",
        "authority_level": 1,
        "doc_type": "regulation",
        "version": "2.1",
        "effective_from": "2024-06-01",
        "effective_to": "",
        "supersedes": "",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "provenance": "T&P Cell Official Portal",
        "retrieved_on": "2026-10-05",
        "synthetic": "N",
        "content": """
TRAINING AND PLACEMENT CELL - NETAIJI SUBHAS UNIVERSITY OF TECHNOLOGY
Campus Placement Policy 2024-2026

Section 3: Student Eligibility for On-Campus Placement Drives
3.1 Minimum Academic Standing: A student must be enrolled in the penultimate or final year of their B.Tech programme.
3.2 CGPA Cut-off: The standard university benchmark for placement drive registration is a minimum CGPA of 7.00. Individual recruiting companies may prescribe higher cut-offs.
3.3 Active Backlogs: A candidate MUST have zero (0) active backlogs at the time of registering for placement season.
3.4 Backlog Clearance: If a student clears their backlogs in a supplementary examination and their result is officially declared before the drive registration deadline, they become eligible for subsequent placement drives provided their CGPA is >= 7.00.
3.5 Disciplinary Standing: Any student found guilty of Unfair Means (UFM) under Part C, D, or E within the academic year shall be debarred from placement assistance.
"""
    }
]

COURSES = [
    ("CS201", "Data Structures", "B.Tech CSE", 3, 4),
    ("CS202", "Operating Systems", "B.Tech CSE", 3, 4),
    ("CS203", "Database Management Systems", "B.Tech CSE", 3, 4),
    ("EC201", "Signals and Systems", "B.Tech ECE", 3, 4),
    ("EC202", "Digital Electronics", "B.Tech ECE", 3, 4),
    ("MA201", "Applied Mathematics III", "B.Tech", 3, 4),
]

RULE_REGISTRY = [
    {
        "rule_id": "ATT-MIN-01",
        "description": "Minimum attendance required to appear for end-semester examinations",
        "parameter": "min_attendance_pct",
        "operator": ">=",
        "value": "75%",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "source_doc_id": "ACAD-REG-2024",
        "source_section": "Clause 11.2"
    },
    {
        "rule_id": "ATT-RELAX-DEAN",
        "description": "Dean Academics attendance relaxation for medical or authorized activities",
        "parameter": "dean_attendance_relaxation_pct",
        "operator": "<=",
        "value": "10%",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "source_doc_id": "ACAD-REG-2024",
        "source_section": "Clause 11.3"
    },
    {
        "rule_id": "ATT-RELAX-COMM",
        "description": "Committee attendance relaxation under exceptional circumstances",
        "parameter": "committee_attendance_relaxation_pct",
        "operator": "<=",
        "value": "5%",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "source_doc_id": "ACAD-REG-2024",
        "source_section": "Clause 11.4"
    },
    {
        "rule_id": "ATT-HARD-FLOOR",
        "description": "Absolute attendance floor below which no student may appear under any relaxation",
        "parameter": "absolute_min_attendance_pct",
        "operator": ">=",
        "value": "60%",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "source_doc_id": "ACAD-REG-2024",
        "source_section": "Clause 11.6"
    },
    {
        "rule_id": "EXAM-PASS-MIN",
        "description": "Minimum aggregate marks required to pass a subject",
        "parameter": "min_pass_marks",
        "operator": ">=",
        "value": "40",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "source_doc_id": "ACAD-REG-2024",
        "source_section": "Clause 8.1"
    },
    {
        "rule_id": "SUPP-ELIG-01",
        "description": "Supplementary exam allowed for regular failed students who are not detained ('FD')",
        "parameter": "supplementary_allowed_if_not_detained",
        "operator": "==",
        "value": "TRUE",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "effective_from": "2026-08-01",
        "effective_to": "",
        "source_doc_id": "ACAD-CIRCULAR-2026-08",
        "source_section": "Clause 2"
    },
    {
        "rule_id": "PLACE-MIN-CGPA",
        "description": "Minimum CGPA cut-off for campus placement drive registration",
        "parameter": "min_placement_cgpa",
        "operator": ">=",
        "value": "7.00",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "effective_from": "2024-06-01",
        "effective_to": "",
        "source_doc_id": "PLACEMENT-POL-2024",
        "source_section": "Clause 3.2"
    },
    {
        "rule_id": "PLACE-MAX-BACKLOG",
        "description": "Maximum active backlogs allowed for placement eligibility",
        "parameter": "max_active_backlogs",
        "operator": "==",
        "value": "0",
        "scope_programmes": "B.Tech",
        "scope_batches": "ALL",
        "effective_from": "2024-06-01",
        "effective_to": "",
        "source_doc_id": "PLACEMENT-POL-2024",
        "source_section": "Clause 3.3"
    }
]

# Generate synthetic students with exact edge cases (Annex C)
# Edge cases:
# - S1001: Standard eligible student, 77.5% attendance, CGPA 8.42, 0 backlogs
# - S1002: Attendance EXACTLY at threshold (30/40 = 75.0% in CS201), CGPA 7.80, 0 backlogs
# - S1003: Attendance ONE class below threshold (29/40 = 72.5% in CS201), needs medical condonation, CGPA 6.90
# - S1004: Detained student (attendance < 60%, 22/40 = 55.0% in CS201, result 'DETAINED' / FD grade), ineligible for supplementary
# - S1005: Failed course just below pass mark (39/100 in CS201, pass is 40), eligible for supplementary exam! CGPA 7.10, 1 backlog
# - S1006: Multiple backlogs (2 backlogs: CS201 failed, MA201 absent), CGPA 6.10, ineligible for placement
# - S1007: CGPA EXACTLY at placement cut-off (7.00 CGPA, 0 backlogs, 80% attendance)
# - S1008 - S1035: Diverse synthetic population across CSE and ECE programmes, batches 2023 and 2024.

def generate_students_and_records():
    students = []
    attendance_records = []
    results = []

    # Defined edge-case profiles
    profiles = [
        # (id, name, prog, batch, sem, cgpa, backlogs, cs201_held, cs201_att, exam_res, exam_marks)
        ("S1001", "Aarav Sharma", "B.Tech CSE", 2023, 5, 8.42, 0, 40, 31, "PASS", 84),      # 77.5% attendance
        ("S1002", "Bhavya Gupta", "B.Tech CSE", 2023, 5, 7.80, 0, 40, 30, "PASS", 76),      # Exactly 75.0% attendance
        ("S1003", "Chirag Verma", "B.Tech CSE", 2023, 5, 6.95, 0, 40, 29, "PASS", 68),      # 72.5% attendance (one below)
        ("S1004", "Deepak Kumar", "B.Tech CSE", 2023, 5, 5.80, 1, 40, 22, "DETAINED", 0),   # 55.0% attendance (Detained / FD)
        ("S1005", "Esha Singhal", "B.Tech CSE", 2023, 5, 7.15, 1, 40, 33, "FAIL", 39),      # 82.5% att, 39 marks (failed by 1 mark)
        ("S1006", "Farhan Ali", "B.Tech CSE", 2023, 5, 6.10, 2, 40, 31, "FAIL", 35),        # 2 backlogs (multiple backlogs)
        ("S1007", "Gauri Deshmukh", "B.Tech CSE", 2023, 5, 7.00, 0, 40, 34, "PASS", 72),    # Exactly 7.00 CGPA (border placement)
        ("S1008", "Harsh Patel", "B.Tech ECE", 2023, 5, 8.10, 0, 40, 36, "PASS", 88),
        ("S1009", "Ishita Saxena", "B.Tech ECE", 2023, 5, 7.60, 0, 40, 32, "PASS", 79),
        ("S1010", "Jai Malhotra", "B.Tech ECE", 2023, 5, 6.80, 0, 40, 30, "PASS", 65),
    ]

    # Additional students to meet 30+ students constraint
    first_names = ["Kavya", "Lakshay", "Manish", "Neha", "Omkar", "Pooja", "Qasim", "Rohan", "Sneha", "Tanmay",
                   "Urvi", "Varun", "Waseem", "Xena", "Yash", "Zoya", "Aditi", "Bharat", "Chetan", "Divya", "Ekta", "Gautam"]
    last_names = ["Mehta", "Chawla", "Bansal", "Mittal", "Nair", "Rao", "Kapoor", "Tyagi", "Reddy", "Sethi"]

    student_counter = 1011
    for i, fname in enumerate(first_names):
        s_id = f"S{student_counter}"
        student_counter += 1
        lname = last_names[i % len(last_names)]
        prog = "B.Tech CSE" if i % 2 == 0 else "B.Tech ECE"
        batch = 2023 if i < 11 else 2024
        sem = 5 if batch == 2023 else 3
        cgpa = round(6.5 + (i * 0.15) % 3.2, 2)
        backlogs = 0 if i % 4 != 0 else 1
        held = 40
        att = 30 + (i % 10)  # 30 to 39 attended
        res = "PASS" if backlogs == 0 else "FAIL"
        marks = 70 + (i * 3) % 25 if backlogs == 0 else 38
        profiles.append((s_id, f"{fname} {lname}", prog, batch, sem, cgpa, backlogs, held, att, res, marks))

    # Build DB records
    for s_id, name, prog, batch, sem, cgpa, backlogs, held, att, res, marks in profiles:
        students.append({
            "student_id": s_id,
            "full_name": name,
            "programme": prog,
            "batch_year": batch,
            "current_semester": sem,
            "cgpa": cgpa,
            "active_backlogs": backlogs
        })
        
        # Add attendance for CS201 or EC201 depending on programme
        primary_course = "CS201" if "CSE" in prog else "EC201"
        attendance_records.append({
            "student_id": s_id,
            "course_code": primary_course,
            "classes_held": held,
            "classes_attended": att
        })
        
        # Add second course attendance (MA201)
        attendance_records.append({
            "student_id": s_id,
            "course_code": "MA201",
            "classes_held": 40,
            "classes_attended": min(held, max(24, att - 2))
        })

        # Add Results
        int_m = min(40, int(marks * 0.4))
        ext_m = marks - int_m
        attendance_status = "DETAINED" if res == "DETAINED" else res
        results.append({
            "student_id": s_id,
            "course_code": primary_course,
            "exam_session": "2026-MAY",
            "exam_type": "REGULAR",
            "internal_marks": int_m,
            "external_marks": ext_m,
            "total_marks": marks,
            "max_marks": 100,
            "result": attendance_status
        })

        if s_id == "S1006":  # Second backlog for S1006 in MA201
            results.append({
                "student_id": s_id,
                "course_code": "MA201",
                "exam_session": "2026-MAY",
                "exam_type": "REGULAR",
                "internal_marks": 0,
                "external_marks": 0,
                "total_marks": 0,
                "max_marks": 100,
                "result": "ABSENT"
            })

    return students, attendance_records, results

def seed_all():
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Courses
        cursor.executemany("""
            INSERT OR REPLACE INTO courses (course_code, course_name, programme, semester, credits)
            VALUES (?, ?, ?, ?, ?)
        """, COURSES)
        
        # Rule Registry
        for r in RULE_REGISTRY:
            cursor.execute("""
                INSERT OR REPLACE INTO rule_registry (
                    rule_id, description, parameter, operator, value,
                    scope_programmes, scope_batches, effective_from, effective_to,
                    source_doc_id, source_section
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["rule_id"], r["description"], r["parameter"], r["operator"], r["value"],
                r["scope_programmes"], r["scope_batches"], r["effective_from"], r["effective_to"],
                r["source_doc_id"], r["source_section"]
            ))
            
        students, attendance, results = generate_students_and_records()
        
        for s in students:
            cursor.execute("""
                INSERT OR REPLACE INTO students (
                    student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (s["student_id"], s["full_name"], s["programme"], s["batch_year"], s["current_semester"], s["cgpa"], s["active_backlogs"]))
            
        for a in attendance:
            cursor.execute("""
                INSERT OR REPLACE INTO attendance (student_id, course_code, classes_held, classes_attended)
                VALUES (?, ?, ?, ?)
            """, (a["student_id"], a["course_code"], a["classes_held"], a["classes_attended"]))
            
        for r in results:
            cursor.execute("""
                INSERT INTO results (
                    student_id, course_code, exam_session, exam_type, internal_marks, external_marks, total_marks, max_marks, result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["student_id"], r["course_code"], r["exam_session"], r["exam_type"],
                r["internal_marks"], r["external_marks"], r["total_marks"], r["max_marks"], r["result"]
            ))
            
        conn.commit()
        
    # Seed Source Register and raw files
    docs_dir = Path("data/university_docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    for doc in DOCUMENTS:
        insert_source_document(doc)
        # Write clean txt file for doc
        filepath = docs_dir / f"{doc['doc_id']}.txt"
        with open(filepath, "w") as f:
            f.write(doc["content"])

if __name__ == "__main__":
    seed_all()
    print("Database seeded successfully with Annex C schema and Source Register!")
