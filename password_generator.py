import itertools
import string
import sys

# 设置控制台编码
if sys.platform.startswith('win'):
    # Windows系统
    sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+
    # 如果上面的方法不行，可以尝试：
    # os.system('chcp 65001')  # 设置命令行窗口为UTF-8编码
else:
    # Linux/Mac系统
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

def generate_wordlist(min_length=4, max_length=8, output_file="wordlist.txt"):
    """
    生成密码字典
    :param min_length: 最小密码长度
    :param max_length: 最大密码长度
    :param output_file: 输出文件名
    """
    # 定义可能的字符集
    chars = string.ascii_letters + string.digits + string.punctuation
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # 添加一些常见密码
        common_passwords = [
            "123456", "password", "12345678", "qwerty", "111111",
            "abc123", "123123", "admin", "letmein", "welcome",
            "monkey", "password1", "123456789", "000000"
        ]
        for password in common_passwords:
            f.write(password + '\n')
        
        # 生成指定长度范围的所有可能组合
        for length in range(min_length, max_length + 1):
            print(f"正在生成长度为 {length} 的密码...")
            for pwd in itertools.product(chars, repeat=length):
                password = ''.join(pwd)
                f.write(password + '\n')
                
        print(f"密码字典已生成到文件: {output_file}")

if __name__ == "__main__":
    min_len = int(input("请输入最小密码长度(建议4): "))
    max_len = int(input("请输入最大密码长度(建议6): "))
    output = input("请输入输出文件名(默认为wordlist.txt): ") or "wordlist.txt"
    
    generate_wordlist(min_len, max_len, output) 