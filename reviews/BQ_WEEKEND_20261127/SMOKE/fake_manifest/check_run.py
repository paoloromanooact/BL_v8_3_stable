import json, sys
m = json.load(open(sys.argv[1] + "/META.json")); print(json.dumps({"fake": True, "status": m["status"], "stop": m.get("stop_reason")}))
