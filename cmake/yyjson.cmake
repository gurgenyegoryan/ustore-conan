FetchContent_Declare(
    yyjson
    GIT_REPOSITORY https://github.com/ibireme/yyjson
    GIT_TAG 0.5.1
)
FetchContent_MakeAvailable(yyjson)
include_directories(${yyjson_SOURCE_DIR}/include)