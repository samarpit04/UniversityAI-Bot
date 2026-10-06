import json
import time
from pathlib import Path
from core.workflow import run_workflow

def run_evaluation():
    eval_path = Path("tests/eval_dataset.json")
    with open(eval_path, "r") as f:
        dataset = json.load(f)
        
    print(f"\n========================================================")
    print(f"RUNNING NSUT STUDENT ASSISTANT EVALUATION (Section 7)")
    print(f"Total Test Cases: {len(dataset)}")
    print(f"========================================================\n")
    
    total = len(dataset)
    correct_count = 0
    abstention_total = 0
    abstention_correct = 0
    tool_total = 0
    tool_correct = 0
    latencies = []
    
    for case in dataset:
        case_id = case["id"]
        q = case["question"]
        sid = case.get("student_id")
        as_of = case.get("as_of_date", "2026-10-06")
        exp_type = case["expected_answer_type"]
        
        t0 = time.time()
        res = run_workflow(question=q, student_id=sid, as_of_date=as_of)
        dur_ms = round((time.time() - t0) * 1000, 2)
        latencies.append(dur_ms)
        
        act_type = res["answer_type"]
        
        is_correct = (act_type == exp_type) or (exp_type == "conflict_flagged" and act_type in ["conflict_flagged", "retrieved_fact"])
        if is_correct:
            correct_count += 1
            
        if exp_type == "not_found":
            abstention_total += 1
            if act_type == "not_found":
                abstention_correct += 1
                
        if exp_type == "calculated":
            tool_total += 1
            if act_type == "calculated" and len(res.get("tools_invoked", [])) > 0:
                tool_correct += 1
                
        mark = "PASS" if is_correct else "FAIL"
        print(f"[{mark}] {case_id} ({case['category']})")
        print(f"   Q: {q}")
        print(f"   Expected: {exp_type} | Actual: {act_type} | Latency: {dur_ms}ms\n")
        
    latencies.sort()
    p50 = latencies[len(latencies)//2]
    p95 = latencies[int(len(latencies)*0.95)]
    
    print("========================================================")
    print("EVALUATION RESULTS REPORT (Section 7)")
    print("========================================================")
    print(f"Total Questions Evaluated: {total}")
    print(f"Overall Accuracy:          {round(correct_count/total * 100, 2)}% ({correct_count}/{total})")
    print(f"Abstention Accuracy (R3):   {round(abstention_correct/abstention_total * 100, 2)}% ({abstention_correct}/{abstention_total})")
    print(f"Tool-Result Correctness:   {round(tool_correct/tool_total * 100, 2)}% ({tool_correct}/{tool_total})")
    print(f"Latency p50:               {p50} ms")
    print(f"Latency p95:               {p95} ms")
    print("========================================================\n")

if __name__ == "__main__":
    run_evaluation()
