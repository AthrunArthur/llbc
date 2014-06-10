A Python script to utilize LLVM bytecode, include building, cleaning, and running LLVM bytecode.

###1. Why llbc?
The key motivation for llbc is I cannot using existing building tools, like CMake, scons and makefile, to utilize LLVM bytecode. Although building LLVM bytecode is quite similar to compiling native C++ code, linking and running are quite different. In C++, we need to specify the linking directories and linking libraries. But we don't do that in *llvm-link*. Instead, we specify the linking libraries when running the target, using *-load=XX*.

Thus, I feel it's quite not consistency with using CMake or makefile. So I write this script to generate LLVM bytecode and to run it.

###2. How to use it?
First of all, it's a python script, and that means you need to write python code.

Second, you need to write an *Env* class in llbc.py, like this:

         class Env:
              LLVM_BIN_DIR = '/Users/xuepengfan/tools/llvm-build/bin/'
              SRC_LIST = [ os.path.join(os.getcwd(), x) for x in srcs]
              TARGET = 'bq_llvm'
              INCLUDE_DIRECTORIES = [os.path.join(os.getcwd(), '../ff/include/')]
              CXX_FLAGS=['-DUSING_FF_NONBLOCKING_QUEUE', '-DNDEBUG']
              LINK_DIRECTORIES = [os.path.join(os.getcwd(), '../bin/')]
              LINK_LIBS = ['boost_program_options', 'ff', 'pthread']

Third, run the python script!

        python llbc.py -gen  #This will build your project!
        python llbc.py -clean  #This will remove all generated files!
        python llbc.py -run   #This will run the targeted bin with llvm!

###Have Fun!
