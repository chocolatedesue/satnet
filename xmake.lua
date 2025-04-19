-- xmake.lua

-- 设置项目元数据 (可选但推荐)
set_project("satnet")
set_version("1.0.0")
-- add_rules("mode.debug")
add_requires("libomp", {optional = true})
-- add_requires("openmp")

-- add_rules("mode.releasedbg")

-- set_defaultmode("releasedbg")

target("satnet")
    -- 设置目标类型为二进制可执行文件
    
    set_kind("binary")
    
    
    set_languages("cxx20")

    set_toolset("cxx", "clang++-21") -- 设置编译器为 clang 21
    set_toolset("cc", "clang-21")   -- 设置 C 编译器为 clang 21

    -- 添加 'src' 目录下的所有 .cpp 文件作为源文件
    -- 如果 'src' 目录下还有子目录，且其中包含需要编译的 .cpp 文件，
    -- 建议使用递归模式 "src/**.cpp"
    -- add_files("src/**.cpp")
    -- 如果确定只有 src 根目录下的 cpp 文件，则 "src/*.cpp" 即可
    add_files("src/*.cpp")

    -- 添加 'include' 目录到头文件搜索路径
    -- 编译器会在此目录下查找 #include 指令引用的头文件
    add_includedirs("include")


    add_packages("libomp")

    set_optimize("faster")

    -- 添加编译标志
    add_cxflags("-fopenmp")        -- 对 C 和 C++ 文件都生效
--     add_cxxflags("-stdlib=libc++") -- 只对 C++ 文件生效，确保使用 libc++
    

    -- 添加链接标志
    add_ldflags("-fopenmp") -- 链接 OpenMP 和 libc++

    set_default(true)


target("satnet-debug")
    -- 设置目标类型为二进制可执行文件
    set_kind("binary")
    add_rules("mode.debug")
    set_languages("cxx20")

    set_toolset("cxx", "clang++-21") -- 设置编译器为 clang 21
    set_toolset("cc", "clang-21")   -- 设置 C 编译器为 clang 21

    -- 添加 'src' 目录下的所有 .cpp 文件作为源文件
    -- 如果 'src' 目录下还有子目录，且其中包含需要编译的 .cpp 文件，
    -- 建议使用递归模式 "src/**.cpp"
    -- add_files("src/**.cpp")
    -- 如果确定只有 src 根目录下的 cpp 文件，则 "src/*.cpp" 即可
    add_files("src/*.cpp")

    -- 添加 'include' 目录到头文件搜索路径
    -- 编译器会在此目录下查找 #include 指令引用的头文件
    add_includedirs("include")


    add_packages("libomp")


    -- 添加编译标志
    add_cxflags("-fopenmp")        -- 对 C 和 C++ 文件都生效
--     add_cxxflags("-stdlib=libc++") -- 只对 C++ 文件生效，确保使用 libc++
    

    -- 添加链接标志
    add_ldflags("-fopenmp") -- 链接 OpenMP 和 libc++

    -- set_default(true)