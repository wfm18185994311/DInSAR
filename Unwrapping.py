import os
import re
import subprocess

# 执行 gpt 命令
def execute_gpt(xml_file_path, gpt_cmd):
    try:
        command = [gpt_cmd, xml_file_path]
        print(f"Executing GPT command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"GPT command output: {result.stdout}")
        return result.stdout  # 返回 GPT 命令的输出路径
    except subprocess.CalledProcessError as e:
        print(f"Error executing GPT command: {e.stderr}")
        raise

# 查找 snaphu.conf 文件并执行 snaphu 命令
def list_files_and_snaphu_command(base_dir):
    # 获取 base_dir 下所有子文件夹
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not subdirs:
        print(f"No subdirectories found in {base_dir}")
        return

    # 按照修改时间排序，获取最新的子文件夹
    latest_subdir = max(subdirs, key=lambda d: os.path.getmtime(os.path.join(base_dir, d)))
    latest_subdir_path = os.path.join(base_dir, latest_subdir)
    print(f"Latest subdirectory: {latest_subdir_path}\n")

    # 查找 snaphu.conf 文件
    snaphu_conf_path = os.path.join(latest_subdir_path, 'snaphu.conf')
    if os.path.isfile(snaphu_conf_path):
        print(f"\nFound snaphu.conf file at {snaphu_conf_path}")

        with open(snaphu_conf_path, 'r') as f:
            # 逐行读取文件并查找以 snaphu -f snaphu.conf 开头的命令
            for line_num, line in enumerate(f, start=1):
                stripped_line = line.strip()  # 去掉行首和行尾的空白和换行符
                match = re.match(r'#\s*(snaphu -f snaphu\.conf[^\n]*)', stripped_line)
                if match:
                    # 提取并打印匹配的命令
                    snaphu_command = match.group(1)
                    print(f"Found snaphu command: {snaphu_command}")

                    # 在 snaphu.conf 所在的目录下运行命令
                    snaphu_dir = os.path.dirname(snaphu_conf_path)
                    print(f"Changing directory to: {snaphu_dir}")
                    os.chdir(snaphu_dir)

                    try:
                        # 使用 subprocess.Popen 实时输出命令的结果
                        print(f"Executing snaphu command: {snaphu_command}")
                        process = subprocess.Popen(
                            snaphu_command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        # 实时输出标准输出和标准错误
                        for stdout_line in iter(process.stdout.readline, b''):
                            print(stdout_line.decode(), end='')  # 输出标准输出
                        for stderr_line in iter(process.stderr.readline, b''):
                            print(stderr_line.decode(), end='')  # 输出标准错误
                        process.stdout.close()
                        process.stderr.close()
                        process.wait()

                        # 检查命令是否执行成功
                        if process.returncode != 0:
                            print(f"snaphu command failed with return code {process.returncode}")
                        else:
                            print("snaphu command executed successfully.")
                    except Exception as e:
                        print(f"Error executing snaphu command: {e}")
                    break
    else:
        print("\nNo snaphu.conf file found in the latest subdirectory.")

# 数据处理流程
def process_gpt_and_snaphu(config):
    try:
        interferogram_path = config["interferogram_path"]
        output_directory = config["output_directory"]
        gpt_cmd = config["gpt_cmd"]
        xml_file_path = config["xml_file_path"]

        # 1. 执行 GPT 命令，获取输出路径
        output_from_gpt = execute_gpt(xml_file_path, gpt_cmd)

        # 2. 使用 GPT 输出路径作为输入，查找并执行 snaphu 命令
        print(f"Using GPT output directory: {output_directory}")
        list_files_and_snaphu_command(output_directory)

    except Exception as e:
        print(f"Error during processing: {e}")
        raise

# 调用示例
if __name__ == "__main__":
    config = {
        "interferogram_path": "/data/wangfengmao_file/aipy/py/test/input/S1A_IW_SLC__1SDV_20220110T231926_20220110T231953_041405_04EC57_103E_interferogram_goldstein.dim",
        "output_directory": "/data/wangfengmao_file/aipy/py/test/output/snaphu",
        "snaphu_cmd": "/home/administrator/.snap/auxdata/snaphu-v2.0.4_linux/bin/snaphu",  # SNAPHU命令
        "gpt_cmd": "gpt",  # GPT命令路径
        "xml_file_path": "/home/administrator/Desktop/myGraph.xml"  # 固定 XML 文件路径
    }

    # 调用数据处理函数
    process_gpt_and_snaphu(config)
