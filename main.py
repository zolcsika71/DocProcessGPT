import sys
import os
from app import app

print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"Contents of current directory: {os.listdir('.')}")




if __name__ == "__main__":
    print("About to start Flask app...")
    app.run(host="0.0.0.0", port=5001, debug=True)
