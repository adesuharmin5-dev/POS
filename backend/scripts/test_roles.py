"""Test Role CRUD endpoints for Aurora Cafe POS"""
import urllib.request
import json

BASE = 'http://127.0.0.1:8000/api'

def req(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload else None
    headers = {'Content-Type': 'application/json'} if data else {}
    r = urllib.request.Request(f'{BASE}{path}', data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# 1. GET roles
code, roles = req('/auth/roles')
print(f'GET /roles: {code} | {len(roles)} jabatan: {[r["name"] for r in roles]}')
assert code == 200, f"Expected 200 got {code}"

# 2. POST new role
payload = {'name': 'Supervisor Test', 'description': 'Test role', 'permissions': json.dumps(['pos', 'reports'])}
code, created = req('/auth/roles', 'POST', payload)
print(f'POST /roles: {code} | id={created.get("id")}, name={created.get("name")}, emp_count={created.get("employee_count")}')
assert code == 200, f"Expected 200 got {code}: {created}"
rid = created['id']

# 3. PUT update
code, updated = req(f'/auth/roles/{rid}', 'PUT', {'name': 'Supervisor Senior', 'description': 'Updated test role'})
print(f'PUT /roles/{rid}: {code} | name={updated.get("name")}')
assert code == 200, f"Expected 200 got {code}: {updated}"

# 4. DELETE
code, deleted = req(f'/auth/roles/{rid}', 'DELETE')
print(f'DELETE /roles/{rid}: {code} | {deleted.get("message")}')
assert code == 200, f"Expected 200 got {code}: {deleted}"

# 5. Guard: cannot delete role with id=1 (Owner/Admin)
code, guarded = req('/auth/roles/1', 'DELETE')
print(f'Guard DELETE /roles/1: {code} | {guarded.get("detail")}')
assert code == 400, f"Expected 400 got {code}: {guarded}"

# 6. GET employees still works
code, emps = req('/auth/employees?outlet_id=1')
print(f'GET /employees: {code} | {len(emps)} karyawan')
assert code == 200, f"Expected 200 got {code}"

# 7. Duplicate name guard
payload2 = {'name': 'Owner / Admin', 'description': 'Duplicate test'}
code, dup = req('/auth/roles', 'POST', payload2)
print(f'Duplicate guard POST /roles: {code} | {dup.get("detail")}')
assert code == 400, f"Expected 400 got {code}: {dup}"

print()
print("=== ALL TESTS PASSED ===")
