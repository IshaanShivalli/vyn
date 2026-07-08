#include "filesystem.h"

#include <filesystem>

namespace fs = std::filesystem;

bool FileSystem::createFolder(const std::string& path)
{
    return fs::create_directories(path);
}

bool FileSystem::removeFolder(const std::string& path)
{
    return fs::remove_all(path);
}

bool FileSystem::copy(const std::string& from,
                      const std::string& to)
{
    fs::copy(from,
             to,
             fs::copy_options::recursive |
             fs::copy_options::overwrite_existing);

    return true;
}

bool FileSystem::exists(const std::string& path)
{
    return fs::exists(path);
}