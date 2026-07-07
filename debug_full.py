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

kb_id = "04b48b04-5283-41be-9fa3-ba45eebc0ac8"

print("=" * 60)
print("1. 知识库详情")
print("=" * 60)
req = urllib.request.Request(f"{BASE_URL}/knowledge-bases/{kb_id}", headers=headers)
with urllib.request.urlopen(req) as resp:
    kb = json.loads(resp.read().decode("utf-8"))
    print(f"名称: {kb['name']}")
    print(f"ID: {kb['id']}")

print("\n" + "=" * 60)
print("2. 知识库的文档列表")
print("=" * 60)
req = urllib.request.Request(f"{BASE_URL}/knowledge-bases/{kb_id}/documents", headers=headers)
with urllib.request.urlopen(req) as resp:
    docs = json.loads(resp.read().decode("utf-8"))
    print(f"文档数量: {len(docs)}")
    for doc in docs:
        print(f"  - {doc['file_name']}")
        print(f"    id: {doc['id']}")
        print(f"    状态: {doc['parse_status']}")

print("\n" + "=" * 60)
print("3. 直接调用 /search 接口")
print("=" * 60)
search_data = json.dumps({"query": "Python有哪些基本数据类型？", "top_k": 5}).encode("utf-8")
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
        print(f"\n  [{i+1}] 文档名: {r.get('document_name', 'N/A')}")
        print(f"       kb_id: {r.get('kb_id', 'N/A')}")
        print(f"       分数: {r.get('similarity_score', 'N/A')}")
        print(f"       来源: {r.get('source_type', 'N/A')}")
        print(f"       chunk_id: {r.get('chunk_id', 'N/A')}")

print("\n" + "=" * 60)
print("4. 直接调用 /qa 接口")
print("=" * 60)
qa_data = json.dumps({"query": "Python有哪些基本数据类型？", "top_k": 5}).encode("utf-8")
req = urllib.request.Request(
    f"{BASE_URL}/knowledge-bases/{kb_id}/qa",
    data=qa_data,
    headers={**headers, "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    print(f"回答:\n{result['answer'][:300]}...")
    print(f"\n引用数量: {len(result['citations'])}")
    for i, c in enumerate(result['citations']):
        print(f"  [{i+1}] 文档: {c.get('document_name', 'N/A')}")
        print(f"       kb_id: {c.get('kb_id', 'N/A')}")
        print(f"       分数: {c.get('similarity_score', 'N/A')}")
    if result.get('retrieval_debug'):
        print(f"\n检索调试: {result['retrieval_debug']}")

print("\n" + "=" * 60)
print("5. 问答页面的对话列表")
print("=" * 60)
req = urllib.request.Request(f"{BASE_URL}/conversations?kb_id={kb_id}", headers=headers)
with urllib.request.urlopen(req) as resp:
    convs = json.loads(resp.read().decode("utf-8"))
    print(f"对话数量: {len(convs)}")
    for conv in convs:
        print(f"  - {conv['title']}")
        print(f"    id: {conv['id']}")
        print(f"    kb_id: {conv.get('kb_id', 'N/A')}")
