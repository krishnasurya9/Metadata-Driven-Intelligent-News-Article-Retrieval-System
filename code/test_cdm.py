import sys
sys.path.append('backend')
from cdm_analytics.clustering import run_clustering
from cdm_analytics.classification import run_classification
from backend.mining_engine import generate_association_rules, analyze_temporal_patterns

print("Running Clustering...")
c = run_clustering(4)
print(f"Clustering Complete. Sampled: {c.get('sampled')}. Purity: {c.get('overall_purity')}")

print("Running Classification...")
clf = run_classification()
print(f"Classification Complete. Winner: {clf.get('winner')}")

print("CDM verified successfully!")
