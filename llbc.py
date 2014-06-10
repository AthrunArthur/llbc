import os
import sys
import types
import subprocess
import argparse
import platform

################################
srcs = ['main.cpp', 'bq.cpp']

class Env:
    LLVM_BIN_DIR = '/Users/xuepengfan/tools/llvm-build/bin/'
    SRC_LIST = [ os.path.join(os.getcwd(), x) for x in srcs]
    TARGET = 'bq_llvm'
    INCLUDE_DIRECTORIES = [os.path.join(os.getcwd(), '../ff/include/')]
    CXX_FLAGS=['-DUSING_FF_NONBLOCKING_QUEUE', '-DNDEBUG']
    LINK_DIRECTORIES = [os.path.join(os.getcwd(), '../bin/')]
    LINK_LIBS = ['boost_program_options', 'ff', 'pthread']

################################
class LSP:
    """
        List or String property
    """
    L = 1
    S = 2

class MRP:
    """Merge or Replace property
    """
    R = 3
    M = 4


all_items = {'CPP_HEADER_DIR':[LSP.S, MRP.R],
             'LLVM_LINKER': [LSP.S, MRP.R],
             'LLVM_EXECUTOR' : [LSP.S, MRP.R],
             'CPP_CLANG':[LSP.S, MRP.R],
             'CXX_FLAGS' : [LSP.L, MRP.M],
             'LLVM_BIN_DIR' : [LSP.S, MRP.R],
             'INCLUDE_DIRECTORIES' : [LSP.L, MRP.M],
             'SRC_LIST': [LSP.L, MRP.M],
             'OUTPUT_DIR' : [LSP.S, MRP.R],
             'TARGET' : [LSP.S, MRP.R],
             'LINK_FLAGS' :[LSP.L, MRP.M],
             'LINK_DIRECTORIES' : [LSP.L, MRP.M],
             'LINK_LIBS' : [LSP.L, MRP.M],
        }
def_env = {'CPP_HEADER_DIR' : '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/../lib/c++/v1',
           'LLVM_LINKER' : 'llvm-link',
           'LLVM_EXECUTOR' : 'lli',
           'CPP_CLANG' : 'clang++',
           'CXX_FLAGS' : ['-stdlib=libc++', '-std=c++11'],
           'OUTPUT_DIR' : os.getcwd(),
           'LINK_DIRECTORIES' : ['/usr/lib/', '/usr/local/lib']
           }

def execute_cmd(cmd):
  p = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  if len(out) != 0:
    print out
  if len(err) != 0:
    print err

def make_sure_list(label, term):
    if type(term) == type('fuck'):
        return [term]
    elif type(term) == type(['fuck']):
        return term
    else:
        print '\033[93m' + label , ' should be either a string or list<string> \033[0m'
        sys.exit(0)


def get_user_env(x):
    members = [attr for attr in dir(x()) if not callable(attr) and not attr.startswith("__") and not attr=='x']
    res = {}
    for m in members:
        v = getattr(x, m)
        if not all_items.has_key(m):
            print '\033[93m Unknown property : ' + m + '\033[0m'
        else:
            ps = all_items[m]
            if LSP.L in ps:
                res[m] = make_sure_list(m, getattr(x, m))
            else:
                res[m] = getattr(x, m)
    return res



def get_whole_environment(env):
    user_env = get_user_env(env)
    res_env = {}
    replace_items = []
    merge_items = []
    for k, v in all_items.items():
        if MRP.R in v:
            replace_items.append(k)
        if MRP.M in v:
            merge_items.append(k)
    #These items can be replaced by user defined env
    for item in replace_items:
        if user_env.has_key(item):
            res_env[item] = user_env[item]
        else:
            res_env[item] = def_env[item]

    for item in merge_items:
        if user_env.has_key(item) and def_env.has_key(item):
            res_env[item] = user_env[item] + def_env[item]
        elif user_env.has_key(item):
            res_env[item] = user_env[item]
        elif def_env.has_key(item):
            res_env[item] = def_env[item]
        else:
            res_env[item] = []

    return res_env


def generate_compile_cmd_with_single_input_and_output(env, input, output):
    cmd = os.path.join(env['LLVM_BIN_DIR'], env['CPP_CLANG']) + ' '
    for item in env['CXX_FLAGS']:
        cmd += item + ' '

    if len(env['CPP_HEADER_DIR']) != 0:
        cmd += '-I' + env['CPP_HEADER_DIR'] + ' '

    for item in env['INCLUDE_DIRECTORIES']:
        if len(item) != 0:
            cmd += '-I' + item + ' '

    cmd += '-emit-llvm' + ' '
    cmd += '-c' + ' '
    cmd += input + ' -o ' + output
    return cmd


def compile_to_bc_for_one_file(env):
    wenv = env
    if len(wenv['SRC_LIST']) == 0:
        print '\033[91m No input files, please specify \'SRC_LIST\'\033[0m'
        sys.exit(0)
    else:
        tmp_outputs = []
        for f in wenv['SRC_LIST']:
            if not os.path.exists(f):
                print '\033[91m Cannot find file ' + f + '! \033[0m'
                sys.exit(0)
        print '\033[92m start compiling...\033[0m'
        for f in wenv['SRC_LIST']:
            tf = os.path.basename(f)
            outfp = os.path.join(env['OUTPUT_DIR'], tf[0 : tf.rfind('.')] + '.bc')
            cmd = generate_compile_cmd_with_single_input_and_output(env, f, outfp)
            print cmd
            execute_cmd(cmd)
            tmp_outputs.append(outfp)
        return tmp_outputs
    pass

def link_to_one_bc(env, tmp_outputs):
    cmd = os.path.join(env['LLVM_BIN_DIR'], env['LLVM_LINKER']) + ' '
    for item in env['LINK_FLAGS']:
        cmd += item + ' '

    #for item in env['LINK_DIRECTORIES']:
    #    if len(item) == 0:
    #        continue
    #    cmd += '-L' + item + ' '

    #for item in env['LINK_LIBS']:
    #    if len(item) == 0:
    #        continue
    #    cmd +='-l' + item + ' '

    for item in tmp_outputs:
        cmd += item + ' '

    cmd += '-o ' + os.path.join(env['OUTPUT_DIR'], env['TARGET'])
    print '\033[92m start linking... \033[0m'
    print cmd
    execute_cmd(cmd)

def check_env(env):
    #1. check LLVM_BIN_DIR
    #print env
    fp1 = os.path.join(env['LLVM_BIN_DIR'], env['CPP_CLANG'])
    if not os.path.exists(fp1):
        print '\033[91m Cannot find ' + fp1 + '\033[0m'
        sys.exit(-1)



def llbc(env):
    wenv = get_whole_environment(env)

    check_env(wenv)
    tmp_outputs = compile_to_bc_for_one_file(wenv)
    link_to_one_bc(wenv, tmp_outputs)
    pass

def clean(env):
    wenv = get_whole_environment(env)
    tmp_outputs = []
    for f in wenv['SRC_LIST']:
        tf = os.path.basename(f)
        outfp = os.path.join(wenv['OUTPUT_DIR'], tf[0 : tf.rfind('.')] + '.bc')
        cmd = generate_compile_cmd_with_single_input_and_output(wenv, f, outfp)
        tmp_outputs.append(outfp)
    ot = os.path.join(wenv['OUTPUT_DIR'], wenv['TARGET'])
    tmp_outputs.append(ot)
    for item in tmp_outputs:
        print 'rm ' + item
        os.remove(item)

def get_platform_shared_lib_suffix():
    sysstr = platform.system()
    if sysstr == 'Windows':
        return '.dll'
    elif sysstr == 'Darwin':
        return '.dylib'
    elif sysstr == 'Linux':
        return '.so'
    else:
        print '\033[91m Unsupported platform ' + sysstr + '\033[0m'
        sys.exit(-1)

def get_platform_shared_lib_prefix():
    sysstr = platform.system()
    if sysstr == 'Windows':
        return ''
    elif sysstr == 'Darwin' or sysstr == 'Linux':
        return 'lib'
    else:
        print '\033[91m Unsupported platform ' + sysstr + '\033[0m'
        sys.exit(-1)


def get_shared_lib(folder, lib):
    l = get_platform_shared_lib_prefix() + lib + get_platform_shared_lib_suffix()
    fp = os.path.join(folder, l)
    if os.path.exists(fp):
        return fp
    else:
        return ''

def run(env):
    wenv = get_whole_environment(env)
    ot = os.path.join(wenv['OUTPUT_DIR'], wenv['TARGET'])
    lib_path = []
    found_lib = []
    for item in wenv['LINK_DIRECTORIES']:
        for l in wenv['LINK_LIBS']:
            ln = get_shared_lib(item, l)
            if len(ln) != 0:
                lib_path.append(ln)
                found_lib.append(l)
    if len(found_lib) != len(wenv['LINK_LIBS']):
        for lib in [x for x in wenv['LINK_LIBS'] if not x in found_lib]:
            print '\033[91m Cannot find lib ' + lib + '\033[0m'
        sys.exit(-1)





    if not os.path.exists(ot):
        print '\033[91m Cannot find target ' + ot + '\033[0m'
        sys.exit(-1)
    cmd = os.path.join(wenv['LLVM_BIN_DIR'], wenv['LLVM_EXECUTOR']) + ' '

    for lp in lib_path:
        cmd += '-load ' + lp + ' '
    cmd += ot
    print cmd
    execute_cmd(cmd)


def parse_args():
    parser = argparse.ArgumentParser(description = "LLVM Bytecode tool wrapper, by Athrun Arthur!")
    parser.add_argument('-gen', action='store_true', help='Generate LLVM Bytecode')
    parser.add_argument('-clean', action='store_true', help='Clean all generated files')
    parser.add_argument('-run', action='store_true', help = 'Run the generated target')
    args = parser.parse_args()
    if not (args.gen or args.clean or args.run):
        parser.print_help()
        parser.error('Action required! Please input -gen, -clean, or -run!')
    return args

if __name__ == '__main__':
    args = parse_args()
    if args.gen:
        llbc(Env)
    elif args.clean:
        clean(Env)
    elif args.run:
        run(Env)
