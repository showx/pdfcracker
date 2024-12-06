import os
import sys
import time
import signal
import PyPDF2
import pdfcracker
import multiprocessing

class PDFCrackerCPP:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        
    def check_file(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
    
    def crack(self, start_num=888, end_num=100000000):
        self.check_file()
        
        # 检查PDF是否加密
        pdf_file = open(self.pdf_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        if not pdf_reader.is_encrypted:
            print("该PDF文件未加密!")
            return None
            
        # 获取CPU核心数
        num_threads = multiprocessing.cpu_count() * 2
        print(f"使用 {num_threads} 个线程进行破解...")
        print(f"范围: {start_num} - {end_num}")
        print("按Ctrl+C可以随时停止破解\n")
        
        start_time = time.time()
        last_update = time.time()
        
        try:
            while True:
                # 调用C++破解函数
                password = pdfcracker.crack_pdf_range(pdf_reader, start_num, end_num, num_threads)
                
                # 更新进度显示
                current_time = time.time()
                if current_time - last_update >= 0.1:
                    attempts = pdfcracker.get_attempts()
                    elapsed_time = current_time - start_time
                    speed = attempts / elapsed_time if elapsed_time > 0 else 0
                    progress = (attempts / (end_num - start_num + 1)) * 100
                    
                    print(f"\r进度: {progress:.1f}% "
                          f"速度: {speed:.0f} 次/秒 "
                          f"已尝试: {attempts}", end='')
                    
                    last_update = current_time
                
                if password:
                    end_time = time.time()
                    attempts = pdfcracker.get_attempts()
                    print(f"\n\n成功找到密码: {password}")
                    print(f"尝试次数: {attempts}")
                    print(f"总用时: {end_time - start_time:.2f} 秒")
                    print(f"平均速度: {attempts/(end_time - start_time):.2f} 次/秒")
                    return password
                    
                if pdfcracker.get_attempts() >= (end_num - start_num + 1):
                    break
                    
        except KeyboardInterrupt:
            print("\n\n破解已取消")
        finally:
            pdfcracker.stop_cracking()
            attempts = pdfcracker.get_attempts()
            print(f"已尝试 {attempts} 个密码")
            print(f"总用时: {time.time() - start_time:.2f} 秒")
        
        return None

if __name__ == "__main__":
    try:
        pdf_path = input("请输入PDF文件路径: ")
        start = int(input("请输入起始数字(默认888): ") or "888")
        end = int(input("请输入结束数字(默认100000000): ") or "100000000")
        
        cracker = PDFCrackerCPP(pdf_path)
        cracker.crack(start, end)
        
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        sys.exit(0) 