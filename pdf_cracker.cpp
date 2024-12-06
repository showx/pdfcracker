#include <Python.h>
#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>

static std::atomic<bool> stop_flag(false);
static std::atomic<uint64_t> total_attempts(0);

// 信号处理函数
void handle_signal(int signal) {
    stop_flag = true;
}

// 尝试密码的函数
bool try_password(PyObject* pdf_reader, const std::string& password) {
    PyGILState_STATE gstate = PyGILState_Ensure();
    
    PyObject* result = PyObject_CallMethod(pdf_reader, "decrypt", "s", password.c_str());
    bool success = (result != nullptr && PyObject_IsTrue(result));
    
    Py_XDECREF(result);
    PyGILState_Release(gstate);
    
    return success;
}

// 破解函数
PyObject* crack_range(PyObject* pdf_reader, uint64_t start, uint64_t end) {
    for (uint64_t num = start; num <= end; ++num) {
        if (stop_flag) {
            break;
        }
        
        std::string password = std::to_string(num);
        total_attempts++;
        
        if (try_password(pdf_reader, password)) {
            return PyUnicode_FromString(password.c_str());
        }
    }
    
    Py_RETURN_NONE;
}

// Python模块方法
static PyObject* crack_pdf_range(PyObject* self, PyObject* args) {
    PyObject* pdf_reader;
    unsigned long long start, end;
    int num_threads;
    
    if (!PyArg_ParseTuple(args, "OKKi", &pdf_reader, &start, &end, &num_threads)) {
        return nullptr;
    }
    
    // 重置计数器
    total_attempts = 0;
    stop_flag = false;
    
    // 设置信号处理
    signal(SIGINT, handle_signal);
    
    // 创建线程
    std::vector<std::thread> threads;
    std::vector<PyObject*> results(num_threads, nullptr);
    
    uint64_t range_size = (end - start + 1) / num_threads;
    
    for (int i = 0; i < num_threads; ++i) {
        uint64_t thread_start = start + i * range_size;
        uint64_t thread_end = (i == num_threads - 1) ? end : thread_start + range_size - 1;
        
        threads.emplace_back([=, &results]() {
            results[i] = crack_range(pdf_reader, thread_start, thread_end);
        });
    }
    
    // 等待所有线程完成
    for (auto& thread : threads) {
        thread.join();
    }
    
    // 检查结果
    for (PyObject* result : results) {
        if (result && result != Py_None) {
            return result;
        }
    }
    
    Py_RETURN_NONE;
}

// 获取尝试次数的方法
static PyObject* get_attempts(PyObject* self, PyObject* args) {
    return PyLong_FromUnsignedLongLong(total_attempts);
}

// 停止破解的方法
static PyObject* stop_cracking(PyObject* self, PyObject* args) {
    stop_flag = true;
    Py_RETURN_NONE;
}

// 模块方法定义
static PyMethodDef CrackerMethods[] = {
    {"crack_pdf_range", crack_pdf_range, METH_VARARGS, "Crack PDF password in range"},
    {"get_attempts", get_attempts, METH_NOARGS, "Get total attempts"},
    {"stop_cracking", stop_cracking, METH_NOARGS, "Stop cracking"},
    {nullptr, nullptr, 0, nullptr}
};

// 模块定义
static struct PyModuleDef crackermodule = {
    PyModuleDef_HEAD_INIT,
    "pdfcracker",
    nullptr,
    -1,
    CrackerMethods
};

// 模块初始化函数
PyMODINIT_FUNC PyInit_pdfcracker(void) {
    return PyModule_Create(&crackermodule);
} 