import os
import shutil
import gettext
import sys
from pathlib import Path

def main():
    """修复翻译文件并编译"""
    print("开始修复翻译文件...")
    
    # 确保我们在正确的目录
    project_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_dir)
    
    # 创建正确的目录结构
    for lang in ['en', 'de', 'zh_hans']:
        os.makedirs(f'locale/{lang}/LC_MESSAGES', exist_ok=True)
    
    # 修复德语翻译
    with open('locale/de/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.write('''# German translation
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-08-17 10:00+0000\\n"
"PO-Revision-Date: 2025-08-17 10:00+0000\\n"
"Last-Translator: Anonymous\\n"
"Language-Team: German\\n"
"Language: de\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "太阳能模拟器"
msgstr "Solarsimulator"

msgid "首页"
msgstr "Startseite"

msgid "太阳能模拟演示 - 所有数据仅供参考，实际性能可能因天气、设备效率等因素而异"
msgstr "Solar-Simulationsdemonstration - Alle Daten dienen nur als Referenz, die tatsächliche Leistung kann aufgrund von Wetter, Geräteeffizienz und anderen Faktoren variieren"
''')

    # 修复英语翻译
    with open('locale/en/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.write('''# English translation
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-08-17 10:00+0000\\n"
"PO-Revision-Date: 2025-08-17 10:00+0000\\n"
"Last-Translator: Anonymous\\n"
"Language-Team: English\\n"
"Language: en\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "太阳能模拟器"
msgstr "Solar Simulator"

msgid "首页"
msgstr "Home"

msgid "太阳能模拟演示 - 所有数据仅供参考，实际性能可能因天气、设备效率等因素而异"
msgstr "Solar Simulation Demo - All data is for reference only, actual performance may vary due to weather, equipment efficiency, and other factors"
''')

    # 修复中文翻译
    with open('locale/zh_hans/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.write('''# Chinese translation
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-08-17 10:00+0000\\n"
"PO-Revision-Date: 2025-08-17 10:00+0000\\n"
"Last-Translator: Anonymous\\n"
"Language-Team: Chinese\\n"
"Language: zh_hans\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"

msgid "太阳能模拟器"
msgstr "太阳能模拟器"

msgid "首页"
msgstr "首页"

msgid "太阳能模拟演示 - 所有数据仅供参考，实际性能可能因天气、设备效率等因素而异"
msgstr "太阳能模拟演示 - 所有数据仅供参考，实际性能可能因天气、设备效率等因素而异"
''')

    # 尝试编译翻译文件
    try:
        print("正在手动编译翻译文件...")
        
        # 创建msgfmt.py脚本（这是Django用来编译.mo文件的工具）
        with open('msgfmt.py', 'w', encoding='utf-8') as f:
            f.write("""
# Written by Martin v. Loewis <loewis@informatik.hu-berlin.de>
#
# Modified by Christian Heimes <cheimes@apache.org>
# Modified by CZ <github.com/czlucius>
# Use 'msgfmt.py [--use-fuzzy] infile.po [outfile.mo]'
#
import array
import ast
import gettext
import os
import struct
import sys

MESSAGES = {}

def add(msgid, transtr, fuzzy):
    global MESSAGES
    if not fuzzy and transtr and transtr != msgid:
        MESSAGES[msgid] = transtr

def generate():
    global MESSAGES
    # 现在创建输出文件
    output = array.array("I")
    keys = sorted(MESSAGES.keys())

    # 头部
    output.append(0x950412de)  # magic number
    output.append(0)           # version
    output.append(len(keys))   # number of entries
    output.append(7*4)         # start of key index
    output.append(7*4+len(keys)*8)  # start of value index
    output.append(0)           # size of hash table
    output.append(0)           # unused

    # key和value索引
    keystart = 7*4+len(keys)*8
    valuestart = keystart
    for key in keys:
        value = MESSAGES[key].encode('utf-8')
        # 添加key
        keydata = key.encode('utf-8')
        keylen = len(keydata)
        valuestart = valuestart + keylen + 1
        output.append(keystart)
        output.append(keylen)
        keystart = keystart + keylen + 1

        # 添加value
        valuelen = len(value)
        output.append(valuestart)
        output.append(valuelen)
        valuestart = valuestart + valuelen + 1

    output = output.tobytes()
    
    # 添加key和value数据
    for key in keys:
        keydata = key.encode('utf-8')
        output = output + keydata + b'\\0'
    
    for key in keys:
        value = MESSAGES[key].encode('utf-8')
        output = output + value + b'\\0'
    
    return output

def process_po_file(filename):
    global MESSAGES
    MESSAGES = {}
    fuzzy = False
    msgid = None
    msgstr = None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"无法读取文件 {filename}: {e}")
        return None
    
    for line in lines:
        line = line.strip()
        if not line:
            # 空行标志一个条目的结束
            if msgid is not None:
                add(msgid, msgstr, fuzzy)
                fuzzy = False
            msgid = None
            msgstr = None
            continue
        
        if line[0] == '#':
            # 注释行
            if line.find('fuzzy') >= 0:
                fuzzy = True
            continue
        
        if line.startswith('msgid '):
            if msgid is not None:
                add(msgid, msgstr, fuzzy)
                fuzzy = False
                msgstr = None
            msgid = ast.literal_eval(line[6:])
        elif line.startswith('msgstr '):
            msgstr = ast.literal_eval(line[7:])
        elif msgid is not None and line.startswith('"') and line.endswith('"'):
            # 多行msgid/msgstr
            if msgstr is not None:
                msgstr += ast.literal_eval(line)
            else:
                msgid += ast.literal_eval(line)
    
    # 最后一个条目
    if msgid:
        add(msgid, msgstr, fuzzy)
    
    # 生成二进制数据
    return generate()

def main():
    if len(sys.argv) < 2:
        print("使用: msgfmt.py [--use-fuzzy] infile.po [outfile.mo]")
        return 1
    
    use_fuzzy = False
    if sys.argv[1] == "--use-fuzzy":
        use_fuzzy = True
        del sys.argv[1]
    
    if len(sys.argv) < 2:
        print("没有指定输入文件")
        return 1
    
    infile = sys.argv[1]
    if not infile.endswith('.po'):
        print("文件必须以.po结尾")
        return 1
    
    if len(sys.argv) > 2:
        outfile = sys.argv[2]
    else:
        outfile = os.path.splitext(infile)[0] + '.mo'
    
    try:
        binary_data = process_po_file(infile)
        if binary_data:
            with open(outfile, 'wb') as f:
                f.write(binary_data)
            print(f"成功写入 {outfile}")
            return 0
        else:
            print(f"处理 {infile} 时出错")
            return 1
    except Exception as e:
        print(f"出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
""")
        
        # 编译所有翻译文件
        for lang in ['en', 'de', 'zh_hans']:
            po_file = f'locale/{lang}/LC_MESSAGES/django.po'
            mo_file = f'locale/{lang}/LC_MESSAGES/django.mo'
            cmd = f'{sys.executable} msgfmt.py {po_file} {mo_file}'
            print(f"执行: {cmd}")
            os.system(cmd)
            
        # 删除临时脚本
        if os.path.exists('msgfmt.py'):
            os.remove('msgfmt.py')
            
        print("翻译文件编译完成")
        
    except Exception as e:
        print(f"编译翻译文件时出错: {e}")
    
    # 修复settings.py中语言配置
    settings_file = 'solar_project/settings.py'
    
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        # 确保使用正确的语言代码顺序，把英语放在第一位
        if 'LANGUAGES = [' in settings_content:
            settings_content = settings_content.replace(
                "LANGUAGES = [\n    ('zh-hans', '中文'),\n    ('en', 'English'),\n    ('de', 'Deutsch'),\n]",
                "LANGUAGES = [\n    ('en', 'English'),\n    ('de', 'Deutsch'),\n    ('zh-hans', '中文'),\n]"
            )
            
            # 确保USE_I18N和其他必要的设置存在
            if 'USE_I18N = True' not in settings_content:
                settings_content = settings_content.replace(
                    'USE_TZ = True',
                    'USE_I18N = True\nUSE_L10N = True\nUSE_TZ = True'
                )
            
            # 写回修改后的文件
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(settings_content)
                print(f"已更新 {settings_file}")
        else:
            print(f"无法在 {settings_file} 中找到 LANGUAGES 设置")
    else:
        print(f"找不到 {settings_file}")
    
    print("\n修复完成！请重启Django服务器来应用更改。")

if __name__ == "__main__":
    main()
