import json, sys
print(json.dumps({"kind": sys.argv[1], "ready": sys.argv[1] == "L2"})); sys.exit(0 if sys.argv[1] == "L2" else 1)
