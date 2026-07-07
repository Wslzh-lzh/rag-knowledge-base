# Python 基础教程

## Python 简介

Python 是一种高级、解释型、通用的编程语言。Python 的设计哲学强调代码的可读性和简洁的语法。

## Python 基本数据类型

### 1. 数字类型 (Number)

Python 支持三种不同的数字类型：

- **整数 (int)**: 可以是任意大小的整数，如 123、-456、0
- **浮点数 (float)**: 带小数点的数字，如 3.14、-2.5、1.0
- **复数 (complex)**: 由实部和虚部组成，如 3+4j

### 2. 字符串 (String)

字符串是 Python 中最常用的数据类型。我们可以使用引号来创建字符串。

```python
str1 = 'Hello World'
str2 = "Python 编程"
str3 = '''多行
字符串'''
```

字符串常用操作：
- 拼接: `"Hello" + " " + "World"` → `"Hello World"`
- 重复: `"Hi" * 3` → `"HiHiHi"`
- 索引: `"Python"[0]` → `"P"`
- 切片: `"Python"[1:4]` → `"yth"`

### 3. 列表 (List)

列表是 Python 中使用最频繁的数据类型，用方括号 `[]` 表示。

```python
fruits = ["apple", "banana", "cherry"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]
```

列表常用方法：
- `append()`: 在列表末尾添加元素
- `pop()`: 删除并返回指定位置的元素
- `len()`: 返回列表长度
- `sort()`: 对列表进行排序

### 4. 元组 (Tuple)

元组与列表类似，不同之处在于元组的元素不能修改。元组使用小括号 `()`。

```python
tup1 = (1, 2, 3)
tup2 = ("a", "b", "c")
```

### 5. 字典 (Dictionary)

字典是无序的键值对集合，用花括号 `{}` 表示。

```python
student = {
    "name": "张三",
    "age": 20,
    "major": "计算机科学"
}
```

字典常用操作：
- 访问: `student["name"]` → `"张三"`
- 添加: `student["grade"] = "大三"`
- 删除: `del student["age"]`

### 6. 集合 (Set)

集合是一个无序的不重复元素序列，用花括号 `{}` 或 `set()` 函数创建。

```python
s1 = {1, 2, 3, 4, 5}
s2 = set([3, 4, 5, 6, 7])
```

集合常用操作：
- 并集: `s1 | s2`
- 交集: `s1 & s2`
- 差集: `s1 - s2`

### 7. 布尔值 (Boolean)

布尔值只有两个：`True` 和 `False`。

```python
is_python_fun = True
is_java_boring = False
```

## Python 运算符

### 算术运算符
- `+` 加法
- `-` 减法
- `*` 乘法
- `/` 除法
- `%` 取模
- `**` 幂运算
- `//` 取整除

### 比较运算符
- `==` 等于
- `!=` 不等于
- `>` 大于
- `<` 小于
- `>=` 大于等于
- `<=` 小于等于

### 逻辑运算符
- `and` 与
- `or` 或
- `not` 非

## Python 流程控制

### if 语句

```python
age = 18
if age >= 18:
    print("成年人")
elif age >= 12:
    print("青少年")
else:
    print("儿童")
```

### for 循环

```python
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
```

### while 循环

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## Python 函数

### 定义函数

```python
def greet(name):
    """问候函数"""
    return f"Hello, {name}!"
```

### 调用函数

```python
message = greet("World")
print(message)  # 输出: Hello, World!
```

## Python 编程技巧

### 列表推导式

列表推导式是 Python 中创建列表的简洁方式：

```python
# 普通方式
squares = []
for x in range(10):
    squares.append(x**2)

# 列表推导式
squares = [x**2 for x in range(10)]
```

### 装饰器

装饰器可以在不修改函数代码的情况下扩展函数功能：

```python
def my_decorator(func):
    def wrapper():
        print("函数执行前")
        func()
        print("函数执行后")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")
```

### 上下文管理器

使用 `with` 语句可以自动管理资源：

```python
with open("file.txt", "r") as f:
    content = f.read()
# 文件自动关闭
```

## Python 常用内置函数

- `print()`: 输出内容
- `len()`: 返回长度
- `type()`: 返回类型
- `range()`: 创建数字序列
- `str()`: 转换为字符串
- `int()`: 转换为整数
- `float()`: 转换为浮点数
- `list()`: 转换为列表
- `dict()`: 转换为字典
- `sum()`: 求和
- `max()`: 返回最大值
- `min()`: 返回最小值
