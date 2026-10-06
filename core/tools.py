from typing import Dict, Any, Optional, List
from core.database import (
    get_student, get_student_attendance, get_student_results, get_rules_by_parameter, get_connection
)

def get_attendance_tool(student_id: str, course_code: str) -> Dict[str, Any]:
    records = get_student_attendance(student_id, course_code)
    if not records:
        return {
            "status": "error",
            "message": f"No attendance record found for student {student_id} in course {course_code}"
        }
    rec = records[0]
    held = rec["classes_held"]
    attended = rec["classes_attended"]
    pct = round((attended / held) * 100, 2) if held > 0 else 0.0
    
    return {
        "status": "success",
        "student_id": student_id,
        "course_code": course_code,
        "course_name": rec.get("course_name", course_code),
        "classes_held": held,
        "classes_attended": attended,
        "attendance_pct": pct
    }

def check_exam_eligibility_tool(student_id: str, course_code: str, as_of_date: str = "2026-10-06") -> Dict[str, Any]:
    att_res = get_attendance_tool(student_id, course_code)
    if att_res.get("status") == "error":
        return att_res
        
    pct = att_res["attendance_pct"]
    
    # Read rules from rule registry
    min_att_rules = get_rules_by_parameter("min_attendance_pct")
    rule = min_att_rules[0] if min_att_rules else {
        "rule_id": "ATT-MIN-01",
        "value": "75%",
        "source_doc_id": "ACAD-REG-2024",
        "source_section": "Clause 11.2"
    }
    
    applied_rules = [{
        "rule_id": rule["rule_id"],
        "value": rule["value"],
        "source_doc_id": rule["source_doc_id"],
        "section": rule["source_section"]
    }]
    
    if pct >= 75.0:
        decision = "ELIGIBLE"
        explanation = f"Your attendance in {course_code} is {pct}%, which is at or above the minimum required threshold of 75.0% specified in {rule['source_doc_id']} {rule['source_section']}."
    elif pct >= 65.0:
        decision = "CONDITIONALLY_ELIGIBLE"
        applied_rules.append({
            "rule_id": "ATT-RELAX-DEAN",
            "value": "<=10%",
            "source_doc_id": "ACAD-REG-2024",
            "section": "Clause 11.3"
        })
        explanation = f"Your attendance in {course_code} is {pct}%, which is below the 75.0% threshold. However, under Clause 11.3, Dean Academics may allow up to 10% relaxation on genuine medical/authorized grounds upon timely document submission to HoD."
    elif pct >= 60.0:
        decision = "CRITICAL_SHORTAGE"
        applied_rules.append({
            "rule_id": "ATT-RELAX-COMM",
            "value": "<=5%",
            "source_doc_id": "ACAD-REG-2024",
            "section": "Clause 11.4"
        })
        explanation = f"Your attendance in {course_code} is {pct}%. This requires exceptional committee relaxation under Clause 11.4. You are at high risk of detention."
    else:
        decision = "DETAINED"
        applied_rules.append({
            "rule_id": "ATT-HARD-FLOOR",
            "value": ">=60%",
            "source_doc_id": "ACAD-REG-2024",
            "section": "Clause 11.6"
        })
        applied_rules.append({
            "rule_id": "ATT-DETENTION-FD",
            "value": "FD_GRADE",
            "source_doc_id": "ACAD-REG-2024",
            "section": "Clause 11.7"
        })
        explanation = f"Your attendance in {course_code} is {pct}%, which is strictly below the 60.0% absolute floor (Clause 11.6). Under Clause 11.7, you are detained ('FD' grade) and cannot appear in the end-semester exam."

    return {
        "status": "success",
        "result": decision,
        "classes_held": att_res["classes_held"],
        "classes_attended": att_res["classes_attended"],
        "attendance_pct": pct,
        "applied_rules": applied_rules,
        "explanation": explanation
    }

def check_supplementary_eligibility_tool(student_id: str, course_code: str, as_of_date: str = "2026-10-06") -> Dict[str, Any]:
    results = get_student_results(student_id, course_code)
    if not results:
        return {
            "status": "error",
            "message": f"No examination records found for student {student_id} in {course_code}"
        }
    latest_result = results[0]
    res_status = latest_result["result"]
    marks = latest_result["total_marks"]
    
    applied_rules = []
    
    if res_status == "DETAINED":
        applied_rules.append({
            "rule_id": "SUPP-DETENTION-BAR",
            "value": "FD_GRADE_INELIGIBLE",
            "source_doc_id": "ACAD-CIRCULAR-2026-08",
            "section": "Clause 3"
        })
        return {
            "status": "success",
            "result": "INELIGIBLE",
            "reason": "DETENTION_FD",
            "applied_rules": applied_rules,
            "explanation": f"Student was detained ('FD' grade) in {course_code}. Under Circular ACAD-CIRCULAR-2026-08 (Clause 3) and Regulation Clause 11.7, detained students are prohibited from supplementary exams and must re-register for the course."
        }
    elif res_status in ("FAIL", "ABSENT"):
        applied_rules.append({
            "rule_id": "SUPP-ELIG-01",
            "value": "ALLOWED_IF_NOT_DETAINED",
            "source_doc_id": "ACAD-CIRCULAR-2026-08",
            "section": "Clause 2"
        })
        return {
            "status": "success",
            "result": "ELIGIBLE",
            "prior_marks": marks,
            "applied_rules": applied_rules,
            "explanation": f"Student secured an 'F' grade (marks: {marks}/100) in {course_code}. Per Circular ACAD-CIRCULAR-2026-08 (Clause 2), students who failed in regular exam and were not detained are eligible to appear in the supplementary examination."
        }
    else:
        return {
            "status": "success",
            "result": "NOT_APPLICABLE",
            "explanation": f"Student already passed {course_code} with {marks}/100 marks. Supplementary examination is not applicable."
        }

def check_placement_eligibility_tool(student_id: str, as_of_date: str = "2026-10-06") -> Dict[str, Any]:
    student = get_student(student_id)
    if not student:
        return {"status": "error", "message": f"Student {student_id} not found."}
        
    cgpa = student["cgpa"]
    backlogs = student["active_backlogs"]
    
    applied_rules = [
        {
            "rule_id": "PLACE-MIN-CGPA",
            "value": ">=7.00",
            "source_doc_id": "PLACEMENT-POL-2024",
            "section": "Clause 3.2"
        },
        {
            "rule_id": "PLACE-MAX-BACKLOG",
            "value": "==0",
            "source_doc_id": "PLACEMENT-POL-2024",
            "section": "Clause 3.3"
        }
    ]
    
    cgpa_ok = cgpa >= 7.00
    backlog_ok = backlogs == 0
    
    if cgpa_ok and backlog_ok:
        eligible = "ELIGIBLE"
        explanation = f"Eligible for on-campus placements. CGPA is {cgpa} (>= 7.00 threshold) and active backlogs are 0 (Clause 3.2 & 3.3)."
    else:
        eligible = "INELIGIBLE"
        reasons = []
        if not cgpa_ok:
            reasons.append(f"CGPA {cgpa} is below the 7.00 threshold (Clause 3.2)")
        if not backlog_ok:
            reasons.append(f"Has {backlogs} active backlogs; maximum permitted is 0 (Clause 3.3)")
        explanation = f"Ineligible for placements: {', '.join(reasons)}."
        
    return {
        "status": "success",
        "result": eligible,
        "cgpa": cgpa,
        "active_backlogs": backlogs,
        "applied_rules": applied_rules,
        "explanation": explanation
    }

def simulate_what_if_tool(student_id: str, course_code: str, hypothesis: str = "pass_supplementary") -> Dict[str, Any]:
    """
    R6 Multi-step / what-if calculation tool
    """
    student = get_student(student_id)
    if not student:
        return {"status": "error", "message": f"Student {student_id} not found."}
        
    supp_check = check_supplementary_eligibility_tool(student_id, course_code)
    current_cgpa = student["cgpa"]
    current_backlogs = student["active_backlogs"]
    
    assumptions = [
        f"Assumed event: Student clears supplementary exam in {course_code}",
        f"Assumed active backlogs reduce from {current_backlogs} to {max(0, current_backlogs - 1)}",
        "Assumed CGPA remains at or above 7.00 after backlog clearance"
    ]
    
    simulated_backlogs = max(0, current_backlogs - 1)
    placement_eligible_after_pass = (current_cgpa >= 7.00) and (simulated_backlogs == 0)
    
    applied_rules = [
        {
            "rule_id": "SUPP-ELIG-01",
            "value": "ALLOWED_IF_NOT_DETAINED",
            "source_doc_id": "ACAD-CIRCULAR-2026-08",
            "section": "Clause 2"
        },
        {
            "rule_id": "PLACE-BACKLOG-CLEAR",
            "value": "CLEAR_BEFORE_DRIVE",
            "source_doc_id": "PLACEMENT-POL-2024",
            "section": "Clause 3.4"
        }
    ]
    
    if placement_eligible_after_pass:
        outcome = "YES_ELIGIBLE"
        explanation = (
            f"If you clear the supplementary exam in {course_code}, your active backlogs will reduce to {simulated_backlogs}. "
            f"Since your CGPA is {current_cgpa} (which meets the >= 7.00 cut-off), you will become eligible for campus placements "
            f"under Placement Policy Clause 3.4."
        )
    else:
        outcome = "STILL_INELIGIBLE"
        reasons = []
        if current_cgpa < 7.00:
            reasons.append(f"CGPA is {current_cgpa} (< 7.00)")
        if simulated_backlogs > 0:
            reasons.append(f"still have {simulated_backlogs} remaining backlogs")
        explanation = f"Even if you pass {course_code}, you will remain ineligible because {', '.join(reasons)}."
        
    return {
        "status": "success",
        "hypothesis": hypothesis,
        "course_code": course_code,
        "assumptions_stated": assumptions,
        "projected_backlogs": simulated_backlogs,
        "projected_placement_status": outcome,
        "applied_rules": applied_rules,
        "explanation": explanation
    }
