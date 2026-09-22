import urllib.request
import json

BASE = 'http://localhost:8000/api'

def req(url, data=None, method='GET'):
    r = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={'Content-Type': 'application/json'},
        method=method
    )
    with urllib.request.urlopen(r) as res:
        return json.loads(res.read().decode())

def run_tests():
    print("=== 1. Checking GET /attendance (Initial State) ===")
    att_day = req(f"{BASE}/attendance?outlet_id=1")
    print(f"Total employees: {att_day['total_employees']}, Present count: {att_day['present_count']}")
    assert att_day['total_employees'] >= 3

    print("\n=== 2. Testing POST /attendance/clock-in ===")
    cin = req(f"{BASE}/attendance/clock-in", {
        "outlet_id": 1,
        "employee_id": 2,
        "notes": "Hadir Uji Coba"
    }, method="POST")
    print(f"Clock In OK: ID={cin['id']}, Employee={cin['employee_name']}, Time={cin['clock_in']}")
    assert cin["employee_name"] == "Risa Aprilia Wahyudi"

    print("\n=== 3. Checking Active Status ===")
    att_day2 = req(f"{BASE}/attendance?outlet_id=1")
    emp2 = next(e for e in att_day2['employees'] if e['employee_id'] == 2)
    print(f"Employee 2 status: {emp2['attendance_status']}, Current In: {emp2['clock_in']}")
    assert emp2['attendance_status'] == 'working'
    assert att_day2['active_working_count'] >= 1

    print("\n=== 4. Testing PUT /attendance/{id}/clock-out ===")
    cout = req(f"{BASE}/attendance/{cin['id']}/clock-out", {
        "notes": "Selesai Shift"
    }, method="PUT")
    print(f"Clock Out OK: Out={cout['clock_out']}, Work Minutes={cout['work_minutes']}")
    assert cout["clock_out"] is not None

    print("\n=== 5. Checking Status After Clock Out ===")
    att_day3 = req(f"{BASE}/attendance?outlet_id=1")
    emp2_after = next(e for e in att_day3['employees'] if e['employee_id'] == 2)
    print(f"Employee 2 status now: {emp2_after['attendance_status']}, Total Work: {emp2_after['work_minutes']} min")
    assert emp2_after['attendance_status'] == 'clocked_out'

    print("\n=== 6. Testing Monthly Summary ===")
    summary = req(f"{BASE}/attendance/summary?outlet_id=1")
    print(f"Summary Month: {summary['month']}, Items: {len(summary['items'])}")
    for item in summary["items"]:
        print(f"  - {item['employee_name']}: {item['total_days_present']} hari, {item['total_work_hours']} jam")

    print("\n=== 7. Cleaning Up Test Attendance Record ===")
    del_res = req(f"{BASE}/attendance/{cin['id']}", method="DELETE")
    print(f"Cleaned up: {del_res}")

    print("\n>>> ALL TESTS COMPLETED AND VERIFIED 100% SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
