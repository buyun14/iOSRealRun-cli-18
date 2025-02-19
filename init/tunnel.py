import re
import logging
import subprocess
import multiprocessing

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def start_tunnel(queue):
    command = ['python3', '-m', 'pymobiledevice3', 'remote', 'start-tunnel']

    logging.info("Tunnel started")

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    rsd_pattern = re.compile(r"--rsd (\S+) (\d+)")
    address, port = None, None

    while True:
        output = process.stdout.readline().strip()
        if output:
            logging.info(output)

        match = rsd_pattern.search(output)
        if match:
            address, port = match.group(1), int(match.group(2))
            queue.put((address, port))
            logging.info(f"RSD Address: {address}, RSD Port: {port}")
            break

    process.wait()

def tunnel():
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=start_tunnel, args=(queue,))
    process.start()
    
    try:
        result = queue.get(timeout=20)
        if result is None:
            raise RuntimeError("❌ 无法建立隧道连接")
        address, port = result
        
        return process, address, port
    except Exception as e:
        logging.error(f"❌ 隧道建立失败: {e}")
        process.terminate()
        process.join(timeout=2)
        if process.is_alive():
            process.kill()

    return None, None, None

# if __name__ == "__main__":
#     address, port = start_tunnel()
#     print(f"RSD Address: {address}, RSD Port: {port}....")
