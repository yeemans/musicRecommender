import os 
os.environ["clientID"] = "ea0ac735771d4e4a83cc88d91b04cc14"
os.environ["clientSecret"] = "5b43b3f4397149928983f1f9ac78d39c"

print(os.getenv("clientSecret"))