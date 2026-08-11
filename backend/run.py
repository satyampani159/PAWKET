import os
os.chdir(r"D:\project\PAWKET\backend")
os.environ["ML_MODELS_DIR"] = os.path.join(os.getcwd(), "ml", "models")

import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8000)
