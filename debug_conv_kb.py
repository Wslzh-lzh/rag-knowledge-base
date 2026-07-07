import urllib.request
import json

BASE_URL = "http://localhost:8000/api/v1"

login_data = json.dumps({"email": "admin@example.com", "password": "Admin123!"}).encode("utf-8")
req = urllib.request.Request(
    f"{BASE_URL}/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    token = result["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 检查 d8ce3361 这个知识库
kb_id = "d8ce3361-f091-4543-9810-e00cc60460f7"
print("=" * 60)
print(f"检查对话实际绑定的知识库: {kb_id}")
print("=" * 60)

req = urllib.request.Request(f"{BASE_URL}/knowledge-bases/{kb_id}", headers=headers)
with urllib.request.urlopen(req) as resp:
    kb = json.loads(resp.read().decode("utf-8"))
    print(f"知识库名称: {kb['name']}")

req = urllib.request.Request(f"{BASE_URL}/knowledge-bases/{kb_id}/documents", headers=headers)
with urllib.request.urlopen(req) as resp:
    docs = json.loads(resp.read().decode("utf-8"))
    print(f"\n文档数量: {len(docs)}")
    for doc in docs:
        print(f"  - {doc['file_name']} (状态: {doc['parse_status']})")

# 测试这个知识库的检索
print("\n--- 测试检索 ---")
search_data = json.dumps({"query": "Python的列表和元组有什么区别", "top_k": 5}).encode("utf-8")
req = urllib.request.Request(
    f"{BASE_URL}/knowledge-bases/{kb_id}/search",
    data=search_data,
    headers={**headers, "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    results = json.loads(resp.read().decode("utf-8"))
    print(f"检索结果数量: {len(results)}")
    for i, r in enumerate(results):
        print(f"  [{i+1}] {r.get('document_name', 'N/A')} (来源: {r.get('source_type', 'N/A')})")
