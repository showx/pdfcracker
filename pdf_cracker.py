import PyPDF2
import time
import os
import sys
import locale

# 设置控制台编码
if sys.platform.startswith('win'):
    # Windows系统
    sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+
    # 如果上面的方法不行，可以尝试：
    # os.system('chcp 65001')  # 设置命令行窗口为UTF-8编码
else:
    # Linux/Mac系统
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

class PDFCracker:
    def __init__(self, pdf_path, wordlist_path):
        self.pdf_path = pdf_path
        self.wordlist_path = wordlist_path
        
    def check_files(self):
        """检查必要文件是否存在"""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
        if not os.path.exists(self.wordlist_path):
            raise FileNotFoundError(f"密码字典不存在: {self.wordlist_path}")
    
    def crack(self):
        """开始破解PDF密码"""
        self.check_files()
        
        # 打开PDF文件
        pdf_file = open(self.pdf_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # 检查PDF是否加密
        if not pdf_reader.is_encrypted:
            print("该PDF文件未加密!")
            return None
        
        # 读取密码字典
        print("正在加载密码字典...")
        with open(self.wordlist_path, 'r', encoding='utf-8') as f:
            passwords = f.readlines()
        
        total_passwords = len(passwords)
        print(f"共加载了 {total_passwords} 个密码")
        
        # 记录开始时间
        start_time = time.time()
        
        # 尝试每个密码
        for i, password in enumerate(passwords, 1):
            password = password.strip()
            print(f"\r进度: {i}/{total_passwords} - 当前尝试: {password}", end="")
            
            try:
                if pdf_reader.decrypt(password):
                    end_time = time.time()
                    print(f"\n\n成功找到密码: {password}")
                    print(f"尝试次数: {i}")
                    print(f"总用时: {end_time - start_time:.2f} 秒")
                    return password
            except:
                continue
        
        print("\n\n未能找到正确的密码")
        return None

if __name__ == "__main__":
    pdf_path = input("请输入PDF文件路径: ")
    wordlist_path = input("请输入密码字典文件路径: ")
    
    cracker = PDFCracker(pdf_path, wordlist_path)
    cracker.crack() 