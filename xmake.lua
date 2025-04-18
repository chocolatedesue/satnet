-- xmake.lua

-- 设置项目元数据 (可选但推荐)
set_project("satnet")
set_version("1.0.0")
add_rules("mode.debug")


target("satnet")
    -- 设置目标类型为二进制可执行文件
    set_kind("binary")

    -- 设置此目标的 C++ 语言标准
    -- 放在 target 内更清晰地表明此特定目标的要求
    set_languages("cxx17")

    -- 添加 'src' 目录下的所有 .cpp 文件作为源文件
    -- 如果 'src' 目录下还有子目录，且其中包含需要编译的 .cpp 文件，
    -- 建议使用递归模式 "src/**.cpp"
    -- add_files("src/**.cpp")
    -- 如果确定只有 src 根目录下的 cpp 文件，则 "src/*.cpp" 即可
    add_files("src/*.cpp")

    -- 添加 'include' 目录到头文件搜索路径
    -- 编译器会在此目录下查找 #include 指令引用的头文件
    add_includedirs("include")

    add_cxflags("-fopenmp") -- 对 C 和 C++ 文件都生效
            -- add_cxxflags("-fopenmp") -- 只对 C++ 文件生效 (如果 cxflags 已加，这个通常不用重复)

            -- 添加链接标志
    add_ldflags("-fopenmp")

    -- [[ 可选: 添加依赖 ]]
    -- 如果你的项目依赖外部库（例如通过 xmake 包管理器安装的库）
    -- 需要先在全局或 target 作用域 `add_requires("libname")`
    -- 然后在 target 内 `add_packages("libname")` 来链接
    -- 例如，依赖 fmtlib:
    -- 在 target 外或全局: add_requires("fmt")
    -- 在 target 内: add_packages("fmt")

    -- [[ 可选: 定义宏 ]]
    -- 例如，为 Debug 模式定义 DEBUG 宏
    -- if is_mode("debug") then
    --     add_defines("DEBUG")
    -- end

    -- 将此目标设置为默认目标
    -- 运行 'xmake' 或 'xmake build' 时会默认构建此目标
    set_default(true)
