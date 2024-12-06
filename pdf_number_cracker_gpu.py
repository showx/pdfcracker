import PyPDF2
import time
import os
import sys
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda
from pycuda.compiler import SourceModule

# CUDA C代码，用于密码生成和测试
cuda_code = """
__global__ void generate_passwords(int start_num, int *results, int max_attempts) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < max_attempts) {
        results[idx] = start_num + idx;
    }
}
"""

class PDFCrackerGPU:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.mod = SourceModule(cuda_code)
        self.generate_passwords = self.mod.get_function("generate_passwords")
        
    def check_file(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
            
    def try_passwords_batch(self, passwords):
        """在CPU上测试一批密码"""
        pdf_file = open(self.pdf_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        try:
            for password in passwords:
                try:
                    if pdf_reader.decrypt(str(password)):
                        return str(password)
                except:
                    continue
            return None
        finally:
            pdf_file.close()

    def crack(self, start_num=888, end_num=100000000, batch_size=10000):
        self.check_file()
        
        # 检查PDF是否加密
        pdf_file = open(self.pdf_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        if not pdf_reader.is_encrypted:
            print("该PDF文件未加密!")
            return None
        pdf_file.close()

        print(f"使用GPU进行破解，范围: {start_num} - {end_num}")
        print("按Ctrl+C可以随时停止破解\n")
        
        # 获取GPU信息
        device = cuda.Device(0)
        print(f"使用GPU: {device.name()}")
        print(f"计算能力: {device.compute_capability()}")
        print(f"最大线程数: {device.max_threads_per_block}\n")

        start_time = time.time()
        total_attempts = 0
        
        try:
            # 分批处理
            for batch_start in range(start_num, end_num, batch_size):
                batch_end = min(batch_start + batch_size, end_num)
                current_batch_size = batch_end - batch_start
                
                # 在GPU上生成密码
                results = np.zeros(current_batch_size, dtype=np.int32)
                results_gpu = cuda.mem_alloc(results.nbytes)
                
                # 配置GPU网格和块大小
                block_size = 256
                grid_size = (current_batch_size + block_size - 1) // block_size
                
                # 在GPU上生成密码
                self.generate_passwords(
                    np.int32(batch_start),
                    results_gpu,
                    np.int32(current_batch_size),
                    block=(block_size, 1, 1),
                    grid=(grid_size, 1)
                )
                
                # 将结果复制回CPU
                cuda.memcpy_dtoh(results, results_gpu)
                
                # 在CPU上测试密码
                password = self.try_passwords_batch(results)
                if password:
                    end_time = time.time()
                    print(f"\n\n成功找到密码: {password}")
                    print(f"尝试次数: {total_attempts + len(results)}")
                    print(f"总用时: {end_time - start_time:.2f} 秒")
                    print(f"平均速度: {(total_attempts + len(results))/(end_time - start_time):.2f} 次/秒")
                    return password
                
                # 更新进度
                total_attempts += current_batch_size
                elapsed_time = time.time() - start_time
                speed = total_attempts / elapsed_time if elapsed_time > 0 else 0
                progress = (total_attempts / (end_num - start_num)) * 100
                
                print(f"\r进度: {progress:.1f}% "
                      f"速度: {speed:.0f} 次/秒 "
                      f"已尝试: {total_attempts}", end='')
                
            print("\n\n未能找到密码")
            print(f"已尝试 {total_attempts} 个密码")
            print(f"总用时: {time.time() - start_time:.2f} 秒")
            return None
            
        except KeyboardInterrupt:
            print("\n\n破解已取消")
            print(f"已尝试 {total_attempts} 个密码")
            print(f"总用时: {time.time() - start_time:.2f} 秒")
            return None
        except Exception as e:
            print(f"\n\n发生错误: {e}")
            return None

if __name__ == "__main__":
    try:
        # 检查CUDA是否可用
        try:
            import pycuda.autoinit
        except:
            print("错误: 未检测到CUDA设备或CUDA未正确安装")
            print("请确保：")
            print("1. 您的电脑有NVIDIA显卡")
            print("2. 已安装CUDA工具��")
            print("3. 已安装PyCUDA (pip install pycuda)")
            sys.exit(1)
            
        pdf_path = input("请输入PDF文件路径: ")
        start = int(input("请输入起始数字(默认888): ") or "888")
        end = int(input("请输入结束数字(默认100000000): ") or "100000000")
        batch = int(input("请输入批处理大小(默认10000): ") or "10000")
        
        cracker = PDFCrackerGPU(pdf_path)
        cracker.crack(start, end, batch)
        
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        sys.exit(0) 