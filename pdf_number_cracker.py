import PyPDF2
import time
import os
import sys
import threading
import signal
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# 设置控制台编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 添加中断处理
def signal_handler(signum, frame):
    print("\n\n正在停止所有线程，请稍候...")
    if hasattr(signal_handler, 'cracker'):
        signal_handler.cracker.stop_flag = True
    else:
        sys.exit(0)

# 注册中断信号处理器
signal.signal(signal.SIGINT, signal_handler)

class MultiProgressBar:
    def __init__(self, total, num_threads, prefix=''):
        self.total = total
        self.num_threads = num_threads
        self.prefix = prefix
        self.thread_progress = {i: 0 for i in range(num_threads)}
        self.thread_current = {i: 0 for i in range(num_threads)}
        self.start_time = time.time()
        self.last_update = 0
        self.bar_length = 30
        
    def update(self, thread_id, current_num, n=1):
        self.thread_progress[thread_id] += n
        self.thread_current[thread_id] = current_num
        current_time = time.time()
        # 每0.1秒更新一次显示
        if current_time - self.last_update >= 0.1:
            self.display()
            self.last_update = current_time
    
    def display(self):
        total_progress = sum(self.thread_progress.values())
        elapsed_time = time.time() - self.start_time
        speed = total_progress / elapsed_time if elapsed_time > 0 else 0
        
        # 清除之前的输出
        sys.stdout.write('\033[2J\033[H')  # 清屏并移动光标到开头
        
        # 显示总体进度
        total_percent = (total_progress / self.total) * 100
        sys.stdout.write(f'{self.prefix} 总进度: {total_percent:.1f}% '
                        f'速度: {speed:.0f}次/秒 '
                        f'已用时: {elapsed_time:.1f}秒\n\n')
        
        # 显示每个线程的进度
        for thread_id in range(self.num_threads):
            progress = self.thread_progress[thread_id]
            current = self.thread_current[thread_id]
            thread_percent = (progress / (self.total / self.num_threads)) * 100
            filled = int(self.bar_length * thread_percent / 100)
            bar = '█' * filled + '-' * (self.bar_length - filled)
            sys.stdout.write(f'线程{thread_id}: |{bar}| {thread_percent:.1f}% '
                           f'当前: {current}\n')
        
        sys.stdout.flush()
    
    def close(self):
        print("\n" * (self.num_threads + 3))  # 为最终结果留出空间

class PDFNumberCracker:
    def __init__(self, pdf_path, start_num=888, end_num=100000000, num_threads=4):
        self.pdf_path = pdf_path
        self.start_num = start_num
        self.end_num = end_num
        self.num_threads = num_threads
        self.found_password = None
        self.stop_flag = False
        self.progress_lock = threading.Lock()
        self.attempts = 0
        # 保存实例到信号处理器
        signal_handler.cracker = self
        
    def try_password_range(self, start, end, thread_id, progress_bar):
        try:
            pdf_file = open(self.pdf_path, 'rb')
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for num in range(start, end + 1):
                if self.stop_flag:
                    return None
                    
                password = str(num)
                
                # 更新进度
                with self.progress_lock:
                    self.attempts += 1
                    progress_bar.update(thread_id, num)
                
                try:
                    if pdf_reader.decrypt(password):
                        self.found_password = password
                        self.stop_flag = True
                        return password
                except:
                    continue
            
            return None
        finally:
            pdf_file.close()
    
    def crack(self):
        try:
            self.check_file()
            
            # 检查PDF是否加密
            pdf_file = open(self.pdf_path, 'rb')
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            if not pdf_reader.is_encrypted:
                print("该PDF文件未加密!")
                return None
            pdf_file.close()
            
            print(f"开始{self.num_threads}线程破解，范围: {self.start_num} - {self.end_num}")
            print("按Ctrl+C可以随时停止破解\n")
            self.total_attempts = self.end_num - self.start_num + 1
            
            # 记录开始时间
            start_time = time.time()
            
            # 将范围分成多个子范围
            chunk_size = (self.end_num - self.start_num + 1) // self.num_threads
            ranges = []
            for i in range(self.num_threads):
                range_start = self.start_num + (i * chunk_size)
                range_end = range_start + chunk_size - 1 if i < self.num_threads - 1 else self.end_num
                ranges.append((range_start, range_end))
            
            # 创建多进度条
            self.progress_bar = MultiProgressBar(self.total_attempts, self.num_threads, prefix='破解进度:')
            
            # 使用线程池
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                futures = [
                    executor.submit(self.try_password_range, start, end, i, self.progress_bar)
                    for i, (start, end) in enumerate(ranges)
                ]
                
                # 等待任意一个线程找到密码或所有线程完成
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        self.stop_flag = True
                        end_time = time.time()
                        self.progress_bar.close()
                        print(f"\n成功找到密码: {result}")
                        print(f"尝试次数: {self.attempts}")
                        print(f"总用时: {end_time - start_time:.2f} 秒")
                        print(f"平均速度: {self.attempts/(end_time - start_time):.2f} 次/秒")
                        return result
            
            self.progress_bar.close()
            print("\n未能找到正确的密码")
            print(f"已尝试 {self.attempts} 个密码")
            print(f"总用时: {time.time() - start_time:.2f} 秒")
            return None

        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在停止...")
            self.stop_flag = True
            return None
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.close()
            print(f"\n已尝试 {self.attempts} 个密码")
            if not self.found_password:
                print("破解已取消")

    def check_file(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")

if __name__ == "__main__":
    try:
        # 获取CPU核心数
        cpu_count = multiprocessing.cpu_count()
        recommended_threads = cpu_count * 2
        
        pdf_path = input("请输入PDF文件路径: ").strip()
        
        # 处理起始数字输入
        while True:
            try:
                start_input = input("请输入起始数字(默认888): ").strip()
                start = int(start_input) if start_input else 888
                break
            except ValueError:
                print("请输入有效的数字")
        
        # 处理结束数字输入
        while True:
            try:
                end_input = input("请输入结束数字(默认100000000): ").strip()
                end = int(end_input) if end_input else 100000000
                break
            except ValueError:
                print("请输入有效的数字")
        
        print(f"\nCPU核心数: {cpu_count}")
        print(f"推荐线程数: {recommended_threads} (CPU核心数的2倍)")
        
        # 处理线程数输入
        while True:
            try:
                threads_input = input(f"请输入线程数量(默认{recommended_threads}): ").strip()
                threads = int(threads_input) if threads_input else recommended_threads
                break
            except ValueError:
                print("请输入有效的数字")
        
        if int(threads) > recommended_threads * 2:
            print(f"\n警告: 设置的线程数({threads})远超推荐值({recommended_threads})")
            print("过多的线程可能会降低性能而不是提升性能")
            confirm = input("是否继续？(y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消操作")
                sys.exit(0)
        
        cracker = PDFNumberCracker(
            pdf_path, 
            int(start), 
            int(end),
            int(threads)
        )
        cracker.crack()
    
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
    finally:
        sys.exit(0) 