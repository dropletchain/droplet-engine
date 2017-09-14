from flask import Flask
from flask import request, g
from ipfs_util import run_ipfs_load
import json
import argparse


FILE = "bench"
app = Flask("IPFS_Benchmark_Server")


@app.route('/ipfs_bench', methods=['POST'])
def run_benchmark():
    addresses = str(request.get_data())
    try:
        data = addresses.splitlines()
        times = run_ipfs_load(data)
        with open("%s" % (FILE,), 'w') as file:
            for time in times:
                file.write("%f\n" % time)
        return json.dumps(times)
    except Exception as e:
        print e
        return "ERROR", 400

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run Basic IPFS bench Server")
    parser.add_argument('--port', type=int, help='port', default=12000, required=False)
    parser.add_argument('--ip', type=str, help='ip', default="127.0.0.1", required=False)
    args = parser.parse_args()
    app.run(host=args.ip, port=args.port)