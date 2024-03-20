from py2neo import Graph

# 连接到Neo4j数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "your_password"))

# 要查询的特定节点ID
specific_id = "your_specific_id_here"

# Cypher查询，获取指定节点的所有邻居和边的权重
query = """
MATCH (n)-[r:RELATES]->(m)
WHERE n.nodeId = $specific_id
RETURN m.nodeId AS neighborId, r.Weight AS weight
"""

# 执行查询
results = graph.run(query, specific_id=specific_id)

# 打印结果
for result in results:
    print(f"Neighbor ID: {result['neighborId']}, Weight: {result['weight']}")
