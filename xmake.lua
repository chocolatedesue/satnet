-- xmake.lua

-- 设置项目元数据 (可选但推荐)
set_project("satnet")
set_version("1.0.0")
add_rules("mode.debug")


-- 定义主可执行文件目标
target("satnet")
    -- 设置目标类型为二进制可执行文件
    set_kind("binary")

    -- 设置 C++ 语言标准 (例如: "cxx11", "cxx14", "cxx17", "cxx20")
    set_languages("cxx17")

    -- 添加 'src' 目录下的所有 .cpp 文件作为源文件
    add_files("src/*.cpp")

    -- 添加 'include' 目录到头文件搜索路径
    -- 这样编译器在处理 #include "satnet/space.hpp" 时，
    -- 会在 include/ 目录下查找 satnet/space.hpp
    add_includedirs("include")
    
    -- (可选) 将此目标设置为默认目标
    -- 这样运行 'xmake' 命令时会默认构建此目标
    set_default(true)