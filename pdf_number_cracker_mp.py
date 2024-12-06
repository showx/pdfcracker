import PyPDF2
import time
import os
import sys
import multiprocessing
from multiprocessing import Pool, Value, Manager
import signal

def init_worker():
    # 忽略子进程的Ctrl+C信号
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def try_password_range(args):
    start, end, pdf_path, counter = args
    try:
        pdf_file = open(pdf_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for num in range(start, end):
            password = str(num)
            
            # 更新计数
            with counter.get_lock():
                counter.value += 1
            
            try:
                if pdf_reader.decrypt(password):
                    return password
            except:
                continue
        
        return None
    finally:
        pdf_file.close()

def crack_pdf_mp(pdf_path, start_num=888, end_num=100000000):
    # 获取CPU核心数
    cpu_count = multiprocessing.cpu_count()
    
    # 创建共享计数器
    counter = Value('i', 0)
    
    # 计算每个进程的范围
    chunk_size = (end_num - start_num) // cpu_count
    ranges = []
    for i in range(cpu_count):
        range_start = start_num + (i * chunk_size)
        range_end = range_start + chunk_size if i < cpu_count - 1 else end_num
        ranges.append((range_start, range_end, pdf_path, counter))
    
    print(f"使用 {cpu_count} 个进程进行破解...")
    start_time = time.time()
    
    try:
        # 创建进程池
        with Pool(cpu_count, initializer=init_worker) as pool:
            # 定期显示进度
            while pool._state == 'RUN':
                total_attempts = counter.value
                elapsed_time = time.time() - start_time
                speed = total_attempts / elapsed_time if elapsed_time > 0 else 0
                progress = (total_attempts / (end_num - start_num)) * 100
                
                print(f"\r进度: {progress:.1f}% "
                      f"速度: {speed:.0f} 次/秒 "
                      f"已尝试: {total_attempts}", end='')
                
                time.sleep(0.1)
                
                # 检查是否找到密码
                if hasattr(crack_pdf_mp, 'password'):
                    return crack_pdf_mp.password
            
            # 等待所有进程完成
            results = pool.map_async(try_password_range, ranges).get(timeout=999999)
            
            # 检查结果
            for result in results:
                if result:
                    return result
            
            return None
            
    except KeyboardInterrupt:
        print("\n\n正在停止所有进程...")
        pool.terminate()
        pool.join()
        return None

if __name__ == "__main__":
    try:
        pdf_path = input("请输入PDF文件路径: ")
        start = int(input("请输入起始数字(默认888): ") or "888")
        end = int(input("请输入结束数字(默认100000000): ") or "100000000")
        
        start_time = time.time()
        password = crack_pdf_mp(pdf_path, start, end)
        
        if password:
            print(f"\n\n成功找到密码: {password}")
        else:
            print("\n\n未找到密码")
        
        print(f"总用时: {time.time() - start_time:.2f} 秒")
        
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        sys.exit(0) 